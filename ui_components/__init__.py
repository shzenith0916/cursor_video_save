import tkinter as tk
from tkinter import ttk
from .base_tab import BaseTab
from .main_tab import MainTab
from .new_tab import NewTab


def create_tabs(root, app):
    """탭들을 생성하고 관리하는 함수"""
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True)

    # 메인 탭 생성
    main_tab = MainTab(notebook, app)
    notebook.add(main_tab.frame, text="비디오 편집")

    # 새로운 탭 생성
    new_tab = NewTab(notebook, app)
    notebook.add(new_tab.frame, text="비디오 추출")

    return notebook
