#!/usr/bin/env python3
"""
비디오 플레이어 실행파일 빌드 스크립트
pyinstaller를 사용하여 Windows/macOS/Linux 실행파일을 생성합니다.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def clean_build_files():
    """빌드 관련 파일들을 정리합니다."""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    files_to_clean = ['*.spec']

    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"✓ {dir_name} 디렉터리 삭제됨")

    # .spec 파일 삭제
    for spec_file in Path('.').glob('*.spec'):
        spec_file.unlink()
        print(f"✓ {spec_file} 파일 삭제됨")


def check_dependencies():
    """필요한 의존성이 설치되어 있는지 확인합니다."""
    try:
        import PyInstaller
        print("PyInstaller 설치됨")
    except ImportError:
        print("PyInstaller가 설치되지 않음")
        print("설치 명령: pip install pyinstaller")
        return False

    # 다른 의존성들 확인 (패키지명 : import명)
    dependencies = {
        'opencv-python': 'cv2',
        'numpy': 'numpy',
        'Pillow': 'PIL',
        'ttkbootstrap': 'ttkbootstrap',
        'pygame': 'pygame',
        'requests': 'requests'
    }

    for package_name, import_name in dependencies.items():
        try:
            __import__(import_name)
            print(f"{package_name} 설치됨")
        except ImportError:
            print(f"{package_name} 설치되지 않음 (import: {import_name})")
            return False

    return True


def create_inno_setup_script(build_folder):
    """Inno Setup 스크립트(.iss)를 생성합니다."""
    iss_content = f'''
[Setup]
AppName=VideoPlayer
AppVersion=1.0
AppPublisher=RSREHAB co., ltd.
AppPublisherURL=https://rsrehab.com/
DefaultDirName={{autopf}}\\VideoPlayer
DefaultGroupName=VideoPlayer
LicenseFile=EULA.txt
AllowNoIcons=yes
OutputDir=.\\installer
OutputBaseFilename=VideoPlayer_Setup
Compression=lzma
SolidCompression=yes
SetupIconFile=rslogo.ico
UninstallDisplayIcon={{app}}\\비디오플레이어.exe
WizardStyle=modern
LanguageDetectionMethod=locale
ShowLanguageDialog=no

[Languages]
Name: "korean"; MessagesFile: "compiler:Languages\\Korean.isl"

[Tasks]
Name: "desktopicon"; Description: "바탕화면 바로가기 생성"; GroupDescription: "추가 아이콘:"
Name: "quicklaunchicon"; Description: "빠른 실행 바로가기 생성"; GroupDescription: "추가 아이콘:"

[Files]
Source: "{build_folder}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "EULA.txt"; DestDir: "{{app}}"

[Icons]
Name: "{{group}}\\VideoPlayer"; Filename: "{{app}}\\비디오플레이어.exe"
Name: "{{group}}\\{{cm:UninstallProgram,VideoPlayer}}"; Filename: "{{uninstallexe}}"
Name: "{{autodesktop}}\\VideoPlayer"; Filename: "{{app}}\\비디오플레이어.exe"; Tasks: desktopicon
Name: "{{userappdata}}\\Microsoft\\Internet Explorer\\Quick Launch\\VideoPlayer"; Filename: "{{app}}\\비디오플레이어.exe"; Tasks: quicklaunchicon

[Run]
Filename: "{{app}}\\비디오플레이어.exe"; Description: "프로그램 실행"; Flags: nowait postinstall skipifsilent
'''

    iss_file = 'video_player_installer.iss'
    with open(iss_file, 'w', encoding='utf-8-sig') as f:  # BOM 포함하여 저장
        f.write(iss_content)

    print(f"Inno Setup 스크립트 생성됨: {iss_file}")
    print("인스톨러 생성 방법:")
    print("1. Inno Setup을 설치하세요: https://jrsoftware.org/isinfo.php")
    print(f"2. Inno Setup에서 {iss_file}를 열고 컴파일하세요")
    print("3. installer 폴더에 설치파일이 생성됩니다")


def compile_inno_setup():
    """Inno Setup 컴파일러를 실행합니다."""
    iss_file = 'video_player_installer.iss'

    # 일반적인 Inno Setup 컴파일러 경로들
    compiler_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
        r"C:\Program Files\Inno Setup 5\ISCC.exe",
    ]

    compiler_path = None
    for path in compiler_paths:
        if os.path.exists(path):
            compiler_path = path
            break

    if not compiler_path:
        print("⚠️ Inno Setup 컴파일러를 찾을 수 없습니다.")
        print("수동으로 설치파일을 생성해주세요.")
        return False

    try:
        print(f"🔨 Inno Setup 컴파일 시작: {iss_file}")

        # 인코딩 문제 해결을 위해 여러 방법 시도
        encodings = ['utf-8', 'cp949', 'euc-kr']

        for encoding in encodings:
            try:
                result = subprocess.run(
                    [compiler_path, iss_file],
                    check=True,
                    capture_output=True,
                    text=True,
                    encoding=encoding,
                    errors='ignore'  # 인코딩 오류 무시
                )
                print("인스톨러 컴파일 성공!")
                print("installer 폴더를 확인하세요")

                # 성공한 경우 출력 표시
                if result.stdout:
                    print(f"컴파일 출력 (인코딩: {encoding}):")
                    print(result.stdout)

                return True

            except UnicodeDecodeError:
                print(f"인코딩 {encoding} 실패, 다음 인코딩 시도...")
                continue
            except subprocess.CalledProcessError as e:
                print(f"인스톨러 컴파일 실패 (인코딩: {encoding}): {e}")
                if e.stderr:
                    print("에러 메시지:")
                    print(e.stderr)
                return False

        print("모든 인코딩 시도 실패")
        return False

    except Exception as e:
        print(f"인스톨러 컴파일 중 예외 발생: {e}")
        return False


def create_spec_file():
    """PyInstaller spec 파일을 생성합니다."""

    # ttkbootstrap 테마 경로 동적 찾기
    try:
        import ttkbootstrap
        import os
        ttkbootstrap_path = os.path.dirname(ttkbootstrap.__file__)
        themes_path = os.path.join(ttkbootstrap_path, 'themes')

        if os.path.exists(themes_path):
            datas_section = f"(r'{themes_path}', 'ttkbootstrap/themes'),\n ('EULA.txt', '.'),"
            print(f"✓ ttkbootstrap 테마 경로 찾음: {themes_path}")
        else:
            # 테마 경로를 찾을 수 없으면 EULA.txt 파일만 추가
            datas_section = "('EULA.txt', '.'),"
            print("⚠️  ttkbootstrap 테마 경로를 찾을 수 없음")
    except ImportError:
        datas_section = ""
        print("⚠️  ttkbootstrap 모듈을 찾을 수 없음")

    # 아이콘 파일 경로 확인
    icon_path = None
    icon_files = ['rslogo.ico', 'app_icon.ico']
    for icon_file in icon_files:
        if os.path.exists(icon_file):
            icon_path = icon_file
            break

    # 아이콘 설정 생성
    icon_setting = f'r"{icon_path}"' if icon_path else 'None'

    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        {datas_section}
    ],
    hiddenimports=[
        'ttkbootstrap.themes',
        'ttkbootstrap.themes.standard',
        'pygame.mixer',
        'pygame._view',
        'cv2',
        'numpy',
        'PIL._tkinter_finder',
        'app',
        'ui_components',
        'ui_components.main_tab',
        'ui_components.new_tab',
        'ui_components.base_tab',
        'ui_components.segment_table',
        'ui_components.command_handlers',
        'ui_components.preview_window',
        'utils',
        'utils.utils',
        'utils.styles',
        'utils.ui_utils',
        'utils.event_system',
        'utils.segment_data_helper',
        'utils.video_playback_helper',
        'extract.extractor',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='비디오플레이어',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI 앱이므로 콘솔 창을 숨김
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon={icon_setting},
)
'''

    with open('video_player.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)

    print("✓ video_player.spec 파일 생성됨")
    if icon_path:
        print(f"✓ 아이콘 파일 포함: {icon_path}")
    else:
        print("ℹ️  아이콘 파일 없음")


def build_executable():
    """실행파일을 빌드합니다."""
    print("\n🔨 실행파일 빌드 시작...")

    # PyInstaller 명령 실행
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--clean',
        '--onedir',  # 폴더 구조로 생성
        '--windowed',
        '--name', '비디오플레이어',
        '--add-data', 'ui_components;ui_components',
        '--add-data', 'utils;utils',
        '--add-data', 'extract;extract',
        '--add-data', 'EULA.txt;.',
        '--add-data', 'app.py;.',
        '--hidden-import', 'ttkbootstrap.themes',
        '--hidden-import', 'ttkbootstrap.themes.standard',
        '--hidden-import', 'pygame.mixer',
        '--hidden-import', 'pygame._view',
        '--hidden-import', 'cv2',
        '--hidden-import', 'numpy',
        '--hidden-import', 'PIL._tkinter_finder',
        'main.py'
    ]

    # 아이콘 파일이 있으면 추가
    icon_files = ['rslogo.ico', 'app_icon.ico']
    icon_found = False

    for icon_file in icon_files:
        if os.path.exists(icon_file):
            cmd.extend(['--icon', icon_file])
            print(f"✓ 아이콘 파일 찾음: {icon_file}")
            icon_found = True
            break

    if not icon_found:
        print("ℹ️  아이콘 파일 없음 (rslogo.ico 또는 app_icon.ico)")

    # 설정 파일이 있으면 추가
    if os.path.exists('config.json'):
        cmd.extend(['--add-data', 'config.json;.'])
        print("✓ 설정 파일 찾음: config.json")

    try:
        result = subprocess.run(
            cmd, check=True, capture_output=True, text=True)
        print("✓ 빌드 성공!")

        # --onedir의 경우 폴더 구조로 생성됨
        dist_folder = os.path.join('dist', '비디오플레이어')
        build_folder = os.path.join('build', '비디오플레이어')
        exe_file = os.path.join(build_folder, '비디오플레이어.exe')

        # dist 폴더를 build 폴더로 복사 (Inno Setup 준비)
        if os.path.exists(dist_folder):
            if os.path.exists('build'):
                shutil.rmtree('build')
            os.makedirs('build', exist_ok=True)
            shutil.copytree(dist_folder, build_folder)
            print(f"📁 Inno Setup용 빌드 폴더 생성: {build_folder}")

            if os.path.exists(exe_file):
                print(f"📁 실행파일 폴더: {build_folder}")
                print(f"🗂️  실행파일: {exe_file}")

                # 폴더 크기 계산
                folder_size = sum(
                    os.path.getsize(os.path.join(dirpath, filename))
                    for dirpath, dirnames, filenames in os.walk(build_folder)
                    for filename in filenames
                ) / (1024*1024)  # MB
                print(f"📊 전체 크기: {folder_size:.1f} MB")

                # Inno Setup 스크립트 생성
                create_inno_setup_script(build_folder)
            else:
                print("⚠️  실행파일을 찾을 수 없습니다.")

        # 빌드 로그 출력
        if result.stdout:
            print("\n빌드 로그:")
            print(result.stdout)

    except subprocess.CalledProcessError as e:
        print(f"❌ 빌드 실패: {e}")
        if e.stderr:
            print("에러 메시지:")
            print(e.stderr)
        return False

    return True


def build_with_spec():
    """spec 파일을 사용하여 빌드합니다."""
    print("\n🔨 spec 파일로 빌드 시작...")

    cmd = [sys.executable, '-m', 'PyInstaller', 'video_player.spec']

    try:
        result = subprocess.run(
            cmd, check=True, capture_output=True, text=True)
        print("✓ spec 파일 빌드 성공!")

        # 결과 파일 확인
        exe_folder = os.path.join('dist', '비디오플레이어')
        exe_file = os.path.join(exe_folder, '비디오플레이어.exe')

        if os.path.exists(exe_file):
            print(f"📁 실행파일 폴더: {exe_folder}")
            print(f"🗂️  실행파일: {exe_file}")

            # 폴더 크기 계산
            folder_size = sum(
                os.path.getsize(os.path.join(dirpath, filename))
                for dirpath, dirnames, filenames in os.walk(exe_folder)
                for filename in filenames
            ) / (1024*1024)  # MB
            print(f"📊 전체 크기: {folder_size:.1f} MB")

    except subprocess.CalledProcessError as e:
        print(f"❌ 빌드 실패: {e}")
        if e.stderr:
            print("에러 메시지:")
            print(e.stderr)
        return False

    return True


def main():
    """메인 함수"""
    print("🚀 비디오 플레이어 실행파일 빌드 시작")
    print("=" * 50)

    # 1. 의존성 확인
    print("\n1. 의존성 확인...")
    if not check_dependencies():
        print("❌ 의존성 확인 실패. 필요한 패키지를 설치하세요.")
        sys.exit(1)

    # 2. 기존 빌드 파일 정리
    print("\n2. 기존 빌드 파일 정리...")
    clean_build_files()

    # 3. 빌드 방법 선택
    print("\n3. 빌드 방법 선택...")
    print("1) 기본 빌드 (권장)")
    print("2) spec 파일 생성 후 빌드")
    print("3) 빌드 후 Inno Setup 인스톨러 자동 생성")

    choice = input("선택하세요 (1, 2, 3, 기본값: 1): ").strip() or '1'

    if choice == '2':
        # spec 파일 생성 후 빌드
        create_spec_file()
        success = build_with_spec()
    elif choice == '3':
        # 빌드 후 인스톨러 자동 생성
        success = build_executable()
        if success:
            print("\n🔧 Inno Setup 인스톨러 자동 생성 시도...")
            compile_inno_setup()
    else:
        # 기본 빌드
        success = build_executable()

    if success:
        print("\n🎉 빌드 완료!")
        print("build 폴더에서 실행파일을 확인하세요.")

        # 실행 방법 안내
        print("\n📋 실행 방법:")
        print("1. build/비디오플레이어 폴더의 비디오플레이어.exe를 더블클릭")
        print("2. 또는 명령창에서: ./build/비디오플레이어/비디오플레이어.exe")
        print("📦 배포 시: build/비디오플레이어 폴더 전체를 복사하여 배포하세요")

        if os.path.exists('video_player_installer.iss'):
            print("\n🔧 Inno Setup 인스톨러:")
            print("- video_player_installer.iss 파일로 Windows 인스톨러를 생성할 수 있습니다")

    else:
        print("\n❌ 빌드 실패")
        sys.exit(1)


if __name__ == "__main__":
    main()
