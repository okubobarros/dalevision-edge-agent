param(
  [string]$InstallDir = $PSScriptRoot
)

$ErrorActionPreference = "Stop"

$installRoot = (Resolve-Path $InstallDir).Path
$exePath = Join-Path $installRoot "dalevision-edge-agent.exe"
$logDir = Join-Path $installRoot "logs"
$logPath = Join-Path $logDir "agent.log"

if (-not (Test-Path $logDir)) {
  New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

if (-not (Test-Path $exePath)) {
  Write-Host "ERRO: executavel nao encontrado: $exePath"
  exit 2
}

$env:DALE_RUN_MODE = "service"
Set-Location -Path $installRoot
& $exePath *>> $logPath
exit $LASTEXITCODE
