
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
UninstallDisplayIcon={app}\videoplayer.exe
WizardStyle=modern
LanguageDetectionMethod=locale
ShowLanguageDialog=no

[Languages]
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"

[Tasks]
Name: "desktopicon"; Description: "바탕화면 바로가기 생성"; GroupDescription: "추가 아이콘:"
Name: "quicklaunchicon"; Description: "빠른 실행 바로가기 생성"; GroupDescription: "추가 아이콘:"

[Files]
Source: "build\video_player\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "EULA.txt"; DestDir: "{app}"
Source: "INSTALL.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\VideoPlayer"; Filename: "{app}\videoplayer.exe"
Name: "{group}\설치 가이드"; Filename: "{app}\INSTALL.md"
Name: "{group}\{cm:UninstallProgram,VideoPlayer}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\VideoPlayer"; Filename: "{app}\videoplayer.exe"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\VideoPlayer"; Filename: "{app}\videoplayer.exe"; Tasks: quicklaunchicon

[Code]
function CheckFFmpegInstallation: Boolean;
var
  FFmpegPath: String;
  PathEnv: String;
  PathList: TStringList;
  I: Integer;
begin
  Result := False;

  // PATH 환경변수에서 FFmpeg 확인
  if RegQueryStringValue(HKEY_LOCAL_MACHINE, 'SYSTEM\CurrentControlSet\Control\Session Manager\Environment', 'Path', PathEnv) then
  begin
    PathList := TStringList.Create;
    try
      PathList.Delimiter := ';';
      PathList.DelimitedText := PathEnv;

      for I := 0 to PathList.Count - 1 do
      begin
        FFmpegPath := PathList[I] + '\ffmpeg.exe';
        if FileExists(FFmpegPath) then
        begin
          Result := True;
          Break;
        end;
      end;
    finally
      PathList.Free;
    end;
  end;

  // 일반적인 설치 경로들도 확인
  if not Result then
  begin
    Result := FileExists('C:\ffmpeg\bin\ffmpeg.exe') or
              FileExists(ExpandConstant('{pf}\ffmpeg\bin\ffmpeg.exe')) or
              FileExists(ExpandConstant('{pf32}\ffmpeg\bin\ffmpeg.exe'));
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
  FFmpegInstalled: Boolean;
begin
  if CurStep = ssPostInstall then
  begin
    FFmpegInstalled := CheckFFmpegInstallation;

    if not FFmpegInstalled then
    begin
      if MsgBox('비디오플레이어 설치 완료!' + #13#10#13#10 +
                '✓ VLC 미디어 라이브러리가 내장되어 비디오 재생이 바로 가능합니다.' + #13#10#13#10 +
                '!!  추가 기능을 위해 FFmpeg 설치를 권장합니다:' + #13#10 +
                '   • 비디오 구간 추출' + #13#10 +
                '   • 오디오 추출' + #13#10 +
                '   • 이미지 프레임 추출' + #13#10#13#10 +
                '지금 FFmpeg 다운로드 페이지를 열까요?',
                mbConfirmation, MB_YESNO) = IDYES then
      begin
        ShellExec('open', 'https://ffmpeg.org/download.html',
                  '', '', SW_SHOWNORMAL, ewNoWait, ResultCode);
      end;

      MsgBox('✓ 설치 완료!' + #13#10#13#10 +
             '✓ 비디오 재생: 즉시 사용 가능' + #13#10 +
             ' • 추출 기능: FFmpeg 설치 후 사용 가능' + #13#10#13#10 +
             '자세한 설치 가이드는 시작 메뉴 > VideoPlayer > 설치 가이드를 참고하세요.',
             mbInformation, MB_OK);
    end else
    begin
      MsgBox('✓ 설치 완료!' + #13#10#13#10 +
             '✓ VLC 미디어 라이브러리: 내장됨' + #13#10 +
             '✓ FFmpeg: 설치됨' + #13#10#13#10 +
             '모든 기능을 바로 사용할 수 있습니다!',
             mbInformation, MB_OK);
    end;
  end;
end;

[Run]
Filename: "{app}\videoplayer.exe"; WorkingDir: "{app}"; Description: "프로그램 실행"; Flags: nowait postinstall skipifsilent
