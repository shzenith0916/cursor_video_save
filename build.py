#!/usr/bin/env python3
"""
비디오 플레이어 실행파일 빌드 스크립트
pyinstaller를 사용하여 Windows/macOS/Linux 실행파일을 생성합니다.
"""

import os
import sys
import subprocess
import shutil
import stat
from pathlib import Path
import textwrap


def get_vlc_path():
    """VLC 설치 경로를 찾습니다."""
    possible_paths = [
        r"C:\Program Files\VideoLAN\VLC",  # 64비트
        r"C:\Program Files (x86)\VideoLAN\VLC",  # 32비트
    ]

    for path in possible_paths:
        if os.path.exists(path) and os.path.exists(os.path.join(path, 'libvlc.dll')):
            return path
    return None


def clean_build_files():
    """빌드 관련 파일들을 정리합니다."""
    # 실행 중일 수 있는 EXE 프로세스를 우선 종료 (파일 잠금 해제)
    try:
        for exe_name in ['videoplayer.exe', '비디오플레이어.exe']:
            try:
                subprocess.run(
                    ["taskkill", "/IM", exe_name, "/F"],
                    check=False,
                    capture_output=True,
                    text=True,
                    encoding='cp949',
                    errors='ignore'
                )
            except Exception:
                pass
    except Exception:
        pass
    dirs_to_clean = ['build', 'dist', '__pycache__']
    files_to_clean = ['video_player.spec']  # 기존 자동 생성 spec만 정리

    def _handle_remove_error(func, path, exc_info):
        # 읽기 전용/권한 문제 시 권한 수정 후 재시도, 그래도 실패하면 경고만 출력
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except Exception as e:
            print(f"⚠️ 삭제 건너뜀 (잠겨있을 수 있음): {path} ({e})")

    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name, onerror=_handle_remove_error)
                print(f"✓ {dir_name} 디렉터리 삭제됨")
            except Exception as e:
                print(f"⚠️ {dir_name} 삭제 중 오류: {e}")
                print(
                    "   실행 중인 .exe가 있으면 종료 후 다시 시도하세요 (예: taskkill /IM videoplayer.exe /F)")

    # spec 파일 삭제
    for target in files_to_clean:
        for spec_file in Path('.').glob(target):
            if spec_file.name.lower() == 'video_player.spec':
                try:
                    spec_file.unlink()
                    print(f"✓ {spec_file} 파일 삭제됨")
                except Exception as e:
                    print(f"⚠️ {spec_file} 삭제 실패: {e}")


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
        'python-vlc': 'vlc',
    }

    for package_name, import_name in dependencies.items():
        try:
            __import__(import_name)
            print(f"{package_name} 설치됨")
        except ImportError:
            print(f"{package_name} 설치되지 않음 (import: {import_name})")
            return False

    return True


