param(
  [string]$Version = "v0.0.0",
  [string]$SourceDir = "",
  [string]$OutputDir = "",
  [string]$InnoCompilerPath = ""
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$issPath = Join-Path $repoRoot "release\DaleVisionEdgeSetup.iss"
if (-not (Test-Path $issPath)) {
  throw "Installer script not found: $issPath"
}

$versionNoV = $Version.Trim()
if ($versionNoV.StartsWith("v")) {
  $versionNoV = $versionNoV.Substring(1)
}
if ([string]::IsNullOrWhiteSpace($versionNoV)) {
  $versionNoV = "0.0.0"
}

$resolvedSourceRaw = if ([string]::IsNullOrWhiteSpace($SourceDir)) { Join-Path $repoRoot "release\win" } else { $SourceDir }
$resolvedOutputRaw = if ([string]::IsNullOrWhiteSpace($OutputDir)) { $repoRoot } else { $OutputDir }

if (-not (Test-Path $resolvedSourceRaw)) {
  throw "SourceDir not found: $resolvedSourceRaw"
}
if (-not (Test-Path $resolvedOutputRaw)) {
  New-Item -ItemType Directory -Path $resolvedOutputRaw -Force | Out-Null
}
$resolvedSource = (Resolve-Path $resolvedSourceRaw).Path
$resolvedOutput = (Resolve-Path $resolvedOutputRaw).Path

$iscc = $InnoCompilerPath
if ([string]::IsNullOrWhiteSpace($iscc)) {
  $candidates = @(
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe"
  )
  foreach ($candidate in $candidates) {
    if (Test-Path $candidate) {
      $iscc = $candidate
      break
    }
  }
}
if ([string]::IsNullOrWhiteSpace($iscc) -or -not (Test-Path $iscc)) {
  throw "ISCC.exe not found. Install Inno Setup 6 or pass -InnoCompilerPath."
}

Write-Host "BUILD_SETUP version=$versionNoV"
Write-Host "BUILD_SETUP source=$resolvedSource"
Write-Host "BUILD_SETUP output=$resolvedOutput"
Write-Host "BUILD_SETUP iscc=$iscc"

& $iscc `
  "/DAppVersion=$versionNoV" `
  "/DSourceDir=$resolvedSource" `
  "/DOutputDir=$resolvedOutput" `
  $issPath

if ($LASTEXITCODE -ne 0) {
  throw "ISCC failed with exit code $LASTEXITCODE"
}

$artifact = Join-Path $resolvedOutput "DaleVisionEdgeSetup-v$versionNoV.exe"
if (-not (Test-Path $artifact)) {
  throw "Installer artifact not found: $artifact"
}

$hash = (Get-FileHash -Algorithm SHA256 -Path $artifact).Hash.ToLowerInvariant()
Write-Host "BUILD_SETUP ok artifact=$artifact sha256=$hash"
