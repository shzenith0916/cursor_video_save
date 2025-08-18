# 시스템 구성 요소 확인 유틸리티 (VLC 번들됨, FFmpeg는 ffmpeg_manager 사용)
from utils.utils import show_custom_messagebox


class SystemChecker:
    """시스템 구성 요소 확인 클래스 (간소화됨)"""

    @staticmethod
    def is_vlc_installed():
        """VLC가 설치되어 있는지 확인 (번들된 VLC는 항상 사용 가능)"""
        # VLC가 번들되어 있으므로 항상 True 반환
        return True

    @staticmethod
    def get_vlc_version():
        """VLC 버전 정보 반환 (번들 버전)"""
        return "VLC 3.0.21 (번들됨)"

    @staticmethod
    def show_install_guide(parent_frame, ffmpeg_manager=None):
        """FFmpeg 설치 안내 메시지 표시 (VLC는 번들됨)"""
        # FFmpeg 확인은 ffmpeg_manager 사용
        if ffmpeg_manager and ffmpeg_manager.is_available():
            return  # FFmpeg 설치됨

        message = (
            "FFmpeg가 설치되지 않았습니다.\n\n"
            "VLC는 이미 프로그램에 포함되어 있지만,\n"
            "비디오/오디오/이미지 추출 기능을 사용하려면 FFmpeg가 필요합니다.\n\n"
            "FFmpeg 설치 방법:\n"
            "1. https://ffmpeg.org/download.html 접속\n"
            "2. Windows 빌드 다운로드 및 PATH 설정\n"
            "3. 또는 'choco install ffmpeg' 명령 사용\n\n"
            "자세한 안내는 프로그램 폴더의 INSTALL.md 파일을 참고하세요."
        )

        show_custom_messagebox(
            parent_frame,
            "FFmpeg 설치 필요",
            message,
            "warning"
        )

        # FFmpeg 다운로드 페이지 열기 제안
        import webbrowser
        from tkinter import messagebox

        if messagebox.askyesno("FFmpeg 다운로드", "지금 FFmpeg 다운로드 페이지를 열까요?"):
            try:
                webbrowser.open("https://ffmpeg.org/download.html")
            except Exception as e:
                print(f"브라우저 열기 실패: {e}")

    @staticmethod
    def check_and_warn(parent_frame, ffmpeg_manager=None, show_warning=True):
        """필수 구성 요소 설치 확인하고 필요시 경고 표시

        Args:
            parent_frame: 부모 프레임
            ffmpeg_manager: FFmpegManager 인스턴스
            show_warning: 경고 메시지 표시 여부

        Returns:
            tuple: (VLC 설치 여부, FFmpeg 설치 여부)
        """
        vlc_installed = True  # VLC는 번들됨
        ffmpeg_installed = ffmpeg_manager.is_available() if ffmpeg_manager else False

        if not ffmpeg_installed and show_warning:
            SystemChecker.show_install_guide(parent_frame, ffmpeg_manager)

        return vlc_installed, ffmpeg_installed


# 하위 호환성을 위한 별칭
class VLCChecker(SystemChecker):
    """VLCChecker는 SystemChecker의 별칭 (하위 호환성)"""
    pass
