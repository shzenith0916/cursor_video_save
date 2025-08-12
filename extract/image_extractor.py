import cv2
import os
from datetime import datetime
from utils.image_utils import ImageUtils


class ImageExtractor:
    """OpenCV를 사용하여 비디오 프레임을 이미지로 추출"""

    @staticmethod
    def extract_frames_from_video(input_path, output_folder, start_time, end_time,
                                  progress_callback=None, cancel_event=None):
        """비디오에서 프레임 추출"""
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise IOError(f"비디오 파일을 열 수 없습니다: {input_path}")

        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            if not fps or fps <= 0:
                # 일부 코덱/컨테이너에서 FPS를 못 읽는 경우 기본값 사용
                fps = 30.0
                try:
                    print("[ImageExtractor] FPS를 읽지 못해 기본 30fps로 진행합니다.")
                except Exception:
                    pass

            frame_skip = ImageUtils.calculate_frame_skip_for_images(fps)
            frames_to_extract = ImageUtils.calculate_frame_range(
                start_time, end_time, fps, frame_skip)
            total_frames = len(frames_to_extract)

            if total_frames == 0:
                return {'extracted_count': 0, 'total_frames': 0, 'fps': fps, 'frame_skip': frame_skip}

            base_filename = os.path.splitext(os.path.basename(input_path))[0]
            timestamp = datetime.now().strftime("%Y%m%d")

            extracted_count = 0
            progress_update_interval = max(1, total_frames // 20)

            for i, frame_num in enumerate(frames_to_extract):
                if cancel_event and cancel_event.is_set():
                    break

                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = cap.read()

                if not ret:
                    print(f"⚠️ 프레임 {frame_num} 읽기 실패")
                    continue

                image_filename = ImageUtils.generate_image_filename(
                    base_filename, timestamp, frame_num)
                image_path = os.path.join(output_folder, image_filename)

                cv2.imwrite(image_path, frame)
                extracted_count += 1

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
