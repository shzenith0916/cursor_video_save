import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import cv2
import threading
import time
import os
from PIL import Image, ImageTk
from utils.utils import VideoUtils
import csv
import asyncio


class PreviewWindow:
    def __init__(self, root, app, video_path, start_time, end_time, auto_play=True):
        self.root = root
        self.app = app  # 메인 앱 참조
        self.video_path = video_path
        self.start_time = start_time
        self.end_time = end_time
        self.auto_play = auto_play  # 자동 재생여부
        # 성능 최적화 관련 속성성
        self.target_fps = 30
        self.frame_skip = 1
        self.frame_count = 0
        self.memory_cleanup_counter = 0

        # 새 창 생성
        self.window = tk.Toplevel(root)
        self.window.title("선택 구간 미리보기")
        self.window.geometry("800x800")

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
        self.cap, self.fps = VideoUtils.initialize_video(video_path)
        if self.cap is None:
            messagebox.showerror("오류", "비디오 초기화에 실패했습니다.")
            self.window.destroy()
            return

        # 초기 프레임 표시 추가!
        self.show_frame_at_time(self.start_time)

        # 비디오 속성 최적화
        if self.cap and self.cap.isOpened():
            self.original_fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.target_fps = VideoUtils.calculate_optimal_fps(
                self.original_fps)
            self.frame_skip = VideoUtils.calculate_frame_skip(
                self.original_fps, self.target_fps)

        # 자동 재생 시작
        if self.auto_play:
            self.window.after(500, self.start_auto_play)  # 500ms 이후 자동 재생생

        # 창닫기 이벤트 바인딩
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

        # # asyncio 이벤트 루프 관리
        # self.loop = asyncio.new_event_loop()
        # self.loop_thread = threading.Thread(
        #     target=self.run_async_loop, daemon=True)
        # self.loop_thread.start()

    def create_ui(self):
        """UI 구성 요소 생성"""
        # 메인 프레임
        self.main_frame = tk.Frame(self.window)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.video_frame = tk.Frame(self.main_frame, bg="black", width=600)
        self.video_frame.pack(side="left", fill=tk.BOTH, expand=False)
        self.video_frame.pack_propagate(False)  # 크기 고정

        # VideoUtils 사용하여 비디오레이블 생성
        self.video_label = VideoUtils.create_video_label(self.video_frame)
        self.video_label.pack(expand=True, fill="both")
        self.video_label.config(bg="black")

        # 우측 프레임 (구간 정보 테이블)
        self.right_frame = tk.Frame(self.main_frame, width=500)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        self.right_frame.pack_propagate(False)  # 최소 너비 유지

        # 우측 프레임의 크기를 고정하기 위해 프레임 내부에 고정 크기의 컨테이너 추가
        self.right_container = tk.Frame(self.right_frame)
        self.right_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 테이블 생성 (right_container 안에 생성)
        self.create_table()

        # 컨트롤 플레임
        self.control_frame = tk.Frame(self.window)
        self.control_frame.pack(fill=tk.X, padx=10, pady=5)

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

        # 창 크기 변경 이벤트 바인딩
        self.window.bind('<Configure>', self._on_window_resize)

    def _on_window_resize(self, event):
        """창 크기 변경 시 비디오 프레임 크기 조정"""
        if event.widget == self.window:  # 메인 창의 크기 변경일 때만 처리
            # 우측 프레임의 너비를 고정하고 남은 공간을 비디오 프레임에 할당
            # 전체 너비에서 우측 프레임(400)과 여백(20) 제외
            available_width = event.width - 420
            if available_width > 0:
                self.video_frame.configure(width=available_width)

    def show_frame_at_time(self, time_sec):
        """지정된 시간의 프레임 표시 (최적화)"""
        try:
            ret, frame = VideoUtils.read_frame_at_position(
                self.cap, time_sec, self.fps
            )

            if ret:
                # 최적화 메서드 사용
                self.show_frame_optimized(frame)
                self.current_time = time_sec
                self.update_position_label()

            else:
                print(f"Failed to read frame at {time_sec}s")

        except Exception as e:
            print(f"Error showing frame at time {time_sec}: {e}")

    def show_frame_optimized(self, frame):
        """프레임 표시 (최적화)"""
        try:
            # VideoUtils의 최적화된 변환 메서드 사용
            photo = VideoUtils.convert_frame_to_photo_optimized(frame)
            if photo:
                self.video_label.config(image=photo)
                self.video_label.image = photo  # 참조 유지
        except Exception as e:
            print(f"Error in show_frame_optimized: {e}")

    def update_frames_optimized(self):
        """프레임 업데이트 (최적화)"""
        if not self.is_playing:
            return

        # 현재시간 확인
        if self.current_time >= self.end_time:
            if self.loop_play:  # 루프 재생: 시작점으로 이동
                self.cap.set(cv2.CAP_PROP_POS_FRAMES,
                             int(self.start_time * self.fps))
                self.current_time = self.start_time
            else:
                # 루프 비활성화 - 재생 중지
                self.is_playing = False
                self.play_button.config(text="▶")
                return

        ret, frame = self.cap.read()
        if ret:
            self.show_frame_optimized(frame)
            self.current_time = self.cap.get(
                cv2.CAP_PROP_POS_FRAMES) / self.fps
            self.update_position_label()

            # 주기적 메모리 정리
            self.memory_cleanup_counter += 1
            if self.memory_cleanup_counter % 100 == 0:
                self.cleanup_memory()

            # 다음 프레임 스케줄링 (window.after 사용)
            frame_interval = int(1000/self.target_fps)
            self.window.after(frame_interval, self.update_frames_optimized)

    def update_position_label(self):  # 2번
        """위치 레이블 업데이트"""
        current_str = VideoUtils.format_time(self.current_time)
        end_str = VideoUtils.format_time(self.end_time)
        self.position_label.config(text=f"{current_str} / {end_str}")

    def cleanup_memory(self):  # 2번
        """주기적 메모리 정리"""
        import gc
        # 가비지 컬렉션 실행
        gc.collect()
        # OpenCV 메모리 정리
        VideoUtils.cleanup_opencv_memory()

    def toggle_play(self):
        """재생/일시정지 토글"""
        if self.is_playing:
            self.is_playing = False
            self.play_button.config(text="▶")
        else:
            # 재생 시작 시 현재 위치가 종료 시간이면 시작 시간으로 이동
            if self.current_time >= self.end_time:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES,
                             int(self.start_time * self.fps))
                self.current_time = self.start_time
                self.show_frame_at_time(self.start_time)

            self.is_playing = True
            self.play_button.config(text="⏸")
            # after 메서드를 사용하여 프레임 업데이트 시작
            self.update_frames_optimized()

    def toggle_loop(self):
        """루프 재생 설정 변경"""
        self.loop_play = self.loop_var.get()

    def run_async_loop(self):
        """
        별도의 스레드에서 asyncio 이벤트 루프 실행.
        :return:
        """
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

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
            'duration': self.end_time - self.start_time,
            'type': os.path.splitext(os.path.basename(self.video_path))[0][-2:]
        }

        # 중복 체크
        for segment in self.app.saved_segments:
            if (abs(segment['start'] - self.start_time) < 0.1) and (abs(segment['end'] - self.end_time) < 0.1):
                messagebox.showinfo("💡알림", "이미 동일한 구간이 저장되어 있습니다.")
                self.window.focus_force()  # 미리보기 창으로 포커스 강제 이동
                return

        self.app.saved_segments.append(new_segment)

        # 테이블 갱신
        self.load_table_data()

        # 메시지 표시 후 미리보기 창으로 포커스 이동
        messagebox.showinfo("💡알림", "구간이 저장되었습니다.")
        self.window.focus_force()  # 미리보기 창으로 포커스 강제 이동

    def create_table(self):
        "테이블 생성"
        # 테이블 위에 표시할 텍스트
        table_label = tk.Label(self.right_container,
                               text="저장된 구간 목록",
                               font=("Arial", 12, "bold"))
        table_label.pack(pady=(10, 5))

        # 테이블 프레임 생성
        table_frame = tk.Frame(self.right_container)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 테이블 프레임 내 스크롤바
        table_scroll = ttk.Scrollbar(table_frame)
        table_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # 테이블 프레임 안 트리뷰로 테이블 생성 (인스턴스 변수 Instance Variable)
        self.table = ttk.Treeview(table_frame,
                                  columns=("파일명", "시작시간", "종료시간",
                                           "길이", "TYPE", "PAS", "잔여물"),
                                  show='headings',
                                  selectmode='browse',
                                  yscrollcommand=table_scroll.set,
                                  height=10)  # 테이블 높이 설정
        self.table.pack(fill=tk.BOTH, expand=True)

        # ✅ 스크롤바와 Treeview 연결
        table_scroll.config(command=self.table.yview)

        # 컬럼 설정
        columns = {
            "파일명": (150, tk.W),      # 파일명은 왼쪽 정렬
            "시작시간": (80, tk.CENTER),
            "종료시간": (80, tk.CENTER),
            "길이": (60, tk.CENTER),
            "TYPE": (80, tk.CENTER),    # TYPE 컬럼 설정 추가
            "PAS": (100, tk.CENTER),
            "잔여물": (100, tk.CENTER)
        }

        # 컬럼 설정 적용
        for col, (width, anchor) in columns.items():
            self.table.heading(col, text=col, anchor=anchor)
            self.table.column(col, width=width, minwidth=width,
                              stretch=True)  # stretch=True로 변경

        # 테이블 크기 조정 이벤트 바인딩
        self.right_container.bind('<Configure>', self._on_container_resize)

        # 편집을 위한 엔트리 위젯 생성 (실제로는 start_edit에서 생성)
        self.entry_edit = None

        # 더블클릭 이벤트 바인딩 (올바른 이벤트 이름으로 수정)
        self.table.bind('<Double-1>', self.on_item_doubleclick)

        # 초기 데이터 로드
        self.load_table_data()

        # 버튼 프레임 생성
        button_frame = tk.Frame(self.right_container)
        button_frame.pack(fill=tk.X, pady=5)

        # 삭제 버튼 추가
        delete_button = tk.Button(button_frame,
                                  text="선택 구간 삭제",
                                  command=self.delete_selected_segment)
        delete_button.pack(side=tk.LEFT, padx=5)

        # CSV 내보내기 버튼 추가
        export_button = tk.Button(button_frame,
                                  text="CSV로 내보내기",
                                  command=self.export_to_csv)
        export_button.pack(side=tk.LEFT, padx=5)

    def _on_container_resize(self, event):
        """컨테이너 크기 변경 시 테이블 컬럼 너비 조정"""
        if event.width > 0:  # 유효한 너비인 경우에만 처리
            # 전체 너비에서 스크롤바 너비(20px)를 제외한 사용 가능한 너비 계산
            available_width = event.width - 20

            # 컬럼 너비 비율 설정 (전체 너비의 비율로)
            width_ratios = {
                "파일명": 0.30,    # 30%
                "시작시간": 0.12,  # 12%
                "종료시간": 0.12,  # 12%
                "길이": 0.08,      # 8%
                "TYPE": 0.10,      # 10% (TYPE 컬럼 비율 추가)
                "PAS": 0.14,       # 14%
                "잔여물": 0.14     # 14%
            }

            # 각 컬럼의 너비 계산 및 적용
            for col, ratio in width_ratios.items():
                width = int(available_width * ratio)
                self.table.column(col, width=width, minwidth=int(width * 0.8))

    def on_item_doubleclick(self, event):
        """더블 클릭시, 편집 시작. 
        선택된 항목 확인. 클릭된 컬럼 식별. 
        컬럼 이름 가져오기. 의견 컬럼인 경우에만 편집 시작"""

        selected_items = self.table.selection()
        if not selected_items:
            return  # 선택된 항목이 없으면 (즉, 더블클릭한 행이 선택되어 있지 않으면) 메서드를 종료합니다

        # 선택된 항목들 중 첫 번째 항목의 ID를 가져오기기
        item = selected_items[0]

        # 클릭된 컬럼 식별 (#1, #2 등의 형식으로 반환됨)
        # 마우스 이벤트의 x 좌표를 기반으로 클릭된 컬럼의 식별자를 가져옵니다
        column = self.table.identify_column(event.x)
        # 컬럼 식별자에서 '#'을 제거하고 숫자로 변환한 후, 0-based 인덱스로 변환
        # 예: '#1' → 1 → 0 (첫 번째 컬럼의 인덱스)
        column_id = int(column.lstrip('#')) - 1

        # 컬럼 이름 가져오기
        column_name = self.table['columns'][column_id]

        # 의견 컬럼인 경우에만 편집 시작
        if column_name in ('잔여물', 'PAS'):
            self.start_edit(item, column)

    def start_edit(self, item, column):
        "편집 모드"
        self.editing_item = item
        self.editing_column = column

        # 현재값 가져오기
        values = self.table.item(item, 'values')
        column_id = int(column.lstrip('#')) - 1
        current_value = values[column_id]

        # 엔트리 위젯 생성 (필요할 때만 생성)
        if self.entry_edit is None:
            self.entry_edit = tk.Entry(self.table)
            self.entry_edit.bind('<Return>', lambda e: self.save_edit())
            self.entry_edit.bind('<Escape>', self.cancel_edit)
            self.entry_edit.bind('<FocusOut>', self.cancel_edit)

        # 엔트리 위젯 위치
        x, y, width, height = self.table.bbox(item, column)
        if x is None:  # bbox가 None을 반환하는 경우 처리
            return

        # 글자수 제한 (30자까지)
        wordlimit_cmd = (self.table.register(self.validate_input), '%P')
        self.entry_edit.config(validate='key', validatecommand=wordlimit_cmd)

        self.entry_edit.place(x=x, y=y, width=width, height=height)
        self.entry_edit.delete(0, tk.END)
        self.entry_edit.insert(0, current_value)
        self.entry_edit.focus()
        self.entry_edit.select_range(0, tk.END)

    def validate_input(self, value):
        "입력 검증: 글자수 제한"
        return len(value) <= 30

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

                # 파일명에서 TYPE 추출 (마지막 2글자)
                filename = segment.get('file', '')
                type_value = os.path.splitext(
                    filename)[0][-2:] if filename else ''

                # 의견 데이터 가져오기 (없으면, 빈 문자열)
                opinion1 = segment.get('opinion1', '')
                opinion2 = segment.get('opinion2', '')

                self.table.insert("", "end", values=(
                    filename,  # 파일명
                    start_str,
                    end_str,
                    duration_str,
                    type_value,  # TYPE 값 (마지막 2글자)
                    opinion1,
                    opinion2))

    def delete_selected_segment(self):
        """선택된 구간 삭제"""
        selected_items = self.table.selection()
        if not selected_items:
            messagebox.showwarning("경고", "삭제할 항목을 선택해주세요.")
            return

        # ✅ 여러 항목이 선택된 경우를 고려하거나, 혹은 1개만 선택하면 나머지 비활성화.
        # if len(selected_items) > 1:
            # if not messagebox.askyesno("확인", f"{len(selected_items)}개 항목을 삭제하시겠습니까?"):
            # return
        # for item in reversed(selected_items): 마지막부터 삭제 (인덱스 변경 방지)
            # index = self.table.index(item)

        # 확인 대화상자
        if messagebox.askyesno("확인", "선택한 구간을 삭제하시겠습니까?"):
            # 선택된 항목의 인덱스 찾기
            index = self.table.index(selected_items[0])  # 첫번째 선택된 항목

            # 메인 앱의 리스트에서 삭제
            if hasattr(self.app, 'saved_segments') and index < len(self.app.saved_segments):
                del self.app.saved_segments[index]

                # 테이블 갱신
                self.load_table_data()
                # 선택구간 미리보기 창으로 돌아오기기
                self.window.focus_force()

    def on_close(self):
        """창 닫기 이벤트"""
        self.is_playing = False  # 스레드 루프 종료 신호
        if self.cap:
            self.cap.release()
        self.window.destroy()

    def export_to_csv(self):
        "데이터 csv 파일로 내보내기"
        # 현재 비디오 파일명을 기반으로 기본 파일명 생성
        base_filename = os.path.splitext(os.path.basename(self.video_path))[0]
        default_filename = f"{base_filename}_구간데이터.csv"

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=default_filename,  # 기본 파일명 설정
            filetypes=[("CSV files", "*.csv")],
            title="구간데이터_저장"
        )

        if file_path and hasattr(self.app, 'saved_segments'):
            try:
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(
                        ['파일명', '시작 시간', '종료 시간', '구간 길이', '식이타입', 'PAS', '잔여물'])

                    for segment in self.app.saved_segments:
                        filename = segment.get('file', '')
                        type_value = os.path.splitext(
                            filename)[0][-2:] if filename else ''  # 마지막 2글자

                        writer.writerow([
                            filename,
                            VideoUtils.format_time(segment['start']),
                            VideoUtils.format_time(segment['end']),
                            VideoUtils.format_time(segment['duration']),
                            type_value,  # TYPE 값 (마지막 2글자)
                            segment.get('opinion1', ''),
                            segment.get('opinion2', '')
                        ])

                messagebox.showinfo(
                    "성공", f"데이터가 {os.path.basename(file_path)}에 저장되었습니다.")
                self.window.focus_force()
            except Exception as e:
                messagebox.showerror("오류", f"파일 저장 중 오류가 발생했습니다: {str(e)}")

    def start_auto_play(self):
        """자동 재생 시작"""
        if self.auto_play and not self.is_playing:
            self.toggle_play()
