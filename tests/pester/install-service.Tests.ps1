Describe "install-service Resolve-AgentBatPath" {

  BeforeAll {

    . "$PSScriptRoot/../../scripts/install-service.ps1"

  }



  It "resolves 03_INICIAR.bat from script root when InstallDir empty" {

    $root = Join-Path $TestDrive "root"

    New-Item -ItemType Directory -Path $root | Out-Null

    New-Item -ItemType File -Path (Join-Path $root "03_INICIAR.bat") | Out-Null



    $result = Resolve-AgentBatPath -InstallDir "" -ScriptRoot $root



    $result | Should Be (Join-Path $root "03_INICIAR.bat")

  }



  It "falls back to 03_INICIAR.bat when new name is missing" {

    $install = Join-Path $TestDrive "install"

    New-Item -ItemType Directory -Path $install | Out-Null

    New-Item -ItemType File -Path (Join-Path $install "03_INICIAR.bat") | Out-Null



    $result = Resolve-AgentBatPath -InstallDir $install -ScriptRoot $TestDrive



    $result | Should Be (Join-Path $install "03_INICIAR.bat")

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



    $command | Should Be "`"$entry`""

  }

}

