from utils.ui_utils import UiUtils
from .base_tab import BaseTab
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, filedialog
import os
import cv2
from datetime import datetime
from utils.utils import VideoUtils, show_custom_messagebox
from .segment_table import SegmentTable
from extract.extractor import VideoExtractor, ExtractConfig
import threading
from .command_handlers import NewTabCommandHandler
from utils.event_system import event_system, Events


class NewTab(BaseTab):
    def __init__(self, root, app):
        super().__init__(root, app)  # super()로 BaseTab 상속
        self.root = root
        self._init_variables()  # NewTab 전용 변수 초기화

        # NewTab Command handler 초기화
        self.new_command_handler = NewTabCommandHandler(app)
        # command_handler에 new_tab 참조 설정
        self.new_command_handler.set_new_tab(self)

        self.create_ui()  # NewTab UI 생성
        self._setup_event_listeners()  # 이벤트 리스너 설정

        # 앱에 NewTab 인스턴스 등록 (PreviewWindow에서 참조할 수 있도록)
        self.app.new_tab_instance = self

    def _setup_event_listeners(self):
        """이벤트 리스너 설정"""

        # 추출 관련 이벤트 구독
        event_system.subscribe(Events.EXTRACTION_START,
                               self._on_extraction_start)
        event_system.subscribe(Events.EXTRACTION_CANCEL,
                               self._on_extraction_cancel)
        event_system.subscribe(Events.EXTRACTION_PROGRESS,
                               self.update_progress)
        event_system.subscribe(Events.EXTRACTION_COMPLETE,
                               self.show_extraction_result)
        event_system.subscribe(Events.EXTRACTION_ERROR,
                               self.show_extraction_error)

        # 이미지 추출 관련 이벤트 구독
        event_system.subscribe(Events.IMAGE_EXTRACTION_START,
                               self._on_image_extraction_start)
        event_system.subscribe(Events.IMAGE_EXTRACTION_PROGRESS,
                               self.update_progress)
        event_system.subscribe(Events.IMAGE_EXTRACTION_COMPLETE,
                               self.show_image_extraction_result)

        # 오디오 추출 관련 이벤트 구독
        event_system.subscribe(Events.AUDIO_EXTRACTION_START,
                               self._on_audio_extraction_start)
        event_system.subscribe(Events.AUDIO_EXTRACTION_PROGRESS,
                               self.update_progress)
        event_system.subscribe(Events.AUDIO_EXTRACTION_COMPLETE,
                               self.show_audio_extraction_result)
        event_system.subscribe(Events.AUDIO_EXTRACTION_ERROR,
                               self.show_audio_extraction_error)

    def _on_extraction_start(self, segments=None, **kwargs):
        """추출 시작 이벤트 처리"""
        # 이미 추출 중이면 무시
        if hasattr(self, '_is_extracting') and self._is_extracting:
            return

        self._is_extracting = True
        self.extract_selected_segment()

    def _on_extraction_cancel(self, **kwargs):
        """추출 취소 이벤트 처리"""
        self._is_extracting = False
        self._is_image_extracting = False  # 이미지 추출도 함께 취소
        self._is_audio_extracting = False  # 오디오 추출도 함께 취소
        self.cancel_extraction()

    def _on_image_extraction_start(self, **kwargs):
        """이미지 추출 시작 이벤트 처리"""
        print(
            f"DEBUG: _on_image_extraction_start 호출됨. 현재 이미지 추출 중: "
            f"{hasattr(self, '_is_image_extracting') and self._is_image_extracting}")

        # 이미 이미지 추출 중이면 무시
        if hasattr(self, '_is_image_extracting') and self._is_image_extracting:
            print("DEBUG: 이미 이미지 추출 중이므로 무시")
            return

        self._is_image_extracting = True
        self.extract_images()

    def _on_audio_extraction_start(self, **kwargs):
        """오디오 추출 시작 이벤트 처리"""
        print(
            f"DEBUG: _on_audio_extraction_start 호출됨. 현재 오디오 추출 중: "
            f"{hasattr(self, '_is_audio_extracting') and self._is_audio_extracting}")

        # 이미 오디오 추출 중이면 무시
        if hasattr(self, '_is_audio_extracting') and self._is_audio_extracting:
            print("DEBUG: 이미 오디오 추출 중이므로 무시")
            return

        self._is_audio_extracting = True
        self.extract_audio()

    def _init_variables(self):
        """NewTab 전용 변수 초기화"""
        # BaseTab에서 이미 root와 app을 초기화했으므로 여기서는 다시 할당하지 않음
        self.video_path = None
        self.start_time = None
        self.end_time = None

        # 구간 추출 관련변수
        self.current_segment = None
        self.extract_config = ExtractConfig()

        # 중복 실행 방지 플래그들
        self._is_extracting = False
        self._is_image_extracting = False
        self._is_audio_extracting = False

        # 취소 이벤트 (백그라운드 작업 중단용)
        self.cancel_event = threading.Event()

        # 성능 최적화 관련 속성
        self.target_fps = 30
        self.frame_skip = 1
        self.frame_count = 0

    def create_ui(self):
        """UI 구성 요소 생성"""
        # 메인 프레임 - 3단 구조 (테이블 | 정보 및 추출 버튼| 저장 설정)
        self.main_frame = ttk.Frame(self.frame)
        self.main_frame.pack(fill=ttk.BOTH, expand=True, padx=5, pady=(5, 15))

        # 1) 왼쪽: 구간 테이블 (고정 너비)
        self.table_frame = ttk.Frame(self.main_frame, width=800)
        self.table_frame.pack(side=ttk.LEFT, fill=ttk.Y, padx=(5, 5))
        self.table_frame.pack_propagate(False)

        # SegmentTable 컴포넌트
        self.segment_table = SegmentTable(self.table_frame, self.app)

        # 2) 중간: 파일 정보 + 프로그레스 바 (고정 너비)
        self.info_frame = ttk.Frame(
            self.main_frame, width=int(450 * UiUtils.get_scaling_factor_by_dpi(self.root)))
        self.info_frame.pack(side=ttk.LEFT, fill=ttk.Y, padx=(5, 5))
        self.info_frame.pack_propagate(False)

        # 파일 정보 섹션 생성
        self.create_info_section()

        # 3) 오른쪽: 저장 설정 섹션
        self.setting_help_freme = ttk.Frame(self.main_frame)
        self.setting_help_freme.pack(
            side=ttk.RIGHT, fill=ttk.BOTH, expand=True, padx=(5, 5))

        # 설정 섹션 생성
        self.create_settings_section()

        # 콜백 설정
        self.segment_table.selection_callback = self.on_segment_selected

    def create_info_section(self):
        """파일 정보 섹션 생성"""

        # 1) 파일 정보 영역 (고정 높이)
        file_info_container = ttk.Frame(
            self.info_frame, height=int(550 * UiUtils.get_scaling_factor_by_dpi(self.root)))
        file_info_container.pack(fill=ttk.X, pady=(0, 5))
        file_info_container.pack_propagate(False)

        # 정보 표시 레이블
        info_title = ttk.Label(
            file_info_container,
            text="📁 파일 정보",
            font=("Arial", 13, "bold")
        )
        info_title.pack(fill=ttk.X, padx=10, pady=(15, 5), anchor="w")

        # 구분선 추가
        separator = ttk.Separator(file_info_container, orient="horizontal")
        separator.pack(fill=ttk.X, pady=(10, 10))

        self.file_info_label = ttk.Label(
            file_info_container,
            text="선택한 구간의 파일 정보가 여기에 표시됩니다.",
            justify=ttk.LEFT,
            anchor="nw",
            wraplength=int(430 * UiUtils.get_scaling_factor_by_dpi(self.root)),
            font=("Arial", 11)
        )
        self.file_info_label.pack(fill=ttk.X, padx=10, pady=10, anchor="nw")

        # 2) 버튼 영역 (고정 높이)
        self.create_info_buttons()

        # 3) 진행률 영역 (고정 높이)
        self.create_progress_controls()

    def file_info_update(self, file_path=None, start_time=None, end_time=None):
        """비디오 파일 정보와 선택된 구간 정보를 업데이트하는 메서드"""
        # 공통 유틸리티 사용
        file_info, error = VideoUtils.get_file_info(file_path)

        if error:
            self.file_info_label.config(text=error)
            return

        # 구간 정보 포맷팅
        segment_info = ""
        if start_time is not None and end_time is not None:
            segment_duration = end_time - start_time
            segment_info = f"""


✂️ 선택된 구간:

시작 시간: {VideoUtils.format_time(start_time)}

종료 시간: {VideoUtils.format_time(end_time)}

구간 길이: {VideoUtils.format_time(segment_duration)}"""

        props = file_info['video_props']
        info_text = f"""파일명: {file_info['file_name']}

크기: {file_info['file_size']}


🎬 비디오 속성:

해상도: {props['width']} x {props['height']}

프레임 레이트: {props['fps']:.2f} fps

전체 길이: {VideoUtils.format_time(props['length'])}

전체 프레임 수: {props['frame_count']:,} 프레임{segment_info}"""

        self.file_info_label.config(text=info_text)

    def on_segment_selected(self, segment_info):
        """SegmentTable에서 구간 행이 선택되었을때 호출되는 콜백 메서드"""

        print(f"선택된 구간: {segment_info}")

        # 선택된 구간의 파일 경로 처리 (공통 메서드 사용)
        file_path = VideoUtils.find_input_file(segment_info['file'], self.app)
        if not file_path:
            file_path = segment_info['file']  # fallback

        # 선택한 구간 정보로 파일 정보 업데이트
        self.file_info_update(
            file_path=file_path,
            start_time=segment_info['start'],
            end_time=segment_info['end']
        )

    def create_info_buttons(self):
        """파일 정보 영역 하단 버튼들 생성 - main_tab 스타일 적용"""
        # 버튼 영역 컨테이너 (고정 높이)
        button_container = ttk.Frame(
            self.info_frame, height=int(180 * UiUtils.get_scaling_factor_by_dpi(self.root)))
        button_container.pack(fill=ttk.X, pady=(0, 5))
        button_container.pack_propagate(False)

        # 구분선 추가
        separator = ttk.Separator(button_container, orient="horizontal")
        separator.pack(fill=ttk.X, pady=(10, 10))

        # 버튼 프레임 - button_container 내에 배치
        button_frame = ttk.Frame(button_container)
        button_frame.pack(fill=ttk.X, padx=20, pady=(10, 10))

        # 비디오 추출 버튼 (3Pastel 스타일)
        self.video_extract_button = ttk.Button(
            button_frame,
            text="비디오 추출",
            style='3Pastel.TButton',
            command=self.new_command_handler.on_extract_segments
        )
        self.video_extract_button.pack(
            pady=5, padx=5, fill=ttk.X, expand=True)

        # 이미지 추출 버튼 (3Pastel 스타일)
        self.image_extract_button = ttk.Button(
            button_frame,
            text="이미지 추출",
            style='3Pastel.TButton',
            command=self.new_command_handler.on_extract_images
        )
        self.image_extract_button.pack(pady=5, padx=5, fill=ttk.X, expand=True)

        # 취소 버튼 (3Pastel 스타일)
        self.cancel_button = ttk.Button(
            button_frame,
            text="작업 취소",
            style='3Pastel.TButton',
            command=self.new_command_handler.on_cancel_extraction
        )
        self.cancel_button.pack(pady=5, padx=5, fill=ttk.X, expand=True)

    def create_progress_controls(self):
        """가장 아래에 작업 진행률 생성"""
        # 진행률 영역 컨테이너 (고정 높이)
        progress_container = ttk.Frame(
            self.info_frame, height=int(120 * UiUtils.get_scaling_factor_by_dpi(self.root)))
        progress_container.pack(fill=ttk.X, pady=(0, 10))
        progress_container.pack_propagate(False)

        # 구분선 추가
        separator = ttk.Separator(progress_container, orient="horizontal")
        separator.pack(fill=ttk.X, pady=(10, 10))

        # 섹션 타이틀 (main_tab 스타일)
        progress_title = ttk.Label(
            progress_container,
            text="⚡ 작업 진행률",
            font=("Arial", 12, "bold")
        )
        progress_title.pack(pady=(5, 5), padx=10, anchor="w")

        # 진행률 바 프레임
        progress_frame = ttk.Frame(progress_container)
        progress_frame.pack(fill=ttk.X, padx=10, pady=(5, 5))

        # 프로그레스바와 퍼센티지를 수평으로 배치
        progress_container = ttk.Frame(progress_frame)
        progress_container.pack(fill=ttk.X, pady=(0, 5))

        # ttkbootstrap 스타일 프로그래스바
        self.progress_bar = ttk.Progressbar(
            progress_container,
            orient="horizontal",
            mode="determinate",
            bootstyle="success-striped"
        )
        self.progress_bar.pack(side=ttk.LEFT, fill=ttk.X,
                               expand=True, padx=(0, 10))

        # 퍼센티지 표시
        self.progress_percentage = ttk.Label(
            progress_container,
            text="0%",
            font=("Arial", 10, "bold"),
            width=6
        )
        self.progress_percentage.pack(side=ttk.RIGHT)

        # 상태 메시지 표시 (main_tab의 도움말 스타일)
        self.progress_status = ttk.Label(
            progress_frame,
            text="ⓘ 작업 대기 중입니다.",
            font=("Arial", 10),
            foreground="gray"
        )
        self.progress_status.pack(fill=ttk.X, pady=(5, 0), anchor="w")

    def refresh_table(self):
        """테이블 새로고침 메서드"""
        print("NewTab: refresh_table 호출됨")

        if hasattr(self, 'segment_table'):
            print("비디오 추출 탭: 테이블 새로고침 중 ...")
            self.segment_table.refresh()
            print("비디오 추출 탭: 테이블 새로고침 완료.")

            # 가장 최근 구간을 자동선택 후 정보 표시
            if self.app.saved_segments:
                latest_segment = self.app.saved_segments[-1]
                print(f"최신 구간 정보로 파일 정보 업데이트: {latest_segment}")

                # 파일 경로 찾기 (공통 메서드 사용)
                file_path = VideoUtils.find_input_file(
                    latest_segment['file'], self.app)
                if not file_path:
                    file_path = latest_segment['file']  # fallback

                self.file_info_update(
                    file_path=file_path,
                    start_time=latest_segment['start'],
                    end_time=latest_segment['end']
                )

                # 가장 최근 구간간 행을 시각적으로도 선택
                if hasattr(self.app, 'segment_table'):
                    items = self.segment_table.tree.get_children()
                    if items:
                        self.segment_table.tree.selection_set(items[-1])
                        self.segment_table.tree.see(items[-1])
                        self.segment_table.tree.focus(items[-1])

        else:
            print("비디오 추출 탭: 선택 구간 테이블이 존재하지 않음")

    def create_settings_section(self):
        """저장 설정 섹션 생성"""

        # 메인 타이틀
        main_title = ttk.Label(self.setting_help_freme,
                               text="저장 설정",
                               font=("Arial", 13, "bold")
                               )
        main_title.pack(fill=ttk.X, padx=10, pady=(15, 5), anchor="w")

        # 구분선 추가
        separator = ttk.Separator(self.setting_help_freme, orient="horizontal")
        separator.pack(fill=ttk.X, padx=10, pady=(10, 15))

        # CSV 파일명 설정 섹션
        csv_frame = ttk.Frame(self.setting_help_freme)
        csv_frame.pack(fill=ttk.X, padx=10, pady=10)
        # 섹션 타이틀
        csv_manual = ttk.Label(
            csv_frame, text="CSV 파일명 설정", font=("Arial", 11, "bold"))
        csv_manual.pack(fill=ttk.X, pady=5, anchor="w")

        # csv 파일명 설명하는 도움말 레이블
        csv_help = ttk.Label(csv_frame,
                             text="ⓘ csv 내보내기 시, 자동으로 생성되는 파일명이 어떻게 생성되는지 확인할 수 있습니다.",
                             font=("Arial", 10),
                             foreground="gray"
                             )
        csv_help.pack(fill=ttk.X, pady=(10, 10), anchor="w")

        # 파일명 조합 설명
        filename_format = ttk.Label(csv_frame,
                                    text="파일명 조합: [비디오명]_구간데이터_[구간수]개_[날짜].csv",
                                    font=("Arial", 9)
                                    )
        filename_format.pack(fill=ttk.X, pady=(10, 2), anchor="w")

        # 예시 설명
        example_text = ttk.Label(csv_frame,
                                 text="예시: 홍길동(1)SF_구간데이터_5개_20250606.csv",
                                 font=("Arial", 9)
                                 )
        example_text.pack(fill=ttk.X, pady=(10, 5), anchor="w")

        # 구분선
        separator1 = ttk.Separator(
            self.setting_help_freme, orient="horizontal")
        separator1.pack(fill=ttk.X, pady=(10, 5))

        # mp4 파일명 설정 섹션
        mp4_frame = ttk.Frame(self.setting_help_freme)
        mp4_frame.pack(fill=ttk.X, padx=10, pady=10)
        # 섹션 타이틀
        mp4_manual = ttk.Label(
            mp4_frame, text="MP4 파일명 설정", font=("Arial", 11, "bold"))
        mp4_manual.pack(fill=ttk.X, pady=5, anchor="w")

        # mp4 파일명 설명하는 도움말 레이블
        mp4_help = ttk.Label(mp4_frame,
                             text="ⓘ mp4 내보내기 시, 자동으로 생성되는 파일명이 어떻게 생성되는지 확인할 수 있습니다.",
                             font=("Arial", 10),
                             foreground="gray"
                             )
        mp4_help.pack(fill=ttk.X, pady=(10, 10), anchor="w")

        # 파일명 조합 설명
        filename_format = ttk.Label(mp4_frame,
                                    text="파일명 조합: [비디오명]_[시작구간 hh-mm-ss]_[종료료구간 hh-mm-ss].mp4",
                                    font=("Arial", 9)
                                    )
        filename_format.pack(fill=ttk.X, pady=(10, 2), anchor="w")

        # 예시 설명
        example_text = ttk.Label(mp4_frame,
                                 text="예시: 홍길동(1)SF_00-00-00_00-00-03.mp4",
                                 font=("Arial", 9)
                                 )
        example_text.pack(fill=ttk.X, pady=(10, 5), anchor="w")

        # 구분선
        separator2 = ttk.Separator(
            self.setting_help_freme, orient="horizontal")
        separator2.pack(fill=ttk.X, pady=(10, 5))

        # 이미지 저장 설정 섹션
        img_frame = ttk.Frame(self.setting_help_freme)
        img_frame.pack(fill=ttk.X, padx=10, pady=10)
        # 섹션 타이틀
        img_manual = ttk.Label(
            img_frame, text="이미지 파일명 설정", font=("Arial", 11, "bold"))
        img_manual.pack(fill=ttk.X, pady=5, anchor="w")

        # img 파일명 설명하는 도움말 레이블
        img_help = ttk.Label(img_frame,
                             text="ⓘ 이미지 추출 시, 자동으로 생성되는 폴더명과 파일명 형식을 확인할 수 있습니다.",
                             font=("Arial", 10),
                             foreground="gray"
                             )
        img_help.pack(fill=ttk.X, pady=(10, 10), anchor="w")

        # 폴더명 조합 설명
        folder_format = ttk.Label(img_frame,
                                  text="📁 폴더명: [비디오명]_[시작구간 hh-mm-ss]_[종료구간 hh-mm-ss]_[날짜]",
                                  font=("Arial", 9)
                                  )
        folder_format.pack(fill=ttk.X, pady=(10, 2), anchor="w")

        # 폴더 예시 설명
        folder_example = ttk.Label(img_frame,
                                   text="예시: 홍길동(1)SF_00-00-00_00-00-03_241201",
                                   font=("Arial", 9)
                                   )
        folder_example.pack(fill=ttk.X, pady=(5, 10), anchor="w")

        # 파일명 조합 설명
        filename_format = ttk.Label(img_frame,
                                    text="📄 파일명: [비디오명]_[날짜]_[프레임번호].jpg",
                                    font=("Arial", 9)
                                    )
        filename_format.pack(fill=ttk.X, pady=(10, 2), anchor="w")

        # 예시 설명
        example_text = ttk.Label(img_frame,
                                 text="예시: 홍길동(1)SF_250601_frame000123.jpg",
                                 font=("Arial", 9)
                                 )
        example_text.pack(fill=ttk.X, pady=(10, 5), anchor="w")

        # 저장 위치 설명
        save_location = ttk.Label(img_frame,
                                  text="💾 저장 위치: 사용자가 선택한 폴더에 자동 생성",
                                  font=("Arial", 9),
                                  foreground="blue"
                                  )
        save_location.pack(fill=ttk.X, pady=(10, 5), anchor="w")

    def extract_selected_segment(self):
        """선택된 구간 추출"""
        try:
            # 취소 이벤트 초기화 (새 작업 시작)
            self.cancel_event.clear()

            # 1. 선택 확인
            selected_items = self.segment_table.table.selection()
            if not selected_items:
                show_custom_messagebox(
                    self.frame, "경고", "추출할 구간을 선택해주세요.", "warning")
                return

            # 2. 구간 정보 가져오기
            index = self.segment_table.table.index(selected_items[0])
            if index >= len(self.app.saved_segments):
                show_custom_messagebox(
                    self.frame, "오류", "구간 정보를 찾을 수 없습니다.", "warning")
                return

            segment_info = self.app.saved_segments[index]

            # 3. 입력 파일 찾기 (공통 메서드 사용)
            input_path = VideoUtils.find_input_file(
                segment_info['file'], self.app)
            if not input_path:
                show_custom_messagebox(
                    self.frame, "오류", "원본 비디오 파일을 찾을 수 없습니다.", "warning")
                return

            # 4. 출력 파일 선택
            default_filename = self.extract_config.generate_filename(
                segment_info)

            output_path = filedialog.asksaveasfilename(
                title="저장할 위치 선택",
                defaultextension=".mp4",
                filetypes=VideoExtractor.get_supported_formats(),
                initialfile=default_filename
            )

            if not output_path:
                return

            # 5. 추출 시작
            print(f"비디오 추출 시작: {segment_info['start']}~{segment_info['end']}초")
            self.progress_bar['value'] = 0

            threading.Thread(
                target=self.do_extraction,
                args=(input_path, output_path, segment_info),
                daemon=True
            ).start()

        except Exception as e:
            show_custom_messagebox(
                self.frame, "오류", f"추출 준비 중 오류: {str(e)}", "warning")

    def do_extraction(self, input_path, output_path, segment_info):
        """실제 추출 작업 (백그라운드)"""
        try:
            # 취소 이벤트 초기화
            self.cancel_event.clear()

            # 취소 확인 (한 번만 체크)
            if self.cancel_event.is_set():
                self.update_progress_safe(0, "취소됨", "취소")
                return

            # 시작 상태 업데이트
            self.update_progress_safe(0, "추출 시작...", "시작...")

            # VideoExtractor로 추출
            result = VideoExtractor.extract_segment(
                input_video_path=input_path,
                output_video_path=output_path,
                start_time=segment_info['start'],
                end_time=segment_info['end'],
                progress_callback=self.extraction_progress_callback,
                ffmpeg_codec_copy=self.extract_config.use_codec_copy
            )

            # 결과 표시
            self.frame.after(0, lambda: self.show_extraction_result(result))

        except Exception as e:
            self.frame.after(0, lambda: self.show_extraction_error(e))

    def extraction_progress_callback(self, msg):
        """추출 진행률 콜백"""
        if not self.cancel_event.is_set():  # 취소되지 않은 경우만 업데이트
            self.update_progress_safe(50, f"🔄 {msg}", "⚙️")

    def show_extraction_result(self, result):
        """추출 결과 표시"""
        # 추출 완료 후 플래그 리셋
        self._is_extracting = False

        if result['success']:
            self.update_progress(100, "추출 완료!", "✅")
            show_custom_messagebox(
                self.frame, "비디오 추출 완료", "추출 성공!", "success")

        else:
            self.update_progress(0, " 추출 실패", "❌")
            show_custom_messagebox(
                self.frame, "실패", f"추출 실패: {result['message']}", "error")

        # 5초 후 진행률 바 초기화
        self.frame.after(5000, lambda: self.update_progress(0, "대기 중...", "⚡"))

    def show_extraction_error(self, error):
        """추출 오류 표시"""
        # 추출 오류 후 플래그 리셋
        self._is_extracting = False

        self.update_progress(0, "오류 발생", "⚠️")
        show_custom_messagebox(
            self.frame, "오류", f"추출 중 오류: {str(error)}", "warning")

    def update_progress_safe(self, value, status="", icon="⚡", **kwargs):  # 백그라운드 작업
        """스레드 안전한 진행률 업데이트 헬퍼 메서드"""
        self.frame.after(0, lambda: self.update_progress(value, status, icon))

    def update_progress(self, value=0, status="", icon="⚡", **kwargs):  # 프론트엔드 작업
        """진행률 업데이트 (main_tab 스타일)"""
        # 키워드 인수로 progress가 전달된 경우 value로 사용
        if 'progress' in kwargs:
            value = kwargs['progress']

        if value is not None:
            self.progress_bar['value'] = value
            self.progress_percentage.config(text=f"{int(value)}%")

        # 상태 메시지 업데이트
        if status:
            self.progress_status.config(text=f"ⓘ {status}")
        elif value == 0:
            self.progress_status.config(text="ⓘ 작업 대기 중입니다.")
        elif value < 100:
            self.progress_status.config(text=f"ⓘ 작업 진행 중... ({int(value)}%)")
        elif value == 100:
            self.progress_status.config(text="ⓘ 작업이 완료되었습니다!")

    def cancel_extraction(self):
        """추출 취소"""
        self.cancel_event.set()  # 취소 신호 전송
        self.update_progress(0, "취소됨", "❌")
        print("❌ 추출 취소 신호 전송됨")  # 터미널 표시 디버깅 메세지

        show_custom_messagebox(
            self.frame, "추출 취소", "사용자에 의해 추출이 취소되었습니다.", "error")

    def extract_images(self):
        """선택된 구간에서 이미지 추출 (FPS 기반 스킵)"""
        try:
            # 취소 이벤트 초기화
            self.cancel_event.clear()

            # 1. 선택된 구간 정보 가져오기
            segment_info = self._get_selected_segment_info()
            if not segment_info:
                return

            # 2. 입력 파일 찾기
            input_path = self._find_input_file(segment_info)
            if not input_path:
                return

            # 3. 출력 폴더 설정
            output_folder = self._setup_output_folder(input_path, segment_info)
            if not output_folder:
                return

            # 4. 이미지 추출 시작
            self._start_image_extraction(
                input_path, output_folder, segment_info)

        except Exception as e:
            show_custom_messagebox(
                self.frame, "오류", f"이미지 추출 준비 중 오류: {str(e)}", "error")

    def _get_selected_segment_info(self):
        """선택된 구간 정보 가져오기"""
        # 선택 확인
        selected_items = self.segment_table.table.selection()
        if not selected_items:
            show_custom_messagebox(
                self.frame, "경고", "이미지를 추출할 구간을 선택해주세요.", "warning")
            return None

        # 구간 정보 가져오기
        index = self.segment_table.table.index(selected_items[0])
        if index >= len(self.app.saved_segments):
            show_custom_messagebox(
                self.frame, "오류", "구간 정보를 찾을 수 없습니다.", "error")
            return None

        return self.app.saved_segments[index]

    def _find_input_file(self, segment_info):
        """입력 파일 찾기"""
        input_path = VideoUtils.find_input_file(segment_info['file'], self.app)
        if not input_path:
            show_custom_messagebox(
                self.frame, "오류", "원본 비디오 파일을 찾을 수 없습니다.", "error")
            return None
        return input_path

    def _setup_output_folder(self, input_path, segment_info):
        """출력 폴더 설정"""
        # 폴더명 생성
        folder_name = VideoUtils.generate_output_folder_name(
            input_path, segment_info['start'], segment_info['end'])

        # 기본 저장 경로
        default_path = VideoUtils.get_default_save_path()

        # 사용자가 폴더 생성 위치 선택
        output_base_folder = filedialog.askdirectory(
            title="이미지 저장할 기본 폴더 선택",
            initialdir=default_path
        )
        if not output_base_folder:
            # 사용자가 취소한 경우 기본 경로 사용
            output_base_folder = default_path

        output_folder = os.path.join(output_base_folder, folder_name)

        # 폴더 존재 확인 및 생성
        if not self._create_output_folder(output_folder, folder_name):
            return None

        return output_folder

    def _create_output_folder(self, output_folder, folder_name):
        """출력 폴더 생성"""
        if os.path.exists(output_folder):
            response = messagebox.askyesno(
                "폴더 존재",
                f"폴더 '{folder_name}'이 이미 존재합니다.\n기존 폴더에 추가하시겠습니까?"
            )
            if not response:
                return False
        else:
            try:
                os.makedirs(output_folder, exist_ok=True)
            except Exception as e:
                show_custom_messagebox(
                    self.frame, "오류", f"폴더 생성 실패: {str(e)}", "error")
                return False
        return True

    def _start_image_extraction(self, input_path, output_folder, segment_info):
        """이미지 추출 시작 프론트 엔드"""

        print(f"이미지 추출 시작: {segment_info['start']}~{segment_info['end']}초")
        print(f"저장 폴더: {output_folder}")

        # 진행률 시작 이벤트 emit (0% 진행률로 시작)
        event_system.emit(
            Events.IMAGE_EXTRACTION_PROGRESS,
            progress=0,
            status="이미지 추출 준비 중...",
            icon="🔄"
        )

        # 스레딩을 사용하여 백그라운드에서 이미지 추출 시작
        threading.Thread(
            target=self.do_image_extraction,
            args=(input_path, output_folder, segment_info),
            daemon=True
        ).start()

    def do_image_extraction(self, input_path, output_folder, segment_info):
        """실제 이미지 추출 작업 (백그라운드) - 공통 유틸리티 사용"""
        try:
            # 공통 유틸리티를 사용하여 프레임 추출
            result = VideoUtils.extract_frames_from_video(
                input_path=input_path,
                output_folder=output_folder,
                start_time=segment_info['start'],
                end_time=segment_info['end'],
                progress_callback=self._image_progress_callback,  # 밑의 콜백 함수 호출
                cancel_event=self.cancel_event
            )

            # 취소 여부 확인
            if self.cancel_event.is_set():
                return  # 취소된 경우 완료 이벤트를 발생시키지 않음
            else:
                # 완료 이벤트 발생
                self._emit_image_extraction_complete(result, output_folder)

        except Exception as e:
            # 에러 이벤트 발생
            if not self.cancel_event.is_set():  # 취소가 아닌 실제 오류인 경우만
                self._emit_image_extraction_error(str(e))

    def _image_progress_callback(self, progress, extracted_count, total_frames):
        """이미지 추출 진행률 콜백"""
        self.frame.after(0, lambda: event_system.emit(
            Events.IMAGE_EXTRACTION_PROGRESS,
            progress=progress,
            status=f"이미지 {extracted_count}/{total_frames} 저장 중...",
            icon="💾"
        ))

    def show_image_extraction_result(self, extracted_count=0, total_extract_frames=0,
                                     output_folder="", fps=0, frame_skip=0,
                                     progress=100, status="", icon="✅", **kwargs):
        """이미지 추출 결과 표시"""
        # 이미지 추출 완료 후 플래그 리셋
        self._is_image_extracting = False

        # 진행률 업데이트
        self.update_progress(progress, status, icon)

        # 결과 다이얼로그 표시
        show_custom_messagebox(
            self.frame,
            "✅ 완료",
            f"이미지 추출 완료!\n"
            f"추출된 이미지: {extracted_count}개\n"
            f"프레임 스킵: {frame_skip} (FPS: {fps:.1f})",
            "success",
            # auto_close_ms=3000  # 3초 후 자동 닫기
        )

        # 5초 후 진행률 바 초기화
        self.frame.after(5000, lambda: self.update_progress(0, "대기 중...", "⚡"))

    def _emit_image_extraction_complete(self, result, output_folder):
        """이미지 추출 완료 이벤트 발생"""
        self.frame.after(0, lambda: event_system.emit(
            Events.IMAGE_EXTRACTION_COMPLETE,
            extracted_count=result['extracted_count'],
            total_extract_frames=result['total_frames'],
            output_folder=output_folder,
            fps=result['fps'],
            frame_skip=result['frame_skip'],
            progress=100,
            status=f"{result['extracted_count']}개 이미지 추출 완료!",
            icon="✅"
        ))

    def _emit_image_extraction_error(self, error_message):
        """이미지 추출 오류 이벤트 발생"""
        self.frame.after(0, lambda: event_system.emit(
            Events.IMAGE_EXTRACTION_ERROR, error=error_message))

    def extract_audio(self):
        """선택된 구간에서 오디오 추출"""
        try:
            # 취소 이벤트 초기화
            self.cancel_event.clear()

            # 1. 선택된 구간 정보 가져오기
            segment_info = self._get_selected_segment_info()
            if not segment_info:
                return

            # 2. 입력 파일 찾기
            input_path = self._find_input_file(segment_info)
            if not input_path:
                return

            # 3. 출력 폴더 설정
            output_folder = self._setup_output_folder(input_path, segment_info)
            if not output_folder:
                return

            # 4. 오디오 추출 시작
            self._start_audio_extraction(
                input_path, output_folder, segment_info)

        except Exception as e:
            show_custom_messagebox(
                self.frame, "오류", f"오디오 추출 준비 중 오류: {str(e)}", "error")

    def _start_audio_extraction(self, input_path, output_folder, segment_info):
        """오디오 추출 시작 프론트 엔드"""

        print(f"오디오 추출 시작: {segment_info['start']}~{segment_info['end']}초")
        print(f"저장 폴더: {output_folder}")

        # 진행률 시작 이벤트 emit (0% 진행률로 시작)
        event_system.emit(
            Events.AUDIO_EXTRACTION_PROGRESS,
            progress=0,
            status="오디오 추출 준비 중...",
            icon="🔄"
        )

        # 스레딩을 사용하여 백그라운드에서 오디오 추출 시작
        threading.Thread(
            target=self.do_audio_extraction,
            args=(input_path, output_folder, segment_info),
            daemon=True
        ).start()

    def do_audio_extraction(self, input_path, output_folder, segment_info):
        """실제 오디오 추출 작업 (백그라운드) - 공통 유틸리티 사용"""
        try:
            # 공통 유틸리티를 사용하여 오디오 추출
            result = VideoUtils.extract_audio_from_video(
                input_path=input_path,
                output_folder=output_folder,
                start_time=segment_info['start'],
                end_time=segment_info['end'],
                progress_callback=self._audio_progress_callback,  # 밑의 콜백 함수 호출
                cancel_event=self.cancel_event
            )

            # 취소 여부 확인
            if self.cancel_event.is_set():
                return  # 취소된 경우 완료 이벤트를 발생시키지 않음
            else:
                # 완료 이벤트 발생
                self._emit_audio_extraction_complete(result, output_folder)

        except Exception as e:
            # 에러 이벤트 발생
            if not self.cancel_event.is_set():  # 취소가 아닌 실제 오류인 경우만
                self._emit_audio_extraction_error(str(e))

    def _audio_progress_callback(self, progress, extracted_count, total_frames):
        """오디오 추출 진행률 콜백"""
        self.frame.after(0, lambda: event_system.emit(
            Events.AUDIO_EXTRACTION_PROGRESS,
            progress=progress,
            status=f"오디오 {extracted_count}/{total_frames} 저장 중...",
            icon="💾"
        ))

    def show_audio_extraction_result(self, extracted_count=0, total_extract_frames=0,
                                     output_folder="", fps=0, frame_skip=0,
                                     progress=100, status="", icon="✅", **kwargs):
        """오디오 추출 결과 표시"""
        # 오디오 추출 완료 후 플래그 리셋
        self._is_audio_extracting = False

        # 진행률 업데이트
        self.update_progress(progress, status, icon)

        # 결과 다이얼로그 표시
        show_custom_messagebox(
            self.frame,
            "✅ 완료",
            f"오디오 추출 완료!\n"
            f"추출된 오디오: {extracted_count}개\n"
            f"프레임 스킵: {frame_skip} (FPS: {fps:.1f})",
            "success",
            # auto_close_ms=3000  # 3초 후 자동 닫기
        )

        # 5초 후 진행률 바 초기화
        self.frame.after(5000, lambda: self.update_progress(0, "대기 중...", "⚡"))

    def _emit_audio_extraction_complete(self, result, output_folder):
        """오디오 추출 완료 이벤트 발생"""
        self.frame.after(0, lambda: event_system.emit(
            Events.AUDIO_EXTRACTION_COMPLETE,
            extracted_count=result['extracted_count'],
            total_extract_frames=result['total_frames'],
            output_folder=output_folder,
            fps=result['fps'],
            frame_skip=result['frame_skip'],
            progress=100,
            status=f"{result['extracted_count']}개 오디오 추출 완료!",
            icon="✅"
        ))

    def _emit_audio_extraction_error(self, error_message):
        """오디오 추출 오류 이벤트 발생"""
        self.frame.after(0, lambda: event_system.emit(
            Events.AUDIO_EXTRACTION_ERROR, error=error_message))

    def show_audio_extraction_error(self, error=None, **kwargs):
        """오디오 추출 오류 표시"""
        # 오디오 추출 오류 후 플래그 리셋
        self._is_audio_extracting = False

        self.update_progress(0, "오류 발생", "⚠️")
        error_message = kwargs.get(
            'error', str(error) if error else "알 수 없는 오류")
        show_custom_messagebox(
            self.frame, "오류", f"오디오 추출 중 오류: {error_message}", "error")