def create_spec_file():
    """PyInstaller spec 파일을 생성합니다. - 옵션 2에서만 실행"""
    try:
        # ttkbootstrap 테마 경로 동적 찾기
        import ttkbootstrap
        import os
        ttkbootstrap_path = os.path.dirname(ttkbootstrap.__file__)
        themes_path = os.path.join(ttkbootstrap_path, 'themes')

        if os.path.exists(themes_path):
            datas_section = f"(r'{themes_path}', 'ttkbootstrap/themes'),\n        ('EULA.txt', '.'),\n        ('INSTALL.md', '.')"
            print(f"✓ ttkbootstrap 테마 경로 찾음: {themes_path}")
        else:
            # 테마 경로를 찾을 수 없으면 기본 파일들만 추가
            datas_section = "('EULA.txt', '.'),\n        ('INSTALL.md', '.')"
            print("⚠️  ttkbootstrap 테마 경로를 찾을 수 없음")
    except ImportError:
        datas_section = "('EULA.txt', '.'),\n        ('INSTALL.md', '.')"
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

    # VLC 경로 찾기
    vlc_path = get_vlc_path()
    if not vlc_path:
        print("⚠️ VLC를 찾을 수 없습니다.")
        return False

    # VLC 바이너리와 데이터 경로 설정
    binaries_section = f"""(r'{vlc_path}\\libvlc.dll', '.'),
        (r'{vlc_path}\\libvlccore.dll', '.')"""

    # VLC 데이터 경로 추가
    datas_section += f""",
        (r'{vlc_path}\\plugins', 'plugins')"""

    spec_content = textwrap.dedent(f"""\
        # -*- mode: python ; coding: utf-8 -*-

        block_cipher = None

        a = Analysis(
            ['main.py'],
            pathex=[],
            binaries=[
                {binaries_section}
            ],
            datas=[
                {datas_section}
            ],
            hiddenimports=[
                'ttkbootstrap.themes',
                'ttkbootstrap.themes.standard',
                'vlc',
                'ctypes.wintypes',
                'ctypes.util',
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
            name='videoplayer',
            debug=False,
            bootloader_ignore_signals=False,
            strip=False,
            upx=True,
            upx_exclude=[],
            runtime_tmpdir=None,
            console=False,
            disable_windowed_traceback=False,
            argv_emulation=False,
            target_arch=None,
            codesign_identity=None,
            entitlements_file=None,
            icon={icon_setting},
        )

        ## 아래는 -onedir 일때 추가 코드
        coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name='videoplayer'
        )
        """)

    with open('video_player.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)

    print("✓ video_player.spec 파일 생성됨")
    return True


def build_executable():
    """실행파일을 빌드합니다. - 기본 빌드 (옵션1 권장)"""
    # 공용 정리 루틴 실행
    clean_build_files()
    print("\n🔨 실행파일 빌드 시작...")

    # VLC 경로 찾기
    vlc_path = get_vlc_path()
    if not vlc_path:
        print("⚠️ VLC를 찾을 수 없습니다. VLC가 설치되어 있는지 확인하세요.")
        return False

    print(f"✓ VLC 경로: {vlc_path}")

    # PyInstaller 명령 구성
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--clean',
        '--noconfirm',
        '--onedir',  # 폴더 구조로 생성
        '--windowed',
        '--name', 'videoplayer',  # 영문 이름 사용
        # VLC 파일 추가 (모든 DLL을 루트에 복사)
        '--add-binary', f'{vlc_path}\\libvlc.dll;.',
        '--add-binary', f'{vlc_path}\\libvlccore.dll;.',
        '--add-data', f'{vlc_path}\\plugins;plugins',
        # 프로젝트 파일 추가
        '--add-data', 'ui_components;ui_components',
        '--add-data', 'utils;utils',
        '--add-data', 'EULA.txt;.',
        '--add-data', 'app.py;.',
        # 필요한 모듈 import
        '--hidden-import', 'ttkbootstrap.themes',
        '--hidden-import', 'ttkbootstrap.themes.standard',
        '--hidden-import', 'vlc',
        '--hidden-import', 'vlc.generated.vlc_structures',
        '--hidden-import', 'vlc.generated.libvlc_structures',
        '--hidden-import', 'ctypes.wintypes',
        '--hidden-import', 'ctypes.util',
        '--hidden-import', 'pythoncom',
        '--hidden-import', 'pywintypes',
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
            cmd, check=True, capture_output=True, text=True,
            encoding='utf-8', errors='ignore')
        print("✓ 빌드 성공!")

        # --onedir의 경우 dist 폴더에 산출
        dist_folder = os.path.join('dist', 'videoplayer')
        exe_file = os.path.join(dist_folder, 'videoplayer.exe')

        if os.path.exists(dist_folder):
            if os.path.exists(exe_file):
                print(f"📁 실행파일 폴더: {dist_folder}")
                print(f"🗂️  실행파일: {exe_file}")

                # 폴더 크기 계산
                folder_size = sum(
                    os.path.getsize(os.path.join(dirpath, filename))
                    for dirpath, dirnames, filenames in os.walk(dist_folder)
                    for filename in filenames
                ) / (1024*1024)  # MB
                print(f"📊 전체 크기: {folder_size:.1f} MB")
            else:
                print("⚠️ 실행파일을 찾을 수 없습니다.")

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


def main():
    """메인 함수"""
    print("✓ 비디오 플레이어 실행파일 빌드 시작")
    print("=" * 50)

    # 1. 의존성 확인
    print("\n1. 의존성 확인...")
    if not check_dependencies():
        print("의존성 확인 실패. 필요한 패키지를 설치하세요.")
        sys.exit(1)

    # 2. 기존 빌드 파일 정리
    print("\n2. 기존 빌드 파일 정리...")
    clean_build_files()

    # 3. 빌드 방법 선택
    print("\n3. 빌드 방법 선택...")
    print("1) 기본 빌드 (권장)")
    print("2) spec 파일 생성만 (수동 빌드용)")

    choice = input("선택하세요 (1, 2, 기본값: 1): ").strip() or '1'

    if choice == '2':
        print("\n🔨 spec 파일 생성...")
        success = create_spec_file()
        if not success:
            print("\n⚠️ spec 파일 생성 실패")
            return
        print("\n➡ 다음 명령으로 수동 빌드를 실행하세요:")
        print("   python -m PyInstaller video_player.spec")
        print("\n출력 위치:")
        print("   dist/videoplayer/videoplayer.exe")
    else:
        # 기본 빌드 (1번 옵션 - 권장)
        success = build_executable()
        if not success:
            print("\n⚠️ 빌드 실패")
            print("1. VLC가 설치되어 있는지 확인하세요")
            print("2. 필요한 Python 패키지가 모두 설치되어 있는지 확인하세요")
            return

    if success:
        print("\n🎉 빌드 완료!")
        print("build 폴더에서 실행파일을 확인하세요.")

        # 실행 방법 안내
        print("\n📋 실행 방법:")
        print("1. dist/videoplayer 폴더의 videoplayer.exe를 더블클릭")
        print("2. 또는 명령창에서: ./dist/videoplayer/videoplayer.exe")
        print("📦 배포 시: dist/videoplayer 폴더 전체를 복사하여 배포하세요")

    else:
        print("\n❌ 빌드 실패")
        sys.exit(1)


if __name__ == "__main__":
    main()
