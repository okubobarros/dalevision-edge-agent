param(
  [string]$InstallDir = $PSScriptRoot,
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

function Get-TaskCommand {
  param(
    [string]$InstallRoot,
    [string]$AgentExePath
  )

  $installRootResolved = (Resolve-Path $InstallRoot).Path
  $exeResolved = (Resolve-Path $AgentExePath).Path
  $logPath = Join-Path $installRootResolved "logs\agent.log"
  $inner = "Set-Location -Path `"$installRootResolved`"; `"$exeResolved`" *>> `"$logPath`""
  return "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command `"$inner`""
}

function Invoke-InstallService {
  param(
    [string]$InstallDir = $PSScriptRoot,
    [string]$TaskName = "DaleVisionEdgeAgent",
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
    $taskCmd = Get-TaskCommand -InstallRoot $installRoot -AgentExePath $agentExe

    Write-Log "Instalando Task Scheduler '$TaskName' em $installRoot"
    Write-Log "Comando: $taskCmd"

    if ($WhatIf) {
      Write-Log "WhatIf: nenhuma alteracao aplicada."
      exit 0
    }

    $existingOutput = & schtasks /Query /TN $TaskName 2>&1
    if ($LASTEXITCODE -eq 0) {
      Write-Log "Tarefa existente encontrada. Sera atualizada."
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

    Write-Log "Servico instalado com sucesso."
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
