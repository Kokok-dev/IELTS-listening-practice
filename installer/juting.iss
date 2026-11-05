#define AppVersion "0.3.0"
#define SourceDir "..\outputs\staging-v0.3.0\句听"

[Setup]
AppId={{9EDC10C1-8D40-4280-8DF2-C00E0C6D7048}
AppName=句听
AppVersion={#AppVersion}
AppPublisher=句听
DefaultDirName={localappdata}\Programs\Juting
DefaultGroupName=句听
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=..\outputs
OutputBaseFilename=句听-安装程序-v{#AppVersion}
SetupIconFile=..\assets\juting.ico
UninstallDisplayIcon={app}\句听.exe
Compression=lzma2/fast
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
CloseApplications=yes
RestartApplications=no
SetupLogging=yes

[Languages]
Name: "chinesesimp"; MessagesFile: "ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "快捷方式："

[Files]
Source: "{#SourceDir}\句听.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#SourceDir}\models\*"; DestDir: "{app}\models"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#SourceDir}\_licenses\*"; DestDir: "{app}\_licenses"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#SourceDir}\使用说明.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\THIRD_PARTY_NOTICES.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "安装说明.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\句听"; Filename: "{app}\句听.exe"; Parameters: "--data-dir ""{localappdata}\Juting\data"""; WorkingDir: "{app}"
Name: "{autodesktop}\句听"; Filename: "{app}\句听.exe"; Parameters: "--data-dir ""{localappdata}\Juting\data"""; WorkingDir: "{app}"; Tasks: desktopicon
Name: "{group}\卸载句听"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\句听.exe"; Parameters: "--data-dir ""{localappdata}\Juting\data"""; Description: "启动句听"; Flags: nowait postinstall skipifsilent
