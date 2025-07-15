import tkinter as tk


class UiUtils:
    """비디오 처리 관련 공통 기능을 제공하는 클래스"""

    @staticmethod
    def get_scaling_factor(window):
        """Tkinter 내부적으로 사용하는 스케일링 팩터, os에서 자동 조정
           폰트 크기, 일부 위젯 자동스케일링 적용용"""

        root = tk.Tk()
        # Tkinter 내부의 스케일링 팩터(보통 1.0, 1.25, 1.5 등)를 반환
        scaling = root.tk.call('tk', 'scaling')

        # 창 닫기
        root.destroy()  # DPI/Scaling 변경시 완전한 재시작 필요. 창을 닫아야 함.
        # root.withdraw() # 창을 숨김. 메모리에는 남아있음

        return scaling

    @staticmethod
    def get_scaling_factor_by_dpi(window):
        """실제 dpi 기반 배율 반환: 픽셀 단위 크기 조정에 더 정확함
           버튼, 캔버스, 이미지 등 크기 조정"""
        # 현재 DPI 가져오기
        dpi = window.winfo_fpixels("1i")

        # 기본 DPI (Windows에서는 96 DPI가 기본 100% 배율)
        default_dpi = 96

        # 배율 계산
        scale = dpi / default_dpi

        return scale

    @staticmethod
    def center_window(window, parent_window, width, height):
        """창을 부모 창의 중앙에 위치시키는 함수"""
        parent_x = parent_window.winfo_rootx()
        parent_y = parent_window.winfo_rooty()
        parent_width = parent_window.winfo_width()
        parent_height = parent_window.winfo_height()

        x = parent_x + (parent_width // 2) - (width // 2)
        y = parent_y + (parent_height // 2) - (height // 2)

        window.geometry(f'{width}x{height}+{x}+{y}')
