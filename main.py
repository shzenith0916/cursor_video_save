import ttkbootstrap as ttk
from ttkbootstrap import Window
from app import VideoEditorApp

if __name__ == "__main__":
    root = Window(themename="flatly")  # ttkbootstrap Window 사용
    app = VideoEditorApp(root)
    root.mainloop()
