import os
import subprocess
from utils.utils import VideoUtils
# 상대경로  from ..image_utils import ImageUtils
# 앱이 ffmpeg 절대경로를 쓰도록 유지하기 위해, ffmpeg_executable='ffmpeg' 로 수정.


class VideoExtractor:
    """비디오 구간 추출을 담당하는 클래스 (항상 재인코딩)"""

    @staticmethod
    def build_ffmpeg_command(input_path, output_path, start_time, end_time, ffmpeg_executable='ffmpeg'):
        command = [
            ffmpeg_executable,
            '-y',
            '-i', input_path,
            '-ss', str(start_time),
            '-to', str(end_time),
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-strict', 'experimental'
        ]
        command.append(output_path)
        return command

    @staticmethod
    def extract_segment(input_video_path, output_video_path, start_time, end_time,
                        progress_callback=None, ffmpeg_executable='ffmpeg'):
        try:
            if not os.path.exists(input_video_path):
                return {
                    'success': False,
                    'message': f"입력 비디오 파일이 존재하지 않습니다: {input_video_path}",
                    'output_path': None
                }

            start_time_str = VideoExtractor.format_time_for_ffmpeg(start_time)
            end_time_str = VideoExtractor.format_time_for_ffmpeg(end_time)

            output_dir = os.path.dirname(output_video_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            command = VideoExtractor.build_ffmpeg_command(
                input_video_path,
                output_video_path,
                start_time_str,
                end_time_str,
                ffmpeg_executable=ffmpeg_executable
            )

            if progress_callback:
                progress_callback("추출 중...")

            result = VideoExtractor.execute_command(command)
            if result.get('success'):
                result['output_path'] = output_video_path
            return result

        except Exception as e:
            return {
                'success': False,
                'message': f"오류 발생: {e}",
                'output_path': None
            }

    @staticmethod
    def format_time_for_ffmpeg(time_value):
        if isinstance(time_value, (int, float)):
            return VideoUtils.format_time(time_value)
        elif isinstance(time_value, str):
            return time_value
        else:
            raise ValueError(
                f"Invalid time format 지원하지 않는 시간 형식: {type(time_value)}")

    @staticmethod
    def execute_command(command):
        try:
            command_str = ' '.join(command)
            print(f"Executing FFmpeg command: {command_str}")

            result = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=300
            )

            print(f"FFmpeg 출력: {result.stdout}")
            if result.stderr:
                print(f"FFmpeg 경고: {result.stderr}")

            return {
                'success': True,
                'message': "비디오 세그먼트 추출 성공",
                'output_path': command[-1]
            }

        except subprocess.CalledProcessError as e:
            error_message = f"FFmpeg 오류 발생: 코드 {e.returncode}"
            if e.stderr:
                error_message += f"\n 오류내용 {e.stderr}"
            return {'success': False, 'message': error_message}

        except subprocess.TimeoutExpired:
            return {'success': False, 'message': "FFmpeg 실행 시간 5분 초과"}

        except FileNotFoundError:
            return {'success': False, 'message': "FFmpeg가 설치되지 않았거나, PATH에 없습니다"}

        except UnicodeDecodeError as e:
            return {'success': False, 'message': f"인코딩 오류: {str(e)}"}

    @staticmethod
    def get_supported_formats():
        return [
            ('mp4 파일', '*.mp4'),
            ('avi 파일', '*.avi'),
            ('mkv 파일', '*.mkv'),
            ('mov 파일', '*.mov'),
            ('flv 파일', '*.flv'),
            ('wmv 파일', '*.wmv'),
            ('webm 파일', '*.webm'),
        ]

    @staticmethod
    def check_ffmpeg_installation():
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True,
                           encoding='utf-8', errors='ignore', timeout=5)
            return True
        except Exception:
            return False


class ExtractConfig:
    """구간 추출 설정을 관리하는 클래스"""

    def __init__(self):
        self.default_output_dir = None
        self.output_format = 'mp4'
        self.create_subfolders = False
        self.filename_template = "{basename}_{start}_{end}"

    def generate_filename(self, segment_info):
        base_name = os.path.splitext(segment_info.get('file', 'video'))[0]
        start_time = VideoUtils.format_time(
            segment_info.get('start', 0)).replace(':', '-')
        end_time = VideoUtils.format_time(
            segment_info.get('end', 0)).replace(':', '-')
        filename = self.filename_template.format(
            basename=base_name, start=start_time, end=end_time)
        return f"{filename}.{self.output_format}"

    def get_output_path(self, segment_info, custom_folder=None):
        folder = custom_folder or self.default_output_dir
        if self.create_subfolders:
            basename = os.path.splitext(segment_info.get('file', 'video'))[0]
            folder = os.path.join(folder, basename)
        filename = self.generate_filename(segment_info)
        return os.path.join(folder, filename)

    def set_filename_template(self, template):
        self.filename_template = template

    def set_output_format(self, format_extension):
        self.output_format = format_extension.lstrip('.')
