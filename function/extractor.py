import tkinter as tk  # gui 모듈 포함하여 import
from tkinter import ttk  # 테이블 모듈 포함하여 import
from utils.ui_components import create_ui
import os
import cv2


class VideoEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title(("비디오 부분 추출 App"))
        self.root.geometry("800x600")
        self.root.resizable(False, False)

        # 비디오 관련 변수
        self.video_path = None
        self.cap = None
        self.fps = None
        self.frame_count = 0
        self.video_length = 0
        self.current_frame = None

        # 재생 관련 변수
        self.is_playing = False
        self.play_thread = None

        # 구간 선택 변수
        self.start_time = 0
        self.end_time = 0

        # 프레임 추출 변수
        self.start_frame = 0
        self.end_frame = 0
        self.frame_interval = 1
        self.frame_count = 0

        self.ui = create_ui(self.root, self)  # 메서드로 호출


def extract_frames(self, start_second, end_second):

    self.start_frame = start_second * self.fps
    self.end_frame = end_second * self.fps

    # for idx, frame_idx in enumerate(range(self.start_frame, self.end_frame + 1)):
    #     if 0 <= frame_idx < self.total_frames:
