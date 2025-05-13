import os
from utils.utils import extract_video_segment

print("test.py 시작")

# 경로에 raw string(r) 표시를 사용하거나 이중 백슬래시(\\)를 사용
input_file = r".\12475366_임란전 (1) SF.avi"
output_file = r".\output.avi"

# 파일 존재 여부 확인
if not os.path.exists(input_file):
    print(f"입력 파일을 찾을 수 없습니다: {input_file}")

# 3초부터 5초까지 추출
result = extract_video_segment(input_file, output_file, "00:00:03", "00:00:05")
if result:
    print("비디오 세그먼트 추출 성공")
else:
    print("비디오 세그먼트 추출 실패")
