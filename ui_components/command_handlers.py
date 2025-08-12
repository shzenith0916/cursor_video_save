# UI 컴포넌트들의 command 메서드들을 관리하는 모듈
# 각 UI 컴포넌트의 이벤트 핸들러들을 별도로 관리하여 코드 구조를 개선합니다.

import tkinter as tk
from tkinter import filedialog, messagebox
import os
import cv2
from utils.utils import show_custom_messagebox, VideoUtils
from utils.event_system import event_system, Events


class MainTabCommandHandler:
    """MainTab의 명령 처리 핸들러"""

    def __init__(self, app):
        self.app = app
        self.main_tab = None  # main_tab 참조를 나중에 설정

    def set_main_tab(self, main_tab):
        """main_tab 참조 설정"""
        self.main_tab = main_tab

    def on_file_select(self):
        """파일 선택 버튼 클릭 시"""

        print(f"[command_handlers.py] event_system id: {id(event_system)}")
        file_path = filedialog.askopenfilename(
            title="비디오 파일 선택창",
            filetypes=[("Video Files", "*.mp4 *.avi")]
        )
        if file_path:

            # main_tab의 video_path_var 업데이트 및 플래그 리셋
            if self.main_tab and hasattr(self.main_tab, 'video_path_var'):
                self.main_tab.video_path_var.set(file_path)
                # 새 비디오 로드 시 플래그 리셋 (버튼 활성화를 위해)
                self.main_tab._video_info_updated = False

            print(f"[command_handlers.py] emit file_path: {file_path}")
            event_system.emit(Events.VIDEO_LOADED, path=file_path)
            print("[command_handlers.py] emit called")

    def on_play_click(self):
        """재생 버튼 클릭 시. VIDEO_PLAY_TOGGLE 이벤트를 발생시킵니다."""
        event_system.emit(Events.VIDEO_PLAY_TOGGLE)

    def on_stop_click(self):
        """정지 버튼 클릭 시"""
        event_system.emit(Events.VIDEO_STOP)

    def on_set_start_click(self):
        """시작 지점 설정 버튼 클릭 시"""
        # 현재 슬라이더 위치(초 단위)를 구간 시작 시간으로 사용
        current_time = self.app.position_slider.get()
        event_system.emit(Events.SEGMENT_START_SET, time=current_time)

    def on_set_end_click(self):
        """종료 지점 설정 버튼 클릭 시"""
        # 현재 슬라이더 위치(초 단위)를 구간 종료 시간으로 사용
        current_time = self.app.position_slider.get()
        event_system.emit(Events.SEGMENT_END_SET, time=current_time)

    def on_save_segment_click(self):
        """구간 저장 버튼 클릭 시"""
        saved_segment = self.app.save_current_segment()
        if saved_segment:  # None이 아니면 (즉, 저장이 성공하면)
            event_system.emit(Events.SEGMENT_SAVED, **saved_segment)

    def on_preview_click(self):
        """미리보기 버튼 클릭 시"""
        # 구간 유효성 검사 후 미리보기 실행
        if hasattr(self.app, 'start_time') and hasattr(self.app, 'end_time') and \
           self.app.start_time < self.app.end_time:
            self.app.preview_selection()


class NewTabCommandHandler:
    """NewTab의 명령 처리 핸들러"""

    def __init__(self, app):
        self.app = app
        self.new_tab = None  # new_tab 참조를 나중에 설정

    def set_new_tab(self, new_tab):
        """new_tab 참조 설정"""
        self.new_tab = new_tab

    def on_extract_segments(self):
        """구간 추출 시작"""
        segments = self.app.get_saved_segments()

        if segments:
            event_system.emit(Events.EXTRACTION_START,
                              segments=segments, extract_type='video')
        else:
            # 사용자에게 알림
            if self.new_tab:
                show_custom_messagebox(
                    self.new_tab.frame, "경고", "추출할 구간이 없습니다.\n먼저 구간을 저장해주세요.", "warning")

    def on_extract_images(self):
        """이미지 추출 시작"""
        segments = self.app.get_saved_segments()
        if segments:
            event_system.emit(Events.IMAGE_EXTRACTION_START, segments=segments)

    def on_extract_audio(self):
        """오디오 추출 시작"""
        segments = self.app.get_saved_segments()
        if segments:
            event_system.emit(Events.AUDIO_EXTRACTION_START, segments=segments)
        else:
            if self.new_tab:
                show_custom_messagebox(
                    self.new_tab.frame, "경고", "추출할 구간이 없습니다.\n먼저 구간을 저장해주세요.", "warning")

    def on_cancel_extraction(self):
        """추출 취소"""
        event_system.emit(Events.EXTRACTION_CANCEL_REQUEST)


class SegmentTableCommandHandler:
    """SegmentTable의 명령 처리 핸들러"""

    def __init__(self, app):
        self.app = app

    def on_delete_segment(self, segment_index):
        """구간 삭제"""
        if 0 <= segment_index < len(self.app.saved_segments):
            deleted_segment = self.app.saved_segments.pop(segment_index)
            event_system.emit(Events.SEGMENT_DELETED,
                              segment=deleted_segment,
                              index=segment_index)
            self.app.update_all_tables()

    def on_export_csv(self):
        """CSV 내보내기"""
        segments = self.app.get_saved_segments()
        if segments:
            event_system.emit(Events.CSV_EXPORT, segments=segments)
