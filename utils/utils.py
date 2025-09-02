import os
import cv2
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from datetime import datetime
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from .ui_utils import UiUtils
from .event_system import event_system, Events
import time


def _parse_time_to_seconds(time_str):
    """시간 문자열을 초 단위로 변환 (HH:MM:SS 형식)"""
    try:
        if not time_str:
            return None

        # HH:MM:SS 형식 파싱
        parts = time_str.split(':')
        if len(parts) == 3:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        elif len(parts) == 2:
            # MM:SS 형식도 지원
            minutes = int(parts[0])
            seconds = int(parts[1])
            return minutes * 60 + seconds
        else:
            return None

    except (ValueError, IndexError):
        return None


def show_custom_messagebox(parent, title, message, msg_type="info", auto_close_ms=None):
    """커스텀 Toplevel 메시지 박스 생성"""
    dialog = tk.Toplevel(parent)
    dialog.title(title)

    # DPI 스케일링 적용 및 중앙 정렬
    width = int(380 * UiUtils.get_scaling_factor_by_dpi(parent))
    height = int(200 * UiUtils.get_scaling_factor_by_dpi(parent))
    UiUtils.center_window(dialog, parent, width, height)

    dialog.resizable(False, False)
    dialog.transient(parent)
    dialog.grab_set()

    # 아이콘과 색상 설정
    icon_configs = {
        "info": {"icon": "ℹ️", "color": "#0d6efd"},
        "success": {"icon": "✅", "color": "#198754"},
        "warning": {"icon": "⚠️", "color": "#fd7e14"},
        "error": {"icon": "❌", "color": "#dc3545"}
    }
    icon_config = icon_configs.get(msg_type, icon_configs["info"])

    main_frame = ttk.Frame(dialog)
    main_frame.pack(fill=BOTH, expand=True, padx=20, pady=15)

    content_frame = ttk.Frame(main_frame)
    content_frame.pack(fill=BOTH, expand=True, pady=(0, 15))

    icon_label = ttk.Label(
        content_frame, text=icon_config["icon"], font=("Arial", 24),
        foreground=icon_config["color"]
    )
    icon_label.pack(side=LEFT, padx=(0, 15), anchor='n')

    message_label = ttk.Label(
        content_frame, text=message, font=("Arial", 11),
        wraplength=width - 120, justify=LEFT
    )
    message_label.pack(side=LEFT, fill=BOTH, expand=True)

    # 확인 버튼 (자동 닫기가 아닐 경우에만 표시)
    if not auto_close_ms:
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=X)
        ok_button = ttk.Button(
            button_frame, text="확인", style="Accent.TButton",
            command=dialog.destroy, width=10
        )
        ok_button.pack(side=RIGHT)
        dialog.bind('<Return>', lambda e: dialog.destroy())
        dialog.bind('<Escape>', lambda e: dialog.destroy())
        ok_button.focus_set()

    # 자동 닫기 설정
    if auto_close_ms:
        dialog.after(auto_close_ms, dialog.destroy)

    dialog.wait_window()


