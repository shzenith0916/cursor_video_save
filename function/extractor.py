import tkinter as tk  # gui 모듈 포함하여 import
from tkinter import ttk  # 테이블 모듈 포함하여 import
from utils.utils import VideoUtils
import os
import subprocess


class VideoExtractor:
    """비디오 구간 추출을 담당하는 클래스"""

    @staticmethod
    def build_ffmpeg_command(input_path, output_path, start_time, end_time, ffmpeg_codec_copy=True):
        """ffmpeg 명령어 구성"""

        command = [
            'ffmpeg',
            '-i', input_path,
            '-ss', str(start_time),
            '-to', str(end_time)
        ]

        if ffmpeg_codec_copy:
            command.extend(['-c', 'copy'])  # 코덱 복사, 처리가 빠름
        else:
            command.extend(
                '-c:v', 'libx264',  # 비디오 코덱
                '-c:a', 'aac',  # 오디오 코덱
                '-strict', 'experimental'  # 현재 버전에서 사용 가능한 최신 옵션
            )

        # 출력파일 경로 추가
        command.append(output_path)

        return command

    @staticmethod
    def extract_segment(input_video_path, output_video_path, start_time, end_time,
                        progress_callback=None, ffmpeg_codec_copy=True):
        """ 주어진 시간 범위에 해당하는 비디오 세그먼트를 추출하는 함수

        Args:
            input_video_path (str): 입력 비디오 파일 경로
            output_video_path (str): 출력 비디오 파일 경로
            start_time (str or float): 시작 시간 (HH:MM:SS)
            end_time (str or float): 종료 시간 (HH:MM:SS)
            progress_callback (function): 진행률 콜백 함수
            ffmpeg_codec_copy (bool): ffmpeg 코덱 복사 사용 여부
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
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # ffmpeg 명령어 구성
            command = VideoExtractor.build_ffmpeg_command(
                input_video_path,
                output_video_path,
                start_time_str,
                end_time_str,
                ffmpeg_codec_copy
            )

            # 진행률 콜백 함수 처리
            if progress_callback:
                progress_callback(0, "추출 중...")

            result = VideoExtractor.execute_command(command)

        except Exception as e:
            return {
                'success': False,
                'message': f"오류 발생: {e}",
                'output_path': None
            }

    @staticmethod
    def format_time_for_ffmpeg(time):
        """시간을 ffmpeg 형식으로 변환"""
        if isinstance(time, (int, float)):
            # 시간이면 HH:MM:SS 형식으로 변환
            return VideoUtils.format_time(time)
        elif isinstance(time, str):
            # 문자열이면 그대로 반환
            return time
        else:
            raise ValueError(
                f"Invalid time format 지원하지 않는 시간 형식식: {type(time)}")

    @staticmethod
    def execute_command(command):
        """명령어 실행"""

        try:
            command_str = ' '.join(command)
            print(f"Executing FFmpeg command: {command_str}")

            result = subprocess.run(command,
                                    check=True,
                                    capture_output=True,
                                    text=True,
                                    timeout=120)  # 2분 타임아웃

            print(f"FFmpeg 출력: {result.stdout}")
            print(f"FFmpeg 오류: {result.stderr}")

            return {
                'success': True,
                'message': "비디오 세그먼트 추출 성공",
                'output_path': command[-1]
            }

        except subprocess.CalledProcessError as e:
            print(f"FFmpeg 오류 발생: {e}")
            return {'success': False, 'message': str(e)}

    @staticmethod
    def generate_filename(segment_info):
        """규간 세그먼트 정보를 기반으로 파일명 생성"""

        # get() 메서드로 'file'명이 존재하면 리턴, 없으면 기본값 'video'를 반환환
        base_name = os.path.splitext(segment_info.get('file', 'video'))[
            0]  # [0]은 파일명, [1]은 확장자
        start_time = VideoUtils.format_time(
            segment_info.get('start', 0))  # get으로 'start'찾고, 없음 0 반환
        end_time = VideoUtils.format_time(segment_info.get('end', 0))

        return f"{base_name}_{start_time}_{end_time}.mp4"

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
