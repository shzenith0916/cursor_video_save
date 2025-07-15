import os
import cv2
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from datetime import datetime
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from .ui_utils import UiUtils
import pygame
import threading
import time


def show_custom_messagebox(parent, title, message, msg_type="info", auto_close_ms=None):
    """커스텀 Toplevel 메시지 박스 생성"""
    dialog = tk.Toplevel(parent)
    dialog.title(title)

    # DPI 스케일링 적용 및 중앙 정렬
    width = int(380 * UiUtils.get_scaling_factor_by_dpi(parent))
    height = int(160 * UiUtils.get_scaling_factor_by_dpi(parent))
    UiUtils.center_window(dialog, parent, width, height)

    dialog.resizable(False, False)
    dialog.transient(parent)
    dialog.grab_set()

    # 아이콘과 색상 설정
    icon_configs = {
        "info": {"icon": "ℹ️", "color": "#0d6efd"},
        "success": {"icon": "✅", "color": "#198754"},
        "warning": {"icon": "⚠️", "color": "#fd7e14"},
        "error": {"icon": "❌", "color": "#dc3545"}
    }
    icon_config = icon_configs.get(msg_type, icon_configs["info"])

    main_frame = ttk.Frame(dialog)
    main_frame.pack(fill=BOTH, expand=True, padx=20, pady=15)

    content_frame = ttk.Frame(main_frame)
    content_frame.pack(fill=BOTH, expand=True, pady=(0, 15))

    icon_label = ttk.Label(
        content_frame, text=icon_config["icon"], font=("Arial", 24),
        foreground=icon_config["color"]
    )
    icon_label.pack(side=LEFT, padx=(0, 15), anchor='n')

    message_label = ttk.Label(
        content_frame, text=message, font=("Arial", 11),
        wraplength=width - 120, justify=LEFT
    )
    message_label.pack(side=LEFT, fill=BOTH, expand=True)

    # 확인 버튼 (자동 닫기가 아닐 경우에만 표시)
    if not auto_close_ms:
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=X)
        ok_button = ttk.Button(
            button_frame, text="확인", style="Accent.TButton",
            command=dialog.destroy, width=10
        )
        ok_button.pack(side=RIGHT)
        dialog.bind('<Return>', lambda e: dialog.destroy())
        dialog.bind('<Escape>', lambda e: dialog.destroy())
        ok_button.focus_set()

    # 자동 닫기 설정
    if auto_close_ms:
        dialog.after(auto_close_ms, dialog.destroy)

    dialog.wait_window()


class AudioPlayer:
    """비디오 재생 시 오디오 동기화를 위한 클래스"""

    def __init__(self):
        self.is_initialized = False
        self.is_playing = False
        self.current_position = 0
        self.audio_length = 0
        self.temp_audio_file = None
        self._init_pygame()

    def _init_pygame(self):
        """Pygame 초기화"""
        try:
            pygame.mixer.pre_init(frequency=22050, size=-
                                  16, channels=2, buffer=512)
            pygame.mixer.init()
            self.is_initialized = True
        except Exception as e:
            print(f"오디오 초기화 실패: {e}")
            self.is_initialized = False

    def load_audio_from_video(self, video_path, start_time=0, end_time=None):
        """비디오에서 오디오 추출 및 로드"""
        if not self.is_initialized:
            return False

        try:
            import tempfile
            from extract.extractor import VideoExtractor

            # 임시 오디오 파일 생성
            temp_dir = tempfile.gettempdir()
            temp_filename = f"temp_audio_{int(time.time())}.wav"
            self.temp_audio_file = os.path.join(temp_dir, temp_filename)

            # 비디오에서 오디오 추출
            if end_time is None:
                # 전체 비디오 길이 가져오기
                cap = cv2.VideoCapture(video_path)
                fps = cap.get(cv2.CAP_PROP_FPS)
                frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                end_time = frame_count / fps
                cap.release()

            result = VideoExtractor.extract_audio_segment(
                input_video_path=video_path,
                output_audio_path=self.temp_audio_file,
                start_time=start_time,
                end_time=end_time,
                audio_format='wav'
            )

            if result['success']:
                # 오디오 파일 로드
                pygame.mixer.music.load(self.temp_audio_file)
                self.audio_length = end_time - start_time
                return True
            else:
                print(f"오디오 추출 실패: {result['message']}")
                return False

        except Exception as e:
            print(f"오디오 로드 실패: {e}")
            return False

    def play(self):
        """오디오 재생"""
        if not self.is_initialized:
            return False

        try:
            pygame.mixer.music.play()
            self.is_playing = True
            return True
        except Exception as e:
            print(f"오디오 재생 실패: {e}")
            return False

    def pause(self):
        """오디오 일시정지"""
        if not self.is_initialized:
            return

        try:
            pygame.mixer.music.pause()
            self.is_playing = False
        except Exception as e:
            print(f"오디오 일시정지 실패: {e}")

    def unpause(self):
        """오디오 재생 재개"""
        if not self.is_initialized:
            return

        try:
            pygame.mixer.music.unpause()
            self.is_playing = True
        except Exception as e:
            print(f"오디오 재개 실패: {e}")

    def stop(self):
        """오디오 정지"""
        if not self.is_initialized:
            return

        try:
            pygame.mixer.music.stop()
            self.is_playing = False
            self.current_position = 0
        except Exception as e:
            print(f"오디오 정지 실패: {e}")

    def set_position(self, position):
        """오디오 위치 설정 (초 단위)"""
        # pygame.mixer.music는 위치 설정을 직접 지원하지 않음
        # 필요시 다른 라이브러리 사용 고려
        self.current_position = position

    def get_position(self):
        """현재 오디오 위치 반환"""
        return self.current_position

    def is_audio_playing(self):
        """오디오 재생 상태 확인"""
        if not self.is_initialized:
            return False
        return pygame.mixer.music.get_busy() and self.is_playing

    def cleanup(self):
        """리소스 정리"""
        try:
            if self.is_initialized:
                pygame.mixer.music.stop()
                pygame.mixer.quit()

            # 임시 파일 삭제
            if self.temp_audio_file and os.path.exists(self.temp_audio_file):
                os.remove(self.temp_audio_file)

        except Exception as e:
            print(f"오디오 정리 실패: {e}")


