import os
from datetime import datetime
from .video_extractor import VideoExtractor


class AudioExtractor:
    """오디오 추출 전용 유틸리티 (ffmpeg 사용)"""

    @staticmethod
    def extract_audio_segment(input_video_path, output_audio_path, start_time, end_time,
                              progress_callback=None, audio_format='mp3', audio_quality='192k',
                              ffmpeg_executable='ffmpeg'):
        try:
            # VideoExtractor의 ffmpeg 실행기 사용을 유지하려면 별도 커맨드 빌드가 필요
            # 간단히 VideoExtractor의 execute_command 재사용
            command = [
                ffmpeg_executable, '-y',
                '-i', input_video_path,
                '-ss', str(start_time),
                '-to', str(end_time),
            ]

            if audio_format == 'mp3':
                command += ['-vn', '-acodec',
                            'libmp3lame', '-ab', audio_quality]
            elif audio_format == 'wav':
                command += ['-vn', '-acodec', 'pcm_s16le']
            else:
                command += ['-vn', '-acodec',
                            'libmp3lame', '-ab', audio_quality]

            command.append(output_audio_path)

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
