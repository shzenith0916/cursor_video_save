import tkinter as tk
from tkinter import ttk


class BaseTab:
    def __init__(self, root, app):
        self.root = root
        self.app = app
        self.frame = tk.Frame(root)  # 탭의 기본 프레임 생성성
        self._init_variables()
        # BaseTab에서는 create_ui() 호출하지 않음
        # 각 자식 클래스에서 직접 호출하도록 함

    def _init_variables(self):
        """기본 변수 초기화"""
        pass

    def create_ui(self):
        """UI 생성 - 자식 클래스에서 구현"""
        pass
