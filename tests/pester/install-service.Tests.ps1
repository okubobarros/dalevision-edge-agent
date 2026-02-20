Describe "install-service Resolve-AgentBatPath" {
  BeforeAll {
    . "$PSScriptRoot/../../scripts/install-service.ps1"
  }

  It "resolves 01_INICIAR_DALEVISION.bat from script root when InstallDir empty" {
    $root = Join-Path $TestDrive "root"
    New-Item -ItemType Directory -Path $root | Out-Null
    New-Item -ItemType File -Path (Join-Path $root "01_INICIAR_DALEVISION.bat") | Out-Null

    $result = Resolve-AgentBatPath -InstallDir "" -ScriptRoot $root

    $result | Should -Be (Join-Path $root "01_INICIAR_DALEVISION.bat")
  }

  It "falls back to Start_DaleVision_Agent.bat when new name is missing" {
    $install = Join-Path $TestDrive "install"
    New-Item -ItemType Directory -Path $install | Out-Null
    New-Item -ItemType File -Path (Join-Path $install "Start_DaleVision_Agent.bat") | Out-Null

    $result = Resolve-AgentBatPath -InstallDir $install -ScriptRoot $TestDrive

    $result | Should -Be (Join-Path $install "Start_DaleVision_Agent.bat")
  }
}

Describe "install-service Get-TaskCommand" {
  BeforeAll {
    . "$PSScriptRoot/../../scripts/install-service.ps1"
  }

  It "returns quoted absolute path" {
    $root = Join-Path $TestDrive "root"
    New-Item -ItemType Directory -Path $root | Out-Null
    $entry = Join-Path $root "DaleVision Edge Agent.exe"
    New-Item -ItemType File -Path $entry | Out-Null

    $command = Get-TaskCommand -EntryPoint $entry

    $command | Should -Be "`"$entry`""
  }
}
