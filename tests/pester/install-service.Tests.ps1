Describe "release bundle" {
  It ".env.template contains all required keys in order" {
    $envPath = Join-Path $PSScriptRoot "../../release/.env.template"
    (Test-Path $envPath) | Should Be $true

    $lines = Get-Content -Path $envPath |
      ForEach-Object { $_.Trim() } |
      Where-Object { $_ -ne "" -and -not $_.StartsWith("#") }

    $expected = @(
      "CLOUD_BASE_URL=https://api.dalevision.com",
      "STORE_ID=",
      "EDGE_TOKEN=",
      "AGENT_ID=edge-001",
      "HEARTBEAT_INTERVAL_SECONDS=30",
      "CAMERA_HEARTBEAT_INTERVAL_SECONDS=30",
      "DASHBOARD_URL=https://app.dalevision.com/app/cameras?onboarding=true",
      "AUTO_UPDATE_ENABLED=0",
      "UPDATE_CHANNEL=stable",
      "UPDATE_GITHUB_REPO=",
      "UPDATE_INTERVAL_SECONDS=21600"
    )

    $lines | Should Be $expected
  }

  It "release_windows.ps1 creates ZIP with required files" {
    $root = Join-Path $TestDrive "repo"
    New-Item -ItemType Directory -Path $root | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $root "dist") | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $root "release") | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $root "scripts") | Out-Null

    New-Item -ItemType File -Path (Join-Path $root "dist/dalevision-edge-agent.exe") | Out-Null
    Set-Content -Path (Join-Path $root "release/README.txt") -Value "README"
    Set-Content -Path (Join-Path $root "release/02_TESTE_RAPIDO.bat") -Value "@echo off"
    Set-Content -Path (Join-Path $root "release/03_INSTALAR_AUTOSTART.bat") -Value "@echo off"
    Set-Content -Path (Join-Path $root "release/04_VERIFICAR_STATUS.bat") -Value "@echo off"
    Set-Content -Path (Join-Path $root "release/05_REMOVER_SERVICO.bat") -Value "@echo off"
    Set-Content -Path (Join-Path $root "release/Start_DaleVision_Agent.bat") -Value "@echo off"
    Set-Content -Path (Join-Path $root "release/Start_DaleVision_Agent.ps1") -Value "Write-Host 'start'"
    Set-Content -Path (Join-Path $root "release/Diagnose.bat") -Value "@echo off"
    Set-Content -Path (Join-Path $root "release/update.ps1") -Value "Write-Host 'update'"
    Set-Content -Path (Join-Path $root "scripts/install-service.ps1") -Value "Write-Host 'install'"
    Set-Content -Path (Join-Path $root "scripts/uninstall-service.ps1") -Value "Write-Host 'uninstall'"
    Set-Content -Path (Join-Path $root "scripts/verify-service.ps1") -Value "Write-Host 'verify'"
    Set-Content -Path (Join-Path $root "release/.env.template") -Value "CLOUD_BASE_URL=https://api.dalevision.com"

    $scriptPath = Join-Path $root "scripts/release_windows.ps1"
    Copy-Item (Join-Path $PSScriptRoot "../../scripts/release_windows.ps1") $scriptPath -Force
    Push-Location $root
    try {
      & $scriptPath -Version "vTest"
    } finally {
      Pop-Location
    }

    $zipPath = Join-Path $root "dalevision-edge-agent-windows.zip"
    (Test-Path $zipPath) | Should Be $true

    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [System.IO.Compression.ZipFile]::OpenRead($zipPath)
    $names = $zip.Entries | ForEach-Object { $_.FullName }
    $zip.Dispose()

    $expected = @(
      "dalevision-edge-agent.exe",
      "02_TESTE_RAPIDO.bat",
      "03_INSTALAR_AUTOSTART.bat",
      "04_VERIFICAR_STATUS.bat",
      "05_REMOVER_SERVICO.bat",
      "Start_DaleVision_Agent.bat",
      "Start_DaleVision_Agent.ps1",
      "Diagnose.bat",
      "update.ps1",
      "install-service.ps1",
      "uninstall-service.ps1",
      "verify-service.ps1",
      "README.txt",
      ".env.template",
      "logs/.keep"
    )

    foreach ($item in $expected) {
      ($names -contains $item) | Should Be $true
    }

    ($names -contains ".env") | Should Be $false
  }

  It "release_windows.ps1 fails when required file is missing" {
    $root = Join-Path $TestDrive "repo_missing"
    New-Item -ItemType Directory -Path $root | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $root "dist") | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $root "release") | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $root "scripts") | Out-Null

    New-Item -ItemType File -Path (Join-Path $root "dist/dalevision-edge-agent.exe") | Out-Null
    Set-Content -Path (Join-Path $root "release/README.txt") -Value "README"
    Set-Content -Path (Join-Path $root "release/02_TESTE_RAPIDO.bat") -Value "@echo off"
    Set-Content -Path (Join-Path $root "release/03_INSTALAR_AUTOSTART.bat") -Value "@echo off"
    Set-Content -Path (Join-Path $root "release/04_VERIFICAR_STATUS.bat") -Value "@echo off"
    Set-Content -Path (Join-Path $root "release/05_REMOVER_SERVICO.bat") -Value "@echo off"
    Set-Content -Path (Join-Path $root "release/Start_DaleVision_Agent.bat") -Value "@echo off"
    Set-Content -Path (Join-Path $root "release/Start_DaleVision_Agent.ps1") -Value "Write-Host 'start'"
    Set-Content -Path (Join-Path $root "release/Diagnose.bat") -Value "@echo off"
    Set-Content -Path (Join-Path $root "release/update.ps1") -Value "Write-Host 'update'"
    Set-Content -Path (Join-Path $root "scripts/install-service.ps1") -Value "Write-Host 'install'"
    Set-Content -Path (Join-Path $root "scripts/uninstall-service.ps1") -Value "Write-Host 'uninstall'"
    Set-Content -Path (Join-Path $root "scripts/verify-service.ps1") -Value "Write-Host 'verify'"
    # Intencionalmente omitindo .env.template

    $scriptPath = Join-Path $root "scripts/release_windows.ps1"
    Copy-Item (Join-Path $PSScriptRoot "../../scripts/release_windows.ps1") $scriptPath -Force
    $threw = $false
    Push-Location $root
    try {
      & $scriptPath -Version "vTest"
    } catch {
      $threw = $true
    } finally {
      Pop-Location
    }

    $threw | Should Be $true
  }
}
