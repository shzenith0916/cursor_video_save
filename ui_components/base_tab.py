import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from utils.event_system import event_system, Events


class BaseTab:
    def __init__(self, parent, app):
        # 1. 기본 초기화
        self.parent = parent
        self.app = app  # 기존 app 인스턴스 유지
        self.frame = ttk.Frame(parent)

        # 2. 이벤트 시스템 구독 (선택적)
        self._setup_event_listeners()

        # 3. 변수 초기화 (서브클래스에서 구현)
        self._init_variables()
        # BaseTab에서는 create_ui() 호출하지 않음
        # 각 자식 클래스에서 직접 호출하도록 함

    def _init_variables(self):
        """기본 변수 초기화"""
        pass  # 기본 구현은 아무것도 하지 않음

    def _setup_event_listeners(self):
        """이벤트 리스너 설정 - 서브클래스에서 오버라이드"""
        pass  # 기본 구현은 아무것도 하지 않음

    def create_ui(self):
        """서브클래스에서 오버라이드할 UI 생성 메서드"""
        pass  # 기본 구현은 아무것도 하지 않음

    def update_ui(self):
        """서브클래스에서 오버라이드할 UI 업데이트 메서드"""
        pass

    def destroy(self):
        """탭 제거 시 이벤트 구독 해제"""
        # 서브클래스에서 구현
        pass
