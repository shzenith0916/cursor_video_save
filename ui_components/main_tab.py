import tkinter as tk
import ttkbootstrap as ttk  # ttkbootstrap으로 변경
from ttkbootstrap.constants import *  # Bootstrap 스타일 상수들

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
        self._init_variables()  # MainTab 전용 변수 초기화

        # 메인탭 Command handler 초기화
        self.main_command_handler = MainTabCommandHandler(app)
        # command_handler에 main_tab 참조 설정
        self.main_command_handler.set_main_tab(self)

        self.create_ui()  # MainTab UI 생성
        self.setup_event_listeners()

        # 추가로 확인할 수 있는 코드 (디버깅 용도)
        print(f"MainTab frame created: {self.frame}")

    def _init_variables(self):
        "Initialize MainTab UI variables"
        # 프레임 변수들
        self.table_frame = None  # 왼쪽
        self.info_frame = None  # 오른쪽

        # 참조 위젯 변수들
        self.videofile_label = None
        self.videofile_entry = None
        self.file_select_button = None
        self.video_info_label = None
        self.video_label = None
        self.position_slider = None
        self.position_label = None
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

    def create_ui(self):
        """MainTab UI 구성 요소를 생성
        모든 최상위 UI 섹션을 생성해야 함. """

        self.create_top_frame()  # 상단
        self.create_video_frame()  # 비디오표시 부분
        self.create_control_frame()  # 컨트롤 부분 (슬라이더 및 편집 섹션)
        self._save_widget_references()

    def create_top_frame(self):
        "상단 프레임 생성 - 파일 선택"
        self.top_frame = ttk.Frame(self.frame)
        self.top_frame.pack(pady=20, padx=20, fill=ttk.X)
        # 자식 위젯 크기에 따라 부모가 수축하지 않도록 막는 설정
        self.top_frame.pack_propagate(False)

        # ✅ top_frame 내에서 column 0 (openfile_frame)에 가중치 부여
        # openfile_frame은 왼쪽에 위치하면서 필요한 공간만 차지
        self.top_frame.columnconfigure(0, weight=1)

        # openfile 프레임 (왼쪽으로 이동)
        self.openfile_frame = tk.Frame(self.top_frame)
        self.openfile_frame.grid(
            row=0, column=0, padx=(15, 0), sticky="w")  # grid에서 column 0, sticky="w"로 왼쪽 붙이기

        # 파일 경로를 표시할 StringVar 생성
        self.video_path_var = tk.StringVar()

        # 비디오 파일 선택 텍스트 - 스타일 개선
        self.videofile_label = ttk.Label(
            self.openfile_frame, text="비디오 파일 선택", font=("Arial", 12, "bold"))
        self.videofile_label.grid(row=0, column=0, padx=(
            5, 5), sticky="w")  # width=60 제거 + sticky="w" 로 왼쪽으로 붙이기

        # 엔트리 위젯에 바인딩 - StringVar 사용
        # 엔트리 박스 크기 조정하여 레이블 바로 옆에 붙이기
        self.videofile_entry = tk.Entry(
            self.openfile_frame, textvariable=self.video_path_var,
            width=40 * int(UiUtils.get_scaling_factor_by_dpi(self.root)))
        # "we"로 가로 방향을 늘릴 수 있습니다.
        self.videofile_entry.grid(row=0, column=1, padx=(0, 5), sticky="we")

        # 비디오 선택 버튼 생성
        self.video_select_button = ttk.Button(
            self.openfile_frame, text="파일 선택", style="InfoLarge.TButton",
            command=self.main_command_handler.on_file_select)
        self.video_select_button.grid(row=0, column=2, padx=(0, 5))

        # info 프레임 (오른쪽으로 이동)
        self.info_frame = tk.Frame(self.top_frame)
        self.info_frame.grid(row=0, column=1, padx=10,
                             pady=10, sticky="w")  # grid에서 column 1, sticky="w"로 왼쪽 붙이기

        # 섹션 타이틀
        self.section_title_label = ttk.Label(
            self.info_frame, text="비디오정보", font=("Arial", 12, "bold"))
        self.section_title_label.pack(
            pady=(0, 2), anchor="w")  # 상단 패딩 약간, 왼쪽 정렬

        # 구분선
        self.separator = ttk.Separator(self.info_frame, orient=tk.HORIZONTAL)
        self.separator.pack(fill=tk.X, pady=(0, 5), expand=True)  # 위아래 패딩 추가

        # 비디오 정보를 인포 프레임에 추가
        self.video_info_label = ttk.Label(
            self.info_frame, text="", font=("Arial", 10), foreground="gray", anchor="w", justify="left")
        self.video_info_label.pack(fill=tk.X, expand=True, padx=5, pady=5)

    def create_video_frame(self):
        """중간 프레임 생성 - 파일 선택 (빨간색 테두리)
            비디오 로딩 안할때 백그라운드 컬러는 black"""
        # 비디오 프레임
        self.video_frame = tk.Frame(
            self.frame, bg="black", width=int(640 * UiUtils.get_scaling_factor_by_dpi(self.root)),
            height=int(360 * UiUtils.get_scaling_factor_by_dpi(self.root)),
            relief="solid", borderwidth=2)
        self.video_frame.pack(fill='both', expand=True, padx=10, pady=10)
        self.video_frame.pack_propagate(False)

        # 비디오 재생할 레이블 생성 및 저장
        self.video_label = tk.Label(self.video_frame)
        self.video_label.pack(expand=True)

    def create_control_frame(self):
        """슬라이더, 구간 설정, 저장/미리보기 버튼을 담는 메인 컨트롤 프레임"""
        self.container_frame = tk.Frame(self.frame)
        self.container_frame.pack(fill=tk.X, padx=10, pady=10)

        # Grid 컬럼 가중치 설정 (예: slider 40%, interval 30%, save 30%)
        self.container_frame.columnconfigure(0, weight=4)  # slider_frame
        self.container_frame.columnconfigure(1, weight=3)  # interval_frame
        self.container_frame.columnconfigure(2, weight=3)  # save_frame

        # 1. 좌측: 슬라이더 및 재생/정지 버튼 프레임
        self.slider_frame = tk.Frame(self.container_frame)
        self.slider_frame.grid(
            row=0, column=0, padx=(0, 5), pady=5, sticky="nsew")
        self.create_slider_section()  # 슬라이더와 재생/정지 버튼 생성 및 배치

        # 2. 중앙: 구간 시작/종료 설정 프레임
        self.interval_frame = tk.Frame(self.container_frame)
        self.interval_frame.grid(
            row=0, column=1, padx=5, pady=5, sticky="nsew")
        self.create_interval_section()  # 구간 설정 위젯 생성 및 배치 (이전 create_edit_section)

        # 3. 우측: 구간 저장 및 미리보기 버튼 프레임
        # save_frame -> save_action_frame으로 이름 변경 고려
        self.save_action_frame = tk.Frame(self.container_frame)
        self.save_action_frame.grid(
            row=0, column=2, padx=(5, 0), pady=5, sticky="nsew")
        self.create_save_action_section()  # 저장/미리보기 버튼 생성 및 배치

    def create_slider_section(self):
        """슬라이더 섹션 생성 (slider_frame 내에 배치)"""
        # 비디오 전체구간 슬라이더 생성
        self.position_slider = ttk.Scale(self.slider_frame,
                                         orient='horizontal',
                                         command=self.app.select_position,
                                         from_=0,
                                         to=100,
                                         length=450,  # 길이 약간 줄임
                                         style='Horizontal.TScale')
        self.position_slider.pack(fill=tk.X, padx=3, pady=5, expand=True)

        self.position_label = ttk.Label(self.slider_frame, text="00:00",
                                        font=("Arial", 11, "bold"))
        self.position_label.pack(pady=3)

        self.create_button_section()  # 재생/정지 버튼은 slider_frame 소속

    def create_button_section(self):
        """재생 컨트롤 버튼들을 slider_frame 내에 생성"""
        control_buttons_subframe = tk.Frame(
            self.slider_frame)  # 버튼들을 담을 내부 프레임
        control_buttons_subframe.pack(pady=8)

        self.play_button = ttk.Button(control_buttons_subframe, text="► 재생",
                                      style="PlayOutline.TButton",
                                      command=self.main_command_handler.on_play_click, width=12,
                                      state=tk.DISABLED)
        self.play_button.pack(side=tk.LEFT, padx=10, pady=2)

        self.stop_button = ttk.Button(control_buttons_subframe, text="◼ 정지",
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
            self.interval_frame, text="구간 시작: 00:00", font=("Arial", 10, "bold"))
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
            self.interval_frame, text="구간 종료: 00:00", font=("Arial", 10, "bold"))
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
                               font=("Tahoma", 11),
                               foreground='gray')
        help_label.grid(row=2, column=0, columnspan=2,
                        sticky="w", pady=(10, 0))

    # <- create_save_button 및 create_preview_button 통합
    def create_save_action_section(self):
        """구간 저장 및 미리보기 버튼 (save_action_frame 내에 배치)"""
        self.save_segment_button = ttk.Button(
            self.save_action_frame,
            text="💾 구간 저장",
            style='2Pastel.TButton',
            command=self.main_command_handler.on_save_segment_click
        )
        self.save_segment_button.pack(
            pady=(10, 5), padx=5, fill=tk.X, expand=True)

        self.preview_button = ttk.Button(
            self.save_action_frame,
            text="🎬 선택구간 미리보기",
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
        elif component == "play_button":
            self._update_play_button()
        elif component == "video_controls":
            self._update_video_controls()
        elif component == "slider":
            self._update_slider()
        elif component == "segment_labels":
            self._update_segment_labels()
        elif component == "save_buttons":
            self._update_save_buttons()

    def _on_player_state_changed(self, is_playing, is_stopped, **kwargs):
        """플레이어 상태 변경 이벤트를 처리하여 UI를 업데이트"""
        if is_stopped:
            self.play_button.config(text="► 재생")
            self.position_slider.set(0)
            self.position_label.config(text="00:00")
            # 비디오 로드 여부에 따라 버튼 상태 결정
            if self.app.cap:
                self.play_button.config(state=tk.NORMAL)
                self.stop_button.config(state=tk.NORMAL)
                self.set_start_button.config(state=tk.NORMAL)
                self.set_end_button.config(state=tk.NORMAL)
            else:
                self.play_button.config(state=tk.DISABLED)
                self.stop_button.config(state=tk.DISABLED)
                self.set_start_button.config(state=tk.DISABLED)
                self.set_end_button.config(state=tk.DISABLED)
        else:  # Playing or Paused
            self.stop_button.config(state=tk.NORMAL)
            if is_playing:
                self.play_button.config(text="|| 일시정지")
                self.set_start_button.config(state=tk.NORMAL)
                self.set_end_button.config(state=tk.NORMAL)
            else:  # Paused
                self.play_button.config(text="► 재생")
                self.set_start_button.config(state=tk.NORMAL)
                self.set_end_button.config(state=tk.NORMAL)

        # 구간이 올바르게 설정되어 있으면 저장 버튼도 활성화
        self.app.update_save_button_state()

    # UI 업데이트 메서드들
    def _update_video_info(self):
        """비디오 정보 업데이트"""
        video_info = self.app_state.get_video_info()
        if video_info['is_loaded']:
            info_text = f"비디오 이름: {os.path.basename(video_info['path'])}\n"
            info_text += f"프레임 레이트: {video_info['fps']}\n"
            info_text += f"동영상 길이: {video_info['duration']}초\n"
            info_text += f"동영상 해상도: {video_info['width']} x {video_info['height']}"
            self.video_info_label.config(text=info_text)

            # 슬라이더 범위 설정
            self.position_slider.config(to=video_info['duration'])

            # 버튼 상태 업데이트
            self._update_button_states()

    def _save_widget_references(self):
        """앱에 위젯 참조 저장"""
        print("_save_widget_references 메서드 호출됨")

        self.app.video_frame = self.video_frame
        self.app.video_label = self.video_label
        self.app.video_info_label = self.video_info_label
        self.app.position_slider = self.position_slider
        self.app.position_label = self.position_label
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
