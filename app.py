import os
import cv2
import numpy as np
import csv
from PIL import Image, ImageTk
import threading

import tkinter as tk  # gui 모듈 포함하여 import
import ttkbootstrap as ttk  # ttkbootstrap으로 변경
from ttkbootstrap.constants import *  # Bootstrap 스타일 상수들
from tkinter import messagebox, filedialog
from utils.styles import AppStyles
from utils.utils import VideoUtils, AudioPlayer
from ui_components import create_tabs
from ui_components.preview_window import PreviewWindow
from utils.ui_utils import UiUtils
from utils.event_system import event_system, Events


class VideoEditorApp:
    def __init__(self, root):
        self.root = root  # root를 self.root로 저장
        self.root.title("비디오 편집기")
        system_scale = UiUtils.get_scaling_factor_by_dpi(root)
        self.root.geometry(
            f"{int(1400 * system_scale)}x{int(900 * system_scale)}+{0}+{0}")
        self.root.resizable(True, True)

        # ttkbootstrap 스타일 객체 생성
        style = ttk.Style()  # theme 인자 제거
        AppStyles.configure_styles(style)  # 스타일 객체를 전달하여 사용자 정의 스타일 설정

        # 비디오 관련 변수
        self.video_path = ""
        self.cap = None
        self.fps = None
        self.frame_count = 0
        self.video_length = 0
        self.current_frame = 0

        # 재생 관련 변수
        self.is_playing = False
        self.current_image = None  # show_frame 함수에서 사용할 이미지 참조용용
        self.video_label = None  # 비디오 표시 레이블

        # 오디오 플레이어 초기화
        self.audio_player = AudioPlayer()

        # 구간 선택 변수
        self.start_time = 0
        self.end_time = 0

        # 저장된 구간 목록 초기화
        self.saved_segments = []

        self.ui = create_tabs(self.root, self)

        # 이벤트 리스너 등록
        self.setup_event_listeners()

        print("App 초기화 완료")

    def setup_event_listeners(self):
        """이벤트 리스너 설정"""
        event_system.subscribe(Events.VIDEO_LOADED, self._on_video_loaded)
        event_system.subscribe(
            Events.VIDEO_PLAY_TOGGLE, self.handle_play_toggle)
        event_system.subscribe(Events.VIDEO_STOP, self.stop_video)
        event_system.subscribe(Events.SEGMENT_START_SET, self.set_start_time)
        event_system.subscribe(Events.SEGMENT_END_SET, self.set_end_time)

    def _on_video_loaded(self, **kwargs):
        """비디오 로드 이벤트 처리"""
        file_path = kwargs.get('path')
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
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # UI 업데이트 이벤트 발행
        event_system.emit(Events.UI_UPDATE,
                          video_path=self.video_path,
                          duration=self.video_length,
                          fps=self.fps,
                          total_frames=self.total_frames)

        # 플레이어 상태 변경 이벤트 발행 (정지 상태, 준비 완료)
        event_system.emit(Events.PLAYER_STATE_CHANGED,
                          is_playing=False, is_stopped=True)

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
                text=f"구간 종료: {VideoUtils.format_time(self.video_length)}")
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

    def handle_play_toggle(self, **kwargs):
        """재생/일시정지 토글 이벤트 처리"""
        if self.is_playing:
            self.pause_video()
        else:
            self.play_video()

    def play_video(self):
        """비디오 재생"""
        if not self.is_playing and self.cap:
            self.is_playing = True

            # 오디오 재생 시작
            if self.video_path and self.audio_player.is_initialized:
                # 현재 비디오 위치 가져오기
                current_pos = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
                current_time = current_pos / self.fps if self.fps > 0 else 0

                # 오디오 로드 및 재생
                if self.audio_player.load_audio_from_video(self.video_path, current_time, self.video_length):
                    self.audio_player.play()

            event_system.emit(Events.PLAYER_STATE_CHANGED,
                              is_playing=True, is_stopped=False)
            self.update_frames()

    def pause_video(self):
        """비디오 일시정지"""
        if self.is_playing:
            self.is_playing = False

            # 오디오 일시정지
            if self.audio_player.is_initialized:
                self.audio_player.pause()

            # 이 로직은 UI 업데이트 이벤트로 처리되어야 함 -> _on_player_state_changed 메서드에서 처리
            # self.play_button.config(text="► 재생")  # 재생 아이콘
            # 일시정지 상태에서 구간 설정 버튼 활성화
            # self.set_start_button.config(state=tk.NORMAL)
            # self.set_end_button.config(state=tk.NORMAL)
            # 구간이 올바르게 설정되어 있으면 저장 버튼도 활성화
            self.update_save_button_state()
            event_system.emit(Events.PLAYER_STATE_CHANGED,
                              is_playing=False, is_stopped=False)

    def stop_video(self, **kwargs):
        """비디오 정지"""
        if self.cap:
        self.is_playing = False

           # 오디오 정지
           if self.audio_player.is_initialized:
                self.audio_player.stop()

            event_system.emit(Events.PLAYER_STATE_CHANGED,
                              is_playing=False, is_stopped=True)

            # 비디오를 처음으로 되돌리기
        if self.cap is not None and self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

            # 슬라이더 위치 초기화 - 이 로직은 UI 업데이트 이벤트로 처리되어야 함 -> _on_player_state_changed 메서드에서 처리
            # self.position_slider.set(0)
            # self.position_label.config(text="00:00")

    def update_frames(self):
        """비디오 프레임 업데이트"""
        if self.is_playing and self.cap is not None and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                self.show_frame(frame)

                # UI 업데이트 (슬라이더 및 시간표시)
                current_pos = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
                current_time = current_pos / self.fps

                self.position_slider.set(current_time)
                # 현재 시간 레이블 업데이트
                self.position_label.config(
                    text=VideoUtils.format_time(int(current_time)))

                # 종료 시간에 도달했는지 확인
                if current_time >= self.end_time and self.is_playing:
                    self.is_playing = False
                    self.is_previewing = False
                    self.play_button.config(text="► 재생")
                    return

                # 다음 프레임 예약
                delay = int(1000 / self.fps)
                self.root.after(delay, self.update_frames)

            else:
                # 비디오 끝에 다다르면 재생 중지
                self.is_playing = False
                self.play_button.config(text="► 재생")
                # 구간 미리보기가 아닐경우, 처음으로 되돌리기
                if not hasattr(self, 'is_previewing') or not self.is_previewing:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    self.show_frame(0)

    def show_frame(self, frame):
        """프레임 화면에 표시"""

        try:
            # 유연한 입력 처리 유지
            if isinstance(frame, int):  # frame 매개변수가 정수(integer)인지 확인하는 조건문
                # 프레임 번호를 프레임 데이터로 변환
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame)
                ret, frame = self.cap.read()
                if not ret:
                    print(f"Error: Could not read frame {frame}")
                    return

            # 이미지를 비디오 레이블에 표시. 동적 레이블 생성 유지
            if self.video_label is None:
                # video_frame은 create_tabs에서  이미 생성된 프레임어야 함
                if hasattr(self, "video_frame") and self.video_frame is not None:
                    print("비디오 레이블 생성 중 ...")
                    self.video_label = tk.Label(self.video_frame)
                    self.video_label.pack(expand=True, fill="both")
                else:
                    print("Warning: 'video_frame' not found, video label을 생성할 수 없습니다.")
                    return

            photo = VideoUtils.convert_frame_to_photo(frame)

            # 메모리 관리 유지 측면상 중요한 코드 라인!! -> 이미지 객체 참조를 저장
            self.current_image = photo
            # 매 프레임마다 self.current_image에 새 이미지 참조가 저장되고, 이전 이미지 참조는 자동으로 가비지 컬렉션 대상
            # 메모리 관리 측면에서, 항상 최신 프레임만 저장하고 메모리가 한 프레임 분량만 사용.

            # 이미지 업데이트
            self.video_label.config(image=photo)
            self.video_label.image = photo  # 중복 참조로 더 안전

        except Exception as e:
            print(f"Error in showing frame: {e}")
            import traceback
            traceback.print_exc()  # 상세한 에러 정보

    def set_start_time(self, time: float):
        """시작 시간 지정 (이벤트 핸들러)"""
        self.start_time = time
        self.start_time_label.config(
            text=f"구간 시작: {VideoUtils.format_time(int(self.start_time))}")
        self.update_save_button_state()

    def set_end_time(self, time: float):
        """종료 시간 지정 (이벤트 핸들러)"""
        self.end_time = time
        self.end_time_label.config(
            text=f"구간 종료: {VideoUtils.format_time(int(self.end_time))}"
        )
        self.update_save_button_state()

    def update_save_button_state(self):
        """구간 저장 버튼 활성화/비활성화 상태 업데이트"""
        # 구간 유효성만 확인 (비디오 로드 시 이미 유효한 초기값이 설정됨)
        if hasattr(self, 'start_time') and hasattr(self, 'end_time') and \
           self.start_time < self.end_time:
            self.save_segment_button.config(state=tk.NORMAL)
        else:
            self.save_segment_button.config(state=tk.DISABLED)

    def select_position(self, value):
        '''슬라이더 값 변경 시 호출되는 함수'''
        if self.cap is None or not self.cap.isOpened():
            return

        try:
            value = float(value)  # 슬라이더 값은 초 단위
            frame_num = int(value * self.fps)

            # 프레임 번호 계산 (초 * fps)
            target_frame = frame_num
            total_frames = self.cap.get(cv2.CAP_PROP_FRAME_COUNT)

            # 프레임 범위 체크
            if target_frame < 0:
                target_frame = 0
            elif target_frame >= total_frames:
                target_frame = int(total_frames - 1)

            # 디버깅용 프린트문
            # print(f"slider_value: {value}, target frame: {target_frame}/{total_frames}")

            # 프레임 위치 설정 및 표시
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            # cv2.CAP_PROP_POS_FRAMES는 "다음에 읽을(Grab할) 프레임의 인덱스"를 나타내는 프로퍼티(property) 상수
            # 현재 동영상 스트림의 읽기 위치(다음에 읽을 프레임 번호)를 target_frame(정수) 번째 프레임으로 옮기라는 의미

            # 현재 캡쳐 객체의 다음 프레임을 가져와 디코딩.
            ret, frame = self.cap.read()
            # ret: 프레임 읽기 성공 여부 (True/False)
            # frame: 실제 이미지 데이터 (numpy array)

            if ret:
                self.show_frame(frame)

                # 실제 현재 시간 계산 (프레임 기반)
                current_frame = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
                current_time_secs = current_frame / self.fps

                # 오디오 위치 동기화 (재생 중이 아닐 때만)
                if not self.is_playing and self.audio_player.is_initialized:
                    self.audio_player.set_position(current_time_secs)

                # UI 업데이트
                current_time_str = VideoUtils.format_time(
                    int(current_time_secs))
                self.position_label.config(text=current_time_str)

                # 현재 시간을 인스턴스 변수에 저장 (다른 메서드에서 사용할 수 있도록)
                self.current_time_str = current_time_secs

            else:
                print(f"Failed to read frame {target_frame}")

        except Exception as e:
            print(f"Error in select_position: {str(e)}")
            import traceback
            traceback.print_exc()  # 상세한 에러 정보

    def _validate_selection(self):
        """구간 선택 유효성 검사 공통 메서드"""
        # 비디오 로드 여부 확인
        if not self.cap or not hasattr(self, "video_path") or self.video_path == "":
            tk.messagebox.showwarning("경고", "비디오를 먼저 로드해주세요.")
            return False

        # start_time과 end_time이 설정되었는지 확인
        if not hasattr(self, 'start_time') or not hasattr(self, 'end_time'):
            tk.messagebox.showwarning("경고", "시작 시간과 종료 시간을 먼저 설정해주세요.")
            return False

        # 구간 유효성 검사
        if self.start_time >= self.end_time:
            tk.messagebox.showwarning("경고", "시작 시간이 종료 시간보다 크거나 같습니다.")
            return False

        # 구간 길이가 너무 짧은지 확인
        if (self.end_time - self.start_time) < 0.1:  # 0.1초 미만
            tk.messagebox.showwarning("경고", "선택 구간이 너무 짧습니다. (최소 0.1초)")
            return False

        return True

    def preview_selection(self):
        '''선택구간 미리보기 버튼을 눌렀을 때 호출되는 함수 (UI 이벤트 핸들러)로 미리보기 창 생성'''

        # 공통 검증 메서드 사용
        if not self._validate_selection():
            return

        # 이미 열린 미리보기 창이 있다면 닫기
        if hasattr(self, 'preview_window') and self.preview_window is not None:
            try:
                self.preview_window.window.destroy()
            except:
                pass

        # 새 미리보기 창 생성 및 인스턴스 유지
        try:
            # 비디오 경로가 StringVar인 경우 처리
            video_path = self.video_path
            if hasattr(video_path, "get"):  # StringVar인 경우
                video_path = video_path.get()

            print(
                f"미리보기 생성중: 파일경로{video_path}, 구간시작:{self.start_time}, 구간종료:{self.end_time}")

            self.preview_window = PreviewWindow(
                self.root,  # 메인 윈도우(root) 를 부모로 전달
                self,  # App instance를 참조로 전달
                video_path,
                self.start_time,
                self.end_time
            )

            # 미리보기 창이 닫힐 때 참조 제거
            self.preview_window.window.protocol("WM_DELETE_WINDOW",
                                                lambda: self._on_preview_window_close())
            # _on_preview_window_close() 는 함수 자체가 아니라, 함수를 실행하는 명령어.

        except Exception as e:
            print(f"미리보기 창 생성 오류: {str(e)}")
            import traceback
            traceback.print_exc()
            tk.messagebox.showerror("오류", f"미리보기 창 생성 중 오류가 발생했습니다:\n{str(e)}")

    def _on_preview_window_close(self):
        """미리보기 창이 닫힐 때 호출되는 콜백 함수"""
        if hasattr(self, 'preview_window') and self.preview_window is not None:
            # ui_components/preview_window.py 파일안 280-310 줄에 on_close() 메서드 정의되어 있음
            self.preview_window.on_close()
            self.preview_window = None

    def play_selection(self):
        """선택 구간만 재생 (비동기 방식으로 수정)"""
        # 공통 검증 메서드 사용
        if not self._validate_selection():
            return

        if not self.cap or not self.cap.isOpened() or self.fps is None:
            return

        # 구간 시작 위치로 이동
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, int(self.start_time * self.fps))

        # 구간 재생 모드 설정
        self.is_playing = True
        self.is_previewing = True  # 구간 재생 중임을 표시
        self.play_button.config(text="|| 일시정지")

        # 비동기 업데이트 시작
        self.update_frames()

    def stop_selection_play(self):
        """구간 재생 중지"""
        self.is_playing = False
        self.is_previewing = False  # 구간 재생 상태 관리
        self.play_button.config(text="► 재생")

    def get_saved_segments(self):
        """저장된 구간 목록 반환"""
        # init 메서드 안에서 saved segments 리스트 초기화 되어 있음
        return self.saved_segments

    def save_segment(self, segment, parent_window=None):
        """구간데이터를 받아서 저장하는 로직 (개선된 버전) - 중복체크 로직 있는 메서드"""
        print(f"save_segment 호출됨: {segment}")

        # 중복 체크 추가
        for existing_segment in self.saved_segments:
            if (abs(existing_segment['start'] - segment['start']) < 0.1) and \
               (abs(existing_segment['end'] - segment['end']) < 0.1):
                if parent_window:
                    # 부모 창 위로 메세지 표시하여 UX 개선
                    messagebox.showinfo(
                        "💡알림", "이미 동일한 구간이 저장되어 있습니다.", parent=parent_window)
                else:
                    messagebox.showinfo("💡알림", "이미 동일한 구간이 저장되어 있습니다.")
                return False

        # 구간 저장
        self.saved_segments.append(segment)  # 여기서만 구간 추가
        print(f"현재 저장된 구간 수: {len(self.saved_segments)}")

        # UI 업데이트 및 알림 추가
        self.update_all_tables()
        # 부모창이 존재하면, 부모 창 위로 메세지 표시하여 UX 개선. 없으면 메인 탭 위로 메세지 표시.
        if parent_window:
            messagebox.showinfo("💡알림", "구간이 저장되었습니다!", parent=parent_window)
        else:
            messagebox.showinfo("💡알림", "구간이 저장되었습니다!")
        return True

    # save_current_segment 메서드에서 분리
    def create_segment_data(self, video_path, start_time, end_time):
        """구간 데이터 생성 공통 메서드"""
        return {
            'file': os.path.basename(video_path),
            'start': start_time,
            'end': end_time,
            'duration': end_time - start_time,
            'type': os.path.splitext(os.path.basename(video_path))[0][-2:],
            'opinion1': '',  # PAS 칼럼
            'opinion2': ''   # 잔여물 칼럼
        }

    def save_current_segment(self, video_path=None, parent_window=None):
        """현재 선택된 구간을 저장하는 중앙화된 메서드"""
        # 재생 중이면 먼저 중지 (저장되었다는 의미로)
        if self.is_playing:
            self.is_playing = False
            self.play_button.config(text="► 재생")

        if self.start_time >= self.end_time:
            if parent_window:
                messagebox.showwarning(
                    "경고", "올바른 구간을 선택해주세요.\n시작 시간이 종료 시간보다 늦습니다.",
                    parent=parent_window)
            else:
                messagebox.showwarning(
                    "경고", "올바른 구간을 선택해주세요.\n시작 시간이 종료 시간보다 늦습니다.")
            return None

        # 비디오 경로 처리 (공통 메서드 사용)
        if not video_path:
            video_path = VideoUtils.get_video_path_from_app(self)

        if not video_path:
            if parent_window:
                messagebox.showerror(
                    "오류", "비디오 파일이 선택되지 않았습니다.", parent=parent_window)
            else:
                messagebox.showerror("오류", "비디오 파일이 선택되지 않았습니다.")
            return None

        # 구간 데이터 생성
        segment_data = self.create_segment_data(
            video_path, self.start_time, self.end_time)

        # 구간 저장
        self.saved_segments.append(segment_data)
        print(f"구간 저장됨: {segment_data}")

        # 모든 테이블 새로고침 (NewTab 포함)
        self.update_all_tables()

        # 구간 저장 완료 메시지 표시
        if parent_window:
            messagebox.showinfo("💡알림", "구간이 저장되었습니다!", parent=parent_window)
        else:
            messagebox.showinfo("💡알림", "구간이 저장되었습니다!")

        return segment_data

    def update_all_tables(self):
        """모든 탭의 테이블을 업데이트하는 중앙화된 메서드"""
        try:
            # NewTab(비디오 추출 탭) 테이블 업데이트
            if hasattr(self, 'new_tab_instance'):
                self.new_tab_instance.refresh_table()
                print("✅ 비디오 추출 탭 테이블 업데이트 완료")

            # 다른 탭들이 있다면 여기에 추가
            # if hasattr(self, 'other_tab_instance'):
            #     self.other_tab_instance.refresh_table()

        except Exception as e:
            print(f"테이블 업데이트 중 오류: {e}")
