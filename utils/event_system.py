from typing import Dict, List, Callable, Any
from collections import defaultdict


class EventSystem:
    """이벤트 시스템 - 컴포넌트 간 느슨한 결합을 위한 이벤트 관리자"""

    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = defaultdict(list)

    def subscribe(self, event_name: str, callback: Callable) -> None:
        """이벤트 구독"""
        self._listeners[event_name].append(callback)

    def unsubscribe(self, event_name: str, callback: Callable) -> None:
        """이벤트 구독 해제"""
        if event_name in self._listeners:
            try:
                self._listeners[event_name].remove(callback)
            except ValueError:
                pass  # 콜백이 없으면 무시

    def emit(self, event_name: str, **kwargs) -> None:
        """이벤트 발생"""
        if event_name in self._listeners:
            for callback in self._listeners[event_name]:
                try:
                    callback(**kwargs)
                except Exception as e:
                    try:
                        import traceback
                        traceback.print_exc()
                    finally:
                        print(f"이벤트 콜백 실행 중 오류: {e}")

    def clear(self) -> None:
        """모든 이벤트 리스너 제거"""
        self._listeners.clear()


# 전역 이벤트 시스템 인스턴스
event_system = EventSystem()


# 이벤트 이름 상수들
class Events:
    """이벤트 이름 상수들"""

    # 비디오 관련 이벤트
    VIDEO_LOADED = "video_loaded"  # 비디오 로드 완료
    VIDEO_PLAY_TOGGLE = "video_play_toggle"  # 재생/일시정지 토글
    VIDEO_STOP = "video_stop"  # 정지 버튼 클릭

    # 구간 관련 이벤트
    SEGMENT_START_SET = "segment_start_set"  # 구간 시작 시간 설정
    SEGMENT_END_SET = "segment_end_set"  # 구간 종료 시간 설정
    SEGMENT_SAVED = "segment_saved"  # 구간 저장
    SEGMENT_DELETED = "segment_deleted"  # 구간 삭제

    # UI 관련 이벤트
    UI_UPDATE = "ui_update"  # UI 업데이트
    TAB_CHANGED = "tab_changed"  # 탭 변경
    PLAYER_STATE_CHANGED = "player_state_changed"  # 플레이어 상태 변경

    # 비디오 추출 관련 이벤트
    VIDEO_EXTRACTION_COMPLETE = "video_extraction_complete"  # 비디오 추출 완료
    VIDEO_EXTRACTION_ERROR = "video_extraction_error"  # 비디오 추출 오류

    # 이미지 추출 관련 이벤트
    IMAGE_EXTRACTION_COMPLETE = "image_extraction_complete"  # 이미지 추출 완료
    IMAGE_EXTRACTION_ERROR = "image_extraction_error"  # 이미지 추출 오류

    # 오디오 추출 관련 이벤트
    AUDIO_EXTRACTION_COMPLETE = "audio_extraction_complete"  # 오디오 추출 완료
    AUDIO_EXTRACTION_ERROR = "audio_extraction_error"  # 오디오 추출 오류

    # 추출 취소 이벤트
    EXTRACTION_CANCEL = "extraction_cancel"  # 추출 취소

    # 프로그래스 업데이트 이벤트
    PROGRESS_UPDATE = "progress_update"  # 프로그래스 업데이트

    # VLC 관련 이벤트
    VLC_TIME_CHANGED = "vlc_time_changed"  # 비디오 시간 변경
    VLC_LENGTH_CHANGED = "vlc_length_changed"  # 비디오 길이 변경

    # # 새로운 구조 관련 이벤트
    # SEGMENT_CHANGED = "segment_changed"  # 구간 변경
    # SEGMENT_ADDED = "segment_added"  # 구간 추가
    # SEGMENT_REMOVED = "segment_removed"  # 구간 제거
    # SEGMENT_UPDATED = "segment_updated"  # 구간 업데이트
    # SEGMENTS_CLEARED = "segments_cleared"  # 구간 초기화
