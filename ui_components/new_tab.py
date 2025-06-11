from .base_tab import BaseTab
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, filedialog
import os
import cv2
from datetime import datetime
from utils.utils import VideoUtils
from .segment_table import SegmentTable
from function.extractor import VideoExtractor, ExtractConfig
import threading


class NewTab(BaseTab):
    def __init__(self, root, app):
        super().__init__(root, app)  # super()로 BaseTab 상속
        self._init_variables()  # NewTab 전용 변수 초기화
        self.create_ui()  # NewTab UI 생성

        # 앱에 NewTab 인스턴스 등록 (PreviewWindow에서 참조할 수 있도록)
        self.app.new_tab_instance = self

    def _init_variables(self):
        """NewTab 전용 변수 초기화"""
        # BaseTab에서 이미 root와 app을 초기화했으므로 여기서는 다시 할당하지 않음
        self.video_path = None
        self.start_time = None
        self.end_time = None

        # 구간 추출 관련변수
        self.current_segment = None
        self.extract_config = ExtractConfig()

        # 취소 이벤트 (백그라운드 작업 중단용)
        self.cancel_event = threading.Event()

        # 성능 최적화 관련 속성
        self.target_fps = 30
        self.frame_skip = 1
        self.frame_count = 0

    def create_ui(self):
        """UI 구성 요소 생성"""
        # 메인 프레임
        self.main_frame = ttk.Frame(self.frame)
        self.main_frame.pack(fill=ttk.BOTH, expand=True, padx=5, pady=5)

        # 상단: 3단 구조 (테이블 | 정보 및 추출 버튼| 저장 설정)
        content_frame = ttk.Frame(self.main_frame)
        content_frame.pack(fill=ttk.BOTH, expand=True, pady=(0, 10))

        # 1) 왼쪽: 구간 테이블 (고정 너비)
        self.table_frame = ttk.Frame(content_frame, width=600)
        self.table_frame.pack(side=ttk.LEFT, fill=ttk.Y, padx=(0, 5))
        self.table_frame.pack_propagate(False)

        # SegmentTable 컴포넌트
        self.segment_table = SegmentTable(self.table_frame, self.app)

        # 2) 중간: 파일 정보 + 프로그레스 바 (고정 너비)
        self.info_frame = ttk.Frame(content_frame, width=400)
        self.info_frame.pack(side=ttk.LEFT, fill=ttk.Y, padx=(0, 5))
        self.info_frame.pack_propagate(False)

        # 3) 오른쪽: 저장 설정 섹션
        self.setting_help_freme = ttk.Frame(content_frame)
        self.setting_help_freme.pack(
            side=ttk.RIGHT, fill=ttk.BOTH, expand=True, padx=(5, 0))

        # 정보 표시 레이블
        info_title = ttk.Label(
            self.info_frame,
            text="📁 파일 정보",
            font=("Arial", 13, "bold")
        )
        info_title.pack(fill=ttk.X, side=ttk.TOP, pady=(15, 5))

        self.file_info_label = ttk.Label(
            self.info_frame,
            text="선택한 구간의 파일 정보가 여기에 표시됩니다.",
            justify=ttk.LEFT,
            anchor="nw",
            wraplength=380,
            font=("Arial", 11)
        )
        self.file_info_label.pack(fill=ttk.BOTH, expand=True, padx=10, pady=10)

        # 파일 정보 하단에 프로그레스 바 추가
        self.create_progress_controls()

        # 파일 정보 영역 하단에 버튼들 추가
        self.create_info_buttons()

        # 설정 섹션 생성
        self.create_settings_sections()

        # 콜백 설정
        self.segment_table.selection_callback = self.on_segment_selected

    def create_progress_controls(self):
        """파일 정보 하단에 프로그레스 바 생성"""
        # 구분선 추가
        separator = ttk.Separator(self.info_frame, orient="horizontal")
        separator.pack(fill=ttk.X, pady=(10, 10))

        # 섹션 타이틀 (main_tab 스타일)
        progress_title = ttk.Label(
            self.info_frame,
            text="⚡ 작업 진행률",
            font=("Arial", 12, "bold")
        )
        progress_title.pack(pady=(5, 2), padx=10, anchor="w")

        # 진행률 바 프레임
        progress_frame = ttk.Frame(self.info_frame)
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

    def create_info_buttons(self):
        """파일 정보 영역 하단 버튼들 생성 - main_tab 스타일 적용"""
        # 구분선 추가
        separator2 = ttk.Separator(self.info_frame, orient="horizontal")
        separator2.pack(fill=ttk.X, pady=(10, 5))

        # 버튼 프레임 - info_frame 내에 배치
        button_frame = ttk.Frame(self.info_frame)
        button_frame.pack(fill=ttk.X, padx=20, pady=(10, 20))

        # 비디오 추출 버튼 (3Pastel 스타일)
        self.video_extract_button = ttk.Button(
            button_frame,
            text="🎬 비디오 추출",
            style='3Pastel.TButton',
            command=self.extract_selected_segment
        )
        self.video_extract_button.pack(
            pady=(5, 3), padx=5, fill=ttk.X, expand=True)

        # 이미지 추출 버튼 (3Pastel 스타일)
        self.image_extract_button = ttk.Button(
            button_frame,
            text="이미지 추출",
            style='3Pastel.TButton',
            command=self.extract_images
        )
        self.image_extract_button.pack(pady=3, padx=5, fill=ttk.X, expand=True)

        # 취소 버튼 (3Pastel 스타일)
        self.cancel_button = ttk.Button(
            button_frame,
            text="❌ 작업 취소",
            style='3Pastel.TButton',
            command=self.cancel_extraction
        )
        self.cancel_button.pack(pady=(3, 5), padx=5, fill=ttk.X, expand=True)

    def file_info_update(self, file_path=None, start_time=None, end_time=None):
        """비디오 파일 정보와 선택된 구간 정보를 업데이트하는 메서드"""
        if not file_path:
            self.file_info_label.config(text="파일정보를 얻을 구간이 선택되지 않았습니다.")
            return

        try:
            # 비디오 속성 가져오기
            cap = cv2.VideoCapture(file_path)
            if not cap.isOpened():
                self.file_info_label.config(
                    text="원본 비디오 파일을 열 수 없어 정보를 불러올 수 없습니다.")
                return

            props = VideoUtils.get_video_properties(cap)
            if not props:
                self.file_info_label.config(text="비디오 속성을 가져오는 중 오류 발생")
                return

            # 파일 기본 정보
            file_stats = os.stat(file_path)
            file_size = file_stats.st_size
            created_time = file_stats.st_ctime
            modified_time = file_stats.st_mtime

            # 파일 크기를 읽기 쉬운 형식으로 변환
            def format_size(size):
                for unit in ['B', 'KB', 'MB', 'GB']:
                    if size < 1024:
                        return f"{size:.1f} {unit}"
                    size /= 1024
                return f"{size:.1f} TB"

            # 구간 정보 포맷팅
            segment_info = ""
            if start_time is not None and end_time is not None:
                segment_duration = end_time - start_time
                segment_info = f"""

✂️ 선택된 구간:
시작 시간: {VideoUtils.format_time(start_time)}
종료 시간: {VideoUtils.format_time(end_time)}
구간 길이: {VideoUtils.format_time(segment_duration)}"""

            info_text = f"""📁 파일 정보:
파일명: {os.path.basename(file_path)}
경로: {file_path}
크기: {format_size(file_size)}
생성일: {datetime.fromtimestamp(created_time).strftime('%Y-%m-%d %H:%M:%S')}
수정일: {datetime.fromtimestamp(modified_time).strftime('%Y-%m-%d %H:%M:%S')}

🎬 비디오 속성:
해상도: {props['width']} x {props['height']}
프레임 레이트: {props['fps']:.2f} fps
전체 길이: {VideoUtils.format_time(props['length'])}
전체 프레임 수: {props['frame_count']:,} 프레임{segment_info}"""

            self.file_info_label.config(text=info_text)
            cap.release()

        except Exception as e:
            self.file_info_label.config(text=f"파일 정보를 불러오는 중 오류 발생: {str(e)}")

    def on_segment_selected(self, segment_info):
        """SegmentTable에서 구간 행이 선택되었을때 호출되는 콜백 메서드"""
        print(f"선택된 구간: {segment_info}")

        # 선택된 구간의 파일 경로 처리
        file_path = segment_info['file']

        # 파일명만 있는 경우 전체 경로로 반환
        if hasattr(self.app, 'video_path') and self.app.video_path:
            if hasattr(self.app.video_path, 'get'):
                full_path = self.app.video_path.get()
            else:
                full_path = self.app.video_path

            # 파일명이 일치하면, 전체경로 사용
            if os.path.basename(full_path) == file_path:
                file_path = full_path

        # 선택한 구간 정보로 파일 정보 업데이트
        self.file_info_update(
            file_path=file_path,
            start_time=segment_info['start'],
            end_time=segment_info['end']
        )

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

                # 파일 경로가 파일명만 있는 경우 전체 경로로 변환
                file_path = latest_segment['file']
                if hasattr(self.app, 'video_path') and self.app.video_path:
                    # video_path가 StringVar인 경우 처리
                    if hasattr(self.app.video_path, 'get'):
                        full_path = self.app.video_path.get()
                    else:
                        full_path = self.app.video_path

                    # 파일명이 일치하면 전체 경로 사용
                    if os.path.basename(full_path) == file_path:
                        file_path = full_path

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

    def create_settings_sections(self):
        """저장 설정 섹션 생성"""

        # 메인 타이틀
        main_title = ttk.Label(self.setting_help_freme,
                               text="저장 설정",
                               font=("Arial", 13, "bold")
                               )
        main_title.pack(fill=ttk.X, padx=10, pady=(10, 5), anchor="w")

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
                                 text="예시: 홍길동_구간데이터_5개_20250606.csv",
                                 font=("Arial", 9),
                                 foreground="gray"
                                 )
        example_text.pack(fill=ttk.X, pady=(10, 5), anchor="w")

        # 구분선
        separator1 = ttk.Separator(
            self.setting_help_freme, orient="horizontal")
        separator1.pack(fill=ttk.X, pady=(10, 5))

    def extract_selected_segment(self):
        """선택된 구간 추출"""
        try:
            # 취소 이벤트 초기화 (새 작업 시작)
            self.cancel_event.clear()

            # 1. 선택 확인
            selected_items = self.segment_table.table.selection()
            if not selected_items:
                messagebox.showwarning("경고", "추출할 구간을 선택해주세요.")
                return

            # 2. 구간 정보 가져오기
            index = self.segment_table.table.index(selected_items[0])
            if index >= len(self.app.saved_segments):
                messagebox.showerror("오류", "구간 정보를 찾을 수 없습니다.")
                return

            segment_info = self.app.saved_segments[index]

            # 3. 입력 파일 찾기
            filename = segment_info['file']
            input_path = None

            if os.path.isabs(filename) and os.path.exists(filename):
                input_path = filename
            elif hasattr(self.app, 'video_path') and self.app.video_path:
                full_path = self.app.video_path.get() if hasattr(
                    self.app.video_path, 'get') else self.app.video_path
                if full_path and os.path.basename(full_path) == filename and os.path.exists(full_path):
                    input_path = full_path

            if not input_path:
                messagebox.showerror("오류", "원본 비디오 파일을 찾을 수 없습니다.")
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
                target=self._do_extraction,
                args=(input_path, output_path, segment_info),
                daemon=True
            ).start()

        except Exception as e:
            messagebox.showerror("오류", f"추출 준비 중 오류: {str(e)}")

    def update_progress(self, value, status="", icon="⚡"):
        """진행률 업데이트 (main_tab 스타일)"""
        self.progress_bar['value'] = value
        self.progress_percentage.config(text=f"{int(value)}%")

        # 상태 메시지 업데이트
        if status:
            self.progress_status.config(text=f"ⓘ {status}")
        elif value == 0:
            self.progress_status.config(text="ⓘ 작업 대기 중입니다.")
        elif value < 100:
            self.progress_status.config(text=f"ⓘ 작업 진행 중... ({int(value)}%)")
        else:
            self.progress_status.config(text="ⓘ 작업이 완료되었습니다!")

    def _do_extraction(self, input_path, output_path, segment_info):
        """실제 추출 작업 (백그라운드)"""
        try:
            # 취소 이벤트 초기화
            self.cancel_event.clear()

            # 취소 확인
            if self.cancel_event.is_set():
                self.root.after(
                    0, lambda: self.update_progress(0, "취소됨", "취소"))
                return

            # 진행률 콜백 (개선된 버전)
            def update_progress_callback(msg):
                if self.cancel_event.is_set():
                    return  # 취소된 경우 진행률 업데이트 중단
                self.root.after(
                    0, lambda: self.update_progress(50, f"🔄 {msg}", "⚙️"))

            # 시작 상태
            self.root.after(
                0, lambda: self.update_progress(0, "추출 시작...", "시작..."))

            # 취소 확인
            if self.cancel_event.is_set():
                self.root.after(
                    0, lambda: self.update_progress(0, "취소됨", "취소"))
                return

            # VideoExtractor로 추출
            result = VideoExtractor.extract_segment(
                input_video_path=input_path,
                output_video_path=output_path,
                start_time=segment_info['start'],
                end_time=segment_info['end'],
                progress_callback=update_progress_callback,
                ffmpeg_codec_copy=self.extract_config.use_codec_copy
            )

            # 취소 확인
            if self.cancel_event.is_set():
                self.root.after(
                    0, lambda: self.update_progress(0, "취소됨", "취소"))
                return

            # 결과 표시
            def show_result():
                if result['success']:
                    self.update_progress(100, "추출 완료!", "✅")
                    messagebox.showinfo(
                        "✅ 완료", f"추출 성공!\n저장 위치: {result['output_path']}")
                else:
                    self.update_progress(0, " 추출 실패", "❌")
                    messagebox.showerror("실패", f"추출 실패: {result['message']}")

                # 5초 후 진행률 바 초기화
                self.root.after(
                    5000, lambda: self.update_progress(0, "대기 중...", "⚡"))

            self.root.after(0, show_result)

        except Exception as e:
            def show_error():
                self.update_progress(0, "오류 발생", "⚠️")
                messagebox.showerror("오류", f"추출 중 오류: {str(e)}")

            self.root.after(0, show_error)

    def cancel_extraction(self):
        """추출 취소"""
        self.cancel_event.set()  # 취소 신호 전송
        self.update_progress(0, "취소됨", "취소")
        print("❌ 추출 취소 신호 전송됨")

    def extract_images(self):
        """선택된 구간에서 이미지 추출 (FPS 기반 스킵)"""
        try:
            # 취소 이벤트 초기화 (새 작업 시작)
            self.cancel_event.clear()

            # 1. 선택 확인
            selected_items = self.segment_table.table.selection()
            if not selected_items:
                messagebox.showwarning("경고", "이미지를 추출할 구간을 선택해주세요.")
                return

            # 2. 구간 정보 가져오기
            index = self.segment_table.table.index(selected_items[0])
            if index >= len(self.app.saved_segments):
                messagebox.showerror("오류", "구간 정보를 찾을 수 없습니다.")
                return

            segment_info = self.app.saved_segments[index]

            # 3. 입력 파일 찾기
            filename = segment_info['file']
            input_path = None

            if os.path.isabs(filename) and os.path.exists(filename):
                input_path = filename
            elif hasattr(self.app, 'video_path') and self.app.video_path:
                full_path = self.app.video_path.get() if hasattr(
                    self.app.video_path, 'get') else self.app.video_path
                if full_path and os.path.basename(full_path) == filename and os.path.exists(full_path):
                    input_path = full_path

            if not input_path:
                messagebox.showerror("오류", "원본 비디오 파일을 찾을 수 없습니다.")
                return

            # 4. 출력 폴더 선택
            output_folder = filedialog.askdirectory(
                title="선택 구간의 추출된 이미지 저장할 폴더 선택"
            )
            if not output_folder:
                return

            # 5. 이미지 추출 시작
            print(
                f"이미지 추출 시작: {segment_info['start']}~{segment_info['end']}초")
            self.update_progress(0, "이미지 추출 중...", "..in progress")

            threading.Thread(
                target=self._do_image_extraction,
                args=(input_path, output_folder, segment_info),
                daemon=True
            ).start()

        except Exception as e:
            messagebox.showerror("오류", f"이미지 추출 준비 중 오류: {str(e)}")

    def _do_image_extraction(self, input_path, output_folder, segment_info):
        """실제 이미지 추출 작업 (백그라운드)"""
        try:
            import cv2
            from datetime import datetime

            # 취소 이벤트 초기화
            self.cancel_event.clear()

            # 취소 확인
            if self.cancel_event.is_set():
                self.root.after(
                    0, lambda: self.update_progress(0, "취소됨", "추출 취소"))
                return

            # 비디오 캡처 초기화
            cap = cv2.VideoCapture(input_path)
            if not cap.isOpened():
                raise Exception("비디오 파일을 열 수 없습니다.")

            # 비디오 정보 가져오기
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            # FPS에 따른 프레임 스킵 계산
            frame_skip = 2 if fps >= 30 else 1  # 30fps 이상이면 매 2번째 프레임만
            print(f"비디오 FPS: {fps:.2f}, 프레임 스킵: {frame_skip}")

            # 시작/끝 프레임 계산
            start_frame = int(segment_info['start'] * fps)
            end_frame = int(segment_info['end'] * fps)

            # 추출할 프레임 목록 생성 (스킵 적용)
            frames_to_extract = list(range(start_frame, end_frame, frame_skip))
            total_extract_frames = len(frames_to_extract)

            print(f"추출할 프레임: {total_extract_frames}개 (스킵: {frame_skip})")

            # 파일명 prefix 생성
            base_filename = os.path.splitext(os.path.basename(input_path))[0]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            extracted_count = 0

            for i, frame_num in enumerate(frames_to_extract):
                # 취소 확인 (매 프레임마다)
                if self.cancel_event.is_set():
                    cap.release()
                    self.root.after(
                        0, lambda: self.update_progress(0, "이미지 추출 취소됨", "추출 취소"))
                    return

                # 프레임 위치로 이동
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = cap.read()

                if not ret:
                    print(f"⚠️ 프레임 {frame_num} 읽기 실패")
                    continue

                # 시간 계산 (초)
                time_sec = frame_num / fps
                time_str = f"{int(time_sec//60):02d}m{int(time_sec%60):02d}s"

                # 파일명 생성
                image_filename = f"{base_filename}_{timestamp}_frame{frame_num:06d}_{time_str}.jpg"
                image_path = os.path.join(output_folder, image_filename)

                # 이미지 저장
                cv2.imwrite(image_path, frame)
                extracted_count += 1

                # 진행률 업데이트
                progress = (i + 1) / total_extract_frames * 100
                self.root.after(0, lambda p=progress: self.update_progress(
                    p, f"이미지 {extracted_count}/{total_extract_frames} 저장 중...", "saving..."))

            cap.release()

            # 취소 확인 (완료 직전)
            if self.cancel_event.is_set():
                self.root.after(
                    0, lambda: self.update_progress(0, "이미지 추출 취소됨", "추출 취소"))
                return

            # 완료 메시지
            def show_result():
                self.update_progress(
                    100, f"{extracted_count}개 이미지 추출 완료!", "✅")
                messagebox.showinfo(
                    "✅ 완료",
                    f"이미지 추출 완료!\n"
                    f"추출된 이미지: {extracted_count}개\n"
                    f"저장 위치: {output_folder}\n"
                    f"프레임 스킵: {frame_skip} (FPS: {fps:.1f})"
                )

                # 5초 후 진행률 바 초기화
                self.root.after(
                    5000, lambda: self.update_progress(0, "대기 중...", "⚡"))

            self.root.after(0, show_result)

        except Exception as e:
            def show_error():
                self.update_progress(0, "💥 이미지 추출 실패", "💥")
                messagebox.showerror("오류", f"이미지 추출 중 오류: {str(e)}")

            self.root.after(0, show_error)
