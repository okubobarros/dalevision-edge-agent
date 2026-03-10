param(
  [string]$InstallDir = (Split-Path -Parent $PSScriptRoot),
  [string]$TaskName = "DaleVisionEdgeAgent",
  [string]$StartupTaskName = "DaleVisionEdgeAgentStartup",
  [string]$UpdateTaskName = "DaleVisionEdgeAgentUpdate",
  [switch]$EnableStartupTask,
  [switch]$WhatIf
)

$ErrorActionPreference = "Stop"
$script:schtasksExe = $null

function Write-Log {
  param([string]$Message)
  $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  $line = "$timestamp $Message"
  try {
    Add-Content -Path $script:LogPath -Value $line
  } catch {
    Write-Host "(log write failed: $($_.Exception.Message))"
  }
  Write-Host $Message
}

function Resolve-InstallRoot {
  param(
    [string]$InstallDir,
    [string]$ScriptRoot
  )

  if ($null -eq $InstallDir) { $InstallDir = "" }
  $InstallDir = $InstallDir.Trim().Trim('"')
  $defaultRoot = Split-Path -Parent $ScriptRoot
  if ([string]::IsNullOrWhiteSpace($InstallDir)) {
    return (Resolve-Path $defaultRoot).Path
  }

  $InstallDir = $InstallDir.Trim().TrimEnd("\", "/").Trim()
  if (Test-Path $InstallDir) {
    $resolved = (Resolve-Path $InstallDir).Path
    $trimmed = $resolved.TrimEnd("\", "/")
    $leaf = Split-Path -Leaf $trimmed
    if ($leaf -ieq "scripts") {
      return (Resolve-Path (Split-Path -Parent $trimmed)).Path
    }
    return $trimmed
  }

  return $InstallDir
}

function Read-EnvFile {
  param([string]$Path)
  $result = @{}
  if (-not (Test-Path $Path)) {
    return $result
  }
  Get-Content -Path $Path | ForEach-Object {
    $line = $_.Trim()
    if ($line -eq "" -or $line.StartsWith("#")) {
      return
    }
    $parts = $line.Split("=", 2)
    if ($parts.Count -eq 2) {
      $key = $parts[0].Trim()
      $value = $parts[1].Trim()
      if ($key -ne "") {
        $result[$key] = $value
      }
    }
  }
  return $result
}

function Invoke-Schtasks {
  param(
    [Parameter(Mandatory = $true)]
    [string[]]$SchtasksArgs,
    [switch]$AllowNotFound
  )

  if ($null -eq $SchtasksArgs -or $SchtasksArgs.Count -eq 0) {
    throw "BUG: Invoke-Schtasks chamado com SchtasksArgs vazio"
  }

  Write-Log ("SCHTASKS_ARGS=" + ($SchtasksArgs -join " "))

  $out = & $script:schtasksExe @SchtasksArgs 2>&1
  $code = $LASTEXITCODE

  Write-Log ("SCHTASKS_EXITCODE=" + $code)
  Write-Log ("SCHTASKS_OUTPUT=" + (($out | Out-String).Trim()))

  if ($code -ne 0) {
    $text = ($out | Out-String)
    $isQuery = ($SchtasksArgs.Count -ge 1 -and $SchtasksArgs[0] -ieq "/Query")
    if ($AllowNotFound -and $isQuery) {
      Write-Log "SCHTASKS_NOTFOUND_OK"
      return @{ Code = $code; Output = $text; NotFound = $true }
    }
    throw ("SCHTASKS_FAILED ExitCode=$code Output=$text")
  }

  return @{ Code = $code; Output = ($out | Out-String); NotFound = $false }
}

function Resolve-AgentExePath {
  param(
    [string]$InstallDir,
    [string]$ScriptRoot
  )

  if ([string]::IsNullOrWhiteSpace($InstallDir)) {
    $InstallDir = Split-Path -Parent $ScriptRoot
  }

  $candidates = @(
    (Join-Path $InstallDir "dalevision-edge-agent.exe"),
    (Join-Path $InstallDir "DaleVision Edge Agent.exe"),
    (Join-Path $InstallDir "scripts\dalevision-edge-agent.exe")
  )

  foreach ($candidate in $candidates) {
    if (Test-Path $candidate) {
      return $candidate
    }
  }

  return $candidates
}

function Resolve-AgentTaskLauncherPath {
  param(
    [string]$InstallRoot,
    [string]$AgentExePath
  )

  $installRootResolved = (Resolve-Path $InstallRoot).Path
  $vbsPath = Join-Path $installRootResolved "run_agent.vbs"
  if (Test-Path $vbsPath) {
    return (Resolve-Path $vbsPath).Path
  }

  $runCmdPath = Join-Path $installRootResolved "run_agent.cmd"
  if (-not (Test-Path $runCmdPath)) {
    throw "launcher nao encontrado (run_agent.vbs/run_agent.cmd): $installRootResolved"
  }
  return (Resolve-Path $runCmdPath).Path
}

function Get-AgentTaskCommand {
  param(
    [string]$LauncherPath
  )

  return "`"$LauncherPath`""
}

function Get-UpdateIntervalHours {
  param(
    [hashtable]$EnvVars
  )

  $raw = $EnvVars["UPDATE_INTERVAL_SECONDS"]
  $intervalSeconds = 21600
  if (-not [string]::IsNullOrWhiteSpace($raw)) {
    $parsed = 0
    if ([int]::TryParse($raw, [ref]$parsed) -and $parsed -gt 0) {
      $intervalSeconds = $parsed
    }
  }
  $hours = [Math]::Ceiling($intervalSeconds / 3600.0)
  if ($hours -lt 1) { $hours = 1 }
  return [int]$hours
}

function Get-UpdateTaskCommand {
  param(
    [string]$InstallRoot
  )
  $updateScript = Join-Path $InstallRoot "scripts\update.ps1"
  return "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$updateScript`" -InstallDir `"$InstallRoot`""
}

function Get-CurrentUserId {
  if (-not [string]::IsNullOrWhiteSpace($env:USERDOMAIN)) {
    return "$($env:USERDOMAIN)\$($env:USERNAME)"
  }
  return $env:USERNAME
}

function Get-StartupTaskEnabled {
  param(
    [hashtable]$EnvVars,
    [bool]$ExplicitEnable
  )

  if ($ExplicitEnable) {
    return $true
  }

  foreach ($key in @("STARTUP_TASK_ENABLED", "EDGE_STARTUP_TASK_ENABLED")) {
    $raw = $EnvVars[$key]
    if ([string]::IsNullOrWhiteSpace($raw)) {
      continue
    }
    return ($raw.Trim() -eq "1")
  }

  return $false
}

function Invoke-InstallService {
  param(
    [string]$InstallDir = $PSScriptRoot,
    [string]$TaskName = "DaleVisionEdgeAgent",
    [string]$StartupTaskName = "DaleVisionEdgeAgentStartup",
    [string]$UpdateTaskName = "DaleVisionEdgeAgentUpdate",
    [switch]$EnableStartupTask,
    [switch]$WhatIf
  )

  $installRoot = Resolve-InstallRoot -InstallDir $InstallDir -ScriptRoot $PSScriptRoot

  $logDir = Join-Path $installRoot "logs"
  if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
  }
  $script:LogPath = Join-Path $logDir "service_install.ps1.log"
  $installLog = $script:LogPath
  $self = $MyInvocation.MyCommand.Path
  if (-not [string]::IsNullOrWhiteSpace($self)) {
    Write-Log "SELF_PATH=$self"
    try {
      $selfHash = (Get-FileHash -Algorithm SHA256 -Path $self).Hash
      Write-Log "SELF_SHA256=$selfHash"
    } catch {
      Write-Log "SELF_SHA256=ERROR $($_.Exception.Message)"
    }
  }

  try {
    $currentUser = Get-CurrentUserId
    Write-Log "RUN_AS_USER=$currentUser"

    $agentExeCandidates = Resolve-AgentExePath -InstallDir $installRoot -ScriptRoot $PSScriptRoot
    $agentExe = $agentExeCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

    if (-not $agentExe) {
      $list = $agentExeCandidates -join "; "
      Write-Log "ERRO: executavel nao encontrado. Procurado em: $list"
      if (Test-Path $installRoot) {
        $files = Get-ChildItem -Path $installRoot -File | Select-Object -ExpandProperty Name
        if ($files) {
          Write-Log "Arquivos encontrados em ${installRoot}:"
          foreach ($file in $files) {
            Write-Log " - $file"
          }
        } else {
          Write-Log "Nenhum arquivo encontrado em $installRoot."
        }
      } else {
        Write-Log "Pasta nao encontrada: $installRoot"
      }
      Write-Log "ATENCAO: esta janela aguarda Enter para sair."
      Write-Log "Pressione Enter para sair."
      Read-Host | Out-Null
      exit 1
    }

    # Executa oculto via PowerShell e grava logs em logs\agent.log.
    $launcherPath = Resolve-AgentTaskLauncherPath -InstallRoot $installRoot -AgentExePath $agentExe
    $taskCmd = Get-AgentTaskCommand -LauncherPath $launcherPath

    $psExePath = Join-Path $env:WINDIR "System32\\WindowsPowerShell\\v1.0\\powershell.exe"
    Write-Log "EXISTS_psExe=$(Test-Path $psExePath)"
    $startPs1Check = Join-Path $installRoot "scripts\\internal\\Start_DaleVision_Agent.ps1"
    Write-Log "EXISTS_startPs1=$(Test-Path $startPs1Check)"

    $script:schtasksExe = (Resolve-Path (Join-Path $env:WINDIR "System32\\schtasks.exe")).Path
    Write-Log "SCHTASKS_PATH=$script:schtasksExe"
    Write-Log "EXISTS_schtasks=$(Test-Path $script:schtasksExe)"

    $envPath = Join-Path $installRoot ".env"
    $envVars = Read-EnvFile -Path $envPath
    $startupTaskEnabled = Get-StartupTaskEnabled -EnvVars $envVars -ExplicitEnable:$EnableStartupTask

    $installInfo = @(
      "installRoot=$installRoot",
      "exeResolved=$agentExe",
      "taskName=$TaskName",
      "startupTaskName=$StartupTaskName",
      "startupTaskEnabled=$startupTaskEnabled",
      "launcherPath=$launcherPath",
      "command=$taskCmd"
    )
    foreach ($line in $installInfo) {
      Write-Host $line
      Add-Content -Path $installLog -Value $line
    }

    Write-Log "Instalando Task Scheduler '$TaskName' em $installRoot"
    Write-Log "Comando: $taskCmd"

    if ($WhatIf) {
      Write-Log "WhatIf: nenhuma alteracao aplicada."
      exit 0
    }

    $resultLabel = "INSTALLED"
    Write-Log "TASK_EXISTS_CHECK: querying..."
    $taskExists = $false

    $tn = $TaskName.Replace('"', '')
    $cmd = $env:ComSpec
    if ([string]::IsNullOrWhiteSpace($cmd)) {
      $cmd = "$env:WINDIR\\System32\\cmd.exe"
    }

    $oldEap = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $queryOut = & $cmd /c "`"$script:schtasksExe`" /Query /TN `"$tn`"" 2>&1
    $queryCode = $LASTEXITCODE
    $ErrorActionPreference = $oldEap

    Write-Log "TASK_EXISTS_QUERY_EXITCODE=$queryCode"
    Write-Log ("TASK_EXISTS_QUERY_OUTPUT=" + (($queryOut | Out-String).Trim()))

    if ($queryCode -eq 0) {
      $taskExists = $true
      Write-Log "TASK_EXISTS=true"
      Write-Log "Tarefa existente encontrada. Sera atualizada."
      $resultLabel = "UPDATED"
    } else {
      Write-Log "TASK_EXISTS=false (expected on first install). Continuing to /Create."
    }

    $taskArgs = @(
      "/Create",
      "/F",
      "/SC", "ONLOGON",
      "/RU", $currentUser,
      "/RL", "LIMITED",
      "/TN", $TaskName,
      "/TR", $taskCmd
    )
    Write-Log "ABOUT_TO_CREATE_TASK"
    $createCode = 0
    $createOutput = ""
    $startupCreateCode = 0
    $startupCreateOutput = ""
    $usedScheduledTasks = $false
    try {
      if (Get-Module -ListAvailable -Name ScheduledTasks) {
        $usedScheduledTasks = $true
        $action = New-ScheduledTaskAction -Execute $launcherPath
        $logonTrigger = New-ScheduledTaskTrigger -AtLogOn -User $currentUser
        $logonPrincipal = New-ScheduledTaskPrincipal -UserId $currentUser -LogonType Interactive -RunLevel Limited
        $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
        $logonTask = New-ScheduledTask -Action $action -Trigger $logonTrigger -Principal $logonPrincipal -Settings $settings
        $createOutput = (Register-ScheduledTask -TaskName $TaskName -InputObject $logonTask -Force | Out-String)
        if ($startupTaskEnabled) {
          $startupTrigger = New-ScheduledTaskTrigger -AtStartup
          $startupPrincipal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
          $startupTask = New-ScheduledTask -Action $action -Trigger $startupTrigger -Principal $startupPrincipal -Settings $settings
          $startupCreateOutput = (Register-ScheduledTask -TaskName $StartupTaskName -InputObject $startupTask -Force | Out-String)
        } else {
          $startupCreateOutput = "SKIPPED startup task disabled"
        }
      } else {
        $createOutput = "ScheduledTasks module not available. Falling back to schtasks."
        $createResult = Invoke-Schtasks -SchtasksArgs $taskArgs
        $createCode = $createResult.Code
        $createOutput = ($createOutput + "`n" + ($createResult.Output | Out-String))
        if ($startupTaskEnabled) {
          $startupTaskArgs = @(
            "/Create",
            "/F",
            "/SC", "ONSTART",
            "/RU", "SYSTEM",
            "/RL", "HIGHEST",
            "/TN", $StartupTaskName,
            "/TR", $taskCmd
          )
          $startupCreateResult = Invoke-Schtasks -SchtasksArgs $startupTaskArgs
          $startupCreateCode = $startupCreateResult.Code
          $startupCreateOutput = ($startupCreateResult.Output | Out-String)
        } else {
          $startupCreateOutput = "SKIPPED startup task disabled"
        }
      }
    } catch {
      $createCode = 1
      $startupCreateCode = 0
      $createOutput = $_.Exception.ToString()
      if ($startupTaskEnabled) {
        $startupCreateCode = 1
        $startupCreateOutput = $_.Exception.ToString()
      } else {
        $startupCreateOutput = "SKIPPED startup task disabled"
      }
      $errorText = $_.Exception.Message
      if ($errorText -match "Acesso negado|Access is denied") {
        Write-Log "PERMISSION_DENIED: falha ao criar task via ScheduledTasks. Tentando fallback com schtasks.exe."
        try {
          $createResult = Invoke-Schtasks -SchtasksArgs $taskArgs
          $createCode = $createResult.Code
          $createOutput = ($createResult.Output | Out-String)
          if ($startupTaskEnabled) {
            $startupTaskArgs = @(
              "/Create",
              "/F",
              "/SC", "ONSTART",
              "/RU", "SYSTEM",
              "/RL", "HIGHEST",
              "/TN", $StartupTaskName,
              "/TR", $taskCmd
            )
            $startupCreateResult = Invoke-Schtasks -SchtasksArgs $startupTaskArgs
            $startupCreateCode = $startupCreateResult.Code
            $startupCreateOutput = ($startupCreateResult.Output | Out-String)
          } else {
            $startupCreateOutput = "SKIPPED startup task disabled"
          }
        } catch {
          $createCode = 1
          if ($startupTaskEnabled) { $startupCreateCode = 1 }
          $createOutput = $_.Exception.ToString()
          if ($startupTaskEnabled) {
            $startupCreateOutput = $_.Exception.ToString()
          } else {
            $startupCreateOutput = "SKIPPED startup task disabled"
          }
          Write-Log "PERMISSION_HINT: se a task existir com outro usuario, delete com admin: schtasks /Delete /TN `"$TaskName`" /F"
        }
      }
    }

    Write-Log ("CREATE_EXITCODE=" + $createCode)
    Write-Log ("CREATE_OUTPUT=" + (($createOutput | Out-String).Trim()))
    Write-Log ("STARTUP_CREATE_EXITCODE=" + $startupCreateCode)
    Write-Log ("STARTUP_CREATE_OUTPUT=" + (($startupCreateOutput | Out-String).Trim()))
    if ($createCode -ne 0 -or ($startupTaskEnabled -and $startupCreateCode -ne 0)) {
      throw "Falha ao criar as tarefas agendadas. logon=$createCode startup=$startupCreateCode"
    }

    try {
      $taskObj = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
      $actionObj = $taskObj.Actions | Select-Object -First 1
      if ($actionObj) {
        Write-Log ("TASK_ACTION=" + $actionObj.Execute)
        Write-Log ("TASK_ARGUMENT=" + $actionObj.Arguments)
      }
      if ($startupTaskEnabled) {
        $startupTaskObj = Get-ScheduledTask -TaskName $StartupTaskName -ErrorAction Stop
        $startupActionObj = $startupTaskObj.Actions | Select-Object -First 1
        if ($startupActionObj) {
          Write-Log ("STARTUP_TASK_ACTION=" + $startupActionObj.Execute)
          Write-Log ("STARTUP_TASK_ARGUMENT=" + $startupActionObj.Arguments)
        }
      } else {
        Write-Log "STARTUP_TASK=DISABLED"
      }
    } catch {
      throw "Tarefa nao encontrada apos criacao. Detalhes: $($_.Exception.Message)"
    }

    $updateScript = Join-Path $installRoot "scripts\update.ps1"
    $autoEnabled = ($envVars["AUTO_UPDATE_ENABLED"] -eq "1")
    $repo = $envVars["UPDATE_GITHUB_REPO"]

    if (-not (Test-Path $updateScript)) {
      Write-Log "UPDATE: update.ps1 nao encontrado. Pulando tarefa de update."
    } elseif (-not $autoEnabled -or [string]::IsNullOrWhiteSpace($repo)) {
      Write-Log "UPDATE: auto-update desabilitado (AUTO_UPDATE_ENABLED=1 e UPDATE_GITHUB_REPO)."
      # Nao consulta/remove task de update quando auto-update esta desabilitado.
    } else {
      $intervalHours = Get-UpdateIntervalHours -EnvVars $envVars
      $updateCmd = Get-UpdateTaskCommand -InstallRoot $installRoot

      $updateArgs = @(
        "/Create",
        "/F",
        "/SC", "HOURLY",
        "/MO", $intervalHours,
        "/RU", $currentUser,
        "/RL", "LIMITED",
        "/TN", $UpdateTaskName,
        "/TR", $updateCmd
      )

      Write-Log "UPDATE: criando tarefa '$UpdateTaskName' (a cada ${intervalHours}h)"
      Invoke-Schtasks -SchtasksArgs $updateArgs | Out-Null
    }

    Write-Log "Servico instalado com sucesso."
    Write-Log "RESULT: $resultLabel"
    Write-Log "Task: $TaskName"
    Write-Log "Para remover: execute uninstall-service.ps1 ou use: schtasks /Delete /TN `"$TaskName`" /F"
    Write-Log "Para checar status: schtasks /Query /TN `"$TaskName`" /V /FO LIST"
  } catch {
    Write-Log "ERRO: $($_.Exception.Message)"
    Write-Log "ATENCAO: esta janela aguarda Enter para sair."
    Write-Log "Pressione Enter para sair."
    Read-Host | Out-Null
    exit 1
  }
}

if ($MyInvocation.InvocationName -ne ".") {
  Invoke-InstallService @PSBoundParameters
}
