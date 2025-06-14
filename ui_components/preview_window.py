import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, filedialog
import cv2
import threading
import time
import os
from PIL import Image, ImageTk
from utils.utils import VideoUtils
from .segment_table import SegmentTable
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

        # 메인 프레임 - 창의 사방에 여백 추가
        self.main_frame = tk.Frame(self.window)
        # 패딩을 늘려서 버튼, 도움말 등이 창에 붙지 않게 처리
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        self.video_frame = tk.Frame(self.main_frame, bg="black", width=500,
                                    relief="solid", borderwidth=2)
        self.video_frame.pack(side="left", fill=tk.BOTH, expand=False)
        self.video_frame.pack_propagate(False)  # 크기 고정

        # VideoUtils 사용하여 비디오레이블 생성
        self.video_label = VideoUtils.create_video_label(self.video_frame)
        self.video_label.pack(expand=True, fill="both")
        self.video_label.config(bg="black")

        # 우측 프레임 (구간 정보 테이블) - 크기 조금 늘림
        self.right_frame = tk.Frame(self.main_frame, width=600)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        self.right_frame.pack_propagate(False)  # 최소 너비 유지

        # SegmentTable 컴포넌트 사용
        self.segment_table = SegmentTable(
            self.right_frame, self.app, preview_window=self)  # preview window 추가

        # 컨트롤 플레임 - window에 직접 배치하되 패딩 증가
        self.video_control_frame = tk.Frame(self.window)
        self.video_control_frame.pack(fill=tk.X, padx=15, pady=(10, 25))

        # 좌측: 재생 컨트롤
        self.control_left = tk.Frame(self.video_control_frame)
        self.control_left.pack(side=tk.LEFT, padx=5)

        # 중앙: 시간 정보
        self.control_center = tk.Frame(self.video_control_frame)
        self.control_center.pack(side=tk.LEFT, padx=5)

        # 우측: 구간 저장 버튼
        self.control_right = tk.Frame(self.video_control_frame)
        self.control_right.pack(side=tk.RIGHT, padx=5)

        # 재생/일시정지 버튼 - PlayOutline 스타일 사용
        self.play_button = ttk.Button(
            self.control_left,
            text="⏸ 일시정지",
            style="PlayOutline.TButton",
            command=self.toggle_play,
            width=10
        )
        self.play_button.pack(side=tk.LEFT, padx=8)

        # 위치 레이블 (먼저 배치) - ttk.Label로 변경
        self.position_label = ttk.Label(
            self.control_center,
            text=f"{VideoUtils.format_time(self.start_time)} / {VideoUtils.format_time(self.end_time)}",
            font=("Arial", 11)
        )
        self.position_label.pack(side=tk.RIGHT, padx=5)

        # 구간 정보 레이블 (위치 레이블 다음 배치) - ttk.Label로 변경
        self.segment_info = f"구간: {VideoUtils.format_time(self.start_time)} - {VideoUtils.format_time(self.end_time)}"
        self.segment_label = ttk.Label(
            self.control_center,
            text=self.segment_info,
            font=("Arial", 11, "bold"))
        self.segment_label.pack(side=tk.RIGHT, padx=5)

        # 저장 버튼 (우측 프레임 먼저 배치. 도움말 다음 배치)
        self.save_button = ttk.Button(
            self.control_right,
            text="💾 구간 저장",
            style="2Pastel.TButton",
            command=self.save_selection
        )
        # ipady 추가로 버튼 세로 크기 증가
        self.save_button.pack(side=tk.LEFT, padx=10, ipady=5)

        # 도움말 레이블 - ttk.Label로 변경
        help_label = ttk.Label(self.control_right,
                               text="ⓘ 구간 목록의 저장, 삭제 내용이 모든 탭 테이블에 반영됩니다.",
                               font=("Open Sans", 11),
                               foreground='gray')
        help_label.pack(side=tk.RIGHT, padx=10)

        # 창 크기 변경 이벤트 바인딩
        self.window.bind('<Configure>', self._on_window_resize)

    def _on_window_resize(self, event):
        """창 크기 변경 시 비디오 프레임 크기 조정"""
        if event.widget == self.window:  # 메인 창의 크기 변경일 때만 처리
            # 우측 프레임의 너비를 고정하고 남은 공간을 비디오 프레임에 할당
            # 전체 너비에서 우측 프레임(620)과 여백(20) 제외
            available_width = event.width - 620
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
            self.play_button.config(text="► 재생")
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
            self.play_button.config(text="► 재생")
        else:
            # 재생 시작 시 현재 위치가 종료 시간이면 시작 시간으로 이동
            if self.current_time >= self.end_time:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES,
                             int(self.start_time * self.fps))
                self.current_time = self.start_time
                self.show_frame_at_time(self.start_time)

            self.is_playing = True
            self.play_button.config(text="|| 일시정지")
            # after 메서드를 사용하여 프레임 업데이트 시작
            self.update_frames_optimized()

    def save_selection(self):
        """현재 선택 구간 저장 - 간소화된 버전"""
        # 구간 데이터 생성
        segment_data = self.app._create_segment_data(
            self.video_path,
            self.start_time,
            self.end_time
        )

        # 중복 체크 및 저장 (미리보기 창을 부모로 전달)
        success = self.app.save_segment(
            segment_data, parent_window=self.window)

        if success:
            # PreviewWindow의 테이블 새로고침
            if hasattr(self, 'segment_table'):
                self.segment_table.refresh()

        # 성공/실패 관계없이 미리보기 창에 포커스 복구
        self.window.focus_force()
        self.window.lift()  # 창을 맨 앞으로 가져오기

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
