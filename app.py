def __init__(self, root):
    self.root = root  # root를 self.root로 저장
    self.root.title("비디오 부분 추출 App")
    self.root.geometry("1000x1000")
    self.root.resizable(True, True)

    # 비디오 관련 변수
    self.video_path = ""
    self.cap = None
    self.fps = None
    self.frame_count = 0
    self.video_length = 0
    self.current_frame = None

    # 재생 관련 변수
    self.is_playing = False
    self.current_image = None  # show_frame 함수에서 사용할 이미지 참조용
    self.video_label = None  # 비디오 표시 레이블

    # 구간 선택 변수
    self.start_time = 0
    self.end_time = 0

    # 저장된 구간 목록 초기화
    self.saved_segments = []

    self.ui = create_tabs(self.root, self)

    print("App 초기화 완료")


def register_segment_update_callback(self, callback):
    """구간 업데이트 콜백 등록 (호환성을 위해 유지)"""
    pass


def unregister_segment_update_callback(self, callback):
    """구간 업데이트 콜백 제거 (호환성을 위해 유지)"""
    pass


def save_segment(self, segment):
    """구간 저장 (단순화된 버전)"""
    print(f"save_segment 호출됨: {segment}")
    self.saved_segments.append(segment)
    print(f"현재 저장된 구간 수: {len(self.saved_segments)}")
