import tkinter as tk  # gui 모듈 포함하여 import
from tkinter import ttk  # 테이블 모듈 포함하여 import
from tkinter import filedialog  # 파일선택 지원
import os
import cv2
from PIL import Image, ImageTk
import threading
from ui_components import create_tabs
from utils.utils import VideoUtils
from ui_components.preview_window import PreviewWindow


class VideoEditorApp:
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
        self.current_image = None  # show_frame 함수에서 사용할 이미지 참조용용
        self.video_label = None  # 비디오 표시 레이블

        # 구간 선택 변수
        self.start_time = 0
        self.end_time = 0

        self.ui = create_tabs(self.root, self)

        print("App 초기화 완료")

    def open_file(self):

        file_path = filedialog.askopenfilename(
            # initialdir="C:/Users/user/Documents/cursor_video_save",
            title="비디오 파일 선택창",
            filetypes=[("Video Files", "*.mp4 *.avi")]
        )

        if file_path:
            self.video_path = file_path
            if self.initialize_video():
                self.get_video_info(self.video_path)
            else:
                # 비디오 초기화 실패 시 오류 메시지 표시
                print("비디오 초기화 실패")

    def initialize_video(self):
        '''OpenCV로 비디오 캡쳐 객체 초기화'''

        if self.cap is not None:
            self.cap.release()

        self.cap = cv2.VideoCapture(self.video_path)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)

        if not self.cap.isOpened():
            print("비디오 파일을 열 수 없습니다.")
            return False

        print(f"Video opened: {self.cap.isOpened()}")  # 비디오 열기 성공 여부
        self.show_frame(0)
        return True

    def get_video_info(self, video_path):
        """OpenCV로 비디오 정보 확인 """

        if self.cap and self.cap.isOpened():

            # 비디오 속성 가져오기
            props = VideoUtils.get_video_properties(self.cap)

            # 속성 저장
            self.frame_count = props['frame_count']
            self.video_length = props['length']
            self.width = props['width']
            self.height = props['height']

            # 비디오 정보 표시
            self.video_name = os.path.basename(video_path)

            # UI 요소 업데이트 (create_ui 함수 구현에 따라 수정 필요)
            self.video_info_label.config(
                text=f"비디오 이름: {self.video_name}\n"
                     f"프레임 레이트: {self.fps}\n"
                     f"동영상 길이: {self.video_length}초\n"
                     f"동영상 해상도: {self.width} x {self.height}"
            )

            # 슬라이더 범위 설정
            self.position_slider.config(to=self.video_length)

            # 초기 종료 위치 비디오 끝으로 설정
            self.end_time_label.config(
                text=VideoUtils.format_time(self.video_length))
            self.end_time = self.video_length

            # 비디오의 첫 프레임(0)으로 위치 설정
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            # 현재 프레임 읽기기
            ret, frame = self.cap.read()
            # ret: 프레임 읽기 성공 여부 (True/False)
            # frame: 실제 이미지 데이터 (numpy array)
            if ret:
                self.show_frame(frame)
            return True

        else:
            print(f"Error: Could not open video file {video_path}")
            return False

    def toggle_play(self):
        '''비디오 재생/일시정지 버튼 클릭 시 호출'''
        if not self.is_playing:
            self.is_playing = True
            self.play_button.config(text="⏸")  # 일시정지 버튼으로 변경
            # 재생 중에는 구간 설정 버튼 비활성화
            self.set_start_button.config(state=tk.DISABLED)
            self.set_end_button.config(state=tk.DISABLED)
            self.update_video()
        else:
            self.is_playing = False
            self.play_button.config(text="▶")  # 재생 버튼으로 변경
            # 일시정지 상태에서는 구간 설정 버튼 활성화
            self.set_start_button.config(state=tk.NORMAL)
            self.set_end_button.config(state=tk.NORMAL)

    def stop_video(self):
        """비디오 중지 버튼 클릭시 호출"""
        self.is_playing = False
        self.play_button.config(text="▶")
        # 비디오를 처음으로 되돌리기 위해, 프레임을 0으로 지정
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        self.show_frame(0)
        # 슬라이더 위치 초기화
        self.position_slider.set(0)
        self.position_label.config(text="00:00")

    def show_frame(self, frame):
        """프레임 화면에 표시"""
        if isinstance(frame, int):  # frame 매개변수가 정수(integer)인지 확인하는 조건문
            # 프레임 번호를 프레임 데이터로 변환
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame)
            ret, frame = self.cap.read()
            if not ret:
                print(f"Error: Could not read frame {frame}")
                return

        # 프레임을 PhotoImage로 변환 (유틸리티 함수 사용)
        photo = VideoUtils.convert_frame_to_photo(frame)

        # 코드상 중요 라인!! -> 이미지 객체 참조를 저장
        self.current_image = photo  #
        # 매 프레임마다 self.current_image에 새 이미지 참조가 저장되고, 이전 이미지 참조는 자동으로 가비지 컬렉션 대상
        # 메모리 관리 측면에서, 항상 최신 프레임만 저장하고 메모리가 한 프레임 분량만 사용.

        # 이미지를 비디오 레이블에 표시
        if self.video_label is None:
            # video_frame은 create_tabs에서  이미 생성된 프레임어야 함
            if hasattr(self, "video_frame") and self.video_frame is not None:
                print("비디오 레이블 생성 중 ...")
                self.video_label = tk.Label(self.video_frame)
                self.video_label.pack(expand=True, fill="both")
            else:
                print("Warning: 'video_frame' not found, video label을 생성할 수 없습니다.")
                return

        # 이미지 업데이트
        self.video_label.config(image=photo)

    def update_video(self):
        """비디오 프레임 업데이트"""
        if self.is_playing and self.cap is not None:
            ret, frame = self.cap.read()
            if ret:
                self.show_frame(frame)
                # 슬라이더/현재 위치 업데이트
                current_pos = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
                current_time = current_pos / self.fps

                # UI 업데이트
                self.position_slider.set(current_time)
                # 현재 시간 레이블 업데이트
                self.position_label.config(
                    text=VideoUtils.format_time(int(current_time)))

                # 종료 시간에 도달했는지 확인
                if current_time >= self.end_time and self.is_playing:
                    self.is_playing = False
                    self.is_previewing = False
                    self.play_button.config(text="▶")
                    return

                # 다음 프레임 예약
                delay = int(1000 / self.fps)
                self.root.after(delay, self.update_video)

            else:
                # 비디오 끝에 다다르면 재생 중지
                self.is_playing = False
                self.play_button.config(text="▶")
                # 구간 미리보기가 아닐경우, 처음으로 되돌리기
                if not self.is_previewing:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    self.show_frame(0)

    def set_start_time(self):
        '''시작 시간 지정'''
        value = self.position_slider.get()
        self.start_time = float(value)
        self.start_time_label.config(
            text=VideoUtils.format_time(int(self.start_time)))

    def set_end_time(self):
        '''종료 시간 지정 '''
        value = self.position_slider.get()
        self.end_time = float(value)
        self.end_time_label.config(
            text=VideoUtils.format_time(int(self.end_time)))

    def select_position(self, value):
        '''슬라이더 값 변경 시 호출되는 함수'''
        if self.cap is None:
            return

        value = float(value)
        frame_num = int(value * self.fps)

        # 프레임 표시
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = self.cap.read()
        if ret:
            self.show_frame(frame)

            # 현재 위치 시간 업데이트
            current_time = VideoUtils.format_time(value)
            self.position_label.config(text=f"현재 위치: {current_time}")

    def preview_selection(self):
        '''선택구간 미리보기" 버튼을 눌렀을 때 호출되는 함수 (UI 이벤트 핸들러)'''
        if not self.cap or self.video_path == "":
            tk.messagebox.showwarning("경고", "비디오를 먼저 로드해주세요.")
            return

        if self.start_time >= self.end_time:
            tk.messagebox.showwarning("경고", "시작 시간이 종료 시간보다 크거나 같습니다.")
            return

        # 새 미리보기 창 생성
        preview_window = PreviewWindow(
            self.root,
            self,  # 앱 자체를 참조로 전달
            self.video_path,
            self.start_time,
            self.end_time
        )

    def preview_selection(self):

        if not self.cap or self.video_path is None:
            return

        # 현재 재생중이면 중지
        self.is_previewing = False
        self.play_button.config(text="재생")

        # 미리보기 시작
        self.is_previewing = True
        self.play_button.config(text="일시정지")
        # 미리보기 스레드 시작
        threading.Thread(target=self.play_selection, daemon=True).start()

    def play_selection(self):
        """선택 구간만 재생"""
        if not self.cap or self.fps is None:
            return

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, int(self.start_time * self.fps))
        current_time = self.start_time

        self.is_playing = True
        while self.is_playing and current_time <= self.end_time:
            ret, frame = self.cap.read()
            if not ret:
                break
            self.show_frame(frame)
            current_time += 1 / self.fps
            self.position_slider.set(current_time)
            self.position_label.config(
                text=VideoUtils.format_time(current_time))
            self.root.update()
            self.root.after(int(1000 / self.fps))
        self.is_playing = False
        self.play_button.config(text="▶")

    def get_saved_segments(self):
        """저장된 구간 목록 반환"""
        return self.saved_segments
