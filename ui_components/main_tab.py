import tkinter as tk
from tkinter import ttk
from .base_tab import BaseTab


class MainTab(BaseTab):
    def __init__(self, root, app):
        super().__init__(root, app)  # BaseTab의 __init__ 호출
        self._init_variables()  # MainTab 전용 변수 초기화
        self.create_ui()  # MainTab UI 생성

        # 추가로 확인할 수 있는 코드 (디버깅 용도)
        print(f"MainTab frame created: {self.frame}")

    def _init_variables(self):
        "Initialize MainTab UI variables"
        # 프레임 변수들
        self.top_frame = None  # 상단 (없음)
        self.openfile_frame = None  # 상단 (파란색)
        self.info_frame = None  # 상단 (노란색)
        self.video_frame = None  # 중간간 (빨간색)
        self.container_frame = None  # 하단 (초록색색)
        self.slider_frame = None  # 하단 (노란색)
        self.control_frame = None  # 하단(파란색)
        self.edit_frame = None  # 하단(보라색)

        # 참조 위젯 변수들
        self.videofile_label = None
        self.videofile_entry = None
        self.video_select_button = None
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

    def create_ui(self):
        """MainTab UI 구성 요소를 생성
        모든 최상위 UI 섹션을 생성해야 함. """

        self.create_top_frame()  # 상단
        self.create_video_frame()  # 비디오표시 부분
        self.create_control_frame()  # 컨트롤 부분 (슬라이더 및 편집 섹션)
        self._save_widget_references()

    def create_top_frame(self):
        "상단 프레임 생성 - 파일 선택 (까만색 테두리)"
        self.top_frame = tk.Frame(
            self.frame, highlightbackground="black", highlightthickness=1)
        self.top_frame.pack(pady=20, padx=20, fill=tk.X)
        # ✅  자식 위젯 크기에 따라 부모가 수축하지 않도록 막는 설정
        self.top_frame.pack_propagate(False)

        # ✅ top_frame 내에서 column 1 (openfile_frame)에 가중치 부여
        # openfile_frame은 top_frame 전체 너비를 차지하면서, 그 안의 Entry도 늘어나게 됩니다.
        self.top_frame.columnconfigure(1, weight=3)

        # info 프레임 (왼쪽)
        self.info_frame = tk.Frame(self.top_frame, highlightbackground="orange",
                                   highlightthickness=1)
        self.info_frame.grid(row=0, column=0, padx=10,
                             pady=10, sticky="nsew")  # grid에서 column 0

        # 비디오 정보를 인포 프레임에 추가
        self.video_info_label = tk.Label(
            self.info_frame, text="", font=("Arial", 10), fg="gray", anchor="w", justify="left")
        self.video_info_label.pack(fill=tk.X, expand=True, padx=5, pady=5)

        # openfile 프레임 (오른쪽)
        self.openfile_frame = tk.Frame(self.top_frame, highlightbackground="blue",
                                       highlightthickness=1)
        self.openfile_frame.grid(
            row=0, column=1, padx=(0, 15), sticky="nsew")  # grid에서 column 1

        # openfile_frame (Entry가 속한 column)이 가로로 늘어나도록 설정
        self.openfile_frame.columnconfigure(1, weight=1)

        # 파일 경로를 표시할 StringVar 생성
        self.app.video_path = tk.StringVar()
        # 비디오 파일 선택 텍스트
        self.videofile_label = tk.Label(
            self.openfile_frame, text="비디오 파일 선택:", font=("Arial", 12))
        self.videofile_label.grid(row=0, column=0, padx=(5, 5), sticky="w")

        # ✅ width=60 제거 + sticky="we"
        self.videofile_entry = tk.Entry(
            self.openfile_frame, textvariable=self.app.video_path, width=60)
        # 엔트리 위젯은 sticky="we" 로 가로 방향을 늘릴 수 있습니다.
        self.videofile_entry.grid(row=0, column=1, padx=(0, 5))

        # 비디오 선택 버튼 생성
        self.video_select_button = tk.Button(
            self.openfile_frame, text="파일 선택", command=self.app.open_file)
        self.video_select_button.grid(row=0, column=2, padx=(0, 5))

    def create_video_frame(self):
        """중간 프레임 생성 - 파일 선택 (빨간색 테두리)
            비디오 로딩 안할때 백그라운드 컬러는 black"""
        # 비디오 프레임
        self.video_frame = tk.Frame(self.frame, bg="black", width=640, height=360,
                                    highlightbackground="red", highlightthickness=1)
        self.video_frame.pack(fill='both', expand=True, padx=10, pady=10)
        self.video_frame.pack_propagate(False)

        # 비디오 재생할 레이블 생성 및 저장
        self.video_label = tk.Label(self.video_frame)
        self.video_label.pack(expand=True)

    def create_control_frame(self):
        """슬라이더랑 구간선택 담을 컨트롤 기능의 컨테이너 프레임 (초록색 테두리)"""
        self.container_frame = tk.Frame(
            self.frame, highlightbackground="green", highlightthickness=1)
        self.container_frame.pack(fill=tk.X, padx=10, pady=10)

        # 슬라이더 섹션 생성, 여기에 안넣으면 creat_ui에 들어가 있어야 합니다.
        self.create_slider_section()
        # 편집 섹션 생성, 하지만 슬라이더와 편집 섹션이 control frame에 종속되기에 여기에서 명시해야합니다.
        self.create_edit_section()

    def create_slider_section(self):
        """슬라이더 섹션 생성"""
        # 슬라이더 프레임 (주황색 테두리)
        self.slider_frame = tk.Frame(
            self.container_frame, highlightbackground="orange", highlightthickness=1)
        self.slider_frame.pack(side=tk.LEFT, padx=10, pady=10,
                               fill=tk.X, expand=True)

        # 비디오 전체구간 슬라이더 생성 - command 제거거
        self.position_slider = ttk.Scale(self.slider_frame,
                                         orient='horizontal',
                                         #  command=self.app.select_position,
                                         from_=0,
                                         to=100,
                                         length=500,
                                         style='Horizontal.TScale')  # 스타일 추가

        # 슬라이더 스타일 설정
        style = ttk.Style()
        style.configure('Horizontal.TScale',
                        background='white',
                        troughcolor='lightgray',
                        sliderthickness=10)  # 슬라이더 두께 증가

        self.position_slider.pack(fill=tk.X, padx=3, pady=5)

        # # 슬라이더 이벤트 바인딩 추가 ref link: https://076923.github.io/posts/Python-tkinter-23/
        # self.position_slider.bind(
        #     '<Button-1>', lambda e: self.app.select_position(self.position_slider.get()))  # <Button-1>마우스 왼족 버튼 누를때
        # self.position_slider.bind(
        #     '<B1-Motion>', lambda e: self.app.select_position(self.position_slider.get()))  # <B1-Motion>마우스 왼쪽 버튼을 누르면서 움직일때때

        # 현재 위치 시간
        self.position_label = tk.Label(self.slider_frame, text="00:00")
        self.position_label.pack(pady=3)

        # 디버깅 출력
        print(f"position_label created: {self.position_label}")

        self.create_button_section()

    def create_button_section(self):
        """재생 컨트롤 버튼들을 담을 프레임 (파란 테두리)"""
        self.control_frame = tk.Frame(
            self.slider_frame, highlightbackground="blue", highlightthickness=1)
        self.control_frame.pack(pady=3)

        self.play_button = tk.Button(self.control_frame, text="▶",
                                     command=self.app.toggle_play)
        self.play_button.pack(side=tk.LEFT)

        self.stop_button = tk.Button(self.control_frame, text="⏹",
                                     command=self.app.stop_video)
        self.stop_button.pack(side=tk.LEFT)

    def create_edit_section(self):
        """선택 구간 섹션 생성"""
        # 편집 내용 프레임 (보라색 테두리)
        self.edit_frame = tk.Frame(
            self.container_frame, highlightbackground="purple", highlightthickness=1)
        self.edit_frame.pack(side=tk.LEFT, padx=10, pady=10)

        self.create_interval()
        self.create_preview_button()

    def create_interval(self):
        """구간의 시작 시간, 끝 시간 설정 섹션 생성"""
        # 시작 시간 관련 위젯들들
        self.start_frame = tk.Frame(self.edit_frame)
        self.start_frame.pack(side=tk.TOP, pady=3)
        self.start_time_label = tk.Label(
            self.start_frame, text="선택구간 시작: 00:00")
        self.start_time_label.pack(side=tk.LEFT)
        self.set_start_button = tk.Button(self.start_frame, text="시작 지점 설정",
                                          command=self.app.set_start_time, state=tk.DISABLED)
        self.set_start_button.pack(side=tk.LEFT, padx=5)

        # 종료 시간 관련 위젯들
        self.end_frame = tk.Frame(self.edit_frame)
        self.end_frame.pack(side=tk.TOP, pady=3)
        self.end_time_label = tk.Label(self.end_frame, text="선택구간 종료: 00:00")
        self.end_time_label.pack(side=tk.LEFT)
        self.set_end_button = tk.Button(self.end_frame, text="종료 지점 설정",
                                        command=self.app.set_end_time, state=tk.DISABLED)
        self.set_end_button.pack(side=tk.LEFT, padx=5)

    def create_preview_button(self):
        """선택구간 미리보기 버튼 생성"""
        self.preview_button = tk.Button(
            self.edit_frame, text="선택구간 미리보기", command=lambda: self.app.preview_selection())
        self.preview_button.pack(side=tk.TOP, pady=3)

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
