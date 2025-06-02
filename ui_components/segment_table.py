import tkinter as tk
from tkinter import ttk, messagebox
import os
from utils.utils import VideoUtils


class SegmentTable:
    def __init__(self, root, app, selection_callback=None, preview_window=None):
        self.root = root
        self.app = app
        self.preview_window = preview_window  # PreviewWindow 직접 참조
        # NewTab의 on_segment_selected 메서드가 저장됨
        self.selection_callback = selection_callback
        self.entry_edit = None
        self.editing_item = None
        self.editing_column = None

        # 테이블 컨테이너 생성
        self.container = tk.Frame(root)
        self.container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 테이블 생성
        self.create_table()

        # 테이블 데이터 업데이트
        self.refresh()

    def create_table(self):
        """테이블 생성"""
        # 테이블 위에 표시할 텍스트
        table_label = tk.Label(self.container,
                               text="저장된 구간 목록",
                               font=("Arial", 12, "bold"))
        table_label.pack(pady=(10, 5))

        # 테이블 프레임 생성
        table_frame = tk.Frame(self.container)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 스크롤바
        table_scroll = ttk.Scrollbar(table_frame)
        table_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # 트리뷰 생성
        self.table = ttk.Treeview(table_frame,
                                  columns=("파일명", "시작시간", "종료시간",
                                           "길이", "TYPE", "PAS", "잔여물"),
                                  show='headings',
                                  selectmode='browse',
                                  yscrollcommand=table_scroll.set,
                                  height=10)
        self.table.pack(fill=tk.BOTH, expand=True)

        # 스크롤바 연결
        table_scroll.config(command=self.table.yview)

        # 컬럼 설정
        columns = {
            "파일명": (150, tk.W),
            "시작시간": (80, tk.CENTER),
            "종료시간": (80, tk.CENTER),
            "길이": (60, tk.CENTER),
            "TYPE": (80, tk.CENTER),
            "PAS": (100, tk.CENTER),
            "잔여물": (100, tk.CENTER)
        }

        # 컬럼 헤더 설정정
        for col, (width, anchor) in columns.items():
            self.table.heading(col, text=col, anchor=anchor)
            self.table.column(col, width=width, minwidth=width, stretch=True)

        # 이벤트 바인딩
        self.container.bind('<Configure>', self._on_container_resize)
        self.table.bind('<Double-1>', self.on_item_doubleclick)
        # 구간 선택 이벤트 추가
        self.table.bind('<<TreeviewSelect>>', self.on_item_select)

        # 버튼 프레임
        button_frame = tk.Frame(self.container)
        button_frame.pack(fill=tk.X, pady=10)

        # 버튼 스타일 설정
        self.button_style = ttk.Style()

        # 기본 버튼 스타일 (RAISED 효과)
        self.button_style.configure(
            "Raised.TButton",
            relief="raised",
            borderwidth=2,
            focuscolor="none",
            padding=(15, 10),  # 패딩 증가로 버튼 크기 증가
            font=("Arial", 10, "bold")
        )

        # 호버 효과 스타일 (테두리 진하게)
        self.button_style.map(
            "Raised.TButton",
            relief=[('pressed', 'sunken'),
                    ('active', 'raised')],
            borderwidth=[('pressed', '3'),
                         ('active', '3'),
                         ('!active', '2')],
            background=[('active', '#E8F4FD'),
                        ('pressed', '#D0E8F2')]
        )

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
            style="Delete.TButton",
            width=20
        )
        delete_button.pack(side=tk.LEFT, padx=8, pady=2)

        # CSV 내보내기 버튼
        export_button = ttk.Button(
            button_frame,
            text="CSV로 내보내기",
            command=self.export_to_csv,
            style="Export.TButton",
            width=20
        )
        export_button.pack(side=tk.LEFT, padx=8, pady=2)

        # 초기 데이터 로드
        self.load_table_data()

    def on_item_select(self, event):
        """구간 선택 시 호출되는 이벤트 핸들러"""

        select = self.table.selection()
        # selection_callback은 함수포인터(콜백 함수)로, newtab에서 정의한 on_segment_selected 메서드를 Segment Table에 전달
        if select and self.selection_callback:
            try:
                # 선택된 행의 인덱스 가져오기
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
                "시작시간": 0.12,
                "종료시간": 0.12,
                "길이": 0.08,
                "TYPE": 0.10,
                "PAS": 0.14,
                "잔여물": 0.14
            }

            for col, ratio in width_ratios.items():
                width = int(available_width * ratio)
                self.table.column(col, width=width, minwidth=int(width * 0.8))

    def on_item_doubleclick(self, event):
        """더블 클릭시 편집 시작"""
        selected_items = self.table.selection()
        if not selected_items:
            return

        item = selected_items[0]
        column = self.table.identify_column(event.x)
        column_id = int(column.lstrip('#')) - 1
        column_name = self.table['columns'][column_id]

        if column_name in ('잔여물', 'PAS'):
            self.start_edit(item, column)

    def start_edit(self, item, column):
        """편집 모드 시작"""
        self.editing_item = item
        self.editing_column = column

        values = self.table.item(item, 'values')
        column_id = int(column.lstrip('#')) - 1
        current_value = values[column_id]

        if self.entry_edit is None:
            self.entry_edit = tk.Entry(self.table)
            self.entry_edit.bind('<Return>', lambda e: self.save_edit())
            self.entry_edit.bind('<Escape>', self.cancel_edit)
            self.entry_edit.bind('<FocusOut>', self.cancel_edit)

        x, y, width, height = self.table.bbox(item, column)
        if x is None:
            return

        wordlimit_cmd = (self.table.register(self.validate_input), '%P')
        self.entry_edit.config(validate='key', validatecommand=wordlimit_cmd)

        self.entry_edit.place(x=x, y=y, width=width, height=height)
        self.entry_edit.delete(0, tk.END)
        self.entry_edit.insert(0, current_value)
        self.entry_edit.focus()
        self.entry_edit.select_range(0, tk.END)

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
            if hasattr(self.app, 'saved_segments') and item_index < len(self.app.saved_segments):
                if column_index == 5:  # PAS
                    self.app.saved_segments[item_index]['opinion1'] = new_value
                elif column_index == 6:  # 잔여물
                    self.app.saved_segments[item_index]['opinion2'] = new_value

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
        """선택한 구간 삭제"""
        selected_items = self.table.selection()
        if not selected_items:
            messagebox.showwarning("경고", "삭제할 항목을 선택해주세요.")
            return

        if messagebox.askyesno("확인", "선택한 구간을 정말 삭제하시겠습니까?"):
            # 여러 항목을 선택한 경우 (현재는 단일 선택만 지원)
            for item in selected_items:
                index = self.table.index(item)
                if hasattr(self.app, 'saved_segments') and self.app.saved_segments and index < len(self.app.saved_segments):
                    del self.app.saved_segments[index]

            self.refresh()
            messagebox.showinfo("성공", "선택한 구간이 삭제되었습니다.")

            # 미리보기 창에서 삭제한 경우, 미리보기 창으로 포커스 복원
            if self.preview_window and hasattr(self.preview_window, 'window'):
                try:
                    self.preview_window.window.focus_force()
                except tk.TclError:
                    pass  # 창이 이미 닫힌 경우 무시

            # 삭제 후 NewTab의 테이블도 업데이트
            if hasattr(self.app, 'new_tab_instance') and hasattr(self.app.new_tab_instance, 'refresh_table'):
                self.app.new_tab_instance.refresh_table()

    def export_to_csv(self):
        """CSV 내보내기"""
        from tkinter import filedialog
        import csv

        if not hasattr(self.app, 'saved_segments'):
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="구간데이터_저장"
        )

        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(
                        ['파일명', '시작 시간', '종료 시간', '구간 길이', '식이타입', 'PAS', '잔여물'])

                    for segment in self.app.saved_segments:
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

                messagebox.showinfo(
                    "성공", f"데이터가 {os.path.basename(file_path)}에 저장되었습니다.")
            except Exception as e:
                messagebox.showerror("오류", f"파일 저장 중 오류가 발생했습니다: {str(e)}")

    def refresh(self):
        """테이블 데이터 새로고침"""
        self.load_table_data()

    def select_first_item(self):
        """첫 번째 항목 선택 (새로고침 후 자동 선택용)"""
        items = self.table.get_children()
        if items:
            self.table.selection_set(items[0])
            self.table.see(items[0])  # 스크롤해서 보이게 하기
