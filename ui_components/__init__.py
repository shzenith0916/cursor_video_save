import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from .base_tab import BaseTab
from .main_tab import MainTab
from .new_tab import NewTab


def create_tabs(parent, app):
    """탭 생성 함수"""

    # 노트북 위젯 생성 (탭 컨테이너)
    notebook = ttk.Notebook(parent)

    # 메인 탭 생성 및 추가
    main_tab = MainTab(notebook, app)
    notebook.add(main_tab.frame, text="메인 탭")

    # New 탭 생성 및 추가
    new_tab = NewTab(notebook, app)
    notebook.add(new_tab.frame, text="편집/추출 탭")
    app.new_tab_instance = new_tab  # app에 new_tab 인스턴스 저장

    notebook.pack(fill='both', expand=True)

    return {
        'notebook': notebook,
        'main_tab': main_tab,
        'new_tab': new_tab
    }
