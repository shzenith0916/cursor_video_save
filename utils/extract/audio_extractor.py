from .video_extractor import VideoExtractor


class AudioExtractor:
    """오디오 추출 전용 유틸리티 (ffmpeg 사용)"""

    @staticmethod
    def build_audio_command(input_video_path, output_audio_path, start_time, end_time,
                            audio_format='mp3', audio_quality='192k', ffmpeg_executable='ffmpeg'):
        """오디오 추출을 위한 FFmpeg 커맨드 생성 - 정확한 시간 처리"""
        # FFmpeg에서 -ss와 -to를 함께 사용하면 -to는 상대적 길이가 됨
        # 절대 종료 시간을 원한다면 -t (duration)를 사용해야 함
        duration = end_time - start_time
        command = [
            ffmpeg_executable, '-y',
            '-ss', str(start_time),  # 시작 시간을 먼저
            '-i', input_video_path,  # 입력 파일 (ss 다음에 위치)
            '-t', str(duration),    # 길이 (duration) 사용
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
                              ffmpeg_executable='ffmpeg', cancel_event=None):
        """오디오 세그먼트 추출 - 정확한 시간 처리"""
        try:
            # 디버깅 정보 출력
            duration = end_time - start_time
            print(f"AudioExtractor: 오디오 추출 시작")
            print(f"AudioExtractor: 입력 파일: {input_video_path}")
            print(f"AudioExtractor: 시작 시간: {start_time}초")
            print(f"AudioExtractor: 종료 시간: {end_time}초")
            print(f"AudioExtractor: 추출 길이: {duration}초 ({duration/60:.1f}분)")
            print(f"AudioExtractor: 출력 파일: {output_audio_path}")

            command = AudioExtractor.build_audio_command(
                input_video_path, output_audio_path, start_time, end_time,
                audio_format, audio_quality, ffmpeg_executable)

            print(f"AudioExtractor: FFmpeg 명령어: {' '.join(command)}")

            if progress_callback:
                progress_callback("오디오 추출 중...")

            result = VideoExtractor.execute_command(
                command, cancel_event=cancel_event)
            if result.get('success'):
                result['output_path'] = output_audio_path
                result['message'] = "오디오 세그먼트 추출 성공"
                print(f"AudioExtractor: 추출 완료 - {output_audio_path}")

                # 실제 추출된 파일의 길이 확인
                try:
                    import subprocess
                    import os
                    if os.path.exists(output_audio_path):
                        # ffprobe로 실제 파일 길이 확인
                        ffprobe_path = ffmpeg_executable.replace(
                            'ffmpeg', 'ffprobe').replace('ffmpeg.EXE', 'ffprobe.EXE')
                        probe_cmd = [
                            ffprobe_path,
                            '-v', 'quiet',
                            '-show_entries', 'format=duration',
                            '-of', 'csv=p=0',
                            output_audio_path
                        ]
                        probe_result = subprocess.run(
                            probe_cmd, capture_output=True, text=True)
                        if probe_result.returncode == 0:
                            actual_duration = float(
                                probe_result.stdout.strip())
                            print(
                                f"AudioExtractor: 실제 추출된 파일 길이: {actual_duration}초 ({actual_duration/60:.1f}분)")
                            print(
                                f"AudioExtractor: 예상 길이와 차이: {abs(actual_duration - duration):.2f}초")
                        else:
                            print("AudioExtractor: ffprobe로 길이 확인 실패")
                    else:
                        print("AudioExtractor: 출력 파일이 존재하지 않음")
                except Exception as probe_e:
                    print(f"AudioExtractor: 길이 확인 중 오류: {probe_e}")
            else:
                print(
                    f"AudioExtractor: 추출 실패 - {result.get('message', 'Unknown error')}")
            return result
        except Exception as e:
            error_msg = f"오디오 추출 중 오류 발생: {e}"
            print(f"AudioExtractor: 예외 발생 - {error_msg}")
            return {
                'success': False,
                'message': error_msg,
                'output_path': None
            }

# 'ffmpeg' 대신 ffmpeg_executable='ffmpeg' 사용하는 이유는,
# 1. 윈도우 환경: FFmpeg가 PATH에 없을 수 있고,
# 2. 절대 경로를 지원하기 위해서 (C:\Program Files\ffmpeg\bin\ffmpeg.exe)
# 3. 여러 경로에서 FFmpeg를 사용할 수 있게 하기 위해서 (자동으로 탐지)
