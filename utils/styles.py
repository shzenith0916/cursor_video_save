import ttkbootstrap as ttk
from ttkbootstrap.constants import *


class AppStyles:
    @staticmethod
    def get_pastel_colors():
        """파스텔 그린 컬러 팔레트 반환 - 실제 버튼 스타일에서 사용되는 색상들"""
        return {
            # 파스텔 그린 계열 (밝은 톤)
            'pastel_hover': '#7DD3C0',    # 1Pastel 버튼 호버 상태 배경
            'pastel_medium': '#52C7B8',   # 2Pastel 버튼 기본 배경, 아웃라인 버튼 테두리/텍스트
            'pastel_light': '#A8E6CF',    # 아웃라인 버튼 테두리, ForestGreen 버튼 비활성화 배경
            'pastel_bg': '#E8F5F3',       # 아웃라인 버튼 호버/클릭 시 배경 (매우 연한 배경)

            # 진한 그린 계열 (어두운 톤)
            'deep_teal': '#007e7f',       # DeepTeal 버튼 기본 배경
            'teal_hover': '#009a9c',      # DeepTeal 버튼 호버 상태
            'forest_hover': '#3A6B5F',    # ForestGreen, 3Pastel 버튼 호버 상태

            # 주요 버튼 색상들
            'text_dark': '#2E5A4F',       # ForestGreen 버튼 기본 배경 (가장 진한 그린)
            'text_medium': '#4A7C69',     # 3Pastel 버튼 기본 배경, ForestGreen 비활성화 텍스트
            'pastel_base': '#6BC4B0'      # 1Pastel 버튼 기본 배경, 2Pastel 버튼 호버 상태
        }

    @staticmethod
    def configure_styles(style):
        """앱 전체에서 사용할 공통 스타일 설정 - 파스텔 그린 테마"""

        # 컬러 팔레트 가져오기
        colors = AppStyles.get_pastel_colors()

        # 1Pastel.TButton
        style.configure('1Pastel.TButton',
                        font=('Arial', 12, 'bold'),
                        foreground='white',
                        background=colors['pastel_base'],  # #6BC4B0
                        borderwidth=0,
                        focuscolor='none',
                        relief='flat',
                        padding=(15, 8))

        style.map('1Pastel.TButton',
                  background=[('active', colors['pastel_hover']),   # #7DD3C0
                              ('pressed', colors['pastel_medium']),  # #52C7B8
                              ('disabled', colors['pastel_bg'])])

        # 2Pastel.TButton
        style.configure('2Pastel.TButton',
                        font=('Arial', 11, 'bold'),
                        foreground='white',
                        background=colors['text_medium'],
                        borderwidth=0,
                        focuscolor='none',
                        relief='flat',
                        padding=(15, 8))

        style.map('2Pastel.TButton',
                  background=[('active', colors['pastel_base']),    # #6BC4B0
                              ('pressed', colors['text_dark']),    # #2E5A4F
                              ('disabled', colors['pastel_bg'])])

        # 3Pastel.TButton > 미리보기 창 구간저장 버튼 스타일
        style.configure('3Pastel.TButton',
                        font=('Arial', 11, 'bold'),
                        foreground='white',
                        background=colors['text_medium'],  # #4A7C69
                        borderwidth=0,
                        focuscolor='none',
                        relief='flat',
                        padding=(15, 8))

        style.map('3Pastel.TButton',
                  background=[('active', colors['text_dark']),  # #3A6B5F
                              ('pressed', colors['text_dark']),    # #2E5A4F
                              ('disabled', colors['pastel_light'])])

        # ===== 파스텔 스타일들 =====

        # 파스텔 아웃라인 (서브 버튼용)
        style.configure('PastelGreenOutline2.TButton',
                        font=('Arial', 11, 'bold'),
                        foreground=colors['pastel_light'],
                        background='white',
                        borderwidth=2,
                        bordercolor=colors['pastel_light'],
                        focuscolor='none',
                        relief='solid',
                        padding=(15, 8))

        style.map('PastelGreenOutline2.TButton',
                  background=[('active', colors['pastel_bg']),      # #E8F5F3
                              ('pressed', colors['pastel_bg'])],
                  foreground=[('active', colors['pastel_base']),   # #6BC4B0
                              ('pressed', colors['text_dark'])],  # #2E5A4F
                  bordercolor=[('disabled', colors['pastel_base'])])  # # 비활성화 시 테두리 deepteal

        # 파스텔 아웃라인 (서브 버튼용)
        style.configure('PastelGreenOutline.TButton',
                        font=('Arial', 11, 'bold'),
                        foreground=colors['pastel_medium'],
                        background='white',
                        borderwidth=2,
                        bordercolor=colors['pastel_medium'],
                        focuscolor='none',
                        relief='solid',
                        padding=(15, 8))

        style.map('PastelGreenOutline.TButton',
                  background=[('active', colors['pastel_bg']),      # #E8F5F3
                              ('pressed', colors['pastel_bg'])],
                  foreground=[('active', colors['pastel_base']),   # #6BC4B0
                              ('pressed', colors['text_dark'])],  # #2E5A4F
                  bordercolor=[('disabled', colors['pastel_base'])])  # # 비활성화 시 테두리 deepteal

        # 딥틸 > 메인탭 구간저장 버튼 스타일
        style.configure('DeepTeal.TButton',
                        font=('Arial', 11, 'bold'),
                        foreground='white',  # 글씨 햐얀색
                        background=colors['deep_teal'],  # #007e7f
                        borderwidth=0,
                        focuscolor='none',
                        relief='flat',
                        padding=(15, 8))

        style.map('DeepTeal.TButton',
                  background=[('active', colors['teal_hover']),  # #009a9c
                              ('pressed', colors['text_dark']),   # #2E5A4F
                              ('disabled', colors['pastel_light'])],  # #A8E6CF (파스텔 그린)
                  foreground=[('disabled', colors['pastel_light'])])  # #4A7C69 (중간 톤 텍스트)

        # 포레스트 그린
        style.configure('ForestGreen.TButton',
                        font=('Arial', 12, 'bold'),
                        foreground='white',  # 글씨 햐얀색
                        background=colors['pastel_light'],    # 파스텔 녹색 배경
                        borderwidth=0,
                        focuscolor='none',
                        relief='flat',
                        padding=(15, 8))

        style.map('ForestGreen.TButton',
                  background=[('active', colors['pastel_medium']),    # #52C7B8 (부드러운 호버)
                              ('pressed', colors['text_medium']),     # #4A7C69
                              # #2E5A4F (진한 그린)
                              ('disabled', colors['text_dark'])],
                  foreground=[('disabled', 'white')])           # 비활성화 시 흰색 텍스트

        # ============재생 버튼 스타일 ==============
        # 재생 버튼 - Success Outline 스타일 (ttkbootstrap 스타일 구현)
        style.configure('PlayOutline.TButton',
                        font=('Arial', 13, 'bold'),
                        foreground='#198754',  # Bootstrap success 색상
                        background='white',
                        borderwidth=2,
                        bordercolor='#198754',
                        focuscolor='none',
                        relief='solid',
                        padding=(15, 8))

        style.map('PlayOutline.TButton',
                  background=[('active', '#198754'),     # hover 시 배경 녹색
                              ('pressed', '#157347')],   # 클릭 시 더 진한 녹색
                  foreground=[('active', 'white'),       # hover 시 텍스트 흰색
                              ('pressed', 'white')])

        # 정지 버튼 - Danger Outline 스타일
        style.configure('StopOutline.TButton',
                        font=('Arial', 13, 'bold'),
                        foreground='#dc3545',  # Bootstrap danger 색상
                        background='white',
                        borderwidth=2,
                        bordercolor='#dc3545',
                        focuscolor='none',
                        relief='solid',
                        padding=(15, 8))

        style.map('StopOutline.TButton',
                  background=[('active', '#dc3545'),     # hover 시 배경 빨강
                              ('pressed', '#b02a37')],   # 클릭 시 더 진한 빨강
                  foreground=[('active', 'white'),       # hover 시 텍스트 흰색
                              ('pressed', 'white')])

        # 파일 선택 버튼 - Primary 스타일 (폰트 확대)
        style.configure('InfoLarge.TButton',
                        font=('Arial', 11, 'bold'),
                        foreground='white',
                        background='#042d4a',  # 더 진한 색상을 기본으로
                        borderwidth=0,
                        focuscolor='none',
                        relief='flat',
                        padding=(15, 8))

        style.map('InfoLarge.TButton',
                  background=[('active', '#053f65'),     # hover 시 더 연한 색상
                              ('pressed', '#031d31')],   # 클릭 시 가장 진한 색상
                  foreground=[('active', 'white'),       # hover 시 텍스트 흰색
                              ('pressed', 'white')])     # 클릭 시 텍스트 흰색
