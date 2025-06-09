import ttkbootstrap as ttk
from ttkbootstrap.constants import *


class AppStyles:
    @staticmethod
    def configure_styles(style):
        """앱 전체에서 사용할 공통 스타일 설정 - 파스텔 그린 테마"""

        # 컬러 팔레트 가져오기
        colors = AppStyles.get_pastel_colors()

        # 삭제 버튼 스타일 (진한 파스텔 그린)
        style.configure('Danger.TButton',
                        font=('Arial', 11, 'bold'),
                        foreground='white',
                        background=colors['outline'],  # #52C7B8
                        borderwidth=0,
                        focuscolor='none',
                        relief='flat',
                        padding=(15, 8))

        style.map('Danger.TButton',
                  background=[('active', colors['pressed']),    # #6BC4B0
                              ('pressed', colors['text_dark']),  # 2E5A4F
                              ('disabled', '#B8B8B8')])

        # 큰 버튼 스타일 (중요한 액션용 - 선명한 파스텔 그린)
        style.configure('Large.TButton',
                        font=('Arial', 12, 'bold'),
                        foreground='white',
                        background=colors['pressed'],  # #6BC4B0
                        borderwidth=0,
                        focuscolor='none',
                        relief='flat',
                        padding=(20, 10))

        style.map('Large.TButton',
                  background=[('active', colors['primary']),   # #7DD3C0
                              ('pressed', colors['outline']),  # #52C7B8
                              ('disabled', '#B8B8B8')])

        # 작은 컨트롤 버튼 스타일 (재생/정지 등 - 차분한 그린)
        style.configure('Control.TButton',
                        font=('Arial', 12, 'bold'),
                        foreground='white',
                        background=colors['text_medium'],  # #4A7C69
                        borderwidth=0,
                        focuscolor='none',
                        relief='flat',
                        padding=(12, 12))

        style.map('Control.TButton',
                  background=[('active', colors['forest_hover']),  # #3A6B5F
                              ('pressed', colors['text_dark']),    # #2E5A4F
                              ('disabled', '#B8B8B8')])

        # ===== 파스텔 스타일들 =====

        # 파스텔 초록 아웃라인 (서브 버튼용)
        style.configure('PastelGreenOutline.TButton',
                        font=('Arial', 11, 'bold'),
                        foreground=colors['outline'],  # #52C7B8
                        background='white',
                        borderwidth=2,
                        bordercolor=colors['large'],   # #A8E6CF
                        focuscolor='none',
                        relief='solid',
                        padding=(15, 8))

        style.map('PastelGreenOutline.TButton',
                  background=[('active', colors['soft']),      # #E8F5F3
                              ('pressed', colors['soft'])],
                  foreground=[('active', colors['pressed']),   # #6BC4B0
                              ('pressed', colors['text_dark'])])  # #2E5A4F

        # 새로운 틸/진한 그린 버튼 스타일 (deep_teal 사용)
        style.configure('DeepTeal.TButton',
                        font=('Arial', 11, 'bold'),
                        foreground='white',
                        background=colors['deep_teal'],  # #007e7f
                        borderwidth=0,
                        focuscolor='none',
                        relief='flat',
                        padding=(15, 8))

        style.map('DeepTeal.TButton',
                  background=[('active', colors['teal_hover']),  # #009a9c
                              ('pressed', colors['text_dark']),   # #2E5A4F
                              ('disabled', '#B8B8B8')])

        # 진한 포레스트 그린 버튼 (어두운 색상)
        style.configure('ForestGreen.TButton',
                        font=('Arial', 11, 'bold'),
                        foreground='white',
                        background=colors['text_dark'],  # #2E5A4F
                        borderwidth=0,
                        focuscolor='none',
                        relief='flat',
                        padding=(15, 8))

        style.map('ForestGreen.TButton',
                  background=[('active', colors['forest_hover']),  # #3A6B5F
                              ('pressed', colors['text_medium']),  # #4A7C69
                              ('disabled', '#B8B8B8')])

    @staticmethod
    def get_pastel_colors():
        """파스텔 그린 컬러 팔레트 반환"""
        return {
            # 기본 파스텔 그린 계열
            'primary': '#7DD3C0',    # 메인 파스텔 그린
            'outline': '#52C7B8',    # 아웃라인/강조용
            'large': '#A8E6CF',      # 라지 버튼용
            'soft': '#E8F5F3',       # 배경용 매우 연한 색

            # 진한 톤들
            'deep_teal': '#007e7f',     # 진한 틸
            'teal_hover': '#009a9c',    # 틸 호버
            'forest_hover': '#3A6B5F',  # 포레스트 호버

            # 텍스트/유틸리티 색상
            'text_dark': '#2E5A4F',     # 어두운 텍스트용 (포레스트 그린)
            'text_medium': '#4A7C69',   # 중간 톤 텍스트용
            'pressed': '#6BC4B0'        # 클릭 효과용
        }
