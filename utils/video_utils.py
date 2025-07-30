import cv2
import os
from datetime import datetime


class VideoUtils:
    """비디오 관련 유틸리티 클래스"""

    @staticmethod
    def format_time(seconds):
        """초를 HH:MM:SS 형식으로 변환"""
        seconds = int(float(seconds))
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    @staticmethod
    def get_opencv_video_info(video_path):
        """OpenCV로 비디오 정보 가져오기"""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return None

            video_info = {
                'duration': cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS),
                'fps': cap.get(cv2.CAP_PROP_FPS),
                'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            }

            cap.release()
            return video_info

        except Exception as e:
            print(f"OpenCV 비디오 정보 가져오기 실패: {e}")
            return None

    @staticmethod
    def convert_frame_to_photo(frame):
        """OpenCV 프레임을 Tkinter PhotoImage로 변환"""
        try:
            import tkinter as tk
            from PIL import Image, ImageTk

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
            import tkinter as tk
            from PIL import Image, ImageTk

            # BGR -> RGB 변환
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(frame_rgb)

            # 타겟 크기가 지정된 경우 리사이즈
            if target_width and target_height:
                pil_img.thumbnail((target_width, target_height),
                                  Image.Resampling.LANCZOS)

            return ImageTk.PhotoImage(pil_img)

        except Exception as e:
            print(f"Frame Conversion Error: {e}")
            return None

    @staticmethod
    def calculate_frame_number(time_seconds, fps):
        """시간(초)을 프레임 번호로 변환"""
        return int(float(time_seconds) * fps)

    @staticmethod
    def calculate_optimal_fps(original_fps, max_fps=30):
        """최적 fps 계산"""
        return min(original_fps, max_fps)

    @staticmethod
    def calculate_frame_skip(original_fps, target_fps):
        """프레임 스킵 계산"""
        if target_fps >= original_fps:
            return 1
        return max(1, round(original_fps / target_fps))

    @staticmethod
    def read_frame_at_position(cap, position, fps=None, is_frame_number=False):
        """지정된 위치에서 프레임 읽기"""
        if not cap or not cap.isOpened():
            return False, None

        if not is_frame_number and fps:
            frame_number = VideoUtils.calculate_frame_number(position, fps)
        else:
            frame_number = position

        # 프레임 위치 설정
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

        # 프레임 읽기
        return cap.read()

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
        """기본 저장 경로 가져오기"""
        default_path = os.path.expanduser("~/Desktop")
        if not os.path.exists(default_path):
            default_path = os.path.expanduser("~/Documents")
        return default_path

    @staticmethod
    def calculate_frame_skip_for_images(fps, max_fps=30):
        """이미지 추출용 프레임 스킵 계산"""
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