class VideoUtils:
    """비디오 처리 관련 공통 기능을 제공하는 클래스"""
    @staticmethod
    def format_time(seconds):
        '''초를 mm:ss 형식으로 변환하는 함수 '''

        seconds = int(float(seconds))  # float에서 int로 변환
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60

        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    @staticmethod
    def convert_frame_to_photo(frame):
        """OpenCV 프레임을 Tkinter PhotoImage로 변환.
           비디오 프레임에서 이 이미지를 이용하여 재생"""

        try:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)
            return ImageTk.PhotoImage(image=pil_image)
        except Exception as e:
            print(f"Frame conversion error: {e}")
            return None

    @staticmethod
    def convert_frame_to_photo_optimized(frame, target_width=None, target_height=None):
        """최적화된 OpenCV 프레임을 Tkinter PhotoImage로 변환"""
        try:
            # BGR -> RGB 변환
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(frame_rgb)

            # PIL 이미지 생성
            # 📌 타겟 크기가 지정된 경우 리사이즈
            if target_width and target_height:
                # 비율 유지하면서 리사이즈
                pil_img.thumbnail((target_width, target_height),
                                  Image.Resampling.LANCZOS)

            return ImageTk.PhotoImage(pil_img)

        except Exception as e:
            print(f"Frame Conversion Error: {e}")
            return None

    @staticmethod
    def get_video_properties(cap):
        """비디오 속성 가져오기"""
        if not cap or not cap.isOpened():
            return None

        properties = {
            'fps': cap.get(cv2.CAP_PROP_FPS),
            'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        }

        # 비디오 길이(초) 계산
        properties['length'] = properties['frame_count'] / \
            properties['fps'] if properties['fps'] > 0 else 0

        return properties

    @staticmethod
    def calculate_frame_number(time_seconds, fps):
        """시간(초)을 프레임 번호로 변환"""
        return int(float(time_seconds) * fps)

    @staticmethod
    def create_video_label(parent_frame):
        """비디오 레이블 생성"""
        if parent_frame:
            video_label = tk.Label(parent_frame)
            video_label.pack(expand=True, fill="both")
            return video_label
        return None

    @staticmethod
    def read_frame_at_position(cap, position, fps=None, is_frame_number=False):
        """지정된 위치에서 프레임 읽기

        Args:
            cap: OpenCV VideoCapture 객체
            position: 위치 (시간(초) 또는 프레임 번호)
            fps: 프레임 레이트 (시간 기준일 경우 필요)
            is_frame_number: position이 프레임 번호인지 여부

        Returns:
            ret, frame: 읽기 성공 여부와 프레임
        """
        if not cap or not cap.isOpened():
            return False, None

        if not is_frame_number and fps:
            # 시간(초)을 프레임 번호로 변환
            frame_number = VideoUtils.calculate_frame_number(position, fps)
        else:
            frame_number = position

        # 프레임 위치 설정
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

        # 프레임 읽기
        return cap.read()

    @staticmethod
    def calculate_optimal_fps(original_fps, max_fps=30):
        """최적 fps 계산"""
        return min(original_fps, max_fps)

    @staticmethod
    def calculate_frame_skip(original_fps, target_fps):
        """프레임 스킵 계산하기"""
        if target_fps >= original_fps:
            return 1
        return max(1, round(original_fps / target_fps))

    @staticmethod
    def initialize_video(video_path):
        """비디오 초기화 및 설정

        Args:
            video_path (str): 비디오 파일 경로

        Returns:
            tuple: (VideoCapture 객체, fps) 또는 실패시 (None, None)
        """
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise Exception("비디오 파일을 열 수 없습니다.")

            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps <= 0:
                raise Exception("비디오 FPS를 읽을 수 없습니다.")

            return cap, fps

        except Exception as e:
            print(f"비디오 초기화 실패: {str(e)}")
            return None, None

    @staticmethod
    def get_file_info(file_path):
        """파일 정보 가져오기 (비디오 속성 + 파일 기본 정보)"""
        try:
            # 비디오 속성 가져오기
            cap = cv2.VideoCapture(file_path)
            if not cap.isOpened():
                return None, "원본 비디오 파일을 열 수 없습니다."

            props = VideoUtils.get_video_properties(cap)
            if not props:
                cap.release()
                return None, "비디오 속성을 가져오는 중 오류 발생"

            # 파일 기본 정보
            file_stats = os.stat(file_path)

            # 파일 크기를 읽기 쉬운 형식으로 변환
            def format_size(size):
                for unit in ['B', 'KB', 'MB', 'GB']:
                    if size < 1024:
                        return f"{size:.1f} {unit}"
                    size /= 1024
                return f"{size:.1f} TB"

            file_info = {
                'video_props': props,
                'file_name': os.path.basename(file_path),
                'file_path': file_path,
                'file_size': format_size(file_stats.st_size)
            }

            cap.release()
            return file_info, None

        except Exception as e:
            return None, f"파일 정보를 불러오는 중 오류 발생: {str(e)}"

    @staticmethod
    def find_input_file(filename, app_instance):
        """입력 파일 경로 찾기 (공통 메서드)

        Args:
            filename (str): 파일명 또는 전체 경로
            app_instance: 앱 인스턴스 (video_path 속성 포함)

        Returns:
            str or None: 찾은 파일 경로 또는 None
        """
        # 절대 경로인 경우 직접 확인
        if os.path.isabs(filename) and os.path.exists(filename):
            return filename

        # app_instance의 video_path에서 찾기
        if hasattr(app_instance, 'video_path') and app_instance.video_path:
            # StringVar인 경우 get() 메서드 사용
            if hasattr(app_instance.video_path, 'get'):
                full_path = app_instance.video_path.get()
            else:
                full_path = app_instance.video_path

            # 파일명이 일치하고 파일이 존재하는 경우
            if full_path and os.path.basename(full_path) == filename and os.path.exists(full_path):
                return full_path

        return None

    @staticmethod
    def get_video_path_from_app(app_instance):
        """앱 인스턴스에서 video_path 가져오기 (StringVar 처리 포함)

        Args:
            app_instance: 앱 인스턴스

        Returns:
            str or None: video_path 값 또는 None
        """
        if hasattr(app_instance, 'video_path') and app_instance.video_path:
            if hasattr(app_instance.video_path, 'get'):
                return app_instance.video_path.get()
            else:
                return app_instance.video_path
        return None

    @staticmethod
    def generate_output_folder_name(input_path, start_time, end_time, timestamp_format="%y%m%d"):
        """이미지 추출용 출력 폴더명 생성"""
        base_filename = os.path.splitext(os.path.basename(input_path))[0]
        timestamp = datetime.now().strftime(timestamp_format)

        # 시작/종료 시간을 파일명에 포함
        start_time_str = VideoUtils.format_time(start_time).replace(':', '-')
        end_time_str = VideoUtils.format_time(end_time).replace(':', '-')

        # 폴더명 생성: [비디오명]_[시작시간]_[종료시간]_[날짜]
        return f"{base_filename}_{start_time_str}_{end_time_str}_{timestamp}"

    @staticmethod
    def get_default_save_path():
        """기본 저장 경로 가져오기 (바탕화면 또는 문서 폴더)"""
        default_path = os.path.expanduser("~/Desktop")
        if not os.path.exists(default_path):
            default_path = os.path.expanduser("~/Documents")
        return default_path

    @staticmethod
    def calculate_frame_skip_for_images(fps, max_fps=30):
        """이미지 추출용 프레임 스킵 계산"""
        # 30fps 이상이면 매 2번째 프레임만, 그 외는 모든 프레임
        return 2 if fps >= max_fps else 1

    @staticmethod
    def calculate_frame_range(start_time, end_time, fps, frame_skip=1):
        """프레임 범위 계산"""
        start_frame = int(start_time * fps)
        end_frame = int(end_time * fps)
        frames_to_extract = list(range(start_frame, end_frame, frame_skip))
        return frames_to_extract

    @staticmethod
    def generate_image_filename(base_filename, timestamp, frame_number):
        """이미지 파일명 생성"""
        return f"{base_filename}_{timestamp}_frame{frame_number:06d}.jpg"

    @staticmethod
    def extract_frames_from_video(input_path, output_folder, start_time, end_time,
                                  progress_callback=None, cancel_event=None):
        """비디오에서 프레임 추출 (공통 메서드)"""
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise Exception("비디오 파일을 열 수 없습니다.")

        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_skip = VideoUtils.calculate_frame_skip_for_images(fps)

            frames_to_extract = VideoUtils.calculate_frame_range(
                start_time, end_time, fps, frame_skip)
            total_frames = len(frames_to_extract)

            if total_frames == 0:
                raise Exception("추출할 프레임이 없습니다.")

            base_filename = os.path.splitext(os.path.basename(input_path))[0]
            timestamp = datetime.now().strftime("%Y%m%d")

            extracted_count = 0
            progress_update_interval = max(1, total_frames // 20)

            for i, frame_num in enumerate(frames_to_extract):
                # 취소 확인
                if cancel_event and cancel_event.is_set():
                    break

                # 프레임 위치로 이동
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = cap.read()

                if not ret:
                    print(f"⚠️ 프레임 {frame_num} 읽기 실패")
                    continue

                # 이미지 파일명 생성
                image_filename = VideoUtils.generate_image_filename(
                    base_filename, timestamp, frame_num)
                image_path = os.path.join(output_folder, image_filename)

                # 이미지 저장
                cv2.imwrite(image_path, frame)
                extracted_count += 1

                # 진행률 콜백 호출
                if progress_callback and (i % progress_update_interval == 0 or i == total_frames - 1):
                    progress = (i + 1) / total_frames * 100
                    progress_callback(progress, extracted_count, total_frames)

            return {
                'extracted_count': extracted_count,
                'total_frames': total_frames,
                'fps': fps,
                'frame_skip': frame_skip
            }

        finally:
            cap.release()

    @staticmethod
    def extract_audio_from_video(input_path, output_folder, start_time, end_time,
                                 progress_callback=None, cancel_event=None,
                                 audio_format='mp3', audio_quality='192k'):
        """비디오에서 오디오 추출 (공통 메서드)"""
        from extract.extractor import VideoExtractor

        try:
            # 오디오 파일명 생성
            base_filename = os.path.splitext(os.path.basename(input_path))[0]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_filename = f"{base_filename}_{timestamp}.{audio_format}"
            output_path = os.path.join(output_folder, audio_filename)

            # 진행률 콜백 호출
            if progress_callback:
                progress_callback(50, 1, 1)  # 50% 진행률로 시작

            # 취소 확인
            if cancel_event and cancel_event.is_set():
                return None

            # VideoExtractor를 사용하여 오디오 추출
            result = VideoExtractor.extract_audio_segment(
                input_video_path=input_path,
                output_audio_path=output_path,
                start_time=start_time,
                end_time=end_time,
                progress_callback=lambda msg: progress_callback(
                    75, 1, 1) if progress_callback else None,
                audio_format=audio_format,
                audio_quality=audio_quality
            )

            # 취소 확인
            if cancel_event and cancel_event.is_set():
                return None

            if result['success']:
                # 완료 시 진행률 업데이트
                if progress_callback:
                    progress_callback(100, 1, 1)

                return {
                    'extracted_count': 1,
                    'total_frames': 1,
                    'fps': 0,  # 오디오는 FPS가 없음
                    'frame_skip': 0,
                    'output_path': output_path,
                    'audio_format': audio_format,
                    'audio_quality': audio_quality
                }
            else:
                raise Exception(result['message'])

        except Exception as e:
            raise Exception(f"오디오 추출 중 오류: {str(e)}")

        finally:
            pass
