param(
  [string]$InstallDir = $PSScriptRoot
)

$ErrorActionPreference = "Stop"

$installDirSafe = $InstallDir
if ($null -eq $installDirSafe) { $installDirSafe = "" }
$installDirSafe = $installDirSafe.Trim().Trim('"').TrimEnd("\", "/").Trim()
$installRoot = (Resolve-Path $installDirSafe).Path
$exePath = Join-Path $installRoot "dalevision-edge-agent.exe"
$logDir = Join-Path $installRoot "logs"

if (-not (Test-Path $logDir)) {
  New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

if (-not (Test-Path $exePath)) {
  Write-Host "ERRO: executavel nao encontrado: $exePath"
  exit 2
}

$env:DALE_RUN_MODE = "service"
Set-Location -Path $installRoot

$oldEap = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& $exePath run
$exitCode = $LASTEXITCODE
$ErrorActionPreference = $oldEap

Write-Host ("EXIT_CODE=" + $exitCode)
exit $exitCode
