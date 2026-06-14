[Setup]
AppName=Muktadha
AppVersion=1.0.0
AppVerName=Muktadha 1.0.0
VersionInfoVersion=1.0.0
AppId={{F4A2B3C8-5D6E-4F7A-9B0C-1D2E3F4A5B6C}
AppPublisher=JonamMadeda
DefaultDirName={autopf}\Muktadha
DefaultGroupName=Muktadha
UninstallDisplayIcon={app}\Muktadha.exe
OutputDir=.
OutputBaseFilename=Muktadha_Installer
SolidCompression=yes
PrivilegesRequired=admin

[Files]
Source: "dist\Muktadha.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Muktadha"; Filename: "{app}\Muktadha.exe"
Name: "{autoprograms}\Muktadha\Uninstall Muktadha"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\Muktadha.exe"; Description: "Launch Muktadha"; Flags: postinstall nowait skipifsilent

[UninstallRun]
Filename: "{cmd}"; Parameters: "/c taskkill /f /im Muktadha.exe 2>nul"; Flags: runhidden

[UninstallDelete]
Type: filesandordirs; Name: "{userappdata}\Muktadha"

[Code]
function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  ResultCode: Integer;
begin
  Exec(ExpandConstant('{cmd}'), '/c taskkill /f /im Muktadha.exe 2>nul', '', 0, ewWaitUntilTerminated, ResultCode);
  Result := '';
end;
