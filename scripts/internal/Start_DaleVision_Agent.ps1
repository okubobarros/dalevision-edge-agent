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

function Get-EnvInt {
  param(
    [string]$Name,
    [int]$DefaultValue
  )

  $raw = [Environment]::GetEnvironmentVariable($Name)
  if ([string]::IsNullOrWhiteSpace($raw)) {
    return $DefaultValue
  }

  $parsed = 0
  if ([int]::TryParse($raw, [ref]$parsed)) {
    return $parsed
  }
  return $DefaultValue
}

function Get-EnvBool {
  param(
    [string]$Name,
    [bool]$DefaultValue
  )

  $raw = [Environment]::GetEnvironmentVariable($Name)
  if ([string]::IsNullOrWhiteSpace($raw)) {
    return $DefaultValue
  }

  switch ($raw.Trim().ToLowerInvariant()) {
    "1" { return $true }
    "true" { return $true }
    "yes" { return $true }
    "on" { return $true }
    "0" { return $false }
    "false" { return $false }
    "no" { return $false }
    "off" { return $false }
    default { return $DefaultValue }
  }
}

$restartEnabled = Get-EnvBool -Name "LAUNCHER_RESTART_ENABLED" -DefaultValue $true
$restartDelaySeconds = Get-EnvInt -Name "LAUNCHER_RESTART_DELAY_SECONDS" -DefaultValue 5
$restartMax = Get-EnvInt -Name "LAUNCHER_RESTART_MAX" -DefaultValue 1000
$restartCount = 0

Write-Host ("LAUNCHER_RESTART_ENABLED=" + $restartEnabled)
Write-Host ("LAUNCHER_RESTART_DELAY_SECONDS=" + $restartDelaySeconds)
Write-Host ("LAUNCHER_RESTART_MAX=" + $restartMax)

while ($true) {
  $restartCount += 1
  Write-Host ("LAUNCH_ATTEMPT=" + $restartCount)

  $oldEap = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  $proc = $null
  try {
    $proc = Start-Process -FilePath $exePath -ArgumentList "run" -WorkingDirectory $installRoot -PassThru -Wait
    $exitCode = $proc.ExitCode
  } catch {
    $exitCode = 9009
    Write-Host ("LAUNCH_ERROR=" + $_.Exception.Message)
  }
  $ErrorActionPreference = $oldEap

  Write-Host ("EXIT_CODE=" + $exitCode)

  if (-not $restartEnabled) {
    exit $exitCode
  }

  if ($exitCode -eq 0) {
    Write-Host "EXIT_REASON=clean_exit"
    exit 0
  }

  if ($restartCount -ge $restartMax) {
    Write-Host "EXIT_REASON=restart_limit_reached"
    exit $exitCode
  }

  Write-Host ("RESTARTING_IN_SECONDS=" + $restartDelaySeconds)
  Start-Sleep -Seconds $restartDelaySeconds
}
