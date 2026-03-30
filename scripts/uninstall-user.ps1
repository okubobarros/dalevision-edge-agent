param(
  [switch]$RemoveData
)

$ErrorActionPreference = "Continue"

function Write-Log {
  param([string]$Message)
  $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  $line = "$timestamp $Message"
  Add-Content -Path $script:LogPath -Value $line -Encoding UTF8
  Write-Host $Message
}

$local = $env:LOCALAPPDATA
$roam = $env:APPDATA
if ([string]::IsNullOrWhiteSpace($local) -or [string]::IsNullOrWhiteSpace($roam)) {
  Write-Host "LOCALAPPDATA/APPDATA nao definidos."
  exit 2
}

$dvLocal = Join-Path $local "DaleVision"
$appRoot = Join-Path $dvLocal "app"
$logDir = Join-Path $dvLocal "logs"
$cacheDir = Join-Path $dvLocal "cache"
$configDir = Join-Path $roam "DaleVision"
$startupLink = Join-Path $roam "Microsoft\Windows\Start Menu\Programs\Startup\DaleVision Edge Agent.lnk"
$desktopDir = [Environment]::GetFolderPath("Desktop")
$configShortcut = Join-Path $desktopDir "DaleVision Config.lnk"

if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$script:LogPath = Join-Path $logDir "uninstall-user.log"
Write-Log "UNINSTALL001 start"

Get-Process -Name "dalevision-edge-agent" -ErrorAction SilentlyContinue |
  ForEach-Object {
    try {
      Stop-Process -Id $_.Id -Force -ErrorAction Stop
      Write-Log "UNINSTALL002 stopped process=dalevision-edge-agent pid=$($_.Id)"
    } catch {
      Write-Log "UNINSTALL002_WARN stop_failed pid=$($_.Id) err=$($_.Exception.Message)"
    }
  }

Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
  Where-Object { $_.CommandLine -like "*Start_DaleVision_Agent.ps1*" -or $_.CommandLine -like "*run_agent.cmd*" } |
  ForEach-Object {
    try {
      Stop-Process -Id $_.ProcessId -Force -ErrorAction Stop
      Write-Log "UNINSTALL003 stopped launcher pid=$($_.ProcessId)"
    } catch {
      Write-Log "UNINSTALL003_WARN launcher_stop_failed pid=$($_.ProcessId) err=$($_.Exception.Message)"
    }
  }

if (Test-Path $startupLink) {
  Remove-Item -Path $startupLink -Force -ErrorAction SilentlyContinue
  Write-Log "UNINSTALL004 startup_link_removed path=$startupLink"
} else {
  Write-Log "UNINSTALL004 startup_link_missing"
}
if (Test-Path $configShortcut) {
  Remove-Item -Path $configShortcut -Force -ErrorAction SilentlyContinue
  Write-Log "UNINSTALL004B config_shortcut_removed path=$configShortcut"
}

# Legacy cleanup (best effort).
foreach ($taskName in @("DaleVisionEdgeAgent", "DaleVisionEdgeAgentStartup", "DaleVisionEdgeAgentUpdate", "DaleVisionEdgeAgentUser")) {
  schtasks /Delete /TN $taskName /F > $null 2>&1
}
Write-Log "UNINSTALL005 legacy_tasks_cleanup_done"

if ($RemoveData) {
  Remove-Item -Path $appRoot -Recurse -Force -ErrorAction SilentlyContinue
  Remove-Item -Path $cacheDir -Recurse -Force -ErrorAction SilentlyContinue
  Remove-Item -Path $configDir -Recurse -Force -ErrorAction SilentlyContinue
  Remove-Item -Path $logDir -Recurse -Force -ErrorAction SilentlyContinue
  Write-Log "UNINSTALL006 data_removed"
} else {
  Write-Log "UNINSTALL006 data_preserved"
}

Write-Log "UNINSTALL999 ok"
