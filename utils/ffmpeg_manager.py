import subprocess
import platform
import webbrowser
from tkinter import messagebox
import shutil
import os
from utils.utils import show_custom_messagebox


class FFmpegManager:
    """FFmpeg 설치 상태 확인 및 경로 관리

    기능:
    - 시스템에서 FFmpeg 자동 탐지 (PATH, 일반적인 설치 경로)
    - FFmpeg 실행 경로 관리 및 제공
    - 설치 안내 메시지 제공 (자동 설치는 지원하지 않음)
    """

    def __init__(self, parent_frame=None):
        self.parent_frame = parent_frame
        self.ffmpeg_path = None
        self._check_ffmpeg_status()

    def _check_ffmpeg_status(self):
        """FFmpeg 설치 상태 확인 후 경로 설정. 성공 여부를 bool로 반환"""
        # 1) which/which-like 탐색
        try:
            which_path = shutil.which('ffmpeg')
            if which_path:
                self.ffmpeg_path = which_path
                return True
        except Exception:
            pass

        # 2) 직접 실행 시도 (PATH에 있으면 동작)
        try:
            result = subprocess.run(['ffmpeg', '-version'],
                                    capture_output=True,
                                    text=True,
                                    timeout=5,
                                    encoding='utf-8')
            if result.returncode == 0:
                self.ffmpeg_path = 'ffmpeg'
                return True
        except Exception:
            pass

        # 3) 윈도우의 흔한 설치 경로 점검 (사용자 제공 경로 포함)
        common_paths = [
            r'C:\\ffmpeg\\bin\\ffmpeg.exe',
            r'C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe',
            r'C:\\Program Files (x86)\\ffmpeg\\bin\\ffmpeg.exe',
            r'C:\\Program Files\\ffmpeg-7.1.1-full_build\\bin\\ffmpeg.exe',
        ]
        for path in common_paths:
            if os.path.isfile(path):
                # 유효성 확인
                try:
                    result = subprocess.run([path, '-version'],
                                            capture_output=True,
                                            text=True,
                                            timeout=5,
                                            encoding='utf-8')
                    if result.returncode == 0:
                        self.ffmpeg_path = path
                        return True
                except Exception:
                    continue

        # 탐색 실패
        self.ffmpeg_path = None
        return False

    def ensure_ffmpeg_available(self):
        """FFmpeg 사용 가능 여부와 안내 메시지를 반환한다. (available: bool, message: str)"""
        if self._check_ffmpeg_status():
            return True, f"FFmpeg 사용 가능: {self.ffmpeg_path}"
        return False,  "FFmpeg를 찾을 수 없습니다. 설치 또는 PATH 추가 후 다시 시도하세요."

    def is_available(self):
        """FFmpeg 사용 가능 여부 확인"""
        return self.ffmpeg_path is not None

    def get_version_info(self):
        """FFmpeg 정보 반환"""
        if not self._check_ffmpeg_status():
            return "FFmpeg가 설치되지 않음"

        try:
            exe = self.ffmpeg_path if os.path.isabs(
                self.ffmpeg_path or '') else 'ffmpeg'
            result = subprocess.run([exe, '-version'],
                                    capture_output=True,
                                    text=True,
                                    timeout=10,
                                    encoding='utf-8')
            if result.returncode == 0 and result.stdout:
                return result.stdout.split('\n')[0]
        except Exception as e:
            return f"버전정보 확인 실패: {e}"

        return "버전정보 없음"

    def require_ffmpeg_or_show_error(self, parent_frame, extraction_type):
        """FFmpeg가 필요한 작업에서 사용. 없으면 에러 메시지 표시하고 False 반환"""
        if self.is_available():
            return True

        available, message = self.ensure_ffmpeg_available()
        show_custom_messagebox(
            parent_frame, "FFmpeg 필요",
            f"{extraction_type} 추출을 위해 FFmpeg가 필요합니다.\n\n{message}",
            "warning")
        return False
