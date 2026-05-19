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
#ifexist "{#SourceDir}\dalevision-edge-agent.exe"
SetupIconFile={#SourceDir}\dalevision-edge-agent.exe
#endif
Uninstallable=no
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Files]
Source: "{#SourceDir}\*"; DestDir: "{tmp}\dalevision_payload"; Flags: recursesubdirs createallsubdirs ignoreversion

[Run]
Filename: "powershell.exe"; \
  Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{tmp}\dalevision_payload\scripts\install-user.ps1"" -SourceRoot ""{tmp}\dalevision_payload"" -Version ""{#AppVersion}"" -ActivationToken ""{code:GetEffectiveActivationToken}"" -ActivationTokenFile ""{param:ACTIVATION_TOKEN_FILE|}"" -CloudBaseUrl ""{param:CLOUD_BASE_URL|https://api.dalevision.com}"" -OpenDashboard ""{param:OPEN_DASHBOARD|0}"""; \
  Flags: runhidden waituntilterminated

[Code]
var
  ActivationPage: TInputQueryWizardPage;
  ActivationTokenDetectedFromFilename: String;

function TrimExeExtension(const FileName: String): String;
begin
  Result := FileName;
  if CompareText(ExtractFileExt(Result), '.exe') = 0 then
    Result := Copy(Result, 1, Length(Result) - 4);
end;

function DecodeTokenFromFilename(const RawFileName: String): String;
var
  NameNoExt: String;
  MarkerPos: Integer;
  Marker: String;
begin
  Result := '';
  NameNoExt := TrimExeExtension(ExtractFileName(RawFileName));

  Marker := '_tk_';
  MarkerPos := Pos(Marker, LowerCase(NameNoExt));
  if MarkerPos = 0 then
  begin
    Marker := '-tk-';
    MarkerPos := Pos(Marker, LowerCase(NameNoExt));
  end;
  if MarkerPos = 0 then
  begin
    Marker := '_token_';
    MarkerPos := Pos(Marker, LowerCase(NameNoExt));
  end;
  if MarkerPos = 0 then
  begin
    Marker := '-token-';
    MarkerPos := Pos(Marker, LowerCase(NameNoExt));
  end;

  if MarkerPos > 0 then
    Result := Trim(Copy(NameNoExt, MarkerPos + Length(Marker), MaxInt));
end;

function GetActivationTokenFromParam: String;
begin
  Result := Trim(ExpandConstant('{param:ACTIVATION_TOKEN|}'));
end;

function GetActivationTokenFromFilename: String;
begin
  if ActivationTokenDetectedFromFilename = '' then
    ActivationTokenDetectedFromFilename := DecodeTokenFromFilename(ExpandConstant('{srcexe}'));
  Result := ActivationTokenDetectedFromFilename;
end;

function HasPreseededActivationToken: Boolean;
begin
  Result :=
    (GetActivationTokenFromParam <> '') or
    (Trim(ExpandConstant('{param:ACTIVATION_TOKEN_FILE|}')) <> '') or
    (GetActivationTokenFromFilename <> '');
end;

function GetEffectiveActivationToken(Param: String): String;
begin
  Result := GetActivationTokenFromParam;
  if Result = '' then
    Result := GetActivationTokenFromFilename;
  if (Result = '') and Assigned(ActivationPage) then
    Result := Trim(ActivationPage.Values[0]);
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if Assigned(ActivationPage) and (CurPageID = ActivationPage.ID) then
  begin
    if Trim(ActivationPage.Values[0]) = '' then
    begin
      MsgBox(
        'Cole o Token de Ativacao para continuar.' + #13#10 + #13#10 +
        'Se preferir, feche este instalador e renomeie o arquivo para algo como:' + #13#10 +
        'DaleVisionEdgeSetup_tk_SEU_TOKEN.exe',
        mbError,
        MB_OK
      );
      Result := False;
    end;
  end;
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := False;
  if Assigned(ActivationPage) and (PageID = ActivationPage.ID) then
    Result := HasPreseededActivationToken;
end;

procedure InitializeWizard;
var
  AutoToken: String;
begin
  ActivationPage := CreateInputQueryPage(
    wpWelcome,
    'Ativacao da Loja',
    'Cole o token para conectar este computador a sua loja',
    'O token nao aparece em logs do instalador. Se este setup ja foi baixado com token no nome do arquivo, esta etapa sera pulada automaticamente.'
  );
  ActivationPage.Add('&Token de Ativacao:', False);

  AutoToken := GetActivationTokenFromFilename;
  if AutoToken <> '' then
    ActivationPage.Values[0] := AutoToken;
end;
