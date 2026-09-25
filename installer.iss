; Inno Setup Script for Pa-O Converter
; Creates a standard Windows installer (.exe) with automatic in-place upgrade/replacement support.

#define MyAppName "Pa-O Converter"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Pa-O Language Community"
#define MyAppURL "https://github.com/khunaungpaing/PaO-Converter"
#define MyAppExeName "PaOConverter.exe"
#define MyAppId "{{C78F369E-A341-4DAF-809D-1C9D2F0E5D1B}}"

[Setup]
; Fixed AppId uniquely identifies this application.
; When installing a newer version, Inno Setup automatically detects the
; previous installation and performs a clean in-place upgrade/replacement.
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\PaOConverter
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=Output
OutputBaseFilename=PaOConverter_v{#MyAppVersion}_Windows_Setup
SetupIconFile=assets\img\app.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
LicenseFile=LICENSE

; Upgrade & Clean Replacement behavior
UsePreviousAppDir=yes
CloseApplications=yes
CloseApplicationsFilter=*.exe
RestartApplications=no
UninstallDisplayName={#MyAppName} v{#MyAppVersion}
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Copy all binaries and assets bundled by PyInstaller
Source: "dist\PaOConverter\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
