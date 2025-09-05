import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, filedialog
import os
import cv2
import threading
import csv
from datetime import datetime
from utils.styles import AppStyles
from utils.ui_utils import UiUtils
from utils.utils import VideoUtils, _parse_time_to_seconds
from utils.vlc_utils import VLCPlayer
from utils.event_system import event_system, Events
from ui_components import create_tabs
from ui_components.preview_window import PreviewWindow


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

        # 비디오 플레이어 초기화
        self.video_player = None

        # 구간 선택 변수
        self.start_time = 0
        self.end_time = 0

        # 저장된 구간 목록 초기화
        self.saved_segments = []

        self.ui = create_tabs(self.root, self)

        # 이벤트 리스너 등록
        self.setup_event_listeners()

        # 애플리케이션 종료 시 VLC 정리
        self.root.protocol("WM_DELETE_WINDOW", self._handle_close)

        print("App 초기화 완료")

    def _handle_close(self):
        """애플리케이션 종료 시 VLC 정리"""
        # VLC 플레이어 정리
        print("App: 종료 프로세스 시작...")
        if hasattr(self, 'vlc_player') and self.vlc_player:
            self.vlc_player.cleanup()
            print("App: VLC 플레이어 리소스 정리 완료")
        self.root.quit()
        self.root.destroy()
        print("App: 종료 프로세스 완료")

    def setup_event_listeners(self):
        """이벤트 리스너 설정"""
        event_system.subscribe(Events.VIDEO_LOADED, self._on_video_loaded)
        print(f"[app.py] event_system id: {id(event_system)}")
        event_system.subscribe(
            Events.VIDEO_PLAY_TOGGLE, self.handle_play_toggle)
        event_system.subscribe(Events.VIDEO_STOP, self.stop_video)
        event_system.subscribe(Events.SEGMENT_START_SET, self.set_start_time)
        event_system.subscribe(Events.SEGMENT_END_SET, self.set_end_time)

    def _on_video_loaded(self, **kwargs):
        """비디오 로드 이벤트 처리하고 VLC 플레이어 초기화"""

        print(f"_on_video_loaded called, kwargs={kwargs}")
        file_path = kwargs.get('path')

        if not file_path:
            print("App: 파일경로 없음")
            return False

        if file_path:
            self.video_path = file_path

            try:
                # 1. video_canvas가 생성되어 있는지 확인
                if not self._validate_video_canvas():
                    return False
                # 2. VLCPlayer 인스턴스 생성
                if not self._create_vlc_player():
                    return False
                # 3. video_canvas를 VLC 플레이어에 연결
                if not self._connect_canvas_to_vlc():
                    return False
                self._load_video_async()
                print("App: 비디오 로드 요청 완료 (비동기처리)")
                return True
            except Exception as e:
                print(f"App: 비디오 로드 중 오류 발생 {e}")
                import traceback
                traceback.print_exc()
                return False

    def _validate_video_canvas(self):
        """video_canvas가 생성되어 있는지 확인"""

        if not hasattr(self, 'video_canvas') or not self.video_canvas:
            print("App: video_canvas가 아직 생성되지 않음. UI 초기화를 기다립니다.")
            return False
        return True

    def _create_vlc_player(self):
        """VLCPlayer 인스턴스 생성 및 제대로 초기화 되었는지 확인"""

        # VLCPlayer 인스턴스 생성
        if not hasattr(self, 'vlc_player') or not self.vlc_player:
            print("App: VLCPlayer 인스턴스 생성")
            self.vlc_player = VLCPlayer()
            # 외부 체커 제거: VLC/FFmpeg 안내는 생략

        # VLC 플레이어가 제대로 초기화되었는지 확인
            if not self.vlc_player or not hasattr(self.vlc_player, 'media_player') or not self.vlc_player.media_player:
                print("App: VLC 플레이어 초기화 실패")
                return False
        return True

    def _connect_canvas_to_vlc(self):
        """video_canvas를 VLC 플레이어에 연결"""
        try:
            print("App: video_canvas를 VLC 플레이어에 연결")
            self.vlc_player.set_video_widget(self.video_canvas)
            return True

        except Exception as e:
            print(f"App: video_canvas를 VLC 플레이어에 연결 중 오류 발생: {e}")
            return False

    def _load_video_async(self):
        """별도 스레드에서 비디오 로드 처리 (UI 블록 방지)"""

        def load_video_async():
            print("App: 비디오 로드 시작")
            try:
                if self.vlc_player.load_video(self.video_path):
                    # UI 업데이트는 메인 스레드에서 처리
                    self.root.after(0, lambda: event_system.emit(
                        Events.UI_UPDATE,
                        video_path=self.video_path,
                        duration=self.vlc_player.duration,
                        component="video_info"
                    ))
                else:
                    print("App: 비디오 로드 실패")
            except Exception as e:
                print(f"App: 비동기 비디오 로드 오류: {e}")

        # 비동기로 비디오 로드
        threading.Thread(target=load_video_async, daemon=True).start()

    def handle_play_toggle(self, **kwargs):
        """재생/일시정지 토글 이벤트 처리"""
        if self.is_playing:
            self.pause_video()
        else:
            self.play_video()

    def play_video(self):
        """VLC 전용 비디오 재생"""
        if self.vlc_player and not self.is_playing:
            self.vlc_player.play()
            self.is_playing = True

    def pause_video(self):
        """VLC 전용 비디오 일시정지"""
        if self.vlc_player and self.is_playing:
            self.vlc_player.pause()
            self.is_playing = False

    def stop_video(self):
        """VLC 전용 비디오 정지"""
        if self.vlc_player:
            self.vlc_player.stop()
            self.is_playing = False

    # OpenCV 관련 메서드들은 제거 (이미지 추출은 별도 모듈에서 처리)
    # update_frames, show_frame 등은 VLC가 자체 처리하므로 불필요

    def get_video_info(self, video_path):
        """VLC로 비디오 정보 확인"""
        if self.vlc_player:
            video_info = self.vlc_player.get_video_info()
            if video_info:
                self.video_length = video_info.get('duration', 0)
                self.video_name = os.path.basename(video_path)
                return True

        print(f"Error: VLC 비디오 정보를 가져올 수 없습니다.")
        return False

    def _get_ui_components(self):
        """UI 컴포넌트들 참조 가져오기"""
        # UI 컴포넌트들을 담을 객체 생성
        class UIComponents:
            pass

        ui_components = UIComponents()

        # UI 컴포넌트들 참조 설정
        if hasattr(self, 'position_slider'):
            ui_components.position_slider = self.position_slider
        if hasattr(self, 'slider_label'):
            ui_components.slider_label = self.slider_label
        if hasattr(self, 'end_time_label'):
            ui_components.end_time_label = self.end_time_label
        if hasattr(self, 'video_info_label'):
            ui_components.video_info_label = self.video_info_label

        ui_components.video_path = self.video_path

        return ui_components

    def set_start_time(self, time: float):
        """시작 시간 지정 - 이벤트 데이터를 받아서 처리하는 이벤트 핸들러"""
        print(f"DEBUG: set_start_time 호출됨 - 받은 시간: {time}초")
        self.start_time = time
        print(f"DEBUG: self.start_time 설정됨: {self.start_time}초")
        # UI 업데이트트
        self.start_time_label.config(
            text=f"구간 시작: {VideoUtils.format_time(int(self.start_time))}")
        print(
            f"DEBUG: UI 라벨 업데이트됨: {VideoUtils.format_time(int(self.start_time))}")
        # 버튼 상태 관리리
        self.update_save_button_state()

    def set_end_time(self, time: float):
        """종료 시간 지정 - 이벤트 데이터를 받아서 처리하는 이벤트 핸들러"""
        print(f"DEBUG: set_end_time 호출됨 - 받은 시간: {time}초")
        self.end_time = time
        print(f"DEBUG: self.end_time 설정됨: {self.end_time}초")
        self.end_time_label.config(
            text=f"구간 종료: {VideoUtils.format_time(int(self.end_time))}"
        )
        print(
            f"DEBUG: UI 라벨 업데이트됨: {VideoUtils.format_time(int(self.end_time))}")
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
        '''VLC 전용 슬라이더 값 변경'''
        if self.vlc_player:
            self.vlc_player.set_position(float(value))

    def _validate_selection(self):
        """구간 선택 유효성 검사 공통 메서드"""
        # 비디오 로드 여부 확인
        if not self.vlc_player or not self.vlc_player.is_video_loaded():
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

