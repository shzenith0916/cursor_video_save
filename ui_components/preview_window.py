import tkinter as tk
import ttkbootstrap as ttk  # ttkbootstrap으로 변경
from ttkbootstrap.constants import *  # Bootstrap 스타일 상수들
from tkinter import messagebox, filedialog
import cv2
import threading
import time
import os
from PIL import Image, ImageTk
from utils.utils import VideoUtils
from ui_components.segment_table import SegmentTable
import csv
import asyncio


class PreviewWindow:
    def __init__(self, root, app, video_path, start_time, end_time, auto_play=True):
        self.root = root
        self.app = app  # 메인 앱 참조
        self.video_path = video_path
        self.start_time = start_time
        self.end_time = end_time
        self.auto_play = auto_play  # 자동 재생여부
        # 성능 최적화 관련 속성성
        self.target_fps = 30
        self.frame_skip = 1
        self.frame_count = 0

        # 새 창 생성
        self.window = tk.Toplevel(root)
        self.window.title("선택 구간 미리보기")
        self.window.geometry("800x800")

        # UI 생성
        self.create_ui()

        # 비디오 관련 변수 초기화
        self.cap = None
        self.fps = None
        self.is_playing = False
        self.current_image = None
        self.current_time = self.start_time  # 변수로 받은 start_time을 넣어주어야 함.
        self.update_thread = None  # 추가!

        # 비디오 초기화
        self.cap, self.fps = VideoUtils.initialize_video(video_path)
        if self.cap is None:
            messagebox.showerror("오류", "비디오 초기화에 실패했습니다.")
            self.window.destroy()
            return

        # 초기 프레임 표시 추가!
        self.show_frame_at_time(self.start_time)

        # 비디오 속성 최적화
        if self.cap and self.cap.isOpened():
            self.original_fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.target_fps = VideoUtils.calculate_optimal_fps(
                self.original_fps)
            self.frame_skip = VideoUtils.calculate_frame_skip(
                self.original_fps, self.target_fps)

        # 자동 재생 시작
        if self.auto_play:
            self.window.after(500, self.start_auto_play)  # 500ms 이후 자동 재생

        # 창닫기 이벤트 바인딩
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

        # # asyncio 이벤트 루프 관리
        # self.loop = asyncio.new_event_loop()
        # self.loop_thread = threading.Thread(
        #     target=self.run_async_loop, daemon=True)
        # self.loop_thread.start()

    def create_ui(self):
        """UI 구성 요소 생성"""

        # 메인 프레임
        self.main_frame = tk.Frame(self.window)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 스타일 설정
        style = ttk.Style()
        style.configure("SavePreview.TButton", font=("Arial", 12, "bold"),
                        background="#007bff", foreground="white", padding=(10, 5))  # 예시: 파란색 배경, 흰색 글씨
        style.map("SavePreview.TButton",
                  background=[('active', '#0056b3')],  # 활성화 시 약간 어둡게
                  foreground=[('active', 'white')])

        self.video_frame = tk.Frame(self.main_frame, bg="black", width=600)
        self.video_frame.pack(side="left", fill=tk.BOTH, expand=False)
        self.video_frame.pack_propagate(False)  # 크기 고정

        # VideoUtils 사용하여 비디오레이블 생성
        self.video_label = VideoUtils.create_video_label(self.video_frame)
        self.video_label.pack(expand=True, fill="both")
        self.video_label.config(bg="black")

        # 우측 프레임 (구간 정보 테이블)
        self.right_frame = tk.Frame(self.main_frame, width=500)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        self.right_frame.pack_propagate(False)  # 최소 너비 유지

        # SegmentTable 컴포넌트 사용
        self.segment_table = SegmentTable(
            self.right_frame, self.app, preview_window=self)  # preview window 추가

        # 컨트롤 플레임
        self.video_control_frame = tk.Frame(self.window)
        self.video_control_frame.pack(fill=tk.X, padx=10, pady=5)

        # 좌측: 재생 컨트롤
        self.control_left = tk.Frame(self.video_control_frame)
        self.control_left.pack(side=tk.LEFT, padx=5)

        # 중앙: 시간 정보
        self.control_center = tk.Frame(self.video_control_frame)
        self.control_center.pack(side=tk.LEFT, padx=5)

        # 우측: 구간 저장 버튼
        self.control_right = tk.Frame(self.video_control_frame)
        self.control_right.pack(side=tk.RIGHT, padx=5)

        # 재생/일시정지 버튼
        self.play_button = ttk.Button(
            self.control_left,
            text="⏸️",
            bootstyle=SUCCESS,
            command=self.toggle_play)
        self.play_button.pack(side=tk.LEFT, padx=8)

        # 위치 레이블 (먼저 배치)
        self.position_label = tk.Label(
            self.control_center,
            text=f"{VideoUtils.format_time(self.start_time)} / {VideoUtils.format_time(self.end_time)}",
            font=("Arial", 11)
        )
        self.position_label.pack(side=tk.RIGHT, padx=5)

        # 구간 정보 레이블 (위치 레이블 다음 배치치)
        self.segment_info = f"구간: {VideoUtils.format_time(self.start_time)} - {VideoUtils.format_time(self.end_time)}"
        self.segment_label = tk.Label(
            self.control_center,
            text=self.segment_info,
            font=("Arial", 11, "bold"),
            fg='#0000FF')  # 더 진한 파란색 사용
        self.segment_label.pack(side=tk.RIGHT, padx=5)

        # 저장 버튼 (우측 프레임 먼저 배치. 도움말 다음 배치)
        self.save_button = ttk.Button(
            self.control_right,
            text="💾 구간 저장",
            style="SavePreview.TButton",  # 커스텀 스타일 적용
            command=self.save_selection
        )
        # ipady 추가로 버튼 세로 크기 증가
        self.save_button.pack(side=tk.LEFT, padx=10, ipady=5)

        # ✅ 추가!! 도움말 레이블
        help_label = tk.Label(self.control_right,
                              text="💡 구간저장 버튼 클릭시, 모든 탭 테이블에 저장됩니다.",
                              font=("Arial", 11),
                              fg='gray')
        help_label.pack(side=tk.RIGHT, padx=10)

        # 창 크기 변경 이벤트 바인딩
        self.window.bind('<Configure>', self._on_window_resize)

    def _on_window_resize(self, event):
        """창 크기 변경 시 비디오 프레임 크기 조정"""
        if event.widget == self.window:  # 메인 창의 크기 변경일 때만 처리
            # 우측 프레임의 너비를 고정하고 남은 공간을 비디오 프레임에 할당
            # 전체 너비에서 우측 프레임(400)과 여백(20) 제외
            available_width = event.width - 420
            if available_width > 0:
                self.video_frame.configure(width=available_width)

    def show_frame_at_time(self, time_sec):
        """지정된 시간의 프레임 표시 (최적화)"""
        try:
            ret, frame = VideoUtils.read_frame_at_position(
                self.cap, time_sec, self.fps
            )

            if ret:
                # 최적화 메서드 사용
                self.show_frame_optimized(frame)
                self.current_time = time_sec
                self.update_position_label()

            else:
                print(f"Failed to read frame at {time_sec}s")

        except Exception as e:
            print(f"Error showing frame at time {time_sec}: {e}")

    def show_frame_optimized(self, frame):
        """프레임 표시 (최적화)"""
        try:
            # VideoUtils의 최적화된 변환 메서드 사용
            photo = VideoUtils.convert_frame_to_photo_optimized(frame)
            if photo:
                self.video_label.config(image=photo)
                self.video_label.image = photo  # 참조 유지
        except Exception as e:
            print(f"Error in show_frame_optimized: {e}")

    def update_frames_optimized(self):
        """프레임 업데이트 (최적화)"""
        if not self.is_playing:
            return

        # 현재시간 확인 - 구간 끝에 도달하면 재생 중지
        if self.current_time >= self.end_time:
            self.is_playing = False
            self.play_button.config(text="▶")
            return

        ret, frame = self.cap.read()
        if ret:
            self.show_frame_optimized(frame)
            self.current_time = self.cap.get(
                cv2.CAP_PROP_POS_FRAMES) / self.fps
            self.update_position_label()

            # 다음 프레임 스케줄링 (window.after 사용)
            frame_interval = int(1000/self.target_fps)
            self.window.after(frame_interval, self.update_frames_optimized)

    def update_position_label(self):
        """위치 레이블 업데이트"""
        current_str = VideoUtils.format_time(self.current_time)
        end_str = VideoUtils.format_time(self.end_time)
        self.position_label.config(text=f"{current_str} / {end_str}")

    def toggle_play(self):
        """재생/일시정지 토글"""
        if self.is_playing:
            self.is_playing = False
            self.play_button.config(text="▶")
        else:
            # 재생 시작 시 현재 위치가 종료 시간이면 시작 시간으로 이동
            if self.current_time >= self.end_time:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES,
                             int(self.start_time * self.fps))
                self.current_time = self.start_time
                self.show_frame_at_time(self.start_time)

            self.is_playing = True
            self.play_button.config(text="⏸")
            # after 메서드를 사용하여 프레임 업데이트 시작
            self.update_frames_optimized()

    def save_selection(self):
        """현재 선택 구간 저장 - 중앙화된 메서드 사용"""
        # 임시로 app의 start_time, end_time을 저장 (기존 값 백업)
        original_start = getattr(self.app, 'start_time', 0)
        original_end = getattr(self.app, 'end_time', 0)

        try:
            # 미리보기 창의 구간 정보를 app에 임시 설정
            self.app.start_time = self.start_time
            self.app.end_time = self.end_time

            # 중앙화된 저장 메서드 사용
            success = self.app.save_current_segment(self.video_path)

            if success:
                # PreviewWindow의 테이블 새로고침
                if hasattr(self, 'segment_table'):
                    self.segment_table.refresh()
                self.window.focus_force()

        finally:
            # 원래 값 복원
            self.app.start_time = original_start
            self.app.end_time = original_end

    def on_close(self):
        """창 닫기 이벤트"""
        self.is_playing = False  # 스레드 루프 종료 신호
        if self.cap:
            self.cap.release()

        # 창이 닫힐 때 NewTab의 테이블 업데이트
        try:
            # app.ui는 notebook을 반환하므로 탭들을 찾아야 함
            if hasattr(self.app, 'ui'):
                # NewTab 인스턴스 찾기 (중복 루프 제거)
                for tab_id in self.app.ui.tabs():
                    # tab_id은 특정 탭의 식별자이고, "text"는 탭의 텍스트를 가져오는 속성
                    tab_text = self.app.ui.tab(tab_id, "text")
                    print(f"탭 발견: {tab_id} - '{tab_text}'")
                    if tab_text == "비디오 추출":  # NewTab의 텍스트
                        print(f"비디오 추출 탭 찾음: {tab_id}")
                        break

            # 더 직접적인 방법: app에 new_tab 참조 저장하도록 수정
            if hasattr(self.app, 'new_tab_instance'):
                print("PreviewWindow 닫힘: 비디오 추출 탭 테이블 업데이트")
                self.app.new_tab_instance.refresh_table()

        except Exception as e:
            print(f"비디오 추출 탭 테이블 업데이트 중 오류: {str(e)}")

        self.window.destroy()

    def start_auto_play(self):
        """자동 재생 시작"""
        if self.auto_play and not self.is_playing:
            self.toggle_play()
