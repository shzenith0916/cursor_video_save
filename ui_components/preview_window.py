import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import threading
import time
import os
from PIL import Image, ImageTk
from utils.utils import VideoUtils


class PreviewWindow:
    def __init__(self, root, app, video_path, start_time, end_time, auto_play=True):
        self.root = root
        self.app = app  # 메인 앱 참조
        self.video_path = video_path
        self.start_time = start_time
        self.end_time = end_time
        self.auto_play = auto_play  # 자동 재생여부

        # 새 창 생성
        self.window = tk.Toplevel(root)
        self.window.title("선택 구간 미리보기")
        self.window.geometry("800x1200")

        # UI 생성
        self.create_ui()

        # 비디오 관련 변수 초기화
        self.cap = None
        self.fps = None
        self.is_playing = False
        self.current_image = None
        self.current_time = self.start_time  # 변수로 받은 start_time을 넣어주어야 함.
        self.update_thread = None  # 추가!
        self.loop_play = True  # 동영상 루프로 재생 여부

        # 비디오 초기화
        self.initialize_video()

        # 초기 프레임 표시 추가!
        self.show_frame_at_time(self.start_time)

        # 자동 재생 시작
        if self.auto_play:
            self.window.after(500, self.start_auto_play)  # 500ms 이후 자동 재생생

        # 창닫기 이벤트 바인딩
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_ui(self):
        """UI 구성 요소 생성"""

        # 메인 프레임
        self.main_frame = tk.Frame(self.window)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 좌측 프레임 (비디오 재생)
        self.video_frame = tk.Frame(self.main_frame, bg="black")
        self.video_frame.pack(side="left", fill=tk.BOTH,
                              expand=True, padx=(0, 10))

        # VideoUtils 사용하여 비디오레이블 생성
        self.video_label = VideoUtils.create_video_label(self.video_frame)
        self.video_label.config(bg="black")

        # 우측 프레임 (구간 정보 테이블)
        self.right_frame = tk.Frame(self.main_frame)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH,
                              padx=(5, 0), width=300)

        # 테이블 생성
        self.create_table()

        # 컨트롤 플레임
        self.control_frame = tk.Frame(self.window)
        self.control_frame.pack(fill=tk.X, padx=10, pady=10)

        # 재생/일시정지 버튼
        self.play_button = tk.Button(
            self.control_frame,
            text="⏸",
            width=5,
            font=("Arial", 12),
            command=self.toggle_play)
        self.play_button.pack(side=tk.LEFT, padx=5)

        # 정지 버튼
        self.loop_var = tk.BooleanVar(value=True)
        self.loop_check = tk.Checkbutton(
            self.control_frame,
            text="루프 재생",
            font=("Arial", 12),
            variable=self.loop_var,
            command=self.toggle_loop)
        self.loop_check.pack(side=tk.LEFT, padx=5)

        # 저장 버튼
        self.save_button = tk.Button(
            self.control_frame,
            text="구간 저장",
            font=("Arial", 12),
            command=self.save_selection)
        self.save_button.pack(side=tk.LEFT, padx=10)

        # 구간 정보 레이블
        self.segment_info = f"구간: {VideoUtils.format_time(self.start_time)} - {VideoUtils.format_time(self.end_time)}"
        self.segment_label = tk.Label(
            self.control_frame,
            text=self.segment_info,
            font=("Arial", 11),
            fg='blue')

        self.segment_label.pack(side=tk.RIGHT, padx=5)

        # 위치 레이블
        self.position_label = tk.Label(
            self.control_frame,
            text=f"{VideoUtils.format_time(self.start_time)} / {VideoUtils.format_time(self.end_time)}",
            font=("Arial", 11)
        )
        self.position_label.pack(side=tk.RIGHT, padx=5)

        # ✅ 추가!! 도움말 레이블
        help_label = tk.Label(self.control_frame,
                              text="💡영상을 클릭하면 재생/일시정지 됩니다.",
                              font=("Arial", 11),
                              fg='gray')
        help_label.pack(side=tk.RIGHT, padx=10)

    def toggle_play(self):
        """재생/일시정지 토글"""
        if self.is_playing:
            self.is_playing = False
            self.play_button.config(text="▶")
        else:
            self.is_playing = True
            self.play_button.config(text="⏸")

            # 이미 재생중이면, 중지
            if self.update_thread and self.update_thread.is_alive():
                return
            # 새 재생 스레드 시작
            self.update_thread = threading.Thread(
                target=self.update_frames, daemon=True)
            self.update_thread.start()

    def toggle_loop(self):
        """루프 재생 설정 변경"""
        self.loop_play = self.loop_var.get()

    def save_selection(self):
        """현재 선택 구간 저장"""
        # 앱의 저장된 구간 리스트에 추가
        if not hasattr(self.app, 'saved_segments'):
            self.app.saved_segments = []

        # 새 구간 추가
        new_segment = {
            'file': os.path.basename(self.video_path),
            'start': self.start_time,
            'end': self.end_time,
            'duration': self.end_time - self.start_time
        }

        # ✅ 중복 체크 (선택 사항)
        for segment in self.app.saved_segments:
            if (abs(segment['start'] - self.start_time) < 0.1) and (abs(segment['end'] - self.end_time) < 0.1):
                messagebox.showinfo("💡알림", "이미 동일한 구간이 저장되어 있습니다.")
                return

        self.app.saved_segments.append(new_segment)

        # 테이블 갱신
        self.load_table_data()

        # 메시지 표시
        tk.messagebox.showinfo("💡알림", "구간이 저장되었습니다.")

    def create_table(self):
        "테이블 생성"
        # 테이블 위에 표시할 텍스트
        table_label = tk.Label(self.right_frame,
                               text="저장된 구간 목록",
                               font=("Arial", 12, "bold"))
        table_label.pack(pady=(10, 10))

        # 테이블 프레임 생성 (지역변수 local variable)
        table_frame = tk.Frame(self.right_frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 테이블 프레임 내 스크롤바 (저장 구간이 많을 경우를 대비해서)
        table_scroll = ttk.Scrollbar(table_frame)
        table_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # 테이블 프레임 안 트리뷰로 테이블 생성 (인스턴스 변수 Instance Variable)
        self.table = ttk.Treeview(table_frame,
                                  columns=("파일명", "시작시간", "종료시간",
                                           "길이", "의견1", "의견2"),
                                  show='headings',
                                  yscrollcommand=table_scroll.set)
        self.table.pack(fill=tk.BOTH, expand=True)

        # ✅ 스크롤바와 Treeview 연결
        table_scroll.config(command=self.table.yview)

        # 컬럼 헤더 설정
        self.table.heading("파일명", text="파일명", anchor=tk.W)
        self.table.heading("시작시간", text="시작 시간")
        self.table.heading("종료시간", text="종료 시간")
        self.table.heading("길이", text="구간 길이")
        self.table.heading("의견1", text="의견1")
        self.table.heading("의견2", text="의견2")

        # 컬럼 너비 설정
        self.table.column("파일명", width=120)
        self.table.column("시작시간", width=100)
        self.table.column("종료시간", width=100)
        self.table.column("길이", width=80)
        self.table.column("의견1", width=100)
        self.table.column("의견2", width=100)

        # 테이블에 행으로 들어갈 데이터 예시. 원래 코드로 추가시 예시.
        # table.insert("", tk.END, text="1", values=("#0", "임aa(1)SF.avi", "00:00", "00:03", "3초", "정상", "잔여물 x"))#

        # 더블클릭으로 편집 가능하도록 이벤트 바인딩
        self.table.bind("<DoubleClick>", self.on_item_doubleclick)

        # 편집을 위한 엔트리 생성
        self.entry_edit = tk.Entry(self.table)
        self.entry_edit.bind("<Return>", self.save_edit)
        self.entry_edit.bind("<FocusOut>", self.save_edit)
        self.entry_edit.bind("<Escape>", self.cancel_edit)

        # 편집 관련 변수
        self.editing_item = None
        self.editing_column = None

        # 초기 데이터 로드
        self.load_table_data()

        # 삭제 버튼 생성
        delete_button = tk.Button(self.right_frame,
                                  text="구간 선택 삭제",
                                  command=self.delete_selected_segment,
                                  font=("Arial", 12))
        delete_button.pack(pady=3)

    def on_item_doubleclick(self, event):
        "더블 클릭시, 편집 시작"
        selected_items = self.table.selection()
        if not selected_items:
            messagebox.showwarning("경고", "편집할 항목을 선택해주세요.")
            return
        item = selected_items[0]
        column = self.table.identify_column(event.x)  # x 좌표에서 컬럼 찾기
        # 예시 row = self.table.identify_column(event.y) # y 좌표에서 행 찾기

        if column in ('의견1', '의견2'):  # 의견 컬럼들만 수정하게게
            self.start_edit(item, column)

    def start_edit(self, item, column):
        "편집 모드"
        self.editing_item = item
        self.editing_column = column

        # 예시: 항목 정보 가져오기
        item_data = self.table.item('item_id', 'values')  # 항목의 값들
        item_text = self.table.item('item_id', 'text')    # 항목의 텍스트

        # 현재값 가져오기
        current_value = self.table.item(item, 'values')[
            int(column.lstrip('#')) - 1]

        # 엔트리 위젯 위치
        x, y, width, height = self.table.bbox(item, column)

        # 글자수 제한
        wordlimit_cmd = (self.table.register(
            self.validate_input), '%P')  # %P는 매개변수
        self.entry_edit.config(validate='key', validatecommand=wordlimit_cmd)

        self.entry_edit.place(x=x, y=y, width=width, height=height)
        self.entry_edit.delete(0, tk.END)
        self.entry_edit.insert(0, current_value)
        self.entry_edit.focus()
        self.entry_edit.select_range(0, tk.END)

    def save_edit(self):
        "편집 내용 저장"
        if self.editing_item and self.editing_column:
            new_value = self.entry_edit.get()
            values = list(self.table.item(self.editing_item, 'values'))

            # 편집된 값으로 업데이트
            column_index = int(self.editing_column.lstrip('#')) - 1
            values[column_index] = new_value
            self.table.item(self.editing_item, values=values)

            # 메인 앱의 데이터도 업데이트
            item_index = self.table.index(self.editing_item)
            if hasattr(self.app, 'saved_segments') and item_index < len(self.app.saved_segments):
                if column_index == 4:  # 의견1
                    self.app.saved_segments[item_index]['opinion1'] = new_value
                elif column_index == 5:  # 의견2
                    self.app.saved_segments[item_index]['opinion2'] = new_value

            self.cancel_edit()

    def cancel_edit(self, event=None):
        "편집 취소"
        self.entry_edit.place_forget()  # 내장함수
        self.editing_item = None
        self.editing_column = None

    def load_table_data(self):
        """테이블 데이터 로드"""
        # 기존 데이터 삭제
        for item in self.table.get_children():
            self.table.delete(item)

        # 저장된 구간 표시 (VideoUtils.format_time 사용)
        if hasattr(self.app, 'saved_segments'):
            for segment in self.app.saved_segments:
                start_str = VideoUtils.format_time(segment['start'])
                end_str = VideoUtils.format_time(segment['end'])
                duration_str = VideoUtils.format_time(segment['duration'])

                self.table.insert("", "end", values=(
                    segment.get('file', ''),  # 파일명 포함
                    start_str,
                    end_str,
                    duration_str))

    def delete_selected_segment(self):
        """선택된 구간 삭제"""
        selected_item = self.table.selection()
        if not selected_item:
            messagebox.showwarning("경고", "삭제할 항목을 선택해주세요.")
            return

        # 확인 대화상자
        if messagebox.askyesno("확인", "선택한 구간을 삭제하시겠습니까?"):
            # 선택된 항목의 인덱스 찾기
            index = self.table.index(selected_item[0])

            # 메인 앱의 리스트에서 삭제
            if hasattr(self.app, 'saved_segments') and index < len(self.app.saved_segments):
                del self.app.saved_segments[index]

                # 테이블 갱신
                self.load_table_data()

    def on_close(self):
        """창 닫기 이벤트"""
        self.is_playing = False  # 스레드 루프 종료 신호
        if self.cap:
            self.cap.release()
        self.window.destroy()
