from .base_tab import BaseTab
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import cv2
import os
from PIL import Image, ImageTk
from datetime import datetime
from utils.utils import VideoUtils
from ui_components.segment_table import SegmentTable

# command = [
#     'ffmpeg',
#     '-i', input_video_path,
#     '-ss', str(start_time),
#     '-to', str(end_time),
#     '-c', 'copy',  # 코덱 복사
#     output_video_path
# ]


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

        # 성능 최적화 관련 속성
        self.target_fps = 30
        self.frame_skip = 1
        self.frame_count = 0

        # create_ui() 호출 및 생성은 __init__에서 처리

    def create_ui(self):
        """UI 구성 요소 생성"""
        # 메인 프레임
        self.main_frame = tk.Frame(self.frame)  # self.root 대신 self.frame 사용
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 왼쪽 프레임 (구간 정보 테이블)
        self.left_frame = tk.Frame(self.main_frame, width=500)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))
        self.left_frame.pack_propagate(False)

        # SegmentTable 컴포넌트 사용
        self.segment_table = SegmentTable(self.left_frame, self.app)

        # 오른쪽 프레임 (비디오 컨트롤)
        self.right_frame = tk.Frame(self.main_frame)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 비디오 정보 프레임 및 레이블 생성
        self.video_info_frame = tk.Frame(self.right_frame)
        self.video_info_frame.pack(expand=True, fill="both", padx=5, pady=5)

        self.file_info_label = tk.Label(
            self.video_info_frame,
            text="선택구간의 원본 파일 정보입니다.",
            justify=tk.LEFT,
            anchor="w",
            wraplength=400
        )
        self.file_info_label.pack(expand=True, fill="both")

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

선택된 구간:
시작 시간: {VideoUtils.format_time(start_time)}
종료 시간: {VideoUtils.format_time(end_time)}
구간 길이: {VideoUtils.format_time(segment_duration)}"""

            info_text = f"""파일 정보:
파일명: {os.path.basename(file_path)}
경로: {file_path}
크기: {format_size(file_size)}
생성일: {datetime.fromtimestamp(created_time).strftime('%Y-%m-%d %H:%M:%S')}
수정일: {datetime.fromtimestamp(modified_time).strftime('%Y-%m-%d %H:%M:%S')}

비디오 속성:
해상도: {props['width']} x {props['height']}
프레임 레이트: {props['fps']:.2f} fps
전체 길이: {VideoUtils.format_time(props['length'])}
전체 프레임 수: {props['frame_count']:,} 프레임{segment_info}"""

            self.file_info_label.config(text=info_text)
            cap.release()

        except Exception as e:
            self.file_info_label.config(text=f"파일 정보를 불러오는 중 오류 발생: {str(e)}")

    def refresh_table(self):
        """테이블 새로고침 메서드"""
        print("NewTab: refresh_table 호출됨")

        if hasattr(self, 'segment_table'):
            print("비디오 추출 탭: 테이블 새로고침 중 ...")
            self.segment_table.refresh()
            print("비디오 추출 탭: 테이블 새로고침 완료.")

            # 가장 최근 정보로 구간정보 업데이트
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
        else:
            print("비디오 추출 탭: 선택 구간 테이블이 존재하지 않음")
