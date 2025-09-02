import os
from datetime import datetime
import cv2
import subprocess
from utils.utils import VideoUtils
from utils.image_utils import ImageUtils


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
            dict: {'extracted_count', 'total_frames', 'fps'}
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

            base_filename = ImageUtils.basename_of_videofile(input_path)

            print(f"[ImageExtractor] 출력 폴더: {output_folder}")

            # 순차적 디코딩 방식 추출 진행
            # 시작 프레임 이동
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

            # frame_count 는 아래 추출 while문을 돌기 위한 카운터
            frame_count = start_frame
            # extracted_count 는 추출된 프레임 개수로 진행률 계산을 위한 카운터터
            extracted_count = 0

            # 저장할 프레임 이미지 총 개수(진행률 계산용)
            try:
                if end_frame >= start_frame:
                    # 예시: 10초이며 fps가 30일때, (300-0) // 1 + 1 = 300개
                    total_exports = (
                        (end_frame - start_frame) // max(frame_skip, 1) + 1)
                else:
                    total_exports = 0
            except Exception:
                total_exports = 0

            # 추출 진행
            while frame_count <= end_frame:
                # 취소 체크
                if cancel_event and cancel_event.is_set():
                    print("[ImageExtractor] 취소 요청 감지 - 추출 중단")
                    break

                # 프레임 읽기 (순차적 디코딩)
                ret, frame = cap.read()
                if not ret:
                    break

                if (frame_count - start_frame) % frame_skip == 0:
                    timestamp = frame_count / fps
                    filename = ImageUtils.generate_image_filename(
                        base_filename, frame_count)
                    filepath = os.path.join(output_folder, filename)

                    # 파일저장 (유니코드 경로 안전)
                    try:
                        ok, buf = cv2.imencode('.jpg', frame)
                        if ok:
                            buf.tofile(filepath)
                        else:
                            raise IOError('imencode 실패')
                    except Exception as e:
                        print(f"저장 실패: {filepath} - {e}")
                        frame_count += 1
                        continue
                    print(f"저장됨: {filepath}")
                    extracted_count += 1

                    # 진행률 콜백
                    try:
                        progress = (extracted_count /
                                    max(1, total_exports)) * 100.0
                        if progress_callback:
                            progress_callback(
                                progress, extracted_count, total_exports)
                    except Exception:
                        pass

                frame_count += 1

            print(
                f"[ImageExtractor] done: saved={extracted_count}/{total_frames}, fps={fps}")
            return {
                'extracted_count': extracted_count,
                'total_frames': total_frames}

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

    # ----------------- FFmpeg 폴백 -----------------

    @staticmethod
    def extract_frames_with_ffmpeg(input_path, output_folder, start_time, end_time,
                                   ffmpeg_executable='ffmpeg', target_fps=None,
                                   quality=2, base_filename=None, timestamp=None,
                                   cancel_event=None):
        """FFmpeg을 사용하여 이미지 프레임 추출 (OpenCV 디코드 실패시 폴백)

        Returns dict: {'success', 'extracted_count', 'message'}
        """
        try:
            # 파일명 생성
            if base_filename is None:
                base_filename = os.path.splitext(
                    os.path.basename(input_path))[0].strip()
            if timestamp is None:
                timestamp = datetime.now().strftime("%y%m%d")

            output_pattern = os.path.join(
                output_folder, f"{base_filename}_{timestamp}_frame%06d.jpg")

            # FFmpeg 커맨드 생성
            command = [
                ffmpeg_executable, '-y',
                '-ss', str(start_time),
                '-to', str(end_time),
                '-i', input_path,
                '-qscale:v', str(quality)
            ]
            # frame skip 대신 FPS 제한으로 opencv에서의 동일 효과 구현
            if target_fps:
                command += ['-vf', f'fps={target_fps}']

            command.append(output_pattern)  # FFmpeg 커맨드에서 마지막은 항상 출력 파일 경로.

            print("[ImageExtractor] Executing FFmpeg (images) command:",
                  ' '.join(command))

            # FFmpeg 실행 (서브프로세스) - 취소 지원
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )

            # 취소 체크하면서 대기 (최적화된 버전)
            while process.poll() is None:  # 프로세스가 실행 중일 때
                if cancel_event and cancel_event.is_set():
                    print("[ImageExtractor] FFmpeg 취소 요청 감지 - 프로세스 종료")
                    process.terminate()
                    try:
                        process.wait(timeout=3)  # 3초로 단축
                    except subprocess.TimeoutExpired:
                        print("[ImageExtractor] 프로세스 강제 종료")
                        process.kill()
                    return {'success': False, 'extracted_count': 0, 'message': '사용자 취소'}

                import time
                time.sleep(0.05)  # 50ms로 단축 - 더 빠른 응답성

            # 프로세스 결과 확인
            stdout, stderr = process.communicate()
            result = subprocess.CompletedProcess(
                args=command,
                returncode=process.returncode,
                stdout=stdout,
                stderr=stderr
            )

            # 성공/실패 여부 확인
            if result.returncode != 0:
                msg = result.stderr or result.stdout or 'ffmpeg 실패'
                print(f"[ImageExtractor] FFmpeg images failed: {msg[:500]}")
                return {'success': False, 'extracted_count': 0, 'message': msg}

            # 생성 파일 개수 추정: glob 패턴 사용으로 최적화
            import glob
            count = 0
            try:
                pattern = os.path.join(
                    output_folder, f"{base_filename}_{timestamp}_frame*.jpg")
                count = len(glob.glob(pattern))
            except Exception:
                pass

            print(f"[ImageExtractor] FFmpeg images success: count={count}")
            return {'success': True, 'extracted_count': count, 'message': 'ffmpeg 이미지 추출 성공'}
        except Exception as e:
            print(f"[ImageExtractor] FFmpeg images exception: {e}")
            return {'success': False, 'extracted_count': 0, 'message': str(e)}
