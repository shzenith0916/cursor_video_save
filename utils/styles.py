import ttkbootstrap as ttk
from ttkbootstrap.constants import *


class AppStyles:
    @staticmethod
    def configure_styles(style):
        """앱 전체에서 사용할 공통 스타일 설정"""

        # 기본 버튼 스타일 (틸 그린)
        style.configure('App.TButton',
                        font=('Arial', 11, 'bold'),
                        foreground='white',
                        background='#26A69A',  # 틸 그린
                        borderwidth=0,
                        focuscolor='none',
                        relief='flat',
                        padding=(15, 8))

        style.map('App.TButton',
                  background=[('active', '#00796B'),
                              ('pressed', '#004D40'),
                              ('disabled', '#B8B8B8')])

        # 저장/추출 버튼 스타일 (밝은 틸)
        style.configure('Success.TButton',
                        font=('Arial', 11, 'bold'),
                        foreground='white',
                        background='#4DB6AC',  # 밝은 틸
                        borderwidth=0,
                        focuscolor='none',
                        relief='flat',
                        padding=(15, 8))

        style.map('Success.TButton',
                  background=[('active', '#26A69A'),
                              ('pressed', '#00796B'),
                              ('disabled', '#B8B8B8')])

        # 삭제 버튼 스타일 (진한 틸)
        style.configure('Danger.TButton',
                        font=('Arial', 11, 'bold'),
                        foreground='white',
                        background='#00695C',  # 진한 틸
                        borderwidth=0,
                        focuscolor='none',
                        relief='flat',
                        padding=(15, 8))

        style.map('Danger.TButton',
                  background=[('active', '#004D40'),
                              ('pressed', '#00363A'),
                              ('disabled', '#B8B8B8')])

        # 미리보기 버튼 스타일 (터키즈)
        style.configure('Preview.TButton',
                        font=('Arial', 12, 'bold'),
                        foreground='white',
                        background='#80CBC4',  # 터키즈
                        borderwidth=0,
                        focuscolor='none',
                        relief='flat',
                        padding=(20, 10))

        style.map('Preview.TButton',
                  background=[('active', '#4DB6AC'),
                              ('pressed', '#26A69A'),
                              ('disabled', '#B8B8B8')])

        # 큰 버튼 스타일 (중요한 액션용 - 밝은 시안)
        style.configure('Large.TButton',
                        font=('Arial', 14, 'bold'),
                        foreground='white',
                        background='#00BCD4',  # 시안
                        borderwidth=0,
                        focuscolor='none',
                        relief='flat',
                        padding=(25, 12))

        style.map('Large.TButton',
                  background=[('active', '#0097A7'),
                              ('pressed', '#006064'),
                              ('disabled', '#B8B8B8')])

        # 작은 컨트롤 버튼 스타일 (재생/정지 등 - 원형 모던 스타일)
        style.configure('Control.TButton',
                        font=('Arial', 14, 'bold'),
                        foreground='white',
                        background='#37474F',  # 진한 회색
                        borderwidth=0,
                        focuscolor='none',
                        relief='flat',
                        padding=(12, 12))  # 정사각형에 가까운 패딩

        style.map('Control.TButton',
                  background=[('active', '#455A64'),
                              ('pressed', '#263238'),
                              ('disabled', '#B8B8B8')])

        # 큰 컨트롤 버튼 스타일 (중요한 재생 버튼용)
        style.configure('PlayControl.TButton',
                        font=('Arial', 16, 'bold'),
                        foreground='white',
                        background='#2E7D32',  # 진한 녹색
                        borderwidth=0,
                        focuscolor='none',
                        relief='flat',
                        padding=(16, 16))

        style.map('PlayControl.TButton',
                  background=[('active', '#388E3C'),
                              ('pressed', '#1B5E20'),
                              ('disabled', '#B8B8B8')])

        # ✨ 새로 추가: 파스텔 초록색 스타일들 (ttkbootstrap 호환)

        # 파스텔 민트 그린 (메인 저장 버튼용)
        style.configure('PastelGreen.TButton',
                        font=('Arial', 20, 'bold'),
                        foreground='white',
                        background='red',
                        borderwidth=0,
                        focuscolor='none',
                        relief='flat',
                        padding=(30, 20))

        style.map('PastelGreen.TButton',
                  background=[('active', '#7DDCC9'),
                              ('pressed', '#6BC4B0'),
                              ('disabled', '#B8B8B8')])

        # 파스텔 초록 아웃라인 (서브 버튼용)
        style.configure('PastelGreenOutline.TButton',
                        font=('Arial', 11, 'bold'),
                        foreground='#6BC4B0',
                        background='white',
                        borderwidth=2,
                        bordercolor='#98E4D6',
                        focuscolor='none',
                        relief='solid',
                        padding=(15, 8))

        style.map('PastelGreenOutline.TButton',
                  background=[('active', '#F0FDF4'),
                              ('pressed', '#E6F7ED')],
                  foreground=[('active', '#5BB3A0'),
                              ('pressed', '#4A9B89')])

        # 파스텔 초록 라지 (큰 저장/완료 버튼용)
        style.configure('PastelGreenLarge.TButton',
                        font=('Arial', 14, 'bold'),
                        foreground='white',
                        background='#98E4D6',
                        borderwidth=0,
                        focuscolor='none',
                        relief='flat',
                        padding=(25, 12))

        style.map('PastelGreenLarge.TButton',
                  background=[('active', '#7DDCC9'),
                              ('pressed', '#6BC4B0'),
                              ('disabled', '#B8B8B8')])

        # 파스텔 세이지 그린 (대안 색상)
        style.configure('PastelSage.TButton',
                        font=('Arial', 11, 'bold'),
                        foreground='white',
                        background='#A8E6CF',  # 더 연한 파스텔 초록
                        borderwidth=0,
                        focuscolor='none',
                        relief='flat',
                        padding=(15, 8))

        style.map('PastelSage.TButton',
                  background=[('active', '#98E4D6'),
                              ('pressed', '#88D8C0'),
                              ('disabled', '#B8B8B8')])

    @staticmethod
    def get_pastel_colors():
        """파스텔 초록 컬러 팔레트 반환 (다른 곳에서 사용할 수 있도록)"""
        return {
            'main': '#98E4D6',      # 메인 파스텔 민트
            'hover': '#7DDCC9',     # 호버
            'pressed': '#6BC4B0',   # 클릭
            'light': '#A8E6CF',     # 연한 버전
            'text': '#5BB3A0',      # 텍스트용
            'bg_light': '#F0FDF4',  # 배경용 연한 색
            'bg_medium': '#E6F7ED'  # 배경용 중간 색
        }
