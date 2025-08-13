import os
from datetime import datetime
import cv2
import subprocess
from utils.utils import VideoUtils
from tkinter import filedialog
import tkinter as tk


class ImageExtractor:
    """OpenCV를 사용하여 비디오 프레임을 이미지로 추출"""

    @staticmethod
    def extract_frames_from_video(input_path, output_folder, start_time, end_time,
                                  progress_callback=None, cancel_event=None):
        """비디오에서 프레임 추출 (퍼블릭 API)

        Args:
            input_path: 입력 비디오 경로
            output_folder: 출력 폴더 경로
            start_time: 시작 초
            end_time: 종료 초
            progress_callback: 진행률 콜백(progress, extracted_count, total_frames)
            cancel_event: 취소 이벤트
        Returns:
            dict: {'extracted_count', 'total_frames', 'fps', 'frame_skip'}
        """

        print(
            f"[ImageExtractor] start: input='{input_path}', out='{output_folder}', segment_time=({start_time}->{end_time}))")

        # 비디오 열기
        cap = ImageExtractor._open_capture(input_path)

        try:
            # FPS 가져오기
            fps = ImageExtractor._resolve_fps(cap)
            # 비디오 총 프레임 개수
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            # 프레임 스킵 계산
            frame_skip = ImageExtractor._calculate_frame_skip_for_images(fps)
            # 추출 시작/종료 프레임 계산
            start_frame = int(start_time * fps)
            end_frame = int(end_time * fps)

            output_folder = ImageUtils.create_output_folder_with_dialog(
                input_path, start_time, end_time)

            base_filename = ImageUtils._basename_of_videofile(input_path)

            print(f"[ImageExtractor] 출력 폴더: {output_folder}")

            # 순차적 디코딩 방식 추출 진행
            # 시작 프레임 이동
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

            frame_count = start_frame
            extracted_count = 0

            # 추출 진행
            while frame_count <= end_frame:
                # 프레임 읽기
                ret, frame = cap.read()
                if not ret:
                    break

                if (frame_count - start_frame) % frame_skip == 0:
                    timestamp = frame_count / fps
                    filename = ImageUtils.generate_image_filename(
                        base_filename, frame_count)
                    filepath = os.path.join(output_folder, filename)

                    # 파일저장
                    cv2.imwrite(filepath, frame)
                    print(f"저장됨: {filepath}")
                    extracted_count += 1

                frame_count += 1

            print(
                f"[ImageExtractor] done: saved={extracted_count}/{total_frames}, fps={fps}")
            return {
                'extracted_count': extracted_count,
                'total_frames': total_frames,
                'fps': fps
            }
        finally:
            cap.release()

    # ----------------- 내부 헬퍼 메서드 -----------------
    @staticmethod
    def _open_capture(input_path):
        """OpenCV를 사용하여 비디오 파일을 열고 비디오 캡처 객체를 반환"""
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise IOError(f"[VideoLoadError]비디오 파일을 열 수 없습니다: {input_path}")
        return cap

    @staticmethod
    def _resolve_fps(cap):
        """비디오의 FPS를 GET하고 없으면 기본값 fps=30을 반환"""
        fps = cap.get(cv2.CAP_PROP_FPS)
        if not fps or fps <= 0:
            fps = 30.0
            print("[ImageExtractor] FPS를 읽지 못해 기본 30fps로 진행합니다.")
        return fps

    @staticmethod
    def _calculate_frame_skip_for_images(fps, max_fps=50):
        """이미지 추출용 프레임 스킵 계산"""
        # 50fps 이상이면 매 2번째 프레임만, 그 외는 모든 프레임
        return 2 if fps >= max_fps else 1

# --------------------------------------- 폴더, 파일명 관련


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
        video_filename = ImageUtils._basename_of_videofile(input_path)
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

    @staticmethod
    def _create_output_folder_with_dialog(input_path, start_time, end_time):
        """폴더 선택 다이얼로그로 출력 폴더 생성"""
        # 폴더명 생성
        folder_name = ImageUtils.generate_output_folder_name(
            input_path, start_time, end_time)

        # 사용자에게 상위 폴더 선택하게 함
        root = tk.Tk()
        root.withdraw()  # 메인 윈도우 숨기기

        base_dir = filedialog.askdirectory(
            title=f"'{folder_name}' 폴더를 생성할 위치를 선택하세요"
        )
        root.destroy()

        if not base_dir:  # 사용자가 취소한 경우
            raise ValueError("폴더 선택이 취소되었습니다.")

        # 전체 폴더 경로 생성
        full_folder_path = os.path.join(base_dir, folder_name)
        os.makedirs(full_folder_path, exist_ok=True)

        print(f"[ImageUtils] 출력 폴더 생성됨: {full_folder_path}")
        return full_folder_path

    # ----------------- FFmpeg 폴백 -----------------

    @staticmethod
    def extract_frames_with_ffmpeg(input_path, output_folder, start_time, end_time,
                                   ffmpeg_executable='ffmpeg', target_fps=None,
                                   quality=2, base_filename=None, timestamp=None):
        """FFmpeg을 사용하여 이미지 프레임 추출 (OpenCV 디코드 실패시 폴백)

        Returns dict: {'success', 'extracted_count', 'message'}
        """
        try:
            if base_filename is None or timestamp is None:
                base_filename, timestamp = ImageExtractor._build_naming(
                    input_path)  # 파일명, 타임스탬프 두개 반환

            output_pattern = os.path.join(
                output_folder, f"{base_filename}_{timestamp}_frame%06d.jpg")

            command = [
                ffmpeg_executable, '-y',
                '-ss', str(start_time),
                '-to', str(end_time),
                '-i', input_path,
                '-qscale:v', str(quality)
            ]
            if target_fps:
                command += ['-vf', f'fps={target_fps}']
            command.append(output_pattern)

            print("[ImageExtractor] Executing FFmpeg (images) command:",
                  ' '.join(command))
            result = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=300
            )
            if result.returncode != 0:
                msg = result.stderr or result.stdout or 'ffmpeg 실패'
                print(f"[ImageExtractor] FFmpeg images failed: {msg[:500]}")
                return {'success': False, 'extracted_count': 0, 'message': msg}

            # 생성 파일 개수 추정: 디렉터리 스캔
            count = 0
            try:
                for name in os.listdir(output_folder):
                    if name.startswith(f"{base_filename}_{timestamp}_frame") and name.endswith('.jpg'):
                        count += 1
            except Exception:
                pass

            print(f"[ImageExtractor] FFmpeg images success: count={count}")
            return {'success': True, 'extracted_count': count, 'message': 'ffmpeg 이미지 추출 성공'}
        except Exception as e:
            print(f"[ImageExtractor] FFmpeg images exception: {e}")
            return {'success': False, 'extracted_count': 0, 'message': str(e)}
