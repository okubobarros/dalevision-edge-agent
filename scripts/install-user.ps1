param(
  [string]$SourceRoot = (Split-Path -Parent $PSScriptRoot),
  [string]$Version = ""
)

$ErrorActionPreference = "Stop"

function Write-Log {
  param([string]$Message)
  $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  $line = "$timestamp $Message"
  Add-Content -Path $script:LogPath -Value $line -Encoding UTF8
  Write-Host $Message
}

function Resolve-Version {
  param([string]$Root)
  if (-not [string]::IsNullOrWhiteSpace($Version)) {
    return $Version.Trim()
  }
  $exePath = Join-Path $Root "dalevision-edge-agent.exe"
  if (Test-Path $exePath) {
    try {
      $fvi = [System.Diagnostics.FileVersionInfo]::GetVersionInfo($exePath)
      if ($fvi -and -not [string]::IsNullOrWhiteSpace($fvi.FileVersion)) {
        return $fvi.FileVersion.Trim()
      }
    } catch {}
  }
  return "unknown"
}

function Ensure-Dir {
  param([string]$Path)
  if (-not (Test-Path $Path)) {
    New-Item -ItemType Directory -Path $Path -Force | Out-Null
  }
}

$local = $env:LOCALAPPDATA
$roam = $env:APPDATA
if ([string]::IsNullOrWhiteSpace($local) -or [string]::IsNullOrWhiteSpace($roam)) {
  throw "LOCALAPPDATA/APPDATA nao definidos."
}

$dvLocal = Join-Path $local "DaleVision"
$appRoot = Join-Path $dvLocal "app"
$logDir = Join-Path $dvLocal "logs"
$cacheDir = Join-Path $dvLocal "cache"
$configDir = Join-Path $roam "DaleVision"
$startupDir = Join-Path $roam "Microsoft\Windows\Start Menu\Programs\Startup"
$startupLink = Join-Path $startupDir "DaleVision Edge Agent.lnk"
$desktopDir = [Environment]::GetFolderPath("Desktop")
$configShortcut = Join-Path $desktopDir "DaleVision Config.lnk"

Ensure-Dir $appRoot
Ensure-Dir $logDir
Ensure-Dir $cacheDir
Ensure-Dir $configDir
Ensure-Dir $startupDir

$script:LogPath = Join-Path $logDir "install-user.log"
Write-Log "INSTALL001 start source=$SourceRoot"

if (-not (Test-Path $SourceRoot)) {
  throw "SourceRoot nao encontrado: $SourceRoot"
}

$versionResolved = Resolve-Version -Root $SourceRoot
$versionSafe = ($versionResolved -replace '[^A-Za-z0-9._-]', '-')
if ([string]::IsNullOrWhiteSpace($versionSafe)) { $versionSafe = "unknown" }
$targetRoot = Join-Path $appRoot $versionSafe
Ensure-Dir $targetRoot
Write-Log "INSTALL002 version=$versionSafe target=$targetRoot"

# Copy package out of Downloads/zip extraction directory to stable per-user app dir.
$robocopyArgs = @(
  $SourceRoot,
  $targetRoot,
  "/E",
  "/R:1",
  "/W:1",
  "/NFL",
  "/NDL",
  "/NJH",
  "/NJS",
  "/XD", "logs", "cache", "_MEI", "tmp",
  "/XF", "*.log"
)
$robocopyOutput = & robocopy @robocopyArgs
$rc = $LASTEXITCODE
Write-Log "INSTALL003 robocopy_exit=$rc"
if ($rc -ge 8) {
  throw "Falha ao copiar pacote para pasta operacional. robocopy_exit=$rc"
}

$envTarget = Join-Path $configDir ".env"
if (-not (Test-Path $envTarget)) {
  $envSource = Join-Path $targetRoot ".env"
  if (Test-Path $envSource) {
    Copy-Item -Path $envSource -Destination $envTarget -Force
    Write-Log "INSTALL004 env_copied source=$envSource target=$envTarget"
  } else {
    New-Item -ItemType File -Path $envTarget -Force | Out-Null
    Write-Log "INSTALL004 env_created target=$envTarget"
  }
}

$runCmd = Join-Path $targetRoot "run_agent.cmd"
if (-not (Test-Path $runCmd)) {
  throw "run_agent.cmd nao encontrado no target: $runCmd"
}

$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($startupLink)
$shortcut.TargetPath = $runCmd
$shortcut.WorkingDirectory = $targetRoot
$shortcut.Description = "DaleVision Edge Agent"
$shortcut.IconLocation = (Join-Path $targetRoot "dalevision-edge-agent.exe")
$shortcut.Save()
Write-Log "INSTALL005 startup_link=$startupLink"

$cfgShortcut = $wsh.CreateShortcut($configShortcut)
$cfgShortcut.TargetPath = "$env:WINDIR\System32\notepad.exe"
$cfgShortcut.Arguments = "`"$envTarget`""
$cfgShortcut.WorkingDirectory = $configDir
$cfgShortcut.Description = "DaleVision Config"
$cfgShortcut.Save()
Write-Log "INSTALL005B config_shortcut=$configShortcut"

$installInfo = @{
  version = $versionSafe
  installed_at_utc = (Get-Date).ToUniversalTime().ToString("o")
  app_path = $targetRoot
  config_path = $configDir
  log_path = $logDir
  cache_path = $cacheDir
  source_path = $SourceRoot
}
$installInfo | ConvertTo-Json -Depth 4 | Set-Content -Path (Join-Path $configDir "install.json") -Encoding UTF8
Write-Log "INSTALL006 install_info_written"

Start-Process -FilePath $runCmd -WorkingDirectory $targetRoot -WindowStyle Hidden
Write-Log "INSTALL007 run_started"
Write-Log "INSTALL999 ok"
