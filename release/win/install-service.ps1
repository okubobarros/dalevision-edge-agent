param(
  [string]$InstallDir = "",
  [string]$TaskName = "DaleVisionEdgeAgent"
)

$ErrorActionPreference = "Stop"

$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
  Write-Host "ERRO: permissao insuficiente."
  Write-Host "Execute este script como Administrador."
  exit 1
}

if ([string]::IsNullOrWhiteSpace($InstallDir)) {
  $InstallDir = $PSScriptRoot
}

$agentBat = Join-Path $InstallDir "Start_DaleVision_Agent.bat"
if (-not (Test-Path $agentBat)) {
  Write-Host "ERRO: arquivo nao encontrado: $agentBat"
  if (Test-Path $InstallDir) {
    $files = Get-ChildItem -Path $InstallDir -File | Select-Object -ExpandProperty Name
    if ($files) {
      Write-Host "Arquivos encontrados em $InstallDir:"
      foreach ($file in $files) {
        Write-Host " - $file"
      }
    } else {
      Write-Host "Nenhum arquivo encontrado em $InstallDir."
    }
  } else {
    Write-Host "Pasta nao encontrada: $InstallDir"
  }
  exit 1
}

$user = "$env:USERDOMAIN\\$env:USERNAME"
$taskCmd = "cmd /c `"$agentBat`""

schtasks /Create /TN $TaskName /SC ONSTART /RU $user /RL LIMITED /TR $taskCmd /F | Out-Null
schtasks /Change /TN $TaskName /RI 1 | Out-Null

Write-Host "OK -> Task Scheduler '$TaskName' instalado para $user"
Write-Host "Para remover: schtasks /Delete /TN $TaskName /F"
