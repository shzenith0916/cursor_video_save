import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import threading
import time
import os
from PIL import Image, ImageTk
from utils.utils import VideoUtils


class PreviewWindow:
    def __init__(self, root, app, video_path, start_time, end_time, auto_play=True):
        self.root = root
        self.app = app  # 메인 앱 참조
        self.video_path = video_path
        self.start_time = start_time
        self.end_time = end_time
        self.auto_play = auto_play  # 자동 재생여부

        # 새 창 생성
        self.window = tk.Toplevel(root)
        self.window.title("선택 구간 미리보기")
        self.window.geometry("800x1200")

        # UI 생성
        self.create_ui()

        # 비디오 관련 변수 초기화
        self.cap = None
        self.fps = None
        self.is_playing = False
        self.current_image = None
        self.curent_time = self.start_time  # 변수로 받은 start_time을 넣어주어야 함.
        self.update_thraed = None  # 추가!
        self.loop_play = True  # 동영상 루프로 재생 여부

        # 비디오 초기화
        self.initialize_video()

        # 초기 프레임 표시 추가!
        self.show_frame_at_time(self.start_time)

        # 자동 재생 시작
        if self.auto_play:
            self.window.after(500, self.start_auto_play)  # 500ms 이후 자동 재생생

        # 창닫기 이벤트 바인딩
        self.window.protocol("Close Window", self.on_close)

    def create_ui(self):
        """UI 구성 요소 생성"""

        # 메인 프레임
        self.main_frame = tk.Frame(self.window)

        # 좌측 프레임 (비디오 재생)
        self.video_frame = tk.Frame(self.main_frame, bg="black")
        self.video_frame.pack(side="left", fill=tk.BOTH,
                              expand=True, padx=(0, 10))

        # VideoUtils 사용하여 비디오레이블 생성
        self.video_label = VideoUtils.create_video_label(self.video_frame)
        self.video_label.config(bg="black")

        # 우측 프레임 (구간 정보 테이블)
        self.right_frame = tk.Frame(self.main_frame)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH,
                              padx=(5, 0), width=300)

        # 테이블 생성
        self.creat_table()

        # 컨트롤 플레임
        self.control_frame = tk.Frame(self.window)
        self.control_frame.pack(fill=tk.X, padx=10, pady=10)

        # 재생/일시정지 버튼
        self.play_button = tk.Button(
            self.control_frame,
            text="⏸",
            width=5,
            font=("Arial", 12),
            command=self.app.toggle_play)
        self.play_button.pack(side=tk.LEFT, padx=5)

        # 정지 버튼
        self.loop_var = tk.BooleanVar(value=True),
        self.loop_check = tk.Checkbutton(
            self.control_frame,
            text="루프 재생",
            font=("Arial", 12),
            variable=self.loop_var,
            command=self.toggle_loop)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # 저장 버튼
        self.save_button = tk.Button(
            self.control_frame,
            text="구간 저장",
            font=("Arial", 12),
            command=self.app.save_selection)
        self.save_button.pack(side=tk.LEFT, padx=10)

        # 구간 정보 레이블
        self.segment_info = f"구간: {VideoUtils.format_time(self.start_time)} - {VideoUtils.format_time(self.end_time)}"
        self.segment_label = tk.Label(
            self.control_frame,
            text=segment_info,
            font=("Arial", 11),
            fg='blue')

        self.segment_label.pack(side=tk.RIGHT, padx=5)

        # 위치 레이블
        self.position_label = tk.Label(
            self.control_frame,
            text=f"{VideoUtils.format_time(self.start_time)} / {VideoUtils.format_time(self.end_time)}",
            font=("Arial", 11)
        )
        self.position_label.pack(side=tk.RIGHT, padx=5)

        # ✅ 추가!! 도움말 레이블
        help_label = tk.Label(self.control_frame,
                              text="영상을 클릭하면 재생/일시정지 됩니다.",
                              font=("Arial", 11),
                              fg='gray')
        help_label.pack(side=tk.RIGHT, padx=10)

    def save_selection(self):
        """현재 선택 구간 저장"""
        # 앱의 저장된 구간 리스트에 추가
        if not hasattr(self.app, 'saved_segments'):
            self.app.saved_segments = []

        # 중복 체크 (선택 사항)
        for segment in self.app.saved_segments:
            if segment['start'] == self.start_time and segment['end'] == self.end_time:
                messagebox.showinfo("알림", "이미 동일한 구간이 저장되어 있습니다.")
                return

        # 새 구간 추가
        new_segment = {
            'start': self.start_time,
            'end': self.end_time,
            'file': self.video_path
        }
        self.app.saved_segments.append(new_segment)

        # 테이블 갱신
        self.load_table_data()

        # 메시지 표시
        tk.messagebox.showinfo("알림", "구간이 저장되었습니다.")

    def on_close(self):
        """창 닫기 이벤트"""
        self.is_playing = False
        if self.cap:
            self.cap.release()
        self.window.destroy()
