import os
import cv2
import tkinter as tk
from PIL import Image, ImageTk
from datetime import datetime


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
    def cleanup_opencv_memory():
        """메모리 정리"""
        cv2.destroyAllWindows()

    @staticmethod
    def validate_video_section(cap, start_time, end_time):
        """비디오 구간 유효성 검사"""
        if not cap or not cap.isOpened():
            return False, "비디오를 열 수 없습니다."

        props = VideoUtils.get_video_properties(cap)
        if not props:
            return False, "비디오 속성을 가져올 수 없습니다."

        if start_time < 0:
            return False, "시작 시간은 0 초 보다 작을 수 없습니다."

        if start_time >= end_time:
            return False, "시작 시간은 종료 시간보다 빨라야 합니다."

        return True, "유효한 구간입니다."

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
