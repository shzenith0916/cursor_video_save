# VLC 라이브러리 번들링 유틸리티 - 간소화됨
import os
import sys
import shutil
import glob
from pathlib import Path


class VLCBundler:
    """VLC 라이브러리를 빌드에 포함시키는 클래스 (빌드 전용)"""

    @staticmethod
    def find_vlc_path():
        """VLC 설치 경로 찾기"""
        vlc_paths = [
            r"C:\Program Files\VideoLAN\VLC",
            r"C:\Program Files (x86)\VideoLAN\VLC",
        ]

        for path in vlc_paths:
            if os.path.exists(path) and os.path.exists(os.path.join(path, 'libvlc.dll')):
                print(f"✓ VLC 설치 경로 발견: {path}")
                return path

        print("⚠️ VLC 설치를 찾을 수 없습니다.")
        return None

    @staticmethod
    def get_vlc_binaries():
        """PyInstaller에 포함할 VLC 바이너리 목록 반환"""
        vlc_path = VLCBundler.find_vlc_path()
        if not vlc_path:
            return []

        binaries = []
        core_dlls = ['libvlc.dll', 'libvlccore.dll']

        for dll in core_dlls:
            dll_path = os.path.join(vlc_path, dll)
            if os.path.exists(dll_path):
                binaries.append((dll_path, '.'))
                print(f"✓ VLC 바이너리 추가: {dll}")

        return binaries

    @staticmethod
    def get_vlc_data():
        """PyInstaller에 포함할 VLC 데이터 목록 반환"""
        vlc_path = VLCBundler.find_vlc_path()
        if not vlc_path:
            return []

        data = []
        plugins_path = os.path.join(vlc_path, 'plugins')
        if os.path.exists(plugins_path):
            data.append((plugins_path, 'vlc/plugins'))
            print(f"✓ VLC 플러그인 폴더 추가: {plugins_path}")

        return data

    @staticmethod
    def print_bundle_info():
        """번들링 정보 출력"""
        vlc_path = VLCBundler.find_vlc_path()

        print("\n" + "="*50)
        print("VLC 번들링 정보")
        print("="*50)
        print(f"VLC 경로: {vlc_path or '없음'}")

        if vlc_path:
            binaries = VLCBundler.get_vlc_binaries()
            data = VLCBundler.get_vlc_data()
            print(f"포함될 바이너리: {len(binaries)}개")
            print(f"포함될 데이터: {len(data)}개")

            # 간단한 크기 계산
            total_size = 0
            for binary_path, _ in binaries:
                if os.path.exists(binary_path):
                    total_size += os.path.getsize(binary_path)

            # 플러그인 폴더 크기 (대략적)
            if data:
                plugins_path = data[0][0]
                try:
                    for root, dirs, files in os.walk(plugins_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            if os.path.exists(file_path):
                                total_size += os.path.getsize(file_path)
                except Exception:
                    pass

            print(f"예상 추가 크기: {total_size / (1024*1024):.1f} MB")

        print("="*50)


if __name__ == "__main__":
    VLCBundler.print_bundle_info()