# ================ 선택 구간 미리보기 창 관련 =================

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
            self.preview_window._handle_close()
            self.preview_window = None

    def play_selection(self):
        """선택 구간만 재생 (비동기 방식으로 수정)"""
        # 공통 검증 메서드 사용
        if not self._validate_selection():
            return

        if not self.vlc_player or not self.vlc_player.is_video_loaded():
            return

        # 구간 시작 위치로 이동
        self.vlc_player.set_position(self.start_time)

        # 구간 재생 모드 설정
        self.is_playing = True
        self.is_previewing = True  # 구간 재생 중임을 표시
        self.play_button.config(text="|| 일시정지")

    def stop_selection_play(self):
        """구간 재생 중지"""
        self.is_playing = False
        self.is_previewing = False  # 구간 재생 상태 관리
        self.play_button.config(text="► 재생")

# ================ 저장된 구간 테이블 관련 =================

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
    def create_segment_data(self, video_path, start_time, end_time, duration):
        """구간 데이터 생성 공통 메서드"""
        return {
            'file': os.path.basename(video_path),
            'start': start_time,
            'end': end_time,
            'duration': duration,
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

        # 구간 데이터 생성 - 정확한 길이 계산
        duration = self.end_time - self.start_time
        segment_data = self.create_segment_data(
            video_path, self.start_time, self.end_time, duration)

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

        except Exception as e:
            print(f"테이블 업데이트 중 오류: {e}")

    def delete_segment(self, index):
        """구간 삭제 - 중앙화된 데이터 관리"""
        try:
            if 0 <= index < len(self.saved_segments):
                deleted_segment = self.saved_segments.pop(index)
                event_system.emit(Events.SEGMENT_DELETED,
                                  segment=deleted_segment, index=index)
                self.update_all_tables()
                return True, "선택한 구간이 삭제되었습니다."
            else:
                return False, "유효하지 않은 구간 인덱스입니다."
        except Exception as e:
            return False, f"구간 삭제 중 오류가 발생했습니다: {str(e)}"

    def export_segments_to_csv(self):
        """구간 데이터 CSV 내보내기 - 중앙화된 데이터 관리"""
        try:
            if not self.saved_segments:
                return False, "내보낼 구간 데이터가 없습니다."

            # 자동 파일명 생성
            default_filename = self.generate_csv_filename()

            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                title="구간데이터_저장",
                initialfile=default_filename
            )

            if not file_path:
                return False, "파일 저장이 취소되었습니다."

            # 윈도우 환경에서 더 안정적인 인코딩 사용
            try:
                with open(file_path, 'w', newline='', encoding='cp949') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(
                        ['파일명', '시작 시간', '종료 시간', '구간 길이', '타입', '의견1', '의견2'])

                    for segment in self.saved_segments:
                        filename = segment.get('file', '')
                        type_value = os.path.splitext(
                            filename)[0][-2:] if filename else ''

                        writer.writerow([
                            filename,
                            VideoUtils.format_time(segment['start']),
                            VideoUtils.format_time(segment['end']),
                            VideoUtils.format_time(segment['duration']),
                            type_value,
                            segment.get('opinion1', ''),
                            segment.get('opinion2', '')
                        ])

                return True, f"데이터가 {os.path.basename(file_path)}에 저장되었습니다."

            except UnicodeEncodeError:
                # cp949로 저장 실패 시 UTF-8로 재시도
                print("CP949 인코딩 실패, UTF-8로 재시도")
                with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(
                        ['파일명', '시작 시간', '종료 시간', '구간 길이', '타입', '의견1', '의견2'])

                    for segment in self.saved_segments:
                        filename = segment.get('file', '')
                        type_value = os.path.splitext(
                            filename)[0][-2:] if filename else ''

                        writer.writerow([
                            filename,
                            VideoUtils.format_time(segment['start']),
                            VideoUtils.format_time(segment['end']),
                            VideoUtils.format_time(segment['duration']),
                            type_value,
                            segment.get('opinion1', ''),
                            segment.get('opinion2', '')
                        ])

                return True, f"데이터가 {os.path.basename(file_path)}에 저장되었습니다. (UTF-8 인코딩)"

        except Exception as e:
            return False, f"파일 저장 중 오류가 발생했습니다: {str(e)}"

    def generate_csv_filename(self):
        """CSV 파일명 자동 생성 - 중앙화된 데이터 관리"""
        # 현재 날짜와 시간
        now = datetime.now()
        date_str = now.strftime("%Y%m%d")

        # 비디오 파일명 가져오기
        video_name = "비디오"
        if hasattr(self, 'video_path') and self.video_path:
            if hasattr(self.video_path, 'get'):
                video_path = self.video_path.get()
            else:
                video_path = self.video_path

            if video_path:
                # 파일명에서 확장자 제거
                video_name = os.path.splitext(os.path.basename(video_path))[0]
                # 파일명에서 특수문자 제거 (Windows 파일명 호환성)
                video_name = "".join(
                    c for c in video_name if c.isalnum() or c in (' ', '-', '_')).strip()
                if not video_name:
                    video_name = "비디오"

        # 구간 수 정보
        segment_count = len(self.saved_segments) if hasattr(
            self, 'saved_segments') else 0

        # 파일명 생성: "비디오명_구간데이터_구간수개_날짜시간.csv"
        filename = f"{video_name}_구간데이터_{segment_count}개_{date_str}.csv"

        # 파일명 길이 제한 (Windows 경로 길이 제한 고려)
        if len(filename) > 100:
            video_name = video_name[:30] + "..."
            filename = f"{video_name}_구간데이터_{segment_count}개_{date_str}.csv"

        return filename

    def import_segments_from_csv(self, file_path):
        """CSV 파일에서 구간 데이터 가져오기 - app에서 중앙화된 데이터 관리"""

        try:
            # 파일 경로 정규화 및 디버깅
            original_path = file_path
            file_path = os.path.normpath(file_path)  # 경로 정규화
            print(f"CSV 가져오기 - 원본 경로: {original_path}")
            print(f"CSV 가져오기 - 정규화된 경로: {file_path}")
            print(f"CSV 가져오기 - 파일 존재 여부: {os.path.exists(file_path)}")
            print(
                f"CSV 가져오기 - 파일 크기: {os.path.getsize(file_path) if os.path.exists(file_path) else 'N/A'} bytes")

            if not os.path.exists(file_path):
                return False, f"CSV 파일을 찾을 수 없습니다.\n경로: {file_path}"

            imported_segments = []
            error_count = 0
            error_details = []

            # 여러 인코딩 시도 (cp949 우선 - 내보내기 형식과 일치)
            encodings = ['cp949', 'utf-8', 'euc-kr',
                         'utf-8-sig']  # BOM 포함 UTF-8 추가
            csvfile = None
            successful_encoding = None

            for encod in encodings:
                try:
                    print(f"CSV 가져오기 - 인코딩 시도: {encod}")
                    csvfile = open(file_path, 'r', encoding=encod)
                    # 헤더를 자동으로 인식하여 딕셔너리 형태로 반환해줌.
                    reader = csv.DictReader(csvfile)

                    # 첫 번째 행 읽기 시도
                    first_row = next(reader, None)
                    if first_row is None:
                        print(f"CSV 가져오기 - {encod}: 파일이 비어있음")
                        continue

                    print(f"CSV 가져오기 - {encod}: 첫 번째 행 읽기 성공")
                    print(f"CSV 가져오기 - {encod}: 헤더: {list(first_row.keys())}")

                    # 첫 번째 행을 다시 처리하기 위해 리셋
                    csvfile.seek(0)
                    reader = csv.DictReader(csvfile)

                    successful_encoding = encod
                    break

                except UnicodeDecodeError:
                    print(f"CSV 가져오기 - {encod}: 인코딩 오류")
                    if csvfile:
                        csvfile.close()
                    continue
                except Exception as e:
                    print(f"CSV 가져오기 - {encod}: 기타 오류 - {str(e)}")
                    if csvfile:
                        csvfile.close()
                    continue
                finally:
                    if csvfile:
                        csvfile.close()

            if successful_encoding is None:
                return False, "모든 인코딩으로 파일을 읽을 수 없습니다. 파일이 손상되었거나 지원되지 않는 형식입니다."

            print(f"CSV 가져오기 - 성공한 인코딩: {successful_encoding}")

            # 성공한 인코딩으로 다시 파일 열기
            with open(file_path, 'r', encoding=successful_encoding) as csvfile:
                reader = csv.DictReader(csvfile)

                for row_num, row in enumerate(reader, start=2):
                    try:
                        # DictReader는 딕셔너리 형태로 반환하므로 키로 접근
                        # 필수 컬럼만 체크 (구간 길이, 타입은 선택사항)
                        if not row.get('파일명') or not row.get('시작 시간') or not row.get('종료 시간'):
                            error_count += 1
                            error_details.append(
                                f"행 {row_num}: 필수 컬럼 누락 (파일명, 시작 시간, 종료 시간)")
                            continue

                        # 문자열로 들어가 있기 때문에 strip()으로 공백 제거
                        start_time_str = row['시작 시간'].strip()
                        end_time_str = row['종료 시간'].strip()

                        # 시간 문자열을 초 단위로 변환 (HH:MM:SS 형식)
                        start_seconds = _parse_time_to_seconds(start_time_str)
                        end_seconds = _parse_time_to_seconds(end_time_str)

                        if start_seconds is None or end_seconds is None:
                            error_count += 1
                            error_details.append(
                                f"행 {row_num}: 시간 형식 오류 ({start_time_str}, {end_time_str})")
                            continue
                        elif start_seconds >= end_seconds:
                            error_count += 1
                            error_details.append(
                                f"행 {row_num}: 시작 시간이 종료 시간보다 크거나 같음")
                            continue

                        # 구간 데이터 생성, app.py의 내부 데이터 구조는 400-410 라인 확인. UI테이블에서의 헤더더와 다름.
                        segment_data = {
                            'file': row['파일명'].strip(),
                            'start': start_seconds,
                            'end': end_seconds,
                            'duration': end_seconds - start_seconds,
                            # row.get을 이용해서 기본값 ''으로 안전한 처리, cvs 파일의 컬럼이 누락되어도 오류 없이 처리하기 위함
                            'opinion1': row.get('의견1', '').strip(),
                            'opinion2': row.get('의견2', '').strip()
                        }

                        imported_segments.append(segment_data)

                    except Exception as e:
                        error_count += 1
                        error_details.append(
                            f"행 {row_num}: 데이터 처리 오류 - {str(e)}")
                        print(f"CSV 행 {row_num} 처리 중 오류: {e}")
                        continue

            if not imported_segments:
                return False, "가져올 수 있는 구간 데이터가 없습니다."

            # 파일명 일치성 확인
            if not self._check_video_filename_match(imported_segments):
                return False, "CSV 가져오기가 취소되었습니다."

            # !!!!!!기존 구간에 추가!!!!!!
            self.saved_segments.extend(imported_segments)

            # 이벤트 발행 및 테이블 업데이트
            event_system.emit(Events.SEGMENT_SAVED, segments=imported_segments)
            self.update_all_tables()

            success_msg = f"{len(imported_segments)}개의 구간을 성공적으로 가져왔습니다."
            if error_count > 0:
                success_msg += f"\n{error_count}개의 행에서 오류가 발생했습니다."

            return True, success_msg

        except Exception as e:
            return False, f"CSV 파일 읽기 중 오류가 발생했습니다: {str(e)}"

    def _check_video_filename_match(self, imported_segments):
        """현재 비디오 파일과 CSV 파일의 일치성 확인"""
        current_video_name = ""
        if hasattr(self, 'video_path') and self.video_path:
            if hasattr(self.video_path, 'get'):
                video_path = self.video_path.get()
            else:
                video_path = self.video_path

            if video_path:
                current_video_name = os.path.splitext(
                    os.path.basename(video_path))[0]

        # CSV에서 가져온 첫 번째 구간의 파일명 확인
        csv_video_name = ""
        if imported_segments and imported_segments[0].get('file'):
            csv_filename = imported_segments[0]['file']
            csv_video_name = os.path.splitext(csv_filename)[0]

        # 파일명 일치성 확인 및 사용자 알림
        if current_video_name and csv_video_name:
            if current_video_name != csv_video_name:
                warning_msg = f"""⚠️ 파일명 불일치 경고

현재 로드된 비디오: {current_video_name}
CSV 파일의 비디오: {csv_video_name}

다른 비디오 파일의 구간 데이터를 가져오려고 합니다.
계속 진행하시겠습니까?"""

                if not messagebox.askyesno("파일명 불일치", warning_msg):
                    return False

        return True
