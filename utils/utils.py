import cv2
import tkinter as tk
from PIL import Image, ImageTk


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
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(frame)
        return ImageTk.PhotoImage(image=image)

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
