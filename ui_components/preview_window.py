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
from utils.event_system import event_system, Events
import csv
import asyncio


class PreviewWindow:
    """미리보기 창 UI 컨트롤러 """

    def __init__(self, root, app, video_path, start_time, end_time, auto_play=True):

        self.root = root
        self.app = app  # app.py의 앱 참조
        self.video_path = video_path
        self.start_time = start_time
        self.end_time = end_time
        self.auto_play = auto_play  # 자동 재생여부

        # 초기화 메서드들 순서대로 호출
        self._init_window()
        self._init_video_properties()
        self._init_video_controller()
        self._init_ui()
        self._init_event_handlers()

        # 자동 재생 설정
        if self.auto_play:
            # 500ms 이후 자동 재생
            self.window.after(500, self.start_auto_play)

    # =================================================================
    # 초기화 및 설정 메서드들
    # =================================================================

    def _init_window(self):
        """창 초기화 """
        self.window = tk.Toplevel(self.root)
        self.window.title("선택 구간 미리보기")
        self.window.geometry("800x800")

        # 창닫기 이벤트 바인딩
        self.window.protocol("WM_DELETE_WINDOW", self._handle_close)

    def _init_video_properties(self):
        """비디오 속성 초기화"""
        # 성능 최적화 관련 비디오 속성
        self.target_fps = 30
        self.frame_skip = 1
        self.frame_count = 0

        # 변수로 받은 start_time을 넣어주어야 함.
        self.current_time = self.start_time
        self.update_thread = None

    def _init_video_controller(self):
        """비디오 컨트롤러(변수) 초기화"""
        # 비디오 관련 변수 초기화
        self.cap = None
        self.fps = None
        self.is_playing = False
        self.current_image = None

        # 비디오 초기화
        self.cap, self.fps = VideoUtils.initialize_video(self.video_path)
        if self.cap is None:
            messagebox.showerror("오류", "비디오 초기화에 실패했습니다.")
            self.window.destroy()
            return

        # 비디오 속성 최적화
        if self.cap and self.cap.isOpened():
            self.original_fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.target_fps = VideoUtils.calculate_optimal_fps(
                self.original_fps)
            self.frame_skip = VideoUtils.calculate_frame_skip(
                self.original_fps, self.target_fps)

        # 초기 프레임 표시
        self._show_frame_at_time(self.start_time)

    def _init_ui(self):
        """create_ui 메서드들 재구성한 UI 초기화"""

        # UI 생성
        self._create_main_layout()
        self._create_video_section()
        self._create_segment_table_section()
        self._create_control_layout()

    def _init_event_handlers(self):
        """이벤트 핸들러 초기화 (이벤트 바인딩)
        창 크기 변경 이벤트 처리"""
        self.window.bind(
            '<Configure>', self._handle_window_resize)

        # 이벤트 구독
        event_system.subscribe(
            Events.VIDEO_PLAY_TOGGLE, self._on_play_toggle)
        event_system.subscribe(
            Events.SEGMENT_SAVED, self._on_segment_saved)

    # =================================================================
    # UI 생성 및 관리 메서드들
    # =================================================================

    def _create_main_layout(self):
        """메인 레이아웃 생성"""
        # 메인 프레임 - 창의 사방에 여백 추가
        self.main_frame = tk.Frame(self.window)
        # 패딩을 늘려서 버튼, 도움말 등이 창에 붙지 않게 처리
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

    def _create_video_section(self):
        """비디오 플레이 영역 생성"""
        self.video_frame = tk.Frame(self.main_frame, bg="black", width=500,
                                    relief="solid", borderwidth=2)
        self.video_frame.pack(side="left", fill=tk.BOTH, expand=False)
        self.video_frame.pack_propagate(False)  # 크기 고정

        # VideoUtils 사용하여 비디오레이블 생성
        self.video_label = VideoUtils.create_video_label(self.video_frame)
        self.video_label.pack(expand=True, fill="both")
        self.video_label.config(bg="black")

    def _create_segment_table_section(self):
        """구간 테이블 생성"""
        # 우측 프레임 (구간 정보 테이블) - 크기 조금 늘림
        self.right_frame = tk.Frame(self.main_frame, width=600)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        self.right_frame.pack_propagate(False)  # 최소 너비 유지

        # SegmentTable 컴포넌트 사용
        self.segment_table = SegmentTable(
            self.right_frame, self.app, preview_window=self)  # preview window 추가

    def _create_control_layout(self):
        """컨트롤 섹션 생성 - 메인 레이아웃와 같은 레벨"""

        # 컨트롤 프레임 - window에 직접 배치하되 패딩 증가
        self.video_control_frame = tk.Frame(self.window)
        self.video_control_frame.pack(fill=tk.X, padx=15, pady=(10, 25))

        self._create_left_playback()
        self._create_center_time_display()
        self._create_right_buttons()

    def _create_left_playback(self):
        """좌측 재생 컨트롤 생성"""
        self.control_left = tk.Frame(self.video_control_frame)
        self.control_left.pack(side=tk.LEFT, padx=5)

        # 재생/일시정지 버튼 - PlayOutline 스타일 사용
        self.play_button = ttk.Button(
            self.control_left,
            text="⏸ 일시정지",
            style="PlayOutline.TButton",
            command=self._handle_toggle_play,
            width=10
        )
        self.play_button.pack(side=tk.LEFT, padx=8)

    def _create_center_time_display(self):
        """중앙 시간 표시 생성"""
        self.control_center = tk.Frame(self.video_control_frame)
        self.control_center.pack(side=tk.LEFT, padx=5)

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

    def _create_right_buttons(self):
        """우측 버튼 생성 """
        # 우측: 구간 저장 버튼
        self.control_right = tk.Frame(self.video_control_frame)
        self.control_right.pack(side=tk.RIGHT, padx=5)

        # 저장 버튼 (우측 프레임 먼저 배치. 도움말 다음 배치)
        self.save_button = ttk.Button(
            self.control_right,
            text="💾 구간 저장",
            style="2Pastel.TButton",
            command=self._handle_save_selection
        )
        # ipady 추가로 버튼 세로 크기 증가
        self.save_button.pack(side=tk.LEFT, padx=10, ipady=5)

        # 도움말 레이블 - ttk.Label로 변경
        help_label = ttk.Label(self.control_right,
                               text="ⓘ 구간 목록의 저장, 삭제 내용이 모든 탭 테이블에 반영됩니다.",
                               font=("Open Sans", 11),
                               foreground='gray')
        help_label.pack(side=tk.RIGHT, padx=10)

    # =================================================================
    # 비디오 재생 제어 메서드들
    # =================================================================

    def _show_frame_at_time(self, time_sec):
        """지정된 시간의 프레임 표시 (최적화)"""
        try:
            ret, frame = VideoUtils.read_frame_at_position(
                self.cap, time_sec, self.fps
            )

            if ret:
                # 최적화 메서드 사용
                self._display_frame(frame)
                self.current_time = time_sec
                self._update_position_label()

            else:
                print(f"Failed to read frame at {time_sec}s")

        except Exception as e:
            print(f"Error showing frame at time {time_sec}: {e}")

    def _display_frame(self, frame):
        """프레임을을 화면 표시 (최적화)"""
        try:
            # VideoUtils의 최적화된 변환 메서드 사용
            photo = VideoUtils.convert_frame_to_photo_optimized(frame)
            if photo:
                self.video_label.config(image=photo)
                self.video_label.image = photo  # 참조 유지
        except Exception as e:
            print(f"Error in show_frame_optimized: {e}")

    def _update_position_label(self):
        """위치 레이블 업데이트"""
        current_str = VideoUtils.format_time(self.current_time)
        end_str = VideoUtils.format_time(self.end_time)
        self.position_label.config(text=f"{current_str} / {end_str}")

    def _start_playback(self):
        """재생 시작하는 작업 수행 메서드"""

        # 재생 시작 시 현재 위치가 종료 시간이면 시작 시간으로 이동
        if self.current_time >= self.end_time:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES,
                         int(self.start_time * self.fps))
            self.current_time = self.start_time
            self._show_frame_at_time(self.start_time)

        self.is_playing = True
        self.play_button.config(text="|| 일시정지")
        # after 메서드를 사용하여 프레임 업데이트 시작
        self._frame_update_loop()

    def _pause_playback(self):
        """재생 일시정지 작업 수행 메서드"""

        self.is_playing = False
        self.play_button.config(text="► 재생")

    def _frame_update_loop(self):
        """연속 재생을 위한 재귀 호출. 프레임 업데이트 루프"""
        if not self.is_playing:
            return

        # 현재시간 확인 - 구간 끝에 도달하면 재생 중지
        if self.current_time >= self.end_time:
            self._pause_playback()
            return

        # 프레임 읽기
        ret, frame = self.cap.read()
        if ret:
            self._display_frame(frame)
            self.current_time = self.cap.get(
                cv2.CAP_PROP_POS_FRAMES) / self.fps
            self._update_position_label()

            # 다음 프레임 스케줄링
            frame_interval = int(1000/self.target_fps)
            self.window.after(frame_interval, self._frame_update_loop)
        else:
            self.pause_play()

    def start_auto_play(self):
        """자동 재생 시작"""
        if self.auto_play and not self.is_playing:
            self._handle_toggle_play()

    # =================================================================
    #  데이터 처리 메서드들
    # =================================================================

    def _save_segment_data(self, segment_data):
        """중복 체크 및 저장 (미리보기 창을 부모로 전달) """
        return self.app.save_segment(
            segment_data, parent_window=self.window)

    def update_table(self):
        """newtab 테이블 새로고침"""

        # app.new_tab_instance가 있으면 바로 refresh_table() 호출
        if hasattr(self.app, 'new_tab_instance') and self.app.new_tab_instance:
            try:
                print("PreviewWindow 닫힘: 비디오 추출 탭 테이블 업데이트")
                self.app.new_tab_instance.refresh_table()
            except Exception as e:
                print(f"비디오 추출 탭 테이블 업데이트 중 오류: {str(e)}")

        self.window.destroy()

    # =================================================================
    # 이벤트 처리 메서드들
    # =================================================================

    def _handle_window_resize(self, event):
        """메인창의 크기 변경이 있을때만, 비디오 프레임 크기 조정
        우측 프레임의 너비를 고정하고, 남은 공간을 비디오 프레임 공간으로 할당.
        전체 너비에서 우측 프레임(620)과 여백(20)을 제외"""
        if event.widget == self.window:
            available_width = event.width - 620
            self._update_video_frame_size(available_width)

    def _update_video_frame_size(self, available_width):
        """비디오 프레임 크기 업데이트"""
        if available_width > 0:
            self.video_frame.configure(width=available_width)

    def _handle_toggle_play(self):
        """재생/일시정지 토글. 이벤트를 발행"""
        event_system.emit(Events.VIDEO_PLAY_TOGGLE)

    def _handle_save_selection(self):
        """선택 구간 저장 이벤트를 발행"""
        # 1. 데이터 생성
        segment_data = self.app.create_segment_data(
            self.video_path,
            self.start_time,
            self.end_time
        )

        # 2. 데이터 저장
        success = self._save_segment_data(segment_data)

        # 3. 저장 성공 시 이벤트 발행
        if success:
            event_system.emit(Events.SEGMENT_SAVED, **segment_data)

    def _on_play_toggle(self):
        """재생/일시정지 이벤트 수신 시 실제 동작 처리"""
        if self.is_playing:
            self._pause_playback()
        else:
            self._start_playback()

    def _on_segment_saved(self, **kwargs):
        """구간 저장 이벤트 수신 시 실제 동작 처리"""
        # 테이블 새로고침
        if hasattr(self, 'segment_table'):
            self.segment_table.refresh()

        # 포커스 복구
        self.window.focus_force()
        self.window.lift()

    def _handle_close(self):
        """창 닫기 이벤트. app.py에서 참조하는 메서드"""
        self.is_playing = False  # 스레드 루프 종료 신호
        if self.cap:
            self.cap.release()

        # 이벤트 구독 해제
        event_system.unsubscribe(
            Events.VIDEO_PLAY_TOGGLE, self._on_play_toggle)
        event_system.unsubscribe(
            Events.SEGMENT_SAVED, self._on_segment_saved)
        self.window.destroy()

# 호환성을 위해서 원래 on_close 메서드 유지. 내부적으로는 _handle_close를 호출하도록 함.

    def on_close(self):
        """기존 메서드 호환성 유지"""
        self._handle_close()
