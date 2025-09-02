import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, filedialog
import os
from datetime import datetime
from utils.utils import VideoUtils


class SegmentTable:
    def __init__(self, root, app, preview_window=None, selection_callback=None):
        self.root = root
        self.app = app
        self.preview_window = preview_window  # PreviewWindow 직접 참조
        # NewTab의 on_segment_selected 메서드가 저장됨
        self.selection_callback = selection_callback
        self.entry_edit = None
        self.editing_item = None
        self.editing_column = None

        # 테이블 컨테이너 생성
        self.container = ttk.Frame(root)
        self.container.pack(fill=ttk.BOTH, expand=True, padx=5, pady=5)

        # 테이블 생성
        self.create_table()

        # 테이블 데이터 업데이트
        self.refresh()

    def create_table(self):
        """테이블 생성"""
        # 테이블 위에 표시할 텍스트
        table_label = ttk.Label(self.container,
                                text="저장된 구간 목록 테이블",
                                font=("Arial", 12, "bold"))
        table_label.pack(pady=(10, 5))

        # 테이블 프레임 생성
        table_frame = ttk.Frame(self.container)
        table_frame.pack(fill=ttk.BOTH, expand=True, padx=5, pady=5)

        # 스크롤바
        table_scroll = ttk.Scrollbar(table_frame)
        table_scroll.pack(side=ttk.RIGHT, fill=ttk.Y)

        # 트리뷰 생성
        self.table = ttk.Treeview(table_frame,
                                  columns=("파일명", "시작시간", "종료시간",
                                           "길이", "TYPE", "의견1", "의견2"),
                                  show='headings',
                                  selectmode='browse',
                                  # 위젯이 세로로 스크롤 될때, 스크롤바의 위치를 자동으로 업데이트하도록 연결 역할.
                                  # 이 코드만으로는, 스크롤바를 움직여도 위젯이 움직이지 않고, 위젯(트리뷰)이 스크롤 될때만 스크롤바 위치 갱신됌.
                                  yscrollcommand=table_scroll.set,
                                  height=10)
        self.table.pack(fill=ttk.BOTH, expand=True)

        # 스크롤바 연결
        # 아래 코드가 있어야, 스크롤바가 위젯의 yview 메서드를 호출하도록 연결해야 양쪽(위젯→스크롤바, 스크롤바→위젯) 모두 정상 작동
        table_scroll.config(command=self.table.yview)

        # 컬럼 설정 -> 전체 합계: 195 + 98 + 98 + 98 + 65 + 52 + 46 = 652px
        columns = {
            "파일명": (195, ttk.W),        # 0.30 * 650 = 195
            "시작시간": (98, ttk.CENTER),   # 0.15 * 650 = 97.5 → 98
            "종료시간": (98, ttk.CENTER),   # 0.15 * 650 = 97.5 → 98
            "길이": (98, ttk.CENTER),      # 0.15 * 650 = 97.5 → 98
            "TYPE": (65, ttk.CENTER),      # 0.10 * 650 = 65
            "의견1": (52, ttk.CENTER),       # 0.08 * 650 = 52
            "의견2": (46, ttk.CENTER)      # 0.07 * 650 = 45.5 → 46
        }

        # 컬럼 헤더 설정
        for col, (width, anchor) in columns.items():
            self.table.heading(col, text=col, anchor=anchor)
            self.table.column(col, width=width, minwidth=width, stretch=True)

        # 이벤트 바인딩
        self.container.bind('<Configure>', self._on_container_resize)
        self.table.bind('<Button-1>', self.on_item_click)  # 싱글클릭으로 편집
        # 구간 선택 이벤트 추가
        self.table.bind('<<TreeviewSelect>>', self.on_item_select)

        # 버튼 프레임
        button_frame = ttk.Frame(self.container)
        button_frame.pack(fill=ttk.X, pady=10)

        # 버튼 스타일 설정
        self.button_style = ttk.Style()

        # 삭제 버튼 (빨간색 계열)
        self.button_style.configure(
            "Delete.TButton",
            relief="raised",
            borderwidth=2,
            focuscolor="none",
            padding=(15, 10),
            font=("Arial", 10, "bold")
        )

        self.button_style.map(
            "Delete.TButton",
            relief=[('pressed', 'sunken'),
                    ('active', 'raised')],
            borderwidth=[('pressed', '3'),
                         ('active', '3'),
                         ('!active', '2')],
            background=[('active', '#FFE8E8'),
                        ('pressed', '#FFD0D0')]
        )

        # 내보내기 버튼 (초록색 계열)
        self.button_style.configure(
            "Export.TButton",
            relief="raised",
            borderwidth=2,
            focuscolor="none",
            padding=(15, 10),
            font=("Arial", 10, "bold")
        )

        self.button_style.map(
            "Export.TButton",
            relief=[('pressed', 'sunken'),
                    ('active', 'raised')],
            borderwidth=[('pressed', '3'),
                         ('active', '3'),
                         ('!active', '2')],
            background=[('active', '#E8F5E8'),
                        ('pressed', '#D0E8D0')]
        )

        # 삭제 버튼
        delete_button = ttk.Button(
            button_frame,
            text="선택 구간 삭제",
            command=self.delete_selected_segment,
            style="Large.primary.TButton",
            width=20
        )
        delete_button.pack(side=ttk.LEFT, padx=8, pady=2)

        # CSV 내보내기 버튼
        export_button = ttk.Button(
            button_frame,
            text="CSV로 내보내기",
            command=self.export_to_csv,
            style="Large.primary.TButton",
            width=20
        )
        export_button.pack(side=ttk.LEFT, padx=8, pady=2)

        # 초기 데이터 로드
        self.load_table_data()

    def on_item_select(self, event):
        """구간 선택 시 호출되는 이벤트 핸들러"""

        select = self.table.selection()
        # selection_callback은 함수포인터(콜백 함수)로, newtab에서 정의한 on_segment_selected 메서드를 Segment Table에 전달
        if select and self.selection_callback:
            try:
                # 선택된 행의 인덱스(첫번째) 가져오기
                index = self.table.index(select[0])

                # 원본 데이터에서 구간 정보 가져오기
                if hasattr(self.app, 'saved_segments') and self.app.saved_segments \
                        and index < len(self.app.saved_segments):

                    selected_segment = self.app.saved_segments[index]
                    print(f"선택된 구간: {selected_segment}")

                    # 콜백 함수 호출
                    self.selection_callback(selected_segment)

            except Exception as e:
                print(f"행 선택 처리 중 오류 발생: {e}")

    def _on_container_resize(self, event):
        """컨테이너 크기 변경 시 테이블 컬럼 너비 조정"""
        if event.width > 0:
            available_width = event.width - 20
            width_ratios = {
                "파일명": 0.30,
                "시작시간": 0.15,
                "종료시간": 0.15,
                "길이": 0.15,
                "TYPE": 0.10,
                "의견1": 0.08,
                "의견2": 0.07
            }
            for col, ratio in width_ratios.items():
                width = int(available_width * ratio)
                self.table.column(col, width=width, minwidth=int(width * 0.8))

    def on_item_click(self, event):  # 더블클릭에서 싱글클릭으로 변경
        """싱글 클릭시 편집 시작"""
        selected_items = self.table.selection()
        if not selected_items:
            return

        item = selected_items[0]
        # ttk.Treeview에서만 사용가능한 내장함수: identify_column(x), identify_row(y), identify_element(x,y), identify_region(x,y) 등이 있음.
        column = self.table.identify_column(event.x)
        # #1, #2 등으로 나오기 때문에, #을 떼주고 -1 처리 해주어야 리스트에서 사용용가능.
        column_id = int(column.lstrip('#')) - 1
        column_name = self.table['columns'][column_id]

        if column_name in ('의견1', '의견2'):
            self.start_edit(item, column)

    def start_edit(self, item, column):
        """편집 모드 시작"""
        self.editing_item = item
        self.editing_column = column

        values = self.table.item(item, 'values')
        column_id = int(column.lstrip('#')) - 1
        current_value = values[column_id]

        if self.entry_edit is None:
            # tkinter Entry 사용하여 텍스트 색상 문제 해결
            self.entry_edit = tk.Entry(
                self.table,
                bg='white',           # 배경색 흰색
                fg='black',           # 텍스트 색상 검은색
                insertbackground='black',  # 커서 색상 검은색
                selectbackground='#0078d4',  # 선택 영역 배경색
                selectforeground='white',    # 선택 영역 텍스트 색상
                relief='solid',
                borderwidth=1,
                font=('Arial', 10)
            )
            # 엔터키 편집내용 저장.
            self.entry_edit.bind('<Return>', lambda e: self.save_edit())
            self.entry_edit.bind('<Escape>', self.cancel_edit)
            self.entry_edit.bind(
                '<FocusOut>', lambda e: self.save_edit())  # 기존 CANCEL_EDIT에 BIND. 수정 완료.
            # 마우스로 포커스 아웃시 편집내용 저장.

        x, y, width, height = self.table.bbox(item, column)
        if x is None:
            return

        wordlimit_cmd = (self.table.register(self.validate_input), '%P')
        self.entry_edit.config(validate='key', validatecommand=wordlimit_cmd)

        self.entry_edit.place(x=x, y=y, width=width, height=height)
        self.entry_edit.delete(0, 'end')  # tk.END 대신 'end' 사용
        self.entry_edit.insert(0, current_value)
        self.entry_edit.focus()
        self.entry_edit.select_range(0, 'end')  # tk.END 대신 'end' 사용

    def validate_input(self, value):
        """입력 검증"""
        return len(value) <= 30

    def save_edit(self):
        """편집 내용 저장"""
        if self.editing_item and self.editing_column:
            new_value = self.entry_edit.get()
            values = list(self.table.item(self.editing_item, 'values'))
            column_index = int(self.editing_column.lstrip('#')) - 1
            values[column_index] = new_value
            self.table.item(self.editing_item, values=values)

            item_index = self.table.index(self.editing_item)
            print(
                f"🔍 save_edit 디버깅: column_index={column_index}, item_index={item_index}, new_value='{new_value}'")

            if hasattr(self.app, 'saved_segments') and item_index < len(self.app.saved_segments):
                print(f"🔍 saved_segments 길이: {len(self.app.saved_segments)}")
                if column_index == 5:  # 의견1 (PAS)
                    self.app.saved_segments[item_index]['opinion1'] = new_value
                    print(f"의견1 저장됨: '{new_value}'")
                elif column_index == 6:  # 의견2 (잔여물)
                    self.app.saved_segments[item_index]['opinion2'] = new_value
                    print(f"의견2 저장됨: '{new_value}'")
                else:
                    print(f"알 수 없는 컬럼 인덱스: {column_index}")

            self.cancel_edit()

    def cancel_edit(self, event=None):
        """편집 취소"""
        if self.entry_edit:
            self.entry_edit.place_forget()
        self.editing_item = None
        self.editing_column = None

    def load_table_data(self):
        """테이블 데이터 로드"""
        for item in self.table.get_children():
            self.table.delete(item)

        if hasattr(self.app, 'saved_segments'):
            for segment in self.app.saved_segments:
                start_str = VideoUtils.format_time(segment['start'])
                end_str = VideoUtils.format_time(segment['end'])
                duration_str = VideoUtils.format_time(segment['duration'])
                filename = segment.get('file', '')
                type_value = os.path.splitext(
                    filename)[0][-2:] if filename else ''
                opinion1 = segment.get('opinion1', '')
                opinion2 = segment.get('opinion2', '')

                self.table.insert("", "end", values=(
                    filename,
                    start_str,
                    end_str,
                    duration_str,
                    type_value,
                    opinion1,
                    opinion2))

    def delete_selected_segment(self):
        """선택한 구간 삭제 - UI만 담당"""
        selected_items = self.table.selection()
        if not selected_items:
            messagebox.showwarning("경고", "삭제할 항목을 선택해주세요.")

            # 사용자 경험 상: 선택 없음 경고 시
            if self.preview_window and hasattr(self.preview_window, 'window'):
                try:
                    self.preview_window.window.focus_force()
                except:
                    pass  # 창이 이미 닫힌 경우 무시
            return

        if messagebox.askyesno("확인", "선택한 구간을 정말 삭제하시겠습니까?"):
            # 여러 항목을 선택한 경우 (현재는 단일 선택만 지원)
            for item in selected_items:
                index = self.table.index(item)
                # App 클래스의 중앙화된 데이터 관리 메서드 호출
                success, message = self.app.delete_segment(index)

                if success:
                    messagebox.showinfo("성공", message)
                else:
                    messagebox.showerror("오류", message)

            # 사용자 경험 상: 삭제 성공 시
            if self.preview_window and hasattr(self.preview_window, 'window'):
                try:
                    self.preview_window.window.focus_force()
                except ttk.TclError:
                    pass  # 창이 이미 닫힌 경우 무시

    def export_to_csv(self):
        """CSV 내보내기 - UI만 담당"""
        # App 클래스의 중앙화된 데이터 관리 메서드 호출
        success, message = self.app.export_segments_to_csv()

        if success:
            messagebox.showinfo("성공", message)
        else:
            messagebox.showwarning("경고", message)

    # generate_csv_filename 메서드는 App 클래스로 이동됨 - 중앙화된 데이터 관리

    def refresh(self):
        """테이블 데이터 새로고침"""
        self.load_table_data()

    def select_first_item(self):
        """첫 번째 항목 선택 (새로고침 후 자동 선택용)"""
        items = self.table.get_children()
        if items:
            self.table.selection_set(items[0])
            self.table.see(items[0])  # 스크롤해서 보이게 하기


# 사용자 액션 → SegmentTable → App 클래스 → 데이터 조작 → 이벤트 발행 → UI 업데이트
