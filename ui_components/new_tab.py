from .base_tab import BaseTab
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import cv2
from datetime import datetime
from utils.utils import VideoUtils
from ui_components.segment_table import SegmentTable
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

        # 성능 최적화 관련 속성
        self.target_fps = 30
        self.frame_skip = 1
        self.frame_count = 0

    def create_ui(self):
        """UI 구성 요소 생성"""
        # 메인 프레임
        self.main_frame = tk.Frame(self.frame)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 상단: 3단 구조 (테이블 | 정보 | 이미지)
        content_frame = tk.Frame(self.main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 1) 왼쪽: 구간 테이블 (고정 너비)
        self.table_frame = tk.Frame(
            content_frame, width=600, relief="solid", bd=1)
        self.table_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        self.table_frame.pack_propagate(False)

        # SegmentTable 컴포넌트
        self.segment_table = SegmentTable(self.table_frame, self.app)

        # 2) 중간: 파일 정보 (고정 너비)
        self.info_frame = tk.Frame(
            content_frame, width=400, relief="sunken", bd=1, bg="white")
        self.info_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        self.info_frame.pack_propagate(False)

        # 정보 표시 레이블
        info_title = tk.Label(
            self.info_frame,
            text="📁 파일 정보",
            bg="lightblue",
            font=("Arial", 11, "bold"),
            pady=5
        )
        info_title.pack(fill=tk.X, side=tk.TOP)

        self.file_info_label = tk.Label(
            self.info_frame,
            text="선택한 구간의 파일 정보가 여기에 표시됩니다.",
            justify=tk.LEFT,
            anchor="nw",
            wraplength=380,
            bg="white",
            font=("Arial", 9)
        )
        self.file_info_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 3) 오른쪽: 이미지 미리보기 영역 (확장 가능)
        self.preview_frame = tk.Frame(
            content_frame, relief="sunken", bd=1, bg="lightgray")
        self.preview_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 미리보기 제목
        preview_title = tk.Label(
            self.preview_frame,
            text="이미지 미리보기",
            bg="lightgreen",
            font=("Arial", 11, "bold"),
            pady=5
        )
        preview_title.pack(fill=tk.X, side=tk.TOP)

        # 미리보기 영역 (나중에 이미지 표시용)
        self.image_preview_label = tk.Label(
            self.preview_frame,
            text="구간을 선택 후\n이미지 추출 시\n추출된 이미지가\n여기에 표시됩니다.",
            bg="lightgray",
            font=("Arial", 10),
            justify=tk.CENTER
        )
        self.image_preview_label.pack(
            fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 하단: 버튼 + 진행률 바
        self.create_bottom_controls()

        # 콜백 설정
        self.segment_table.selection_callback = self.on_segment_selected

    def create_bottom_controls(self):
        """하단 컨트롤 영역 생성"""
        # 하단 프레임 (높이를 더 크게)
        bottom_frame = tk.Frame(
            self.main_frame, relief="raised", bd=2, bg="#f0f0f0", height=100)
        bottom_frame.pack(fill=tk.X, pady=8)
        bottom_frame.pack_propagate(False)  # 크기 고정

        # 왼쪽: 진행률 바 영역 (패딩 증가)
        progress_frame = tk.Frame(bottom_frame, bg="#f0f0f0")
        progress_frame.pack(side=tk.LEFT, padx=20, pady=20)

        # 진행률 바 제목과 아이콘
        progress_title_frame = tk.Frame(progress_frame, bg="#f0f0f0")
        progress_title_frame.pack(fill=tk.X, pady=(0, 8))

        self.progress_icon = tk.Label(
            progress_title_frame,
            text="⚡",  # 번개 아이콘
            bg="#f0f0f0",
            font=("Arial", 14),  # 아이콘 크기 증가
            fg="#FF6B35"
        )
        self.progress_icon.pack(side=tk.LEFT, padx=(0, 8))

        tk.Label(
            progress_title_frame,
            text="작업 진행률",
            bg="#f0f0f0",
            font=("Arial", 11, "bold"),  # 폰트 크기 증가
            fg="#333333"
        ).pack(side=tk.LEFT)

        # 진행률 바와 퍼센티지를 담을 프레임
        progress_bar_frame = tk.Frame(progress_frame, bg="#f0f0f0")
        progress_bar_frame.pack(fill=tk.X, pady=(0, 5))

        # 진행률 바 (더 길고 두껍게)
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            "Custom.Horizontal.TProgressbar",
            troughcolor='#E0E0E0',
            background='#4CAF50',
            lightcolor='#4CAF50',
            darkcolor='#4CAF50',
            borderwidth=1,
            relief='solid',
            pbarrelief='flat',
            thickness=30  # 두께 설정
        )

        self.progress_bar = ttk.Progressbar(
            progress_bar_frame,
            orient="horizontal",
            length=500,
            mode="determinate",
            style="Custom.Horizontal.TProgressbar"
        )
        self.progress_bar.pack(side=tk.LEFT, padx=(
            0, 12), pady=5)  # pady 추가로 시각적 여백

        # 퍼센티지 표시
        self.progress_percentage = tk.Label(
            progress_bar_frame,
            text="0%",
            bg="#f0f0f0",
            font=("Arial", 11, "bold"),  # 폰트 크기 증가
            fg="#333333",
            width=5
        )
        self.progress_percentage.pack(side=tk.LEFT)

        # 상태 메시지 표시
        self.progress_status = tk.Label(
            progress_frame,
            text="대기 중...",
            bg="#f0f0f0",
            font=("Arial", 9),
            fg="#666666"
        )
        self.progress_status.pack(fill=tk.X, pady=(5, 0))

        # 오른쪽: 버튼들 (패딩 증가)
        button_frame = tk.Frame(bottom_frame, bg="#f0f0f0")
        button_frame.pack(side=tk.RIGHT, padx=20, pady=20)

        # 버튼 스타일 설정
        button_style = ttk.Style()
        button_style.configure(
            "Modern.TButton",
            relief="flat",
            borderwidth=1,
            focuscolor="none",
            padding=(10, 8)
        )

        # 비활성화된 버튼 스타일
        button_style.configure(
            "Disabled.TButton",
            relief="flat",
            borderwidth=0,
            focuscolor="none",
            padding=(10, 8)
        )

        # 이미지 추출 버튼 (미래 기능)
        ttk.Button(
            button_frame,
            text="이미지 추출",
            command=self.extract_images,
            width=16,
            style="Disabled.TButton",
            state="disabled"
        ).pack(side=tk.RIGHT, padx=6, pady=4)

        # 비디오 추출 버튼
        ttk.Button(
            button_frame,
            text="🎬 비디오 추출",
            command=self.extract_selected_segment,
            width=16,
            style="Modern.TButton"
        ).pack(side=tk.RIGHT, padx=6, pady=4)

        # 취소 버튼
        ttk.Button(
            button_frame,
            text="❌ 취소",
            command=self.cancel_extraction,
            width=12,
            style="Modern.TButton"
        ).pack(side=tk.RIGHT, padx=6, pady=4)

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

    def extract_selected_segment(self):
        """선택된 구간 추출"""
        try:
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
            print(f"🎬 추출 시작: {segment_info['start']}~{segment_info['end']}초")
            self.progress_bar['value'] = 0

            threading.Thread(
                target=self._do_extraction,
                args=(input_path, output_path, segment_info),
                daemon=True
            ).start()

        except Exception as e:
            messagebox.showerror("오류", f"추출 준비 중 오류: {str(e)}")

    def update_progress(self, value, status="", icon="⚡"):
        """진행률 업데이트 (개선된 버전)"""
        self.progress_bar['value'] = value
        self.progress_percentage.config(text=f"{int(value)}%")

        if status:
            self.progress_status.config(text=status)

        # 아이콘 변경
        if icon:
            self.progress_icon.config(text=icon)

        # 진행률에 따른 색상 변경
        if value == 0:
            self.progress_icon.config(fg="#999999")
            self.progress_status.config(text="대기 중...")
        elif value < 50:
            self.progress_icon.config(fg="#FF6B35")
        elif value < 100:
            self.progress_icon.config(fg="#FFA500")
        else:
            self.progress_icon.config(fg="#4CAF50")
            self.progress_status.config(text="✅ 완료!")

    def _do_extraction(self, input_path, output_path, segment_info):
        """실제 추출 작업 (백그라운드)"""
        try:
            # 진행률 콜백 (개선된 버전)
            def update_progress_callback(msg):
                self.root.after(
                    0, lambda: self.update_progress(50, f"🔄 {msg}", "⚙️"))

            # 시작 상태
            self.root.after(
                0, lambda: self.update_progress(0, "🚀 추출 시작...", "🚀"))

            # VideoExtractor로 추출
            result = VideoExtractor.extract_segment(
                input_video_path=input_path,
                output_video_path=output_path,
                start_time=segment_info['start'],
                end_time=segment_info['end'],
                progress_callback=update_progress_callback,
                ffmpeg_codec_copy=self.extract_config.use_codec_copy
            )

            # 결과 표시
            def show_result():
                if result['success']:
                    self.update_progress(100, "✅ 추출 완료!", "🎉")
                    messagebox.showinfo(
                        "✅ 완료", f"추출 성공!\n저장 위치: {result['output_path']}")
                else:
                    self.update_progress(0, "❌ 추출 실패", "💥")
                    messagebox.showerror("❌ 실패", f"추출 실패: {result['message']}")

                # 5초 후 진행률 바 초기화
                self.root.after(
                    5000, lambda: self.update_progress(0, "대기 중...", "⚡"))

            self.root.after(0, show_result)

        except Exception as e:
            def show_error():
                self.update_progress(0, "💥 오류 발생", "💥")
                messagebox.showerror("오류", f"추출 중 오류: {str(e)}")

            self.root.after(0, show_error)

    def cancel_extraction(self):
        """추출 취소"""
        self.update_progress(0, "🛑 취소됨", "🛑")
        print("❌ 추출 취소됨")

    def extract_images(self):
        """이미지 추출 (미래 구현 예정)"""
        messagebox.showinfo("알림", "이미지 추출 기능은 곧 구현될 예정입니다! 🚧")
        # TODO: 나중에 구현
        # 1. 선택된 구간에서 프레임들 추출
        # 2. 이미지 파일로 저장
        # 3. 미리보기 영역에 표시
