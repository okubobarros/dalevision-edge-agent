param(

  [string]$InstallDir = "",

  [string]$TaskName = "DaleVision Edge Agent",

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



function Resolve-AgentBatPath {

  param(

    [string]$InstallDir,

    [string]$ScriptRoot

  )



  if ([string]::IsNullOrWhiteSpace($InstallDir)) {

    $InstallDir = $ScriptRoot

  }



  $candidates = @(

    (Join-Path $InstallDir "03_INICIAR.bat"),

    (Join-Path $InstallDir "Start_Agent.bat"),

    (Join-Path $InstallDir "Start_DaleVision_Agent.bat"),

    (Join-Path $InstallDir "01_INICIAR_DALEVISION.bat"),

    (Join-Path $InstallDir "01 - Iniciar Agent.bat")

  )



  foreach ($candidate in $candidates) {

    if (Test-Path $candidate) {

      return $candidate

    }

  }



  return $candidates[0]

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

    (Join-Path $InstallDir "DaleVision Edge Agent.exe"),

    (Join-Path $InstallDir "dalevision-edge-agent.exe")

  )



  foreach ($candidate in $candidates) {

    if (Test-Path $candidate) {

      return $candidate

    }

  }



  return $candidates[0]

}



function Get-TaskCommand {

  param(

    [string]$EntryPoint

  )



  $absolute = (Resolve-Path $EntryPoint).Path

  return "`"$absolute`""

}



function Invoke-InstallService {

  param(

    [string]$InstallDir = "",

    [string]$TaskName = "DaleVision Edge Agent",

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

    $agentBat = Resolve-AgentBatPath -InstallDir $installRoot -ScriptRoot $PSScriptRoot



    $entryPoint = $null

    if (Test-Path $agentExe) {

      $entryPoint = $agentExe

    } elseif (Test-Path $agentBat) {

      $entryPoint = $agentBat

    }



    if (-not $entryPoint) {

      Write-Log "ERRO: arquivo nao encontrado: $agentExe"

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



    $stdout = Join-Path $logDir "stdout.log"

    $stderr = Join-Path $logDir "stderr.log"



    $taskCmd = Get-TaskCommand -EntryPoint $entryPoint

    $cmdArgs = "/c $taskCmd >> `"$stdout`" 2>> `"$stderr`""



    Write-Log "Instalando Task Scheduler '$TaskName' em $installRoot"

    Write-Log "Comando: $taskCmd"



    if ($WhatIf) {

      Write-Log "WhatIf: nenhuma alteracao aplicada."

      exit 0

    }



    $action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument $cmdArgs -WorkingDirectory $installRoot

    $triggers = @(

      (New-ScheduledTaskTrigger -AtStartup),

      (New-ScheduledTaskTrigger -AtLogOn)

    )

    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew

    $principalTask = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest



    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $triggers -Settings $settings -Principal $principalTask -Force | Out-Null



    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

    if (-not $task) {

      throw "Falha ao criar a tarefa agendada."

    }



    Write-Log "Service installed OK"

    Write-Log "Para remover: schtasks /Delete /TN `"$TaskName`" /F"

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

