param(
  [string]$SourceRoot = (Split-Path -Parent $PSScriptRoot),
  [string]$Version = "",
  [string]$ActivationToken = "",
  [string]$ActivationTokenFile = "",
  [string]$CloudBaseUrl = "",
  [string]$OpenDashboard = "0"
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

function Resolve-ActivationToken {
  param(
    [string]$Token,
    [string]$TokenFile
  )
  if (-not [string]::IsNullOrWhiteSpace($Token)) {
    return $Token.Trim()
  }
  if (-not [string]::IsNullOrWhiteSpace($TokenFile) -and (Test-Path $TokenFile)) {
    try {
      $raw = Get-Content -Path $TokenFile -Raw -ErrorAction Stop
      $candidate = [string]($raw -split "\r?\n" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -First 1)
      if (-not [string]::IsNullOrWhiteSpace($candidate)) {
        return $candidate.Trim()
      }
    } catch {}
  }
  return ""
}

function Get-MaskedToken {
  param([string]$Token)
  if ([string]::IsNullOrWhiteSpace($Token)) {
    return ""
  }
  $t = $Token.Trim()
  if ($t.Length -le 8) {
    return "****"
  }
  return "{0}...{1}" -f $t.Substring(0, 4), $t.Substring($t.Length - 4, 4)
}

function Stop-ExistingDaleVisionProcesses {
  try {
    $candidates = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
      ($_.Name -match "dalevision-edge-agent\.exe") -or
      (
        ($_.Name -match "powershell\.exe|pwsh\.exe|cmd\.exe") -and
        ($_.CommandLine -match "Start_DaleVision_Agent\.ps1|DaleVision\\app\\")
      )
    }
    foreach ($proc in $candidates) {
      try {
        Stop-Process -Id $proc.ProcessId -Force -ErrorAction Stop
        Write-Log ("INSTALL000A process_stopped pid={0} name={1}" -f $proc.ProcessId, $proc.Name)
      } catch {
        Write-Log ("INSTALL000B process_stop_failed pid={0} name={1} err={2}" -f $proc.ProcessId, $proc.Name, $_.Exception.Message)
      }
    }
    Start-Sleep -Milliseconds 800
  } catch {
    Write-Log ("INSTALL000C process_scan_failed err={0}" -f $_.Exception.Message)
  }
}

function Upsert-EnvValue {
  param(
    [string]$EnvPath,
    [string]$Key,
    [string]$Value
  )
  if ([string]::IsNullOrWhiteSpace($EnvPath) -or [string]::IsNullOrWhiteSpace($Key)) {
    return
  }
  $lines = @()
  if (Test-Path $EnvPath) {
    try {
      $lines = Get-Content -Path $EnvPath -Encoding UTF8
    } catch {
      $lines = @()
    }
  }
  $updated = $false
  for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match "^\s*$Key=") {
      $lines[$i] = "$Key=$Value"
      $updated = $true
      break
    }
  }
  if (-not $updated) {
    $lines += "$Key=$Value"
  }
  $lines | Set-Content -Path $EnvPath -Encoding UTF8
}

function Resolve-AppDashboardUrl {
  param(
    [string]$CloudBaseUrl,
    [string]$StoreId
  )
  $defaultBase = "https://app.dalevision.com"
  if ([string]::IsNullOrWhiteSpace($CloudBaseUrl)) {
    if (-not [string]::IsNullOrWhiteSpace($StoreId)) {
      return ("{0}/app/dashboard?store={1}&openEdgeSetup=1" -f $defaultBase.TrimEnd("/"), $StoreId)
    }
    return ("{0}/app/dashboard?openEdgeSetup=1" -f $defaultBase.TrimEnd("/"))
  }
  $base = $CloudBaseUrl.Trim()
  if ($base -match "^https?://api\.") {
    $base = $base -replace "^https?://api\.", "https://app."
  }
  $base = $base -replace "/api/?$", ""
  if ($base -notmatch "^https?://") {
    $base = $defaultBase
  }
  $base = $base.TrimEnd("/")
  if (-not [string]::IsNullOrWhiteSpace($StoreId)) {
    return ("{0}/app/dashboard?store={1}&openEdgeSetup=1" -f $base, $StoreId)
  }
  return ("{0}/app/dashboard?openEdgeSetup=1" -f $base)
}

