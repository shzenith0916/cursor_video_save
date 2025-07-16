[Setup]
AppName=VideoPlayer
AppVersion=1.0
AppPublisher=RSREHAB co., ltd.
AppPublisherURL=https://rsrehab.com/
DefaultDirName={autopf}\VideoPlayer
DefaultGroupName=VideoPlayer
LicenseFile=EULA.txt
AllowNoIcons=yes
OutputDir=.\installer
OutputBaseFilename=VideoPlayer_Setup
Compression=lzma
SolidCompression=yes
SetupIconFile=rslogo.ico
UninstallDisplayIcon={app}\비디오플레이어.exe
WizardStyle=modern
LanguageDetectionMethod=locale
ShowLanguageDialog=no

[Languages]
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"

[Tasks]
Name: "desktopicon"; Description: "바탕화면 바로가기 생성"; GroupDescription: "추가 아이콘:"
Name: "quicklaunchicon"; Description: "빠른 실행 바로가기 생성"; GroupDescription: "추가 아이콘:"

[Files]
Source: "build\비디오플레이어\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "EULA.txt"; DestDir: "{app}"

[Icons]
Name: "{group}\VideoPlayer"; Filename: "{app}\비디오플레이어.exe"
Name: "{group}\{cm:UninstallProgram,VideoPlayer}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\VideoPlayer"; Filename: "{app}\비디오플레이어.exe"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\VideoPlayer"; Filename: "{app}\비디오플레이어.exe"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\비디오플레이어.exe"; Description: "프로그램 실행"; Flags: nowait postinstall skipifsilent
