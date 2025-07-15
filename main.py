import sys
import os
import ttkbootstrap as ttk
from ttkbootstrap import Window
from app import VideoEditorApp

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

if __name__ == "__main__":
    root = Window(themename="flatly")  # ttkbootstrap Window 사용
    app = VideoEditorApp(root)
    root.mainloop()
