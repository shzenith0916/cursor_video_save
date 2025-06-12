import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *


class CustomMessageBox:
    def __init__(self, parent, title, message, msg_type="info", width=400, height=200):
        self.result = None

        # 다이얼로그 창 생성
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry(f"{width}x{height}")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # 부모 창 중앙에 위치
        self.center_window(parent, width, height)

        # 아이콘과 색상 설정
        icon_config = self.get_icon_config(msg_type)

        # 메인 프레임
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=BOTH, expand=True, padx=20, pady=20)

        # 아이콘과 메시지 프레임
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=BOTH, expand=True, pady=(0, 20))

        # 아이콘
        icon_label = ttk.Label(
            content_frame,
            text=icon_config["icon"],
            font=("Arial", 24),
            foreground=icon_config["color"]
        )
        icon_label.pack(side=LEFT, padx=(0, 15))

        # 메시지
        message_label = ttk.Label(
            content_frame,
            text=message,
            font=("Arial", 11),
            wraplength=width-100,
            justify=LEFT
        )
        message_label.pack(side=LEFT, fill=BOTH, expand=True)

        # 버튼 프레임
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=X)

        # 확인 버튼
        ok_button = ttk.Button(
            button_frame,
            text="확인",
            style="Accent.TButton",
            command=self.ok_clicked,
            width=10
        )
        ok_button.pack(side=RIGHT)

        # Enter 키 바인딩
        self.dialog.bind('<Return>', lambda e: self.ok_clicked())
        self.dialog.bind('<Escape>', lambda e: self.ok_clicked())

        # 포커스 설정
        ok_button.focus_set()

    def get_icon_config(self, msg_type):
        """메시지 타입에 따른 아이콘과 색상 반환"""
        configs = {
            "info": {"icon": "ℹ️", "color": "#0d6efd"},
            "success": {"icon": "✅", "color": "#198754"},
            "warning": {"icon": "⚠️", "color": "#fd7e14"},
            "error": {"icon": "❌", "color": "#dc3545"}
        }
        return configs.get(msg_type, configs["info"])

    def center_window(self, parent, width, height):
        """부모 창 중앙에 다이얼로그 위치"""
        parent.update_idletasks()

        # 부모 창 위치와 크기
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()

        # 중앙 위치 계산
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2

        self.dialog.geometry(f"{width}x{height}+{x}+{y}")

    def ok_clicked(self):
        """확인 버튼 클릭"""
        self.result = "ok"
        self.dialog.destroy()

    def show(self):
        """다이얼로그 표시하고 결과 반환"""
        self.dialog.wait_window()
        return self.result


class CustomConfirmBox:
    def __init__(self, parent, title, message, width=400, height=200):
        self.result = None

        # 다이얼로그 창 생성
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry(f"{width}x{height}")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # 부모 창 중앙에 위치
        self.center_window(parent, width, height)

        # 메인 프레임
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=BOTH, expand=True, padx=20, pady=20)

        # 아이콘과 메시지 프레임
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=BOTH, expand=True, pady=(0, 20))

        # 아이콘
        icon_label = ttk.Label(
            content_frame,
            text="❓",
            font=("Arial", 24),
            foreground="#6f42c1"
        )
        icon_label.pack(side=LEFT, padx=(0, 15))

        # 메시지
        message_label = ttk.Label(
            content_frame,
            text=message,
            font=("Arial", 11),
            wraplength=width-100,
            justify=LEFT
        )
        message_label.pack(side=LEFT, fill=BOTH, expand=True)

        # 버튼 프레임
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=X)

        # 취소 버튼
        cancel_button = ttk.Button(
            button_frame,
            text="취소",
            command=self.cancel_clicked,
            width=10
        )
        cancel_button.pack(side=RIGHT, padx=(10, 0))

        # 확인 버튼
        ok_button = ttk.Button(
            button_frame,
            text="확인",
            style="Accent.TButton",
            command=self.ok_clicked,
            width=10
        )
        ok_button.pack(side=RIGHT)

        # 키 바인딩
        self.dialog.bind('<Return>', lambda e: self.ok_clicked())
        self.dialog.bind('<Escape>', lambda e: self.cancel_clicked())

        # 포커스 설정
        ok_button.focus_set()

    def center_window(self, parent, width, height):
        """부모 창 중앙에 다이얼로그 위치"""
        parent.update_idletasks()

        # 부모 창 위치와 크기
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()

        # 중앙 위치 계산
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2

        self.dialog.geometry(f"{width}x{height}+{x}+{y}")

    def ok_clicked(self):
        """확인 버튼 클릭"""
        self.result = True
        self.dialog.destroy()

    def cancel_clicked(self):
        """취소 버튼 클릭"""
        self.result = False
        self.dialog.destroy()

    def show(self):
        """다이얼로그 표시하고 결과 반환"""
        self.dialog.wait_window()
        return self.result


# 편의 함수들
def show_info(parent, title, message, width=400, height=200):
    """정보 메시지박스 표시"""
    dialog = CustomMessageBox(parent, title, message, "info", width, height)
    return dialog.show()


def show_success(parent, title, message, width=400, height=200):
    """성공 메시지박스 표시"""
    dialog = CustomMessageBox(parent, title, message, "success", width, height)
    return dialog.show()


def show_warning(parent, title, message, width=400, height=200):
    """경고 메시지박스 표시"""
    dialog = CustomMessageBox(parent, title, message, "warning", width, height)
    return dialog.show()


def show_error(parent, title, message, width=400, height=200):
    """에러 메시지박스 표시"""
    dialog = CustomMessageBox(parent, title, message, "error", width, height)
    return dialog.show()


def ask_confirm(parent, title, message, width=400, height=200):
    """확인 다이얼로그 표시"""
    dialog = CustomConfirmBox(parent, title, message, width, height)
    return dialog.show()
