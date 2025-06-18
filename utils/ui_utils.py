class UiUtils:
    """비디오 처리 관련 공통 기능을 제공하는 클래스"""
    @staticmethod
    def get_scaling_factor(window):
        # 현재 DPI 가져오기
        dpi = window.winfo_fpixels("1i")

        # 기본 DPI (Windows에서는 96 DPI가 기본 100% 배율)
        default_dpi = 96

        # 배율 계산
        scale = dpi / default_dpi
        return scale
