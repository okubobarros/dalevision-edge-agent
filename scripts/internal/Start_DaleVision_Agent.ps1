param(
  [string]$InstallDir = $PSScriptRoot,
  [string]$ConfigDir = "",
  [string]$LogDir = "",
  [string]$CacheDir = ""
)

$ErrorActionPreference = "Stop"

$installDirSafe = $InstallDir
if ($null -eq $installDirSafe) { $installDirSafe = "" }
$installDirSafe = $installDirSafe.Trim().Trim('"').TrimEnd("\", "/").Trim()
$installRoot = (Resolve-Path $installDirSafe).Path
$exePath = Join-Path $installRoot "dalevision-edge-agent.exe"
$configDirSafe = $ConfigDir
if ([string]::IsNullOrWhiteSpace($configDirSafe)) {
  if (-not [string]::IsNullOrWhiteSpace($env:APPDATA)) {
    $configDirSafe = Join-Path $env:APPDATA "DaleVision"
  } else {
    $configDirSafe = Join-Path $installRoot "config"
  }
}
$logDirSafe = $LogDir
if ([string]::IsNullOrWhiteSpace($logDirSafe)) {
  if (-not [string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) {
    $logDirSafe = Join-Path $env:LOCALAPPDATA "DaleVision\logs"
  } else {
    $logDirSafe = Join-Path $installRoot "logs"
  }
}
$cacheDirSafe = $CacheDir
if ([string]::IsNullOrWhiteSpace($cacheDirSafe)) {
  if (-not [string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) {
    $cacheDirSafe = Join-Path $env:LOCALAPPDATA "DaleVision\cache"
  } else {
    $cacheDirSafe = Join-Path $installRoot "cache"
  }
}
$launcherMutexName = "Global\DaleVisionEdgeAgentLauncher"

foreach ($dir in @($configDirSafe, $logDirSafe, $cacheDirSafe)) {
  if (-not (Test-Path $dir)) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
  }
}

if (-not (Test-Path $exePath)) {
  Write-Host "ERRO: executavel nao encontrado: $exePath"
  exit 2
}

try {
  Unblock-File -Path $exePath -ErrorAction SilentlyContinue
} catch {
  # Best effort only.
}

$env:DALE_RUN_MODE = "service"

# Harden runtime environment for Scheduled Task (SYSTEM):
# - avoid inherited Python vars from host/session
# - force a writable, stable temp directory for PyInstaller extraction
foreach ($name in @("PYTHONHOME", "PYTHONPATH", "PYTHONSTARTUP", "PYTHONEXECUTABLE")) {
  Remove-Item -Path "Env:$name" -ErrorAction SilentlyContinue
}

$version = "unknown"
try {
  $fvi = [System.Diagnostics.FileVersionInfo]::GetVersionInfo($exePath)
  if ($fvi -and -not [string]::IsNullOrWhiteSpace($fvi.FileVersion)) {
    $version = $fvi.FileVersion.Trim()
  }
} catch {
  $version = "unknown"
}
$versionSafe = ($version -replace '[^A-Za-z0-9._-]', '-')
if ([string]::IsNullOrWhiteSpace($versionSafe)) { $versionSafe = "unknown" }
$env:DALEVISION_EDGE_AGENT_VERSION = $versionSafe
$runtimeRoot = Join-Path $cacheDirSafe "runtime\$versionSafe"
$tmpDir = Join-Path $runtimeRoot ([DateTimeOffset]::UtcNow.ToUnixTimeSeconds().ToString())
if (-not (Test-Path $tmpDir)) {
  New-Item -ItemType Directory -Path $tmpDir -Force | Out-Null
}

try {
  if (Test-Path $runtimeRoot) {
    $dirs = Get-ChildItem -Path $runtimeRoot -Directory -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
    $keep = 0
    foreach ($dir in $dirs) {
      $keep += 1
      if ($keep -le 3) { continue }
      $ageSeconds = ([DateTime]::UtcNow - $dir.LastWriteTimeUtc).TotalSeconds
      if ($ageSeconds -lt (7 * 24 * 3600)) { continue }
      try { Remove-Item -Path $dir.FullName -Recurse -Force -ErrorAction Stop } catch { Write-Host ("RUNTIME_TMP_CLEANUP_SKIP=" + $dir.FullName + " reason=" + $_.Exception.Message) }
    }
  }
} catch {
  Write-Host ("RUNTIME_TMP_CLEANUP_ERROR=" + $_.Exception.Message)
}
$env:TEMP = $tmpDir
$env:TMP = $tmpDir
$env:DALE_APP_DIR = $installRoot
$env:DALE_CONFIG_DIR = $configDirSafe
$env:DALE_LOG_DIR = $logDirSafe
$env:DALE_CACHE_DIR = $cacheDirSafe
$env:DALE_ENV_PATH = (Join-Path $configDirSafe ".env")
$env:DALE_AGENT_CONFIG_PATH = (Join-Path $configDirSafe "agent_config.json")

Write-Host ("RUN_MODE=" + $env:DALE_RUN_MODE)
Write-Host ("TEMP=" + $env:TEMP)
Write-Host ("TMP=" + $env:TMP)
Write-Host ("USER=" + $env:USERNAME)
Write-Host ("CONFIG_DIR=" + $env:DALE_CONFIG_DIR)
Write-Host ("LOG_DIR=" + $env:DALE_LOG_DIR)
Write-Host ("CACHE_DIR=" + $env:DALE_CACHE_DIR)

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

$createdNew = $false
$mutex = $null
try {
  $mutex = New-Object System.Threading.Mutex($true, $launcherMutexName, [ref]$createdNew)
  if (-not $createdNew) {
    Write-Host "LAUNCHER_ALREADY_RUNNING=1"
    exit 0
  }

  while ($true) {
    $restartCount += 1
    Write-Host ("LAUNCH_ATTEMPT=" + $restartCount)

    if (-not (Test-Path $exePath)) {
      Write-Host ("LAUNCH_ERROR=exe_missing path=" + $exePath)
      $exitCode = 9009
    } else {
      $oldEap = $ErrorActionPreference
      $ErrorActionPreference = "Continue"
      try {
        & $exePath run
        $exitCode = $LASTEXITCODE
      } catch {
        $exitCode = 9009
        Write-Host ("LAUNCH_ERROR=" + $_.Exception.Message)
      }
      $ErrorActionPreference = $oldEap
    }

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
} finally {
  if ($mutex -ne $null -and $createdNew) {
    try {
      $mutex.ReleaseMutex() | Out-Null
      $mutex.Dispose()
    } catch {
      # ignore
    }
  }
}
