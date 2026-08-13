; ==========================================
; 🛠️ SCRIPT INNO SETUP POUR SOKOMASTER
; Développé pour CRYPT Enterprise
; ==========================================

#define MyAppName "SokoMaster"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "CRYPT Enterprise"
#define MyAppURL "https://crypt.cd"
#define MyAppExeName "main.exe" 

[Setup]
AppId={{A8B3C4D5-E6F7-4A8B-9C0D-1E2F3A4B5C6D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppPublisher}\{#MyAppName}
DisableProgramGroupPage=yes
OutputBaseFilename=SokoMaster_Setup_v1.0
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Inclusion de TOUT le dossier d'exécution généré par Nuitka dans le dossier 'dist/main.dist'
Source: "dist\main.dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
