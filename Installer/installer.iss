#define MyAppName "Remeinium FocusPro"
#define MyAppVersion "1.3.0"
#define MyAppPublisher "Remeinium Corp."
#define MyAppURL "https://focuspro.whatsthetime.online"
#define MyAppExeName "Remeinium FocusPro.exe"
#define MyLauncherExeName "FocusPro Launcher.exe"
#define MyAppAssocName MyAppName + ""
#define MyAppAssocExt ".myp"
#define MyAppAssocKey StringChange(MyAppAssocName, " ", "") + MyAppAssocExt

[Setup]
AppId={{5F58F298-9439-436A-B5E6-1E42F52DFF50}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
ChangesAssociations=yes
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=C:\Users\Kusal Darshana\Desktop\Focus\License.txt
InfoBeforeFile=C:\Users\Kusal Darshana\Desktop\Focus\README.md
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=C:\Users\Kusal Darshana\Desktop\Focus\Installer
OutputBaseFilename=FocusProSetup
SetupIconFile=C:\Users\Kusal Darshana\Desktop\Focus\focuspro.ico
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startup"; Description: "Start FocusPro automatically with Windows"; GroupDescription: "Startup Options"; Flags: checkedonce

[Files]
; ✅ Main app EXE
Source: "C:\Users\Kusal Darshana\Desktop\Focus\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; ✅ Protocol launcher
Source: "C:\Users\Kusal Darshana\Desktop\Focus\dist\{#MyLauncherExeName}"; DestDir: "{app}"; Flags: ignoreversion

; ✅ Other files
Source: "C:\Users\Kusal Darshana\Desktop\Focus\focuspro.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Kusal Darshana\Desktop\Focus\focuspro.wav"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Kusal Darshana\Desktop\Focus\graph.html"; DestDir: "{app}"; Flags: ignoreversion

[Registry]
; File type association
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocExt}\OpenWithProgids"; ValueType: string; ValueName: "{#MyAppAssocKey}"; ValueData: ""; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}"; ValueType: string; ValueName: ""; ValueData: "{#MyAppAssocName}"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""

; ✅ Custom URL Protocol: focuspro:// (points to launcher)
Root: HKCU; Subkey: "Software\Classes\focuspro"; ValueType: string; ValueName: ""; ValueData: "URL:FocusPro Protocol"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\focuspro"; ValueType: string; ValueName: "URL Protocol"; ValueData: ""; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\focuspro\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyLauncherExeName},1"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\focuspro\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyLauncherExeName}"" ""%1"""; Flags: uninsdeletekey

; Startup registry entry
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "{#MyAppName}"; ValueData: """{app}\{#MyAppExeName}"""; Tasks: startup; Flags: uninsdeletevalue

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:ProgramOnTheWeb,{#MyAppName}}"; Filename: "{#MyAppURL}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
