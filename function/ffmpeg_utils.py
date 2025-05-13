import os
import subprocess


def extract_video_segment(input_video_path, output_video_path, start_time, end_time):
    """
    주어진 시간 범위에 해당하는 비디오 세그먼트를 추출하는 함수

    input_path: 입력 비디오 파일 경로
    output_path: 출력 비디오 파일 경로
    start_time: 시작 시간 (HH:MM:SS)
    end_time: 종료 시간 (HH:MM:SS)

    returns: 
        bool 성공여부부
    """

    # ffmpeg 명령어 구성
    command = [
        'ffmpeg',
        '-i', input_video_path,
        '-ss', str(start_time),
        '-to', str(end_time),
        '-c', 'copy',  # 코덱 복사
        output_video_path
    ]

    # 명령어 출력
    command_str = ' '.join(command)
    print(f"Executing command: {command_str}")

    # 명령어 실행
    try:
        subprocess.run(command, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"오류 발생: {e}")
        return False

# ffmpeg -i input.mp4 -ss 00:04:40 -to 00:04:50 output.mp4
# 'codec="copy"' applies to both video and audio. Work as the line -vcodec -acodec in FFmpeg.
# # Without the codec line, the video quality is not assured.
