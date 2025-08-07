# -*- coding: utf-8 -*-
import app
from app import VideoEditorApp

import tkinter as tk
from tkinter import font
import ttkbootstrap as ttk
from ttkbootstrap import Window

import sys
import os
import locale

# 한글 인코딩 설정 - WSL 환경 고려
try:
    if sys.platform.startswith('win'):
        locale.setlocale(locale.LC_ALL, 'Korean_Korea.UTF-8')
    else:
        # WSL/Linux 환경에서 사용 가능한 locale 시도
        try:
            locale.setlocale(locale.LC_ALL, 'ko_KR.UTF-8')
        except locale.Error:
            try:
                locale.setlocale(locale.LC_ALL, 'C.UTF-8')
            except locale.Error:
                locale.setlocale(locale.LC_ALL, '')
except locale.Error as e:
    print(f"Locale 설정 실패: {e}")
    # locale 설정 실패 시에도 프로그램은 계속 실행

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

if __name__ == "__main__":

    # Ttkbootstrap Window 명시적 사용
    root = ttk.Window(themename="flatly")

    # 시스템 폰트 확인 및 설정
    available_fonts = font.families()
    # 한글 폰트 목록 선언언
    korean_fonts = ['Malgun Gothic', '맑은 고딕',
                    'Gulim', '굴림', 'Dotum', '돋움', 'Batang', '바탕']

    selected_font = 'TkDefaultFont'
    for font_name in korean_fonts:
        if font_name in available_fonts:
            selected_font = font_name
            break

    print(f"선택된 폰트: {selected_font}")

    # 기본 폰트 설정 (더 강력하게)
    default_font = (selected_font, 9)

    # Ttkbootstrap 스타일 적용
    style = ttk.Style()
    style.configure('.', font=default_font)
    style.configure('TButton', font=default_font)
    style.configure('TLabel', font=default_font)
    style.configure('TEntry', font=default_font)

# 정상적으로 mainloop가 호출되는 라인인
    app = VideoEditorApp(root)
    root.mainloop()