function Parse-BoolString {
  param([string]$RawValue)
  if ([string]::IsNullOrWhiteSpace($RawValue)) {
    return $false
  }
  switch ($RawValue.Trim().ToLowerInvariant()) {
    "1" { return $true }
    "true" { return $true }
    "yes" { return $true }
    "on" { return $true }
    default { return $false }
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
Stop-ExistingDaleVisionProcesses

try {
  schtasks /Delete /TN "DaleVisionEdgeAgentUser" /F *> $null
  Write-Log "INSTALL001B removed_legacy_schtask=DaleVisionEdgeAgentUser"
} catch {
  Write-Log ("INSTALL001C legacy_schtask_not_removed err={0}" -f $_.Exception.Message)
}

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

$tokenResolved = Resolve-ActivationToken -Token $ActivationToken -TokenFile $ActivationTokenFile
$agentConfigPath = Join-Path $configDir "agent_config.json"
if (-not (Test-Path $agentConfigPath)) {
  "{}" | Set-Content -Path $agentConfigPath -Encoding UTF8
}
try {
  $agentConfigRaw = Get-Content -Path $agentConfigPath -Raw -ErrorAction Stop
  $agentConfigObj = ConvertFrom-Json -InputObject $agentConfigRaw -ErrorAction Stop
  $agentConfig = @{}
  if ($null -ne $agentConfigObj) {
    foreach ($prop in $agentConfigObj.PSObject.Properties) {
      $agentConfig[$prop.Name] = $prop.Value
    }
  }
} catch {
  $agentConfig = @{}
}
if (-not [string]::IsNullOrWhiteSpace($tokenResolved)) {
  $agentConfig["activation_token"] = $tokenResolved
  Write-Log ("INSTALL003B activation_token_seeded token={0}" -f (Get-MaskedToken -Token $tokenResolved))
}
if (-not [string]::IsNullOrWhiteSpace($CloudBaseUrl)) {
  $agentConfig["cloud_base_url"] = $CloudBaseUrl.Trim()
  Write-Log ("INSTALL003C cloud_base_url_set value={0}" -f $CloudBaseUrl.Trim())
}
if ($agentConfig.Count -gt 0) {
  $agentConfig | ConvertTo-Json -Depth 4 | Set-Content -Path $agentConfigPath -Encoding UTF8
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
if (-not [string]::IsNullOrWhiteSpace($CloudBaseUrl)) {
  Upsert-EnvValue -EnvPath $envTarget -Key "CLOUD_BASE_URL" -Value $CloudBaseUrl.Trim()
}

if (-not [string]::IsNullOrWhiteSpace($tokenResolved) -and -not [string]::IsNullOrWhiteSpace($CloudBaseUrl)) {
  try {
    $deviceKey = ""
    if ($agentConfig.ContainsKey("device_key")) {
      $deviceKey = [string]$agentConfig["device_key"]
    }
    if ([string]::IsNullOrWhiteSpace($deviceKey)) {
      $suffix = [Guid]::NewGuid().ToString("N").Substring(0, 12)
      $deviceKey = ("edge-{0}-{1}" -f $env:COMPUTERNAME, $suffix).ToLower()
    }
    $activationBody = @{
      activation_token = $tokenResolved
      device_key = $deviceKey
      installed_version = $versionSafe
      update_channel = "stable"
    } | ConvertTo-Json
    $activateUrl = ($CloudBaseUrl.TrimEnd("/") + "/api/v1/stores/activate/")
    $activateResp = Invoke-RestMethod -Method Post -Uri $activateUrl -ContentType "application/json" -Body $activationBody -TimeoutSec 20
    if ($activateResp -and $activateResp.ok -eq $true) {
      $storeId = [string]$activateResp.store_id
      $edgeToken = [string]$activateResp.edge_token
      if (-not [string]::IsNullOrWhiteSpace($storeId) -and -not [string]::IsNullOrWhiteSpace($edgeToken)) {
        $agentConfig["store_id"] = $storeId
        $agentConfig["edge_token"] = $edgeToken
        $agentConfig["device_key"] = [string]$activateResp.device_key
        $agentConfig["edge_device_id"] = [string]$activateResp.device_id
        $agentConfig["installed_version"] = [string]$activateResp.installed_version
        $agentConfig["update_channel"] = [string]$activateResp.update_channel
        $agentConfig.Remove("activation_token")
        $agentConfig | ConvertTo-Json -Depth 4 | Set-Content -Path $agentConfigPath -Encoding UTF8

        Upsert-EnvValue -EnvPath $envTarget -Key "STORE_ID" -Value $storeId
        Upsert-EnvValue -EnvPath $envTarget -Key "EDGE_TOKEN" -Value $edgeToken
        Write-Log ("INSTALL004B activation_bootstrap_ok store_id={0} device_key={1}" -f $storeId, [string]$activateResp.device_key)
      } else {
        Write-Log "INSTALL004C activation_bootstrap_missing_fields"
      }
    } else {
      Write-Log "INSTALL004D activation_bootstrap_response_not_ok"
    }
  } catch {
    Write-Log ("INSTALL004E activation_bootstrap_failed err={0}" -f $_.Exception.Message)
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
$shouldOpenDashboard = Parse-BoolString -RawValue $OpenDashboard
if ($shouldOpenDashboard) {
  try {
    $storeForRedirect = ""
    if ($agentConfig.ContainsKey("store_id")) {
      $storeForRedirect = [string]$agentConfig["store_id"]
    }
    $appUrl = Resolve-AppDashboardUrl -CloudBaseUrl $CloudBaseUrl -StoreId $storeForRedirect
    Start-Process -FilePath $appUrl | Out-Null
    Write-Log ("INSTALL008 app_opened url={0}" -f $appUrl)
  } catch {
    Write-Log ("INSTALL008E app_open_failed err={0}" -f $_.Exception.Message)
  }
} else {
  Write-Log "INSTALL008S app_open_skipped"
}
Write-Log "INSTALL999 ok"
