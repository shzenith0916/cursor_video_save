from .video_extractor import VideoExtractor


class AudioExtractor:
    """오디오 추출 전용 유틸리티 (ffmpeg 사용)"""

    @staticmethod
    def build_audio_command(input_video_path, output_audio_path, start_time, end_time,
                            audio_format='mp3', audio_quality='192k', ffmpeg_executable='ffmpeg'):
        """오디오 추출을 위한 FFmpeg 커맨드 생성"""
        command = [
            ffmpeg_executable, '-y',
            '-i', input_video_path,
            '-ss', str(start_time),
            '-to', str(end_time),
        ]

        if audio_format == 'mp3':
            command += ['-vn', '-acodec', 'libmp3lame', '-ab', audio_quality]
        elif audio_format == 'wav':
            command += ['-vn', '-acodec', 'pcm_s16le']
        else:
            command += ['-vn', '-acodec', 'libmp3lame', '-ab', audio_quality]

        command.append(output_audio_path)
        return command

    @staticmethod
    def extract_audio_segment(input_video_path, output_audio_path, start_time, end_time,
                              progress_callback=None, audio_format='mp3', audio_quality='192k',
                              ffmpeg_executable='ffmpeg'):
        """오디오 세그먼트 추출"""
        try:
            command = AudioExtractor.build_audio_command(
                input_video_path, output_audio_path, start_time, end_time,
                audio_format, audio_quality, ffmpeg_executable)

            if progress_callback:
                progress_callback("오디오 추출 중...")

            result = VideoExtractor.execute_command(command)
            if result.get('success'):
                result['output_path'] = output_audio_path
                result['message'] = "오디오 세그먼트 추출 성공"
            return result
        except Exception as e:
            return {
                'success': False,
                'message': f"오디오 추출 중 오류 발생: {e}",
                'output_path': None
            }

# 'ffmpeg' 대신 ffmpeg_executable='ffmpeg' 사용하는 이유는,
# 1. 윈도우 환경: FFmpeg가 PATH에 없을 수 있고,
# 2. 절대 경로를 지원하기 위해서 (C:\Program Files\ffmpeg\bin\ffmpeg.exe)
# 3. 여러 경로에서 FFmpeg를 사용할 수 있게 하기 위해서 (자동으로 탐지)
