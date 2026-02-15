param(
  [string]$InstallDir = "$PSScriptRoot\\..\\release\\win",
  [string]$TaskName = "DaleVisionEdgeAgent"
)

$ErrorActionPreference = "Stop"

$agentBat = Join-Path $InstallDir "Start_DaleVision_Agent.bat"
if (-not (Test-Path $agentBat)) {
  throw "Arquivo nao encontrado: $agentBat"
}

$user = "$env:USERDOMAIN\\$env:USERNAME"
$taskCmd = "cmd /c `"$agentBat`""

schtasks /Create /TN $TaskName /SC ONSTART /RU $user /RL LIMITED /TR $taskCmd /F | Out-Null
schtasks /Change /TN $TaskName /RI 1 | Out-Null

Write-Host "OK -> Task Scheduler '$TaskName' instalado para $user"
Write-Host "Para remover: schtasks /Delete /TN $TaskName /F"
