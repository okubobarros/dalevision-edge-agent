#define AppName "DaleVision Edge Setup"
#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#ifndef SourceDir
  #define SourceDir ".\release\win"
#endif
#ifndef OutputDir
  #define OutputDir "."
#endif

[Setup]
AppId={{D2E5CBB2-8A3D-4DCC-8A11-3D07A4C9C5B1}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=DaleVision
WizardStyle=modern
DefaultDirName={localappdata}\DaleVision\installer
DisableDirPage=yes
DisableProgramGroupPage=yes
Compression=lzma
SolidCompression=yes
OutputDir={#OutputDir}
OutputBaseFilename=DaleVisionEdgeSetup-v{#AppVersion}
PrivilegesRequired=lowest
SetupIconFile={#SourceDir}\dalevision-edge-agent.exe
Uninstallable=no
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Files]
Source: "{#SourceDir}\*"; DestDir: "{tmp}\dalevision_payload"; Flags: recursesubdirs createallsubdirs ignoreversion

[Run]
Filename: "powershell.exe"; \
  Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{tmp}\dalevision_payload\scripts\install-user.ps1"" -SourceRoot ""{tmp}\dalevision_payload"" -Version ""{#AppVersion}"" -ActivationToken ""{param:ACTIVATION_TOKEN|}"" -ActivationTokenFile ""{param:ACTIVATION_TOKEN_FILE|}"" -CloudBaseUrl ""{param:CLOUD_BASE_URL|}"""; \
  Flags: runhidden waituntilterminated
