import tkinter as tk  # gui 모듈 포함하여 import
from tkinter import ttk  # 테이블 모듈 포함하여 import
from utils.utils import VideoUtils
import os
import subprocess


class VideoExtractor:
    """비디오 구간 추출을 담당하는 클래스"""

    @staticmethod
    def build_ffmpeg_command(input_path, output_path, start_time, end_time):
        """ffmpeg 명령어 구성"""

        command = [
            'ffmpeg',
            '-y',  # 파일 덮어쓰기 허용 추가
            '-i', input_path,
            '-ss', str(start_time),
            '-to', str(end_time)
        ]

        command.extend([
            '-c:v', 'libx264',  # 비디오 코덱
            '-c:a', 'aac',  # 오디오 코덱
            '-strict', 'experimental'  # 현재 버전에서 사용 가능한 최신 옵션
        ])

        # 출력파일 경로 추가
        command.append(output_path)

        return command

    @staticmethod
    def extract_segment(input_video_path, output_video_path, start_time, end_time,
                        progress_callback=None):
        """ 주어진 시간 범위에 해당하는 비디오 세그먼트를 추출하는 함수 (항상 재인코딩)

        Args:
            input_video_path (str): 입력 비디오 파일 경로
            output_video_path (str): 출력 비디오 파일 경로
            start_time (str or float): 시작 시간 (HH:MM:SS)
            end_time (str or float): 종료 시간 (HH:MM:SS)
            progress_callback (function): 진행률 콜백 함수
        Returns:
            dict: {'sucesss': bool, 'message': str, 'output_path': str}
        """

        try:
            if not os.path.exists(input_video_path):
                return {
                    'success': False,
                    'message': f"입력 비디오 파일이 존재하지 않습니다: {input_video_path}",
                    'output_path': None
                }

            start_time_str = VideoExtractor.format_time_for_ffmpeg(start_time)
            end_time_str = VideoExtractor.format_time_for_ffmpeg(end_time)

            # 출력 디렉토리 확인 및 없으면 생성
            output_dir = os.path.dirname(output_video_path)
            # 빈 문자열 체크 + 존재 확인
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # ffmpeg 명령어 구성
            command = VideoExtractor.build_ffmpeg_command(
                input_video_path,
                output_video_path,
                start_time_str,
                end_time_str
            )

            # 진행률 콜백 함수 처리
            if progress_callback:
                progress_callback("추출 중...")

            result = VideoExtractor.execute_command(command)

            # output_path 추가
            if result['success']:
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
        """시간을 ffmpeg 형식으로 변환"""
        if isinstance(time_value, (int, float)):
            # 시간이면 HH:MM:SS 형식으로 변환
            return VideoUtils.format_time(time_value)
        elif isinstance(time_value, str):
            # 문자열이면 그대로 반환
            return time_value
        else:
            raise ValueError(
                f"Invalid time format 지원하지 않는 시간 형식식: {type(time_value)}")

    @staticmethod
    def execute_command(command):
        """명령어 실행"""

        try:
            command_str = ' '.join(command)
            print(f"Executing FFmpeg command: {command_str}")

            # Windows 환경에서 인코딩 문제 해결
            result = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                encoding='utf-8',  # UTF-8 인코딩 명시
                errors='ignore',   # 디코딩 오류 시 무시
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
        """지원하는 비디오 포맷 반환"""
        return [('mp4 파일', '*.mp4'),
                ('avi 파일', '*.avi'),
                ('mkv 파일', '*.mkv'),
                ('mov 파일', '*.mov'),
                ('flv 파일', '*.flv'),
                ('wmv 파일', '*.wmv'),
                ('webm 파일', '*.webm')]

    @staticmethod
    def check_ffmpeg_installation():
        """FFmpeg 설치 여부 확인"""
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=5
            )
            return True
        except:
            return False

    @staticmethod
    def extract_audio_segment(input_video_path, output_audio_path, start_time, end_time,
                              progress_callback=None, audio_format='mp3', audio_quality='192k'):
        """주어진 시간 범위에 해당하는 오디오 세그먼트를 추출하는 함수

        Args:
            input_video_path (str): 입력 비디오 파일 경로
            output_audio_path (str): 출력 오디오 파일 경로
            start_time (str or float): 시작 시간 (HH:MM:SS)
            end_time (str or float): 종료 시간 (HH:MM:SS)
            progress_callback (function): 진행률 콜백 함수
            audio_format (str): 오디오 포맷 (mp3, wav, aac 등)
            audio_quality (str): 오디오 품질 (192k, 256k, 320k 등)
        Returns:
            dict: {'success': bool, 'message': str, 'output_path': str}
        """
        try:
            if not os.path.exists(input_video_path):
                return {
                    'success': False,
                    'message': f"입력 비디오 파일이 존재하지 않습니다: {input_video_path}",
                    'output_path': None
                }

            start_time_str = VideoExtractor.format_time_for_ffmpeg(start_time)
            end_time_str = VideoExtractor.format_time_for_ffmpeg(end_time)

            # 출력 디렉토리 확인 및 생성
            output_dir = os.path.dirname(output_audio_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # ffmpeg 명령어 구성 (오디오 추출용)
            command = VideoExtractor.build_audio_ffmpeg_command(
                input_video_path,
                output_audio_path,
                start_time_str,
                end_time_str,
                audio_format,
                audio_quality
            )

            # 진행률 콜백 함수 처리
            if progress_callback:
                progress_callback("오디오 추출 중...")

            result = VideoExtractor.execute_command(command)

            # output_path 추가
            if result['success']:
                result['output_path'] = output_audio_path
                result['message'] = "오디오 세그먼트 추출 성공"

            return result

        except Exception as e:
            return {
                'success': False,
                'message': f"오디오 추출 중 오류 발생: {e}",
                'output_path': None
            }

    @staticmethod
    def build_audio_ffmpeg_command(input_path, output_path, start_time, end_time,
                                   audio_format='mp3', audio_quality='192k'):
        """오디오 추출용 ffmpeg 명령어 구성"""
        command = [
            'ffmpeg',
            '-y',  # 파일 덮어쓰기 허용
            '-i', input_path,
            '-ss', str(start_time),
            '-to', str(end_time),
            '-vn',  # 비디오 스트림 제외
            '-acodec', 'libmp3lame' if audio_format == 'mp3' else 'pcm_s16le',
            '-ab', audio_quality,
            output_path
        ]

        return command

    @staticmethod
    def get_supported_audio_formats():
        """지원하는 오디오 포맷 반환"""
        return [
            ('MP3 파일', '*.mp3'),
            ('WAV 파일', '*.wav'),
            ('AAC 파일', '*.aac'),
            ('OGG 파일', '*.ogg'),
            ('FLAC 파일', '*.flac')
        ]


class ExtractConfig:
    """구간 추출 설정을 관리하는 클래스"""

    def __init__(self):
        self.default_output_dir = None
        self.output_format = 'mp4'  # '*.avi' -> 'mp4' 확장자만 표기하기
        self.create_subfolders = False
        self.filename_template = "{basename}_{start}_{end}"

    def generate_filename(self, segment_info):
        """파일명 생성"""
        # 확장자 제거 후 파일명 추출
        # get() 메서드로 'file'명이 존재하면 리턴, 없으면 기본값 'video'를 반환.
        base_name = os.path.splitext(segment_info.get('file', 'video'))[
            0]  # [0]은 파일명, [1]은 확장자

        # 시간 정보를 파일명에 안전한 형식으로 변환 (콜론을 하이픈으로)
        # get으로 'start'찾고, 없음 0 반환
        start_time = VideoUtils.format_time(
            segment_info.get('start', 0)).replace(':', '-')
        end_time = VideoUtils.format_time(
            segment_info.get('end', 0)).replace(':', '-')

        # 템플릿 적용
        filename = self.filename_template.format(
            basename=base_name, start=start_time, end=end_time)

        return f"{filename}.{self.output_format}"

    def get_output_path(self, segment_info, custom_folder=None):  # custom_folder 매개변수 추가
        """출력 경로 생성"""
        folder = custom_folder or self.default_output_dir

        if self.create_subfolders:
            # 원본 파일명을 서브폴더명으로 생성
            basename = os.path.splitext(segment_info.get('file', 'video'))[0]
            folder = os.path.join(folder, basename)

        filename = self.generate_filename(segment_info)
        return os.path.join(folder, filename)

    def set_filename_template(self, template):
        """파일명 템플릿 변경"""

        self.filename_template = template

    def set_output_format(self, format_extension):
        """출력 포맷 변경"""

        self.output_format = format_extension.lstrip(".")  # 점 제거
