import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *


class BaseTab:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.frame = ttk.Frame(parent)
        self._init_variables()
        # BaseTab에서는 create_ui() 호출하지 않음
        # 각 자식 클래스에서 직접 호출하도록 함

    def _init_variables(self):
        """기본 변수 초기화"""
        pass

    def create_ui(self):
        """서브클래스에서 오버라이드할 UI 생성 메서드"""
        pass

    def update_ui(self):
        """서브클래스에서 오버라이드할 UI 업데이트 메서드"""
        pass