class VideoUtils:
    """비디오 관련 유틸리티 클래스"""
    @staticmethod
    def format_time(seconds):
        '''초를 mm:ss 형식으로 변환하는 함수 '''

        seconds = int(float(seconds))  # float에서 int로 변환
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60

        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    @staticmethod
    def convert_frame_to_photo(frame):
        """OpenCV 프레임을 Tkinter PhotoImage로 변환.
           비디오 프레임에서 이 이미지를 이용하여 재생"""

        try:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)
            return ImageTk.PhotoImage(image=pil_image)
        except Exception as e:
            print(f"Frame conversion error: {e}")
            return None

    @staticmethod
    def convert_frame_to_photo_optimized(frame, target_width=None, target_height=None):
        """최적화된 OpenCV 프레임을 Tkinter PhotoImage로 변환"""
        try:
            # BGR -> RGB 변환
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(frame_rgb)

            # PIL 이미지 생성
            # 📌 타겟 크기가 지정된 경우 리사이즈
            if target_width and target_height:
                # 비율 유지하면서 리사이즈
                pil_img.thumbnail((target_width, target_height),
                                  Image.Resampling.LANCZOS)

            return ImageTk.PhotoImage(pil_img)

        except Exception as e:
            print(f"Frame Conversion Error: {e}")
            return None

    @staticmethod
    def get_opencv_video_info(video_path):
        """OpenCV로 비디오 정보 가져오기 - 메인탭 오른쪽 상단 정보 표시"""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return None

            video_info = {
                'duration': cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS),
                'fps': cap.get(cv2.CAP_PROP_FPS),
                'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            }

            cap.release()
            return video_info

        except Exception as e:
            print(f"OpenCV 비디오 정보 가져오기 실패: {e}")
            return None

    @staticmethod
    def update_video_ui_components(video_info, ui_components):
        """UI 컴포넌트 업데이트"""
        try:
            if video_info and hasattr(ui_components, 'video_info_label'):
                info_text = f"길이: {VideoUtils.format_time(int(video_info['duration']))}\n"
                info_text += f"해상도: {video_info['width']}x{video_info['height']}\n"
                info_text += f"FPS: {video_info['fps']:.1f}"
                ui_components.video_info_label.config(text=info_text)
        except Exception as e:
            print(f"UI 업데이트 실패: {e}")

    @staticmethod
    def get_video_path_from_app(app_instance):
        """앱에서 비디오 경로 가져오기"""
        if hasattr(app_instance, 'video_path'):
            return app_instance.video_path
        return None

    @staticmethod
    def get_file_info(file_path):
        """파일 정보 가져오기 - new_tab/추출탭의 중간 프레임 부분분"""
        try:
            cap = cv2.VideoCapture(file_path)
            if not cap.isOpened():
                return None, "비디오 파일을 열 수 없습니다."

            props = {
                'fps': cap.get(cv2.CAP_PROP_FPS),
                'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'length': cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS)
            }

            file_stats = os.stat(file_path)
            file_info = {
                'video_props': props,
                'file_name': os.path.basename(file_path),
                'file_path': file_path,
                'file_size': f"{file_stats.st_size / (1024*1024):.1f} MB"
            }

            cap.release()
            return file_info, None

        except Exception as e:
            return None, f"파일 정보 오류: {str(e)}"

    @staticmethod
    def create_video_label(parent_frame):
        """비디오 레이블 생성"""
        if parent_frame:
            video_label = tk.Label(parent_frame)
            video_label.pack(expand=True, fill="both")
            return video_label
        return None

    @staticmethod
    def find_input_file(filename, app_instance):
        """입력 파일 경로 찾기 (공통 메서드)

        Args:
            filename (str): 파일명 또는 전체 경로
            app_instance: 앱 인스턴스 (video_path 속성 포함)

        Returns:
            str or None: 찾은 파일 경로 또는 None
        """
        # 절대 경로인 경우 직접 확인
        if os.path.isabs(filename) and os.path.exists(filename):
            return filename

        # app_instance의 video_path에서 찾기
        if hasattr(app_instance, 'video_path') and app_instance.video_path:
            # StringVar인 경우 get() 메서드 사용
            if hasattr(app_instance.video_path, 'get'):
                full_path = app_instance.video_path.get()
            else:
                full_path = app_instance.video_path

            # 파일명이 일치하고 파일이 존재하는 경우
            if full_path and os.path.basename(full_path) == filename and os.path.exists(full_path):
                return full_path

        return None

    @staticmethod
    def get_default_save_path():
        """기본 저장 경로 가져오기 (바탕화면 또는 문서 폴더)"""
        default_path = os.path.expanduser("~/Desktop")
        if not os.path.exists(default_path):
            default_path = os.path.expanduser("~/Documents")
        return default_path
