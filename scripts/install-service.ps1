param(
  [string]$InstallDir = "",
  [string]$TaskName = "DaleVisionEdgeAgent"
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($InstallDir)) {
  $InstallDir = $PSScriptRoot
  $fallback = Join-Path $PSScriptRoot "..\\release\\win"
  $agentBat = Join-Path $InstallDir "01 - Iniciar Agent.bat"
  if (-not (Test-Path $agentBat) -and (Test-Path $fallback)) {
    $InstallDir = $fallback
  }
}

$agentBat = Join-Path $InstallDir "01 - Iniciar Agent.bat"
if (-not (Test-Path $agentBat)) {
  throw "Arquivo nao encontrado: $agentBat"
}

$user = "$env:USERDOMAIN\\$env:USERNAME"
$taskCmd = "cmd /c `"$agentBat`""

schtasks /Create /TN $TaskName /SC ONSTART /RU $user /RL LIMITED /TR $taskCmd /F | Out-Null
schtasks /Change /TN $TaskName /RI 1 | Out-Null

Write-Host "OK -> Task Scheduler '$TaskName' instalado para $user"
Write-Host "Para remover: schtasks /Delete /TN $TaskName /F"
