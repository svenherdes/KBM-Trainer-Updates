#define MyAppName "KBM Trainer"
#define MyAppVersion "1.4.3"
#define MyAppNumericVersion "1.4.3.0"
#define MyAppPublisher "Sven Herdes"
#define MyAppExeName "KBM-Trainer.exe"

[Setup]
AppId={{A0A82A8F-3A52-4E69-98B0-20C7E58B1D38}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\KBM Trainer
DefaultGroupName=KBM Trainer
DisableProgramGroupPage=yes
DisableDirPage=no
UsePreviousAppDir=yes
UsePreviousTasks=yes
PrivilegesRequired=lowest
OutputDir=dist\installer
OutputBaseFilename=KBM-Trainer-Setup-1.4.3
SetupIconFile=assets\kbm_trainer.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
CloseApplications=no
RestartApplications=no
VersionInfoVersion={#MyAppNumericVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=Installationsprogramm fuer KBM Trainer
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppNumericVersion}
VersionInfoCopyright=Copyright 2026 Sven Herdes

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Tasks]
Name: "desktopicon"; Description: "Desktop-Symbol erstellen"; GroupDescription: "Zusaetzliche Aufgaben:"; Flags: checkedonce

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "KBM-Update-Helper.cmd"; DestDir: "{app}"; Flags: ignoreversion
Source: "DATENSCHUTZ_QUELLEN_2026-09.txt"; DestDir: "{app}"; Flags: ignoreversion

[InstallDelete]
; Einmalige Bereinigung der experimentellen 1.3.7.7/1.3.7.8-Datei.
Type: files; Name: "{app}\KBM-Trainer-App.exe"

[Icons]
Name: "{group}\KBM Trainer"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\KBM Trainer"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
; Nur bei einer normalen manuellen Installation. Bei einem stillen Auto-Update
; startet ausschliesslich KBM-Update-Helper.cmd die neue Programmdatei.
Filename: "{app}\{#MyAppExeName}"; Description: "KBM Trainer jetzt starten"; Flags: nowait postinstall skipifsilent
