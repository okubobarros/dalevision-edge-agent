param(
  [string]$InstallDir = $PSScriptRoot
)

$ErrorActionPreference = "Stop"

function Write-Log {
  param([string]$Message)
  $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  $line = "$timestamp $Message"
  Add-Content -Path $script:LogPath -Value $line
  Write-Host $Message
}

try {
  [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
} catch {
}

function Read-EnvFile {
  param([string]$Path)
  $result = @{}
  if (-not (Test-Path $Path)) {
    return $result
  }
  Get-Content -Path $Path | ForEach-Object {
    $line = $_.Trim()
    if ($line -eq "" -or $line.StartsWith("#")) {
      return
    }
    $parts = $line.Split("=", 2)
    if ($parts.Count -eq 2) {
      $key = $parts[0].Trim()
      $value = $parts[1].Trim()
      if ($key -ne "") {
        $result[$key] = $value
      }
    }
  }
  return $result
}

function Get-CurrentVersion {
  param(
    [string]$InstallRoot,
    [string]$ExePath
  )

  $versionFile = Join-Path $InstallRoot "VERSION"
  if (Test-Path $versionFile) {
    return (Get-Content -Path $versionFile | Select-Object -First 1).Trim()
  }

  if (Test-Path $ExePath) {
    try {
      $output = & $ExePath --version 2>$null
      if ($LASTEXITCODE -eq 0 -and $output) {
        return ($output | Select-Object -First 1).Trim()
      }
    } catch {
      return "0.0.0"
    }
  }

  return "0.0.0"
}

function Get-ReleaseApiUrl {
  param(
    [string]$Repo,
    [string]$Channel,
    [string]$BetaTag
  )

  if ([string]::IsNullOrWhiteSpace($Repo)) {
    return ""
  }
  if ($Channel -eq "beta" -and -not [string]::IsNullOrWhiteSpace($BetaTag)) {
    return "https://api.github.com/repos/$Repo/releases/tags/$BetaTag"
  }
  return "https://api.github.com/repos/$Repo/releases/latest"
}

function Compare-Version {
  param(
    [string]$Current,
    [string]$Incoming
  )
  $currentParts = [regex]::Matches($Current, "\d+") | ForEach-Object { [int]$_.Value }
  $incomingParts = [regex]::Matches($Incoming, "\d+") | ForEach-Object { [int]$_.Value }
  $len = [Math]::Max($currentParts.Count, $incomingParts.Count)
  for ($i = 0; $i -lt $len; $i++) {
    $a = if ($i -lt $currentParts.Count) { $currentParts[$i] } else { 0 }
    $b = if ($i -lt $incomingParts.Count) { $incomingParts[$i] } else { 0 }
    if ($a -lt $b) { return -1 }
    if ($a -gt $b) { return 1 }
  }
  return 0
}

function Download-Asset {
  param(
    [string]$Url,
    [string]$DestinationPath
  )
  $client = New-Object System.Net.WebClient
  $client.Headers["User-Agent"] = "dalevision-edge-agent"
  $client.DownloadFile($Url, $DestinationPath)
}

$installRoot = (Resolve-Path $InstallDir).Path
$logDir = Join-Path $installRoot "logs"
if (-not (Test-Path $logDir)) {
  New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}
$script:LogPath = Join-Path $logDir "update.log"

try {
  $envPath = Join-Path $installRoot ".env"
  $envVars = Read-EnvFile -Path $envPath

  $autoEnabled = ($envVars["AUTO_UPDATE_ENABLED"] -eq "1")
  $channel = $envVars["UPDATE_CHANNEL"]
  if ([string]::IsNullOrWhiteSpace($channel)) { $channel = "stable" }
  $repo = $envVars["UPDATE_GITHUB_REPO"]
  $betaTag = $envVars["UPDATE_BETA_TAG"]

  if ([string]::IsNullOrWhiteSpace($repo)) {
    Write-Log "UPD000 repo nao configurado (UPDATE_GITHUB_REPO)."
    exit 0
  }

  $exePath = Join-Path $installRoot "dalevision-edge-agent.exe"
  $currentVersion = Get-CurrentVersion -InstallRoot $installRoot -ExePath $exePath
  Write-Log "UPD001 current_version=$currentVersion channel=$channel"

  $apiUrl = Get-ReleaseApiUrl -Repo $repo -Channel $channel -BetaTag $betaTag
  if ([string]::IsNullOrWhiteSpace($apiUrl)) {
    Write-Log "UPD002 url invalida."
    exit 0
  }

  $client = New-Object System.Net.WebClient
  $client.Headers["User-Agent"] = "dalevision-edge-agent"
  $json = $client.DownloadString($apiUrl) | ConvertFrom-Json

  $latestVersion = $json.tag_name
  if ([string]::IsNullOrWhiteSpace($latestVersion)) {
    Write-Log "UPD003 tag_name ausente."
    exit 0
  }

  if ((Compare-Version -Current $currentVersion -Incoming $latestVersion) -ge 0) {
    Write-Log "UPD004 sem update disponivel."
    exit 0
  }

  $asset = $null
  foreach ($a in $json.assets) {
    if ($a.name -like "*.zip" -or $a.name -like "*.exe") {
      $asset = $a
      break
    }
  }
  if (-not $asset) {
    Write-Log "UPD005 asset nao encontrado."
    exit 0
  }

  Write-Log "UPD010 update encontrado: $latestVersion ($($asset.name))"
  if (-not $autoEnabled) {
    Write-Log "UPD011 auto-update desabilitado (AUTO_UPDATE_ENABLED=1 para aplicar)."
    exit 0
  }

  $staging = Join-Path $installRoot "updates"
  if (-not (Test-Path $staging)) {
    New-Item -ItemType Directory -Path $staging -Force | Out-Null
  }
  $downloadPath = Join-Path $staging $asset.name

  Write-Log "UPD020 baixando..."
  Download-Asset -Url $asset.browser_download_url -DestinationPath $downloadPath

  $newExePath = $downloadPath
  if ($downloadPath.EndsWith(".zip")) {
    $extractDir = Join-Path $staging ("extract-" + $latestVersion)
    if (-not (Test-Path $extractDir)) {
      New-Item -ItemType Directory -Path $extractDir -Force | Out-Null
    }
    Expand-Archive -Path $downloadPath -DestinationPath $extractDir -Force
    $candidate = Get-ChildItem -Path $extractDir -Recurse -Filter "dalevision-edge-agent.exe" | Select-Object -First 1
    if (-not $candidate) {
      Write-Log "UPD021 exe nao encontrado no ZIP."
      exit 0
    }
    $newExePath = $candidate.FullName
  }

  Write-Log "UPD030 aplicando update..."
  $processes = Get-Process -Name "dalevision-edge-agent" -ErrorAction SilentlyContinue
  if ($processes) {
    $processes | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
  }

  $backup = Join-Path $installRoot "dalevision-edge-agent.exe.bak"
  if (Test-Path $backup) {
    Remove-Item $backup -Force -ErrorAction SilentlyContinue
  }
  if (Test-Path $exePath) {
    Move-Item -Path $exePath -Destination $backup -Force
  }
  Copy-Item -Path $newExePath -Destination $exePath -Force

  $versionFile = Join-Path $installRoot "VERSION"
  Set-Content -Path $versionFile -Value $latestVersion

  Write-Log "UPD031 update aplicado com sucesso."
} catch {
  Write-Log "UPD999 erro: $($_.Exception.Message)"
  exit 1
}
