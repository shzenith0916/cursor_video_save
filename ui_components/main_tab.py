import tkinter as tk
import ttkbootstrap as ttk  # ttkbootstrap으로 변경
from ttkbootstrap.constants import *  # Bootstrap 스타일 상수들
from tkinter import font
from tkinter import messagebox

from utils.ui_utils import UiUtils
from .base_tab import BaseTab
import os
from utils.utils import VideoUtils
from utils.styles import AppStyles
from utils.event_system import event_system, Events
from .command_handlers import MainTabCommandHandler
from .command_handlers import NewTabCommandHandler
from .command_handlers import SegmentTableCommandHandler
from tkinter import filedialog


class MainTab(BaseTab):
    def __init__(self, root, app):
        """
        기본 탭 초기화

        Args:
            root: GUI 부모 컨테이너
            app: 애플리케이션 인스턴스
        """

        # 부모 클래스(BaseTab)의 초기화 메서드 호출
        super().__init__(root, app)  # BaseTab의 __init__ 호출
        self.root = root
        # self.app = app  # 기존 app 인스턴스 유지

        # 한글 폰트 설정
        self.korean_font = AppStyles.get_korean_font()

        self._init_variables()  # MainTab 전용 변수 초기화

        # 메인탭 Command handler 초기화
        self.main_command_handler = MainTabCommandHandler(app)
        # command_handler에 main_tab 참조 설정
        self.main_command_handler.set_main_tab(self)

        self.create_ui()  # MainTab UI 생성
        self.setup_event_listeners()

        # 추가로 확인할 수 있는 코드 (디버깅 용도)
        print(f"MainTab frame created: {self.frame}")
        print(f"선택된 한글 폰트: {self.korean_font}")

    def _init_variables(self):
        "Initialize MainTab UI variables"
        # 프레임 변수들
        self.table_frame = None  # 왼쪽
        self.info_frame = None  # 오른쪽

        # 슬라이더 드래그 상태 변수
        self.is_slider_dragging = False

        # 참조 위젯 변수들
        self.videofile_label = None
        self.videofile_entry = None
        self.file_select_button = None
        self.video_info_label = None
        self.video_label = None
        self.position_slider = None
        self.slider_label = None
        self.play_button = None
        self.stop_button = None
        self.start_time_label = None
        self.end_time_label = None
        self.set_start_button = None
        self.set_end_button = None
        self.preview_button = None

    def setup_event_listeners(self):
        """이벤트 리스너 설정 - UI 업데이트 전담"""
        # UI 업데이트 이벤트만 구독
        event_system.subscribe(Events.UI_UPDATE, self._on_ui_update)
        event_system.subscribe(
            Events.PLAYER_STATE_CHANGED, self._on_player_state_changed)
        event_system.subscribe(Events.VLC_TIME_CHANGED,
                               self._on_vlc_time_changed)

    def create_ui(self):
        """MainTab UI 구성 요소를 생성
        모든 최상위 UI 섹션을 생성해야 함. """

        self.create_top_frame()  # 상단
        self.create_video_frame()  # 비디오표시 부분
        self.create_control_frame()  # 컨트롤 부분 (슬라이더 및 편집 섹션)
        self._save_widget_references()

    def create_top_frame(self):
        """상단 프레임 생성 - 파일 선택"""
        self.top_frame = ttk.Frame(self.frame)
        self.top_frame.pack(pady=20, padx=20, fill=ttk.X)
        self.top_frame.columnconfigure(0, weight=1)

        self.openfile_frame = ttk.Frame(self.top_frame)
        self.openfile_frame.grid(
            row=0, column=0, padx=(15, 0), sticky="w")

        self.video_path_var = tk.StringVar()

        self.videofile_label = ttk.Label(
            self.openfile_frame, text="비디오 파일 선택", font=(self.korean_font, 12, "bold"))
        self.videofile_label.grid(row=0, column=0, padx=(5, 5), sticky="w")

        self.videofile_entry = ttk.Entry(
            self.openfile_frame, textvariable=self.video_path_var,
            width=40 * int(UiUtils.get_scaling_factor_by_dpi(self.root)),
            font=(self.korean_font, 9))
        self.videofile_entry.grid(row=0, column=1, padx=(0, 5), sticky="we")

        self.video_select_button = ttk.Button(
            self.openfile_frame, text="파일 선택", style="InfoLarge.TButton",
            command=self.main_command_handler.on_file_select)
        self.video_select_button.grid(row=0, column=2, padx=(0, 5))

        self.info_frame = ttk.Frame(self.top_frame)
        self.info_frame.grid(row=0, column=1, padx=10,
                             pady=10, sticky="w")

        self.section_title_label = ttk.Label(
            self.info_frame, text="비디오정보", font=(self.korean_font, 12, "bold"))
        self.section_title_label.pack(pady=(0, 2), anchor="w")

        self.separator = ttk.Separator(self.info_frame, orient=tk.HORIZONTAL)
        self.separator.pack(fill=tk.X, pady=(0, 5), expand=True)

        self.video_info_label = ttk.Label(
            self.info_frame, text="", font=(self.korean_font, 10), foreground="gray", anchor="w", justify="left")
        self.video_info_label.pack(fill=tk.X, expand=True, padx=5, pady=5)

    def create_video_frame(self):
        """비디오 프레임 생성"""
        self.video_frame = ttk.Frame(
            self.frame,
            width=int(640 * UiUtils.get_scaling_factor_by_dpi(self.root)),
            height=int(360 * UiUtils.get_scaling_factor_by_dpi(self.root)),
            relief="sunken", borderwidth=2)
        self.video_frame.pack(fill='both', expand=True, padx=10, pady=10)
        self.video_frame.pack_propagate(False)

        self.video_canvas = tk.Canvas(self.video_frame, bg="black")
        self.video_canvas.pack(fill=tk.BOTH, expand=True)

        # app.py에 video_canvas 참조 설정
        self.app.video_canvas = self.video_canvas

        # VLC Player 인스턴스에 연결
        if hasattr(self.app, 'vlc_player') and self.app.vlc_player:
            print("MainTab: VLC 플레이어에 video_canvas 연결")
            self.app.vlc_player.set_video_widget(self.video_canvas)
        else:
            print("MainTab: VLC 플레이어가 아직 초기화되지 않음")

    def create_control_frame(self):
        """컨트롤 프레임 생성"""
        self.container_frame = ttk.Frame(self.frame)
        self.container_frame.pack(fill=tk.X, padx=10, pady=10)

        self.container_frame.columnconfigure(0, weight=4)
        self.container_frame.columnconfigure(1, weight=3)
        self.container_frame.columnconfigure(2, weight=3)

        self.slider_frame = ttk.Frame(self.container_frame)
        self.slider_frame.grid(
            row=0, column=0, padx=(0, 5), pady=5, sticky="nsew")
        self.create_slider_section()

        self.interval_frame = ttk.Frame(self.container_frame)
        self.interval_frame.grid(
            row=0, column=1, padx=5, pady=5, sticky="nsew")
        self.create_interval_section()

        self.save_action_frame = ttk.Frame(self.container_frame)
        self.save_action_frame.grid(
            row=0, column=2, padx=(5, 0), pady=5, sticky="nsew")
        self.create_save_action_section()

    def create_slider_section(self):
        """슬라이더 섹션 생성 (slider_frame 내에 배치)"""
        # 비디오 전체구간 슬라이더 생성
        self.progress_variable = tk.DoubleVar()
        self.position_slider = ttk.Scale(self.slider_frame,
                                         orient='horizontal',
                                         variable=self.progress_variable,
                                         from_=0,
                                         to=100,  # 초기값, 나중에 비디오 길이로 업데이트
                                         length=450,
                                         style='Horizontal.TScale')
        self.position_slider.pack(fill=tk.X, pady=(0, 5))

        # 마우스 이벤트 바인딩으로 드래그 감지
        self.position_slider.bind('<Button-1>', self._on_slider_click)
        self.position_slider.bind('<B1-Motion>', self._on_slider_drag)
        self.position_slider.bind(
            '<ButtonRelease-1>', self._on_slider_release)

        # 시간 표시
        self.slider_label = ttk.Label(
            self.slider_frame, text="00:00:00 / 00:00:00", font=(self.korean_font, 11, "bold"))
        self.slider_label.pack(pady=3)

        self.create_button_section()  # 재생/정지 버튼은 slider_frame 소속

    def update_slider_range(self, duration):
        """슬라이더 범위를 비디오 길이에 맞게 업데이트"""
        if duration > 0:
            self.position_slider.config(to=duration)
            self.progress_variable.set(0)

    def _on_slider_click(self, event):
        """슬라이더 클릭 시 - 드래그 시작 - VLC 기반"""
        self.is_slider_dragging = True
        # 비디오 일시정지 (드래그 중에는 재생 중지)
        if hasattr(self.app, 'is_playing') and self.app.is_playing:
            self.app.pause_video()
            print("MainTab: 슬라이더 드래그 시작 - 재생 일시정지")

    def _on_slider_drag(self, event):
        """슬라이더 드래그 중 - 시간 표시만 업데이트"""
        if self.is_slider_dragging and hasattr(self.app, 'vlc_player') and self.app.vlc_player.duration > 0:
            # 슬라이더 값으로 시간 계산 (직접 시간 값 사용)
            current_time = self.progress_variable.get()

            # 시간 표시 업데이트
            time_str = VideoUtils.format_time(int(current_time))
            total_time = VideoUtils.format_time(
                int(self.app.vlc_player.duration))
            self.slider_label.config(text=f"{time_str} / {total_time}")

    def _on_slider_release(self, event):
        """슬라이더 놓을 시 - 실제 비디오 위치 동기화 - VLC 기반"""
        if self.is_slider_dragging and hasattr(self.app, 'vlc_player') and self.app.vlc_player.duration > 0:
            # 슬라이더 값으로 시간 계산 (직접 시간 값 사용)
            target_time = self.progress_variable.get()

            # VLC 플레이어 위치 설정
            if hasattr(self.app, 'vlc_player') and self.app.vlc_player:
                self.app.select_position(target_time)
                print(f"MainTab: 슬라이더로 위치 변경 - {target_time}초")
            # 드래그 상태 해제
            self.is_slider_dragging = False

    def create_button_section(self):
        """버튼 섹션 생성"""
        control_buttons_subframe = ttk.Frame(
            self.slider_frame)
        control_buttons_subframe.pack(pady=8)

        self.play_button = ttk.Button(control_buttons_subframe, text="► 재생",
                                      style="PlayOutline.TButton",
                                      command=self.main_command_handler.on_play_click, width=12,
                                      state=tk.DISABLED)
        self.play_button.pack(side=tk.LEFT, padx=10, pady=2)

        self.stop_button = ttk.Button(control_buttons_subframe, text="■ 정지",
                                      style="StopOutline.TButton",
                                      command=self.main_command_handler.on_stop_click, width=12,
                                      state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=10, pady=2)

    def create_interval_section(self):  # <- create_edit_section 에서 이름 변경
        """구간의 시작 시간, 끝 시간 설정 섹션 (interval_frame 내에 배치)"""

        # Grid 컬럼 설정 - 레이블과 버튼 정렬을 위해
        self.interval_frame.columnconfigure(0, weight=0)  # 레이블 컬럼 (고정 크기)
        self.interval_frame.columnconfigure(1, weight=1)  # 버튼 컬럼 (유연한 크기)

        # 시작 시간 관련 위젯들
        self.start_time_label = ttk.Label(
            self.interval_frame, text="구간 시작: 00:00", font=(self.korean_font, 10, "bold"))
        self.start_time_label.grid(
            row=0, column=0, sticky="w", pady=(0, 3), padx=(0, 10))

        self.set_start_button = ttk.Button(self.interval_frame,
                                           text="시작 지점 설정",
                                           style='PastelGreenOutline.TButton',
                                           command=self.main_command_handler.on_set_start_click,
                                           state=tk.DISABLED)
        self.set_start_button.grid(row=0, column=1, sticky="w", pady=(0, 3))

        # 종료 시간 관련 위젯들
        self.end_time_label = ttk.Label(
            self.interval_frame, text="구간 종료: 00:00", font=(self.korean_font, 10, "bold"))
        self.end_time_label.grid(
            row=1, column=0, sticky="w", pady=(3, 10), padx=(0, 10))

        self.set_end_button = ttk.Button(self.interval_frame,
                                         text="종료 지점 설정",
                                         style='PastelGreenOutline.TButton',
                                         command=self.main_command_handler.on_set_end_click,
                                         state=tk.DISABLED)
        self.set_end_button.grid(row=1, column=1, sticky="w", pady=(3, 10))

        # 도움말 레이블 (옵션)
        help_label = ttk.Label(self.interval_frame,
                               text="ⓘ 구간 설정 후 저장/미리보기가 가능합니다.",
                               font=(self.korean_font, 11),
                               foreground='gray')
        help_label.grid(row=2, column=0, columnspan=2,
                        sticky="w", pady=(10, 0))

    # <- create_save_button 및 create_preview_button 통합
    def create_save_action_section(self):
        """구간 저장 및 미리보기 버튼 (save_action_frame 내에 배치)"""
        self.save_segment_button = ttk.Button(
            self.save_action_frame,
            text="구간 저장",
            style='2Pastel.TButton',
            command=self.main_command_handler.on_save_segment_click
        )
        self.save_segment_button.pack(
            pady=(10, 5), padx=5, fill=tk.X, expand=True)

        self.preview_button = ttk.Button(
            self.save_action_frame,
            text="선택구간 미리보기",
            style='3Pastel.TButton',
            command=self.main_command_handler.on_preview_click
        )
        self.preview_button.pack(pady=5, padx=5, fill=tk.X, expand=True)

    # UI 업데이트 이벤트 리스너

    def _on_ui_update(self, **kwargs):  # 함수의 매개변수로 여러 개의 키-값 쌍을 전달, Dict 형태로 전달
        """UI 업데이트 이벤트 처리"""
        component = kwargs.get('component', '')

        if component == "video_info":
            self._update_video_info()

        elif component == "slider":
            self._update_slider()

        elif component == "segment_labels":
            self._update_segment_labels()

        elif component == "save_buttons":
            self._update_save_buttons()

    # UI 업데이트 메서드들
    def _update_video_info(self):
        """비디오 정보 업데이트 (VLC 전용)"""
        # 비디오 정보 라벨 업데이트
        self._update_video_info_label()

        # 슬라이더 범위 업데이트
        if hasattr(self.app, 'vlc_player') and self.app.vlc_player.duration > 0:
            self.update_slider_range(self.app.vlc_player.duration)
            print(f"MainTab: 슬라이더 범위 업데이트됨 - {self.app.vlc_player.duration}초")

            # 슬라이더 시간 표시 업데이트
            if hasattr(self, 'slider_label'):
                total_time = VideoUtils.format_time(
                    int(self.app.vlc_player.duration))
                self.slider_label.config(text=f"00:00:00 / {total_time}")

        # 비디오가 새로 로드된 경우에만 플레이어 상태 이벤트 발생
        # (슬라이더 등에서 emit한 상태를 덮어쓰지 않도록 조건부 처리)
        if not hasattr(self, '_video_info_updated') or not self._video_info_updated:
            self._video_info_updated = True
            print("MainTab: 비디오 로드 완료 - 플레이어 상태 이벤트 발생")

            event_system.emit(Events.PLAYER_STATE_CHANGED,
                              is_playing=False, is_stopped=True)
        else:
            print("MainTab: 비디오 정보 업데이트 완료 (상태 이벤트 생략)")

    def _update_video_info_label(self):
        """비디오 정보 라벨 업데이트"""
        if hasattr(self.app, 'video_path') and self.app.video_path:
            info_text = f"비디오 이름: {os.path.basename(self.app.video_path)}\n"

            # OpenCV를 사용하여 비디오 메타데이터 가져오기
            video_info = VideoUtils.get_opencv_video_info(self.app.video_path)
            if video_info:
                if video_info.get('duration', 0) > 0:
                    info_text += f"동영상 길이: {VideoUtils.format_time(int(video_info['duration']))}\n"
                if video_info.get('fps', 0) > 0:
                    info_text += f"프레임 레이트: {video_info['fps']:.2f} fps\n"
                if video_info.get('width', 0) > 0 and video_info.get('height', 0) > 0:
                    info_text += f"동영상 해상도: {video_info['width']} x {video_info['height']}\n"
            else:
                # 폴백: 기본 정보만 표시
                if hasattr(self.app, 'vlc_player') and self.app.vlc_player.duration > 0:
                    info_text += f"동영상 길이: {VideoUtils.format_time(int(self.app.vlc_player.duration))}"

            self.video_info_label.config(text=info_text)

    def _update_slider(self):
        """슬라이더 상태 업데이트"""
        if hasattr(self.app, 'vlc_player') and self.app.vlc_player.duration > 0:
            self.update_slider_range(self.app.vlc_player.duration)

    def _update_segment_labels(self):
        """구간 라벨 업데이트"""
        if hasattr(self.app, 'start_time'):
            start_text = f"구간 시작: {VideoUtils.format_time(int(self.app.start_time))}"
            self.start_time_label.config(text=start_text)

        if hasattr(self.app, 'end_time'):
            end_text = f"구간 종료: {VideoUtils.format_time(int(self.app.end_time))}"
            self.end_time_label.config(text=end_text)

    def _update_save_buttons(self):
        """저장 버튼 상태 업데이트"""
        if hasattr(self.app, 'update_save_button_state'):
            self.app.update_save_button_state()

    def _on_player_state_changed(self, is_playing, is_stopped, **kwargs):
        """플레이어 상태 변경 이벤트를 처리하여 UI를 업데이트"""
        print(f"MainTab: 플레이어 상태 변경 - 재생:{is_playing}, 정지:{is_stopped}")

        if is_stopped:  # 정지 상태일때,
            self._handle_stopped_state()
        else:  # 재생 혹은 일시정지 상태일때
            self._handle_playing_or_paused_state(is_playing)

        # 구간 저장 버튼 상태 업데이트
        self._update_save_button_state()

    def _handle_stopped_state(self):
        """정지 상태일 때 UI 업데이트"""
        # 재생 버튼 텍스트 및 슬라이더 초기화
        self.play_button.config(text="► 재생")
        self.position_slider.set(0)
        self.slider_label.config(text="00:00:00 / 00:00:00")

        # 비디오 로드 여부에 따라 버튼 상태 결정
        video_loaded = self._is_video_loaded()
        self._set_all_buttons_state(tk.NORMAL if video_loaded else tk.DISABLED)

        print(f"MainTab: 정지 상태 처리 완료 - 비디오 로드됨:{video_loaded}")

    def _handle_playing_or_paused_state(self, is_playing):
        """재생/일시정지 상태일 때 UI 업데이트"""
        # 정지 버튼은 항상 활성화
        self.stop_button.config(state=tk.NORMAL)

        # 재생 중 상태일때, 일시정지로 보여주기
        if is_playing:
            self.play_button.config(text="|| 일시정지")
            print("MainTab: 재생 상태 UI 업데이트")
        # 일시정지 상태일때, 재생으로 보여주기
        else:
            self.play_button.config(text="► 재생")
            print("MainTab: 일시정지 상태 UI 업데이트")

        # 구간 설정 버튼들 활성화
        self.set_start_button.config(state=tk.NORMAL)
        self.set_end_button.config(state=tk.NORMAL)

    def _update_save_button_state(self):
        """구간 저장 버튼 상태 업데이트"""
        if hasattr(self.app, 'update_save_button_state'):
            self.app.update_save_button_state()

    def _is_video_loaded(self):
        """비디오가 로드되었는지 확인"""
        return (hasattr(self.app, 'vlc_player') and
                self.app.vlc_player and
                self.app.vlc_player.is_video_loaded())

    def _set_all_buttons_state(self, state):
        """모든 컨트롤 버튼들의 상태를 일괄 설정
           - 재생/일시정지
           - 정지
           - 구간시작설정
           - 구간종료설정"""

        # 구간 저장 버튼 미포함
        button_names = ['play_button', 'stop_button',
                        'set_start_button', 'set_end_button']
        for button_name in button_names:
            if hasattr(self, button_name):
                button = getattr(self, button_name)
                button.config(state=state)

    def _on_vlc_time_changed(self, time):
        """VLC 시간 변경 이벤트 처리"""
        if not self.is_slider_dragging:
            # 슬라이더 업데이트
            if hasattr(self.app, 'vlc_player') and self.app.vlc_player.duration > 0:
                self.progress_variable.set(time)

            # 시간 표시 업데이트
            time_str = VideoUtils.format_time(int(time))
            total_time = VideoUtils.format_time(
                int(self.app.vlc_player.duration))
            self.slider_label.config(text=f"{time_str} / {total_time}")

    def _save_widget_references(self):
        """앱에 위젯 참조 저장"""
        print("_save_widget_references 메서드 호출됨")

        self.app.video_frame = self.video_frame
        self.app.video_canvas = self.video_canvas
        self.app.video_label = self.video_label
        self.app.video_info_label = self.video_info_label
        self.app.position_slider = self.position_slider
        self.app.position_label = self.slider_label
        # 해당 속성이 있는지 확인 후 저장
        if hasattr(self, 'start_time_label') and self.start_time_label is not None:
            self.app.start_time_label = self.start_time_label
        if hasattr(self, 'end_time_label') and self.end_time_label is not None:
            self.app.end_time_label = self.end_time_label

        self.app.play_button = self.play_button
        self.app.stop_button = self.stop_button
        self.app.set_start_button = self.set_start_button
        self.app.set_end_button = self.set_end_button

        # 구간 저장 버튼 참조 추가
        if hasattr(self, 'save_segment_button'):
            self.app.save_segment_button = self.save_segment_button
