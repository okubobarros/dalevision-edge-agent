param(
  [string]$InstallDir = $PSScriptRoot
)

$ErrorActionPreference = "Stop"

$installRoot = (Resolve-Path $InstallDir).Path
$batPath = Join-Path $installRoot "Start_DaleVision_Agent.bat"

if (-not (Test-Path $batPath)) {
  Write-Host "ERRO: arquivo nao encontrado: $batPath"
  exit 1
}

$env:DALE_RUN_MODE = "service"

Start-Process -FilePath "cmd.exe" `
  -ArgumentList "/c", "`"$batPath`"" `
  -WorkingDirectory $installRoot `
  -WindowStyle Hidden `
  -Wait
