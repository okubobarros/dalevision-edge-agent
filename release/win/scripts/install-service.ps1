param(
  [string]$InstallDir = $PSScriptRoot,
  [string]$TaskName = "DaleVisionEdgeAgent",
  [string]$UpdateTaskName = "DaleVisionEdgeAgentUpdate",
  [switch]$WhatIf
)

$ErrorActionPreference = "Stop"

function Write-Log {
  param([string]$Message)
  $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  $line = "$timestamp $Message"
  Add-Content -Path $script:LogPath -Value $line
  Write-Host $Message
}

function Resolve-InstallRoot {
  param(
    [string]$InstallDir,
    [string]$ScriptRoot
  )

  if ([string]::IsNullOrWhiteSpace($InstallDir)) {
    return (Resolve-Path $ScriptRoot).Path
  }

  if (Test-Path $InstallDir) {
    return (Resolve-Path $InstallDir).Path
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

function Resolve-AgentExePath {
  param(
    [string]$InstallDir,
    [string]$ScriptRoot
  )

  if ([string]::IsNullOrWhiteSpace($InstallDir)) {
    $InstallDir = $ScriptRoot
  }

  $candidates = @(
    (Join-Path $InstallDir "dalevision-edge-agent.exe"),
    (Join-Path $InstallDir "DaleVision Edge Agent.exe")
  )

  foreach ($candidate in $candidates) {
    if (Test-Path $candidate) {
      return $candidate
    }
  }

  return $candidates[0]
}

function Get-AgentTaskCommand {
  param(
    [string]$InstallRoot,
    [string]$AgentExePath
  )

  $startPs1 = Join-Path $InstallRoot "scripts\internal\Start_DaleVision_Agent.ps1"
  if (Test-Path $startPs1) {
    return "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$startPs1`" -InstallDir `"$InstallRoot`""
  }

  $installRootResolved = (Resolve-Path $InstallRoot).Path
  $exeResolved = (Resolve-Path $AgentExePath).Path
  $logPath = Join-Path $installRootResolved "logs\agent.log"
  $inner = "Set-Location -Path `"$installRootResolved`"; `"$exeResolved`" *>> `"$logPath`""
  return "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command `"$inner`""
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

function Invoke-InstallService {
  param(
    [string]$InstallDir = $PSScriptRoot,
    [string]$TaskName = "DaleVisionEdgeAgent",
    [string]$UpdateTaskName = "DaleVisionEdgeAgentUpdate",
    [switch]$WhatIf
  )

  $installRoot = Resolve-InstallRoot -InstallDir $InstallDir -ScriptRoot $PSScriptRoot

  $logDir = Join-Path $installRoot "logs"
  if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
  }
  $script:LogPath = Join-Path $logDir "service_install.log"

  try {
    $principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
      Write-Log "ERRO: permissao insuficiente."
      Write-Log "Execute este script como Administrador."
      Write-Log "Pressione Enter para sair."
      Read-Host | Out-Null
      exit 1
    }

    $agentExe = Resolve-AgentExePath -InstallDir $installRoot -ScriptRoot $PSScriptRoot

    if (-not (Test-Path $agentExe)) {
      Write-Log "ERRO: executavel nao encontrado: $agentExe"
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
      Write-Log "Pressione Enter para sair."
      Read-Host | Out-Null
      exit 1
    }

    # Executa oculto via PowerShell e grava logs em logs\agent.log.
    $taskCmd = Get-AgentTaskCommand -InstallRoot $installRoot -AgentExePath $agentExe

    Write-Log "Instalando Task Scheduler '$TaskName' em $installRoot"
    Write-Log "Comando: $taskCmd"

    if ($WhatIf) {
      Write-Log "WhatIf: nenhuma alteracao aplicada."
      exit 0
    }

    $resultLabel = "INSTALLED"
    $existingOutput = & schtasks /Query /TN $TaskName 2>&1
    if ($LASTEXITCODE -eq 0) {
      Write-Log "Tarefa existente encontrada. Sera atualizada."
      $resultLabel = "UPDATED"
    }

    $taskArgs = @(
      "/Create",
      "/F",
      "/SC", "ONSTART",
      "/RU", "SYSTEM",
      "/RL", "HIGHEST",
      "/DELAY", "0000:30",
      "/TN", $TaskName,
      "/TR", $taskCmd
    )

    Write-Log "Criando tarefa..."
    Write-Log ("schtasks " + ($taskArgs -join " "))

    $createOutput = & schtasks @taskArgs 2>&1
    if ($LASTEXITCODE -ne 0) {
      throw "Falha ao criar a tarefa agendada. Detalhes: $createOutput"
    }

    $queryOutput = & schtasks /Query /TN $TaskName 2>&1
    if ($LASTEXITCODE -ne 0) {
      throw "Tarefa nao encontrada apos criacao. Detalhes: $queryOutput"
    }

    $updateScript = Join-Path $installRoot "scripts\update.ps1"
    $envPath = Join-Path $installRoot ".env"
    $envVars = Read-EnvFile -Path $envPath
    $autoEnabled = ($envVars["AUTO_UPDATE_ENABLED"] -eq "1")
    $repo = $envVars["UPDATE_GITHUB_REPO"]

    if (-not (Test-Path $updateScript)) {
      Write-Log "UPDATE: update.ps1 nao encontrado. Pulando tarefa de update."
    } elseif (-not $autoEnabled -or [string]::IsNullOrWhiteSpace($repo)) {
      Write-Log "UPDATE: auto-update desabilitado (AUTO_UPDATE_ENABLED=1 e UPDATE_GITHUB_REPO)."
      $updateExists = & schtasks /Query /TN $UpdateTaskName 2>$null
      if ($LASTEXITCODE -eq 0) {
        Write-Log "UPDATE: removendo tarefa antiga '$UpdateTaskName'."
        & schtasks /Delete /TN $UpdateTaskName /F | Out-Null
      }
    } else {
      $intervalHours = Get-UpdateIntervalHours -EnvVars $envVars
      $updateCmd = Get-UpdateTaskCommand -InstallRoot $installRoot

      $updateArgs = @(
        "/Create",
        "/F",
        "/SC", "HOURLY",
        "/MO", $intervalHours,
        "/RU", "SYSTEM",
        "/RL", "HIGHEST",
        "/TN", $UpdateTaskName,
        "/TR", $updateCmd
      )

      Write-Log "UPDATE: criando tarefa '$UpdateTaskName' (a cada ${intervalHours}h)"
      Write-Log ("schtasks " + ($updateArgs -join " "))
      $updateOutput = & schtasks @updateArgs 2>&1
      if ($LASTEXITCODE -ne 0) {
        throw "Falha ao criar tarefa de update. Detalhes: $updateOutput"
      }
    }

    Write-Log "Servico instalado com sucesso."
    Write-Log "RESULT: $resultLabel"
    Write-Log "Para remover: execute uninstall-service.ps1 ou use: schtasks /Delete /TN `"$TaskName`" /F"
    Write-Log "Para checar status: schtasks /Query /TN `"$TaskName`" /V /FO LIST"
  } catch {
    Write-Log "ERRO: $($_.Exception.Message)"
    Write-Log "Pressione Enter para sair."
    Read-Host | Out-Null
    exit 1
  }
}

if ($MyInvocation.InvocationName -ne ".") {
  Invoke-InstallService @PSBoundParameters
}
