Describe "install-service Resolve-AgentBatPath" {
  BeforeAll {
    . "$PSScriptRoot/../../scripts/install-service.ps1"
  }

  It "resolves Start_DaleVision_Agent.bat from script root when InstallDir empty" {
    $root = Join-Path $TestDrive "root"
    New-Item -ItemType Directory -Path $root | Out-Null
    New-Item -ItemType File -Path (Join-Path $root "Start_DaleVision_Agent.bat") | Out-Null

    $result = Resolve-AgentBatPath -InstallDir "" -ScriptRoot $root

    $result | Should Be (Join-Path $root "Start_DaleVision_Agent.bat")
  }
}

Describe "install-service Get-TaskCommand" {
  BeforeAll {
    . "$PSScriptRoot/../../scripts/install-service.ps1"
  }

  It "returns powershell command with hidden window" {
    $root = Join-Path $TestDrive "root"
    New-Item -ItemType Directory -Path $root | Out-Null
    $entry = Join-Path $root "Start_DaleVision_Agent.ps1"
    New-Item -ItemType File -Path $entry | Out-Null

    $command = Get-TaskCommand -InstallRoot $root -AgentPs1Path $entry

    $expected = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -WorkingDirectory `"$root`" -Command `"& `"$entry`"`""
    $command | Should Be $expected
  }
}
