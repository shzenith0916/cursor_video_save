import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import cv2
from moviepy.editor import VideoFileClip
import os
import threading
from PIL import Image, ImageTk
import time


class VideoExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("비디오 부분 추출기")
        self.root.geometry("800x600")

        # 변수 초기화
        self.video_path = ""
        self.cap = None
        self.video_duration = 0
        self.current_frame = 0
        self.fps = 0
        self.total_frames = 0
        self.playing = False
        self.play_thread = None
        self.start_time = 0
        self.end_time = 0

        # UI 구성
        self.create_widgets()

    def create_widgets(self):
        # 상단 프레임 - 비디오 파일 선택
        top_frame = tk.Frame(self.root)
        top_frame.pack(pady=10, fill="x", padx=10)

        tk.Label(top_frame, text="비디오 파일:").pack(side="left")
        self.file_path_var = tk.StringVar()
        tk.Entry(top_frame, textvariable=self.file_path_var,
                 width=50).pack(side="left", padx=5)
        tk.Button(top_frame, text="찾아보기",
                  command=self.open_file).pack(side="left")

        # 비디오 표시 영역
        self.video_frame = tk.Frame(
            self.root, bg="black", width=640, height=360)
        self.video_frame.pack(pady=10)
        self.video_frame.pack_propagate(False)

        self.video_label = tk.Label(self.video_frame, bg="black")
        self.video_label.pack(fill="both", expand=True)

        # 컨트롤 프레임
        control_frame = tk.Frame(self.root)
        control_frame.pack(pady=10, fill="x", padx=10)

        # 시간 슬라이더
        self.time_slider = ttk.Scale(
            control_frame, from_=0, to=100, orient="horizontal", length=600, command=self.on_slider_change)
        self.time_slider.pack(pady=10)

        # 시간 표시 프레임
        time_display_frame = tk.Frame(self.root)
        time_display_frame.pack(fill="x", padx=10)

        tk.Label(time_display_frame, text="현재 시간:").grid(
            row=0, column=0, padx=5)
        self.current_time_var = tk.StringVar(value="00:00:00")
        tk.Label(time_display_frame, textvariable=self.current_time_var).grid(
            row=0, column=1, padx=5)

        tk.Label(time_display_frame, text="총 시간:").grid(
            row=0, column=2, padx=5)
        self.total_time_var = tk.StringVar(value="00:00:00")
        tk.Label(time_display_frame, textvariable=self.total_time_var).grid(
            row=0, column=3, padx=5)

        # 재생 컨트롤 프레임
        playback_frame = tk.Frame(self.root)
        playback_frame.pack(pady=10)

        self.play_btn = tk.Button(
            playback_frame, text="재생", width=10, command=self.toggle_play)
        self.play_btn.pack(side="left", padx=5)

        # 부분 추출 프레임
        extract_frame = tk.Frame(self.root)
        extract_frame.pack(pady=10, fill="x", padx=10)

        # 시작 시간
        tk.Label(extract_frame, text="시작 시간:").grid(
            row=0, column=0, padx=5, pady=5)
        self.start_time_var = tk.StringVar(value="00:00:00")
        tk.Entry(extract_frame, textvariable=self.start_time_var,
                 width=10).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(extract_frame, text="현재 시간으로 설정", command=self.set_start_time).grid(
            row=0, column=2, padx=5, pady=5)

        # 종료 시간
        tk.Label(extract_frame, text="종료 시간:").grid(
            row=1, column=0, padx=5, pady=5)
        self.end_time_var = tk.StringVar(value="00:00:00")
        tk.Entry(extract_frame, textvariable=self.end_time_var,
                 width=10).grid(row=1, column=1, padx=5, pady=5)
        tk.Button(extract_frame, text="현재 시간으로 설정", command=self.set_end_time).grid(
            row=1, column=2, padx=5, pady=5)

        # 추출 버튼
        extract_btn = tk.Button(
            self.root, text="비디오 부분 추출하기", width=20, command=self.extract_video)
        extract_btn.pack(pady=10)

        # 상태 표시줄
        self.status_var = tk.StringVar(value="준비 완료")
        status_bar = tk.Label(
            self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def open_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Video files", "*.mp4 *.avi *.mkv *.mov"),
                       ("All files", "*.*")]
        )
        if file_path:
            self.video_path = file_path
            self.file_path_var.set(file_path)
            self.load_video()

    def load_video(self):
        # 기존 비디오가 열려있으면 닫기
        if self.cap is not None:
            self.cap.release()

        try:
            # OpenCV로 비디오 열기
            self.cap = cv2.VideoCapture(self.video_path)
            if not self.cap.isOpened():
                messagebox.showerror("오류", "비디오 파일을 열 수 없습니다.")
                return

            # 비디오 정보 가져오기
            self.fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.video_duration = self.total_frames / self.fps

            # 시간 슬라이더 설정
            self.time_slider.config(to=self.video_duration)

            # 총 시간 표시
            self.total_time_var.set(self.format_time(self.video_duration))

            # 종료 시간을 비디오 전체 길이로 설정
            self.end_time_var.set(self.format_time(self.video_duration))
            self.end_time = self.video_duration

            # 첫 프레임 표시
            self.show_frame(0)

            self.status_var.set(
                f"비디오 로드 완료: {os.path.basename(self.video_path)}")
        except Exception as e:
            messagebox.showerror("오류", f"비디오 로딩 중 오류 발생: {str(e)}")

    def show_frame(self, frame_index=None):
        if self.cap is None:
            return

        if frame_index is not None:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)

        ret, frame = self.cap.read()
        if ret:
            # 현재 프레임 갱신
            self.current_frame = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
            current_time = self.current_frame / self.fps

            # 현재 시간 표시 업데이트
            self.current_time_var.set(self.format_time(current_time))

            # 슬라이더 위치 업데이트 (재생 중에만)
            if self.playing and not self.time_slider.instate(['pressed']):
                self.time_slider.set(current_time)

            # OpenCV BGR에서 RGB로 변환
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # 프레임 크기 조정
            h, w = frame_rgb.shape[:2]
            video_ratio = w / h

            display_w = 640
            display_h = int(display_w / video_ratio)

            if display_h > 360:
                display_h = 360
                display_w = int(display_h * video_ratio)

            frame_resized = cv2.resize(frame_rgb, (display_w, display_h))

            # PIL 이미지로 변환
            img = Image.fromarray(frame_resized)
            photo = ImageTk.PhotoImage(image=img)

            # 라벨에 이미지 표시
            self.video_label.config(image=photo)
            self.video_label.image = photo  # 참조 유지

            return True
        return False

    def on_slider_change(self, value):
        if self.cap is None:
            return

        # 문자열을 실수로 변환
        value = float(value)

        # 프레임 인덱스 계산
        target_frame = int(value * self.fps)

        # 프레임 표시
        self.show_frame(target_frame)

    def toggle_play(self):
        if self.cap is None:
            messagebox.showinfo("알림", "비디오 파일을 먼저 선택해주세요.")
            return

        if self.playing:
            self.playing = False
            self.play_btn.config(text="재생")
        else:
            self.playing = True
            self.play_btn.config(text="일시정지")

            # 스레드에서 비디오 재생
            if self.play_thread is None or not self.play_thread.is_alive():
                self.play_thread = threading.Thread(target=self.play_video)
                self.play_thread.daemon = True
                self.play_thread.start()

    def play_video(self):
        while self.playing:
            if not self.show_frame():
                # 비디오 끝에 도달
                self.playing = False
                self.play_btn.config(text="재생")
                # 처음으로 돌아가기
                self.show_frame(0)
                break

            # 프레임 레이트 유지를 위한 대기
            time.sleep(1/self.fps)

    def format_time(self, seconds):
        """초를 HH:MM:SS 형식으로 변환"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def parse_time(self, time_str):
        """HH:MM:SS 형식의 문자열을 초로 변환"""
        try:
            h, m, s = map(int, time_str.split(':'))
            return h * 3600 + m * 60 + s
        except:
            messagebox.showerror("오류", "시간 형식이 올바르지 않습니다. HH:MM:SS 형식을 사용하세요.")
            return 0

    def set_start_time(self):
        if self.cap is None:
            return

        current_time = self.current_frame / self.fps
        self.start_time = current_time
        self.start_time_var.set(self.format_time(current_time))

    def set_end_time(self):
        if self.cap is None:
            return

        current_time = self.current_frame / self.fps
        self.end_time = current_time
        self.end_time_var.set(self.format_time(current_time))

    def extract_video(self):
        if not self.video_path:
            messagebox.showinfo("알림", "비디오 파일을 먼저 선택해주세요.")
            return

        # 시작 및 종료 시간 가져오기
        start_time = self.parse_time(self.start_time_var.get())
        end_time = self.parse_time(self.end_time_var.get())

        if start_time >= end_time:
            messagebox.showerror("오류", "시작 시간은 종료 시간보다 작아야 합니다.")
            return

        # 저장 파일 대화상자
        output_path = filedialog.asksaveasfilename(
            defaultextension=".mp4",
            filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")]
        )

        if not output_path:
            return

        # 상태 업데이트
        self.status_var.set("비디오 추출 중...")
        self.root.update()

        try:
            # MoviePy를 사용하여 비디오 추출
            video = VideoFileClip(self.video_path)

            # 시작 시간과 종료 시간으로 비디오 자르기
            video_clip = video.subclip(start_time, end_time)

            # 비디오 저장
            video_clip.write_videofile(
                output_path,
                codec="libx264",
                audio_codec="aac"
            )

            video.close()
            video_clip.close()

            self.status_var.set(
                f"비디오 부분이 저장되었습니다: {os.path.basename(output_path)}")
            messagebox.showinfo("완료", f"비디오 부분이 성공적으로 저장되었습니다:\n{output_path}")

        except Exception as e:
            self.status_var.set("오류 발생")
            messagebox.showerror("오류", f"비디오 추출 중 오류 발생: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = VideoExtractorApp(root)
    root.mainloop()
