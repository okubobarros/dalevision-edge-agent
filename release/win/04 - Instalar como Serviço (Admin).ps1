param(
  [string]$InstallDir = "",
  [string]$TaskName = "DaleVisionEdgeAgent",
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

function Resolve-AgentBatPath {
  param(
    [string]$InstallDir,
    [string]$ScriptRoot
  )

  if ([string]::IsNullOrWhiteSpace($InstallDir)) {
    $InstallDir = $ScriptRoot
  }

  $candidates = @(
    (Join-Path $InstallDir "01_INICIAR_DALEVISION.bat"),
    (Join-Path $InstallDir "Start_DaleVision_Agent.bat"),
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

  $candidate = Join-Path $InstallDir "DaleVision Edge Agent.exe"
  if (Test-Path $candidate) {
    return $candidate
  }
  return $candidate
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
    [string]$TaskName = "DaleVisionEdgeAgent",
    [switch]$WhatIf
  )

  $logRoot = $env:PROGRAMDATA
  if ([string]::IsNullOrWhiteSpace($logRoot)) {
    $logRoot = $PSScriptRoot
  }
  $logDir = Join-Path $logRoot "DaleVision\\logs"
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

    $resolvedInstallDir = $InstallDir
    if ([string]::IsNullOrWhiteSpace($resolvedInstallDir)) {
      $resolvedInstallDir = $PSScriptRoot
    }
    $agentExe = Resolve-AgentExePath -InstallDir $InstallDir -ScriptRoot $PSScriptRoot
    $agentBat = Resolve-AgentBatPath -InstallDir $InstallDir -ScriptRoot $PSScriptRoot

    $entryPoint = $null
    if (Test-Path $agentExe) {
      $entryPoint = $agentExe
    } elseif (Test-Path $agentBat) {
      $entryPoint = $agentBat
    }

    if (-not $entryPoint) {
      Write-Log "ERRO: arquivo nao encontrado: $agentExe"
      if (Test-Path $resolvedInstallDir) {
        $files = Get-ChildItem -Path $resolvedInstallDir -File | Select-Object -ExpandProperty Name
        if ($files) {
          Write-Log "Arquivos encontrados em $resolvedInstallDir:"
          foreach ($file in $files) {
            Write-Log " - $file"
          }
        } else {
          Write-Log "Nenhum arquivo encontrado em $resolvedInstallDir."
        }
      } else {
        Write-Log "Pasta nao encontrada: $resolvedInstallDir"
      }
      Write-Log "Pressione Enter para sair."
      Read-Host | Out-Null
      exit 1
    }

    $user = "$env:USERDOMAIN\\$env:USERNAME"
    $taskCmd = Get-TaskCommand -EntryPoint $entryPoint

    Write-Log "Instalando Task Scheduler '$TaskName' para $user"
    Write-Log "Comando: $taskCmd"

    if ($WhatIf) {
      Write-Log "WhatIf: nenhuma alteracao aplicada."
      exit 0
    }

    schtasks /Create /TN $TaskName /SC ONSTART /RU $user /RL LIMITED /TR $taskCmd /F | Out-Null
    schtasks /Change /TN $TaskName /RI 1 | Out-Null

    Write-Log "OK -> Task Scheduler '$TaskName' instalado para $user"
    Write-Log "Para remover: schtasks /Delete /TN $TaskName /F"
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
