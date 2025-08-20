import vlc
import os
import sys
import threading
import time
import platform
from .event_system import event_system, Events
import ctypes


def setup_bundled_vlc():
    """번들된 VLC 환경 설정"""
    try:
        if getattr(sys, 'frozen', False):
            # PyInstaller로 패키징된 경우
            if hasattr(sys, '_MEIPASS'):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(
                os.path.dirname(os.path.abspath(__file__)))

        print(f"VLC 환경 설정 시작, base_path: {base_path}")

        # VLC 루트 경로 설정
        vlc_root = os.path.join(base_path, '_internal', 'vlc')
        if not os.path.exists(vlc_root):
            print(f"⚠️ VLC 루트 경로를 찾을 수 없음: {vlc_root}")
            return False

        # VLC 플러그인 경로 설정
        plugins_path = os.path.join(vlc_root, 'plugins')
        if os.path.exists(plugins_path):
            os.environ['VLC_PLUGIN_PATH'] = plugins_path
            print(f"✓ VLC 플러그인 경로 설정: {plugins_path}")
        else:
            print("⚠️ VLC 플러그인 경로를 찾을 수 없음")
            return False

        # DLL 검색 경로 추가 (Windows 10+)
        if hasattr(os, 'add_dll_directory'):
            try:
                os.add_dll_directory(vlc_root)
                print(f"✓ DLL 검색 경로 추가: {vlc_root}")
            except Exception as e:
                print(f"DLL 검색 경로 추가 실패: {e}")
                return False

        # python-vlc가 libvlc를 찾도록 환경 변수 설정
        os.environ['PYTHON_VLC_MODULE_PATH'] = vlc_root
        os.environ['PYTHON_VLC_LIB_PATH'] = vlc_root
        print(f"✓ PYTHON_VLC_MODULE_PATH/LIB_PATH 설정: {vlc_root}")

        # PATH 환경변수에도 VLC 경로 추가
        current_path = os.environ.get('PATH', '')
        if vlc_root not in current_path:
            os.environ['PATH'] = vlc_root + os.pathsep + current_path
            print(f"✓ PATH에 추가: {vlc_root}")

        return True

    except Exception as e:
        print(f"번들된 VLC 설정 오류: {e}")
        return False

# VLC 이벤트 → vlc_utils.py → event_system → main_tab.py → UI 업데이트


