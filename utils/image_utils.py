import os
from datetime import datetime
from utils.utils import VideoUtils


class ImageUtils:
    """이미지 관련 보조 계산 유틸리티 (상태 없음)"""

    @staticmethod
    def basename_of_videofile(input_path):
        """비디오 파일명 추출 - 폴더명 생성에 사용"""
        import re
        # 비디오 파일명 추출(확장자 제거)
        base_filename = os.path.splitext(os.path.basename(input_path))[0]
        # 파일명에서 특수문자 제거 및 공백 제거 (특수문자 제거 정규식)
        video_filename = re.sub(r'[^a-zA-Z0-9]', '', base_filename)
        return video_filename

    @staticmethod
    def generate_output_folder_name(input_path, start_time, end_time):
        """이미지 추출용 출력 폴더명 생성"""
        # 비디오 파일명 추출
        video_filename = ImageUtils.basename_of_videofile(input_path)
        start_time_str = VideoUtils.format_time(start_time).replace(':', '-')
        end_time_str = VideoUtils.format_time(end_time).replace(':', '-')

        # 날짜 추가
        today = datetime.now().strftime("%Y%m%d")

        # 폴더명 생성: [비디오명]_[시작시간]_[종료시간]_[날짜]
        return f"{video_filename}_{start_time_str}_{end_time_str}_{today}"

    @staticmethod
    def generate_image_filename(base_filename, frame_number):
        """이미지 파일명 생성 (타임스탬프 포함)"""
        timestamp = datetime.now().strftime("%y%m%d")
        return f"{base_filename}_{timestamp}_frame{frame_number:06d}.jpg"
