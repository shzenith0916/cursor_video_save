import os
import cv2
from datetime import datetime
from .utils import VideoUtils


class ImageUtils:
    """이미지 관련 보조 계산 유틸리티 (상태 없음)"""

    @staticmethod
    def generate_output_folder_name(input_path, start_time, end_time, timestamp_format="%y%m%d"):
        """이미지 추출용 출력 폴더명 생성"""
        base_filename = os.path.splitext(os.path.basename(input_path))[0]
        timestamp = datetime.now().strftime(timestamp_format)
        start_time_str = VideoUtils.format_time(start_time).replace(':', '-')
        end_time_str = VideoUtils.format_time(end_time).replace(':', '-')

        # 폴더명 생성: [비디오명]_[시작시간]_[종료시간]_[날짜]
        return f"{base_filename}_{start_time_str}_{end_time_str}_{timestamp}"

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
    def calculate_frame_number(time_seconds, fps):
        """시간(초)을 프레임 번호로 변환"""
        return int(float(time_seconds) * fps)

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
            frame_skip = ImageUtils.calculate_frame_skip_for_images(fps)

            frames_to_extract = ImageUtils.calculate_frame_range(
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
                image_filename = ImageUtils.generate_image_filename(
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