class VLCPlayer:
    """VLC 플레이어"""

    def __init__(self):
        # VLC 인스턴스 생성 (임베딩을 위한 옵션)
        vlc_args = [
            '--quiet',
            '--no-video-title-show',
            '--no-video-deco',  # 비디오 장식 제거
            '--intf=dummy',  # 인터페이스 비활성화
        ]

        try:
            self.vlc_instance = vlc.Instance(vlc_args)
            if not self.vlc_instance:
                raise Exception("VLC 인스턴스 생성 실패")

            self.media_player = self.vlc_instance.media_player_new()
            if not self.media_player:
                raise Exception("VLC 미디어 플레이어 생성 실패")

            print("VLC 인스턴스 및 미디어 플레이어 생성 성공")
        except Exception as e:
            print(f"VLC 초기화 실패: {e}")
            self.vlc_instance = None
            self.media_player = None

        self.video_widget = None  # 나중에 연결

        # 상태 변수
        self.media = None
        self.duration = 0
        self.is_playing = False
        self.current_time = 0
        self.volume = 100

        # VLC 이벤트 매니저
        self.event_manager = None
        if self.media_player:
            self.setup_vlc_events()

    def set_video_widget(self, widget):
        """비디오 위젯 설정"""
        self.video_widget = widget
        print(f"비디오 위젯 설정됨: {widget}")

        # 미디어가 이미 로드된 경우 즉시 임베딩
        if self.media:
            print("미디어가 로드되어 있음, 즉시 임베딩 시도")
            self.embed_video()
        else:
            print("미디어가 아직 로드되지 않음, 나중에 임베딩됨")

    def load_video(self, video_path):
        """비디오 로드"""
        if not self.vlc_instance or not self.media_player:
            print("VLC 인스턴스가 초기화되지 않았습니다.")
            return False

        try:
            if self.media:
                self.media.release()

            # 경로 정규화 및 URI 변환 (한글/공백/유니코드 경로 대응)
            try:
                from pathlib import Path
                path_obj = Path(video_path).resolve()
                if not path_obj.exists():
                    print(f"VLC 로드: 파일이 존재하지 않습니다 - {video_path}")
                file_uri = path_obj.as_uri()
                print(f"VLC 로드: 파일 URI 사용 - {file_uri}")
                self.media = self.vlc_instance.media_new(file_uri)
            except Exception as uri_e:
                print(f"VLC 로드: URI 변환 실패, 원본 경로로 시도 - {uri_e}")
                self.media = self.vlc_instance.media_new(video_path)
            if not self.media:
                print("미디어 객체 생성 실패")
                return False

            self.media_player.set_media(self.media)

            # 볼륨 설정
            self.media_player.audio_set_volume(self.volume)

            # 미디어 파싱 및 길이 정보 업데이트 (재생하지 않고)
            self.media.parse()

            # 비디오 위젯이 설정되어 있다면 임베딩
            if self.video_widget:
                print(f"VLC 로드: 비디오 위젯 발견, 임베딩 시도")
                self.embed_video()
                # 임베딩 후 최소한의 지연만 (0.2초 → 0.05초)
                time.sleep(0.05)
            else:
                print(f"VLC 로드: 비디오 위젯이 설정되지 않음")

            # 미디어 길이 정보 업데이트 (재생하지 않고 파싱만으로)
            try:
                # 미디어 파싱으로 길이 정보 시도
                duration_ms = self.media.get_duration()
                if duration_ms > 0:
                    self.duration = duration_ms / 1000
                    print(f"VLC 로드: 파싱으로 길이 정보 획득 - {self.duration}초")
                else:
                    # 파싱 실패 시에만 최소한의 재생으로 정보 획득
                    print("VLC 로드: 파싱 실패, 최소 재생으로 길이 정보 획득 시도")
                    if self.video_widget:  # 임베딩된 경우에만
                        self.media_player.play()
                        # 매우 짧은 시간만 대기
                        import threading

                        def stop_after_delay():
                            time.sleep(0.1)  # 0.3초 → 0.1초로 단축
                            self.media_player.stop()
                            print("VLC 로드: 길이 정보 로드 완료, 정지")

                        # 별도 스레드에서 정지 처리
                        threading.Thread(
                            target=stop_after_delay, daemon=True).start()

                        # 메인 스레드는 즉시 진행
                        self.duration = 0  # 일단 0으로 설정, 나중에 업데이트
            except Exception as e:
                print(f"VLC 로드: 길이 정보 획득 실패 - {e}")
                self.duration = 0

            print(f"VLC 비디오 로드 완료: {video_path}")
            return True

        except Exception as e:
            print(f"VLC 비디오 로드 실패: {e}")
            return False

    def embed_video(self):
        """플랫폼별 VLC 임베딩"""
        if not self.video_widget:
            print("VLC 임베딩: 비디오 위젯이 설정되지 않음")
            return

        try:
            # 위젯 ID 가져오기
            widget_id = self.video_widget.winfo_id()
            print(
                f"VLC 임베딩: 위젯 ID={widget_id}, 위젯 타입={type(self.video_widget)}")

            if platform.system() == "Windows":
                # Windows에서 더 안정적인 임베딩
                self.hwnd = widget_id
                print(f"VLC 임베딩: Windows HWND 설정 시도 - {self.hwnd}")
                self.media_player.set_hwnd(self.hwnd)
                print(f"VLC 임베딩: Windows 임베딩 완료 - HWND={self.hwnd}")

                # 임베딩 후 최소한의 지연만
                import time
                time.sleep(0.02)  # 0.2초 → 0.02초로 대폭 단축

                # 임베딩 확인
                current_hwnd = self.media_player.get_hwnd()
                print(f"VLC 임베딩: 현재 설정된 HWND={current_hwnd}")

            elif platform.system() == "Darwin":  # macOS
                self.hwnd = widget_id
                self.media_player.set_nsobject(self.hwnd)
                print(f"VLC 임베딩: macOS 임베딩 완료 - NSObject={self.hwnd}")
            else:  # Linux
                self.hwnd = widget_id
                self.media_player.set_xwindow(self.hwnd)
                print(f"VLC 임베딩: Linux 임베딩 완료 - XWindow={self.hwnd}")

            print(f"VLC 임베딩: {platform.system()} 플랫폼에서 임베딩 완료")
        except Exception as e:
            print(f"VLC 임베딩 오류: {e}")
            import traceback
            traceback.print_exc()

    def play(self):
        """재생 시작"""
        if self.media_player and self.media:
            print("VLC 재생 시작")

            # 임베딩 상태 확인 (디버깅용)
            if self.video_widget and self.is_embedded():
                print("VLC: 임베딩된 상태에서 재생 시작")
            else:
                print("VLC: 경고 - 임베딩되지 않은 상태에서 재생 시도")

            self.media_player.play()
            self.is_playing = True
            event_system.emit(Events.PLAYER_STATE_CHANGED,
                              is_playing=True, is_stopped=False)
            print("VLC: 재생 상태 변경 완료")
        else:
            print("미디어 플레이어 또는 미디어가 없습니다.")

    def pause(self):
        """일시정지"""
        if self.media_player and self.media:
            print("VLC 일시정지")
            self.media_player.pause()
            self.is_playing = False
            event_system.emit(Events.PLAYER_STATE_CHANGED,
                              is_playing=False, is_stopped=False)
        else:
            print("미디어 플레이어 또는 미디어가 없습니다.")

    def stop(self):
        """정지"""
        if self.media_player and self.media:
            self.media_player.stop()
            self.is_playing = False
            event_system.emit(Events.PLAYER_STATE_CHANGED,
                              is_playing=False, is_stopped=True)
        else:
            print("미디어 플레이어 또는 미디어가 없습니다.")

    def set_position(self, position):
        """위치 설정 (초 단위)"""
        if self.media_player and self.duration > 0:
            vlc_position = max(0.0, min(1.0, position / self.duration))
            self.media_player.set_position(vlc_position)
            # 위치 변경 후에는 '일시정지' 상태가 되므로, UI 업데이트를 위해 이벤트를 발생시킵니다.
            self.is_playing = False
            event_system.emit(Events.PLAYER_STATE_CHANGED,
                              is_playing=False, is_stopped=False)

    def get_position(self):
        """현재 위치 반환 (초 단위)"""
        if self.media_player:
            return self.media_player.get_time() / 1000
        return 0

    def get_duration(self):
        """전체 길이 반환"""
        return self.duration

    def set_volume(self, volume):
        """볼륨 설정 (0-100)"""
        self.volume = max(0, min(100, volume))
        if self.media_player:
            self.media_player.audio_set_volume(self.volume)

    def get_volume(self):
        """현재 볼륨 반환"""
        return self.volume

    def get_video_info(self):
        """비디오 정보 가져오기"""
        try:
            if not self.media:
                return None

            self.media.parse()
            tracks = self.media.tracks_get()

            video_info = {
                'duration': self.duration,
                'fps': 0,
                'width': 0,
                'height': 0,
                'codec': ''
            }

            return video_info

        except Exception as e:
            print(f"비디오 정보 가져오기 실패: {e}")
            return None

    def is_video_loaded(self):
        """비디오가 로드되었는지 확인"""
        return self.media is not None

    def is_embedded(self):
        """비디오가 임베드되었는지 확인"""
        if not self.media_player:
            return False

        try:
            if platform.system() == "Windows":
                hwnd = self.media_player.get_hwnd()
                return hwnd is not None and hwnd != 0
            elif platform.system() == "Darwin":
                # macOS에서는 다른 방법으로 확인
                return self.video_widget is not None
            else:
                # Linux에서는 다른 방법으로 확인
                return self.video_widget is not None
        except:
            return False

    def setup_vlc_events(self):
        """VLC 이벤트 매니저 설정"""
        try:
            self.event_manager = self.media_player.event_manager()

            # 이벤트 핸들러 등록
            self.event_manager.event_attach(
                vlc.EventType.MediaPlayerTimeChanged, self.on_time_changed)
            self.event_manager.event_attach(
                vlc.EventType.MediaPlayerPositionChanged, self.on_position_changed)
            self.event_manager.event_attach(
                vlc.EventType.MediaPlayerLengthChanged, self.on_length_changed)
            self.event_manager.event_attach(
                vlc.EventType.MediaPlayerEndReached, self.on_end_reached)

            print("VLC 이벤트 매니저 설정 완료")
        except Exception as e:
            print(f"VLC 이벤트 매니저 설정 실패: {e}")

    def on_time_changed(self, event):
        """시간 변경 이벤트 핸들러"""
        try:
            new_time = self.media_player.get_time() / 1000
            self.current_time = new_time
            event_system.emit(Events.VLC_TIME_CHANGED, time=new_time)
        except Exception as e:
            print(f"시간 변경 이벤트 처리 실패: {e}")

    def on_position_changed(self, event):
        """위치 변경 이벤트 핸들러"""
        try:
            position = self.media_player.get_position()
            # 위치 변경 이벤트는 필요에 따라 추가 처리
        except Exception as e:
            print(f"위치 변경 이벤트 처리 실패: {e}")

    def on_length_changed(self, event):
        """길이 변경 이벤트 핸들러"""
        try:
            new_duration = self.media_player.get_length() / 1000
            self.duration = new_duration
            event_system.emit(Events.VLC_LENGTH_CHANGED, duration=new_duration)
        except Exception as e:
            print(f"길이 변경 이벤트 처리 실패: {e}")

    def on_end_reached(self, event):
        """재생 종료 이벤트 핸들러"""
        try:
            self.is_playing = False
            print("비디오 재생 종료")
        except Exception as e:
            print(f"재생 종료 이벤트 처리 실패: {e}")

    def cleanup(self):
        """리소스 정리"""
        # 이벤트 매니저 정리
        if self.event_manager:
            try:
                self.event_manager.event_detach(
                    vlc.EventType.MediaPlayerTimeChanged)
                self.event_manager.event_detach(
                    vlc.EventType.MediaPlayerPositionChanged)
                self.event_manager.event_detach(
                    vlc.EventType.MediaPlayerLengthChanged)
                self.event_manager.event_detach(
                    vlc.EventType.MediaPlayerEndReached)
            except:
                pass

        if self.media_player:
            self.media_player.stop()
        if self.media:
            self.media.release()
        if self.vlc_instance:
            self.vlc_instance.release()


# VLC 초기화 전에 환경 설정
setup_bundled_vlc()
