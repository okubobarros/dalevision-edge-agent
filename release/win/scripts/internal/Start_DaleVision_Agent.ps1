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

# Harden runtime environment for Scheduled Task (SYSTEM):
# - avoid inherited Python vars from host/session
# - force a writable, stable temp directory for PyInstaller extraction
foreach ($name in @("PYTHONHOME", "PYTHONPATH", "PYTHONSTARTUP", "PYTHONEXECUTABLE")) {
  Remove-Item -Path "Env:$name" -ErrorAction SilentlyContinue
}

$tmpDir = Join-Path $installRoot "cache\tmp"
if (-not (Test-Path $tmpDir)) {
  New-Item -ItemType Directory -Path $tmpDir -Force | Out-Null
}
$env:TEMP = $tmpDir
$env:TMP = $tmpDir

Write-Host ("RUN_MODE=" + $env:DALE_RUN_MODE)
Write-Host ("TEMP=" + $env:TEMP)
Write-Host ("TMP=" + $env:TMP)
Write-Host ("USER=" + $env:USERNAME)

Set-Location -Path $installRoot

$oldEap = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& $exePath run
$exitCode = $LASTEXITCODE
$ErrorActionPreference = $oldEap

Write-Host ("EXIT_CODE=" + $exitCode)
exit $exitCode
