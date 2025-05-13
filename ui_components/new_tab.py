from .base_tab import BaseTab
import tkinter as tk
from tkinter import ttk


class NewTab(BaseTab):
    def __init__(self, root, app):
        super().__init__(root, app)  # super()로 BaseTab 상속속
        self.create_ui()

    # def _init_variables(self):
    #     "Initialize NewTab(Extract) UI variables"
    #     # 프레임 변수들
    #     self.top_frame = None  # 상단 (없음)
    #     self.openfile_frame = None  # 상단 (파란색)

    #     # 참조 위젯 변수들
    #     self.videofile_label = None
    #     self.videofile_entry = None

    # def create_ui(self):
    #     """MainTab UI 구성 요소를 생성"""

    #     self.create_top_frame()
    #     self.create_video_frame()
    #     self.create_crontrol_frame()
    #     self.create_edit_frame()
    #     self._save_widget_references()
