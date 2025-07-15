import ttkbootstrap as ttb
from ttkbootstrap.constants import *
import threading
import time


class ProgressBarDemo:
    def __init__(self):
        # 윈도우 생성
        self.root = ttb.Window(themename="superhero")
        self.root.title("ttkbootstrap 프로그레스바 데모")
        self.root.geometry("600x1000")

        # 프로그레스바들을 저장할 리스트
        self.progressbars = []

        # 스크롤 가능한 프레임 생성
        self.create_scrollable_frame()

        # UI 생성
        self.create_widgets()

    def create_scrollable_frame(self):
        """스크롤 가능한 프레임 생성"""
        # 캔버스와 스크롤바 생성
        canvas = ttb.Canvas(self.root)
        scrollbar = ttb.Scrollbar(
            self.root, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttb.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # 마우스 휠 스크롤 이벤트
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # 패킹
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 컨테이너를 scrollable_frame으로 설정
        self.container = self.scrollable_frame

    def create_widgets(self):
        # 제목
        title = ttb.Label(
            self.container,
            text="🎨 ttkbootstrap 프로그레스바 스타일 테스트",
            font=("Arial", 18, "bold")
        )
        title.pack(pady=20)

        # 컨트롤 프레임을 맨 위에 배치
        control_frame = ttb.LabelFrame(
            self.container, text="🎛️ 컨트롤 패널", padding=15)
        control_frame.pack(fill="x", padx=20, pady=10)

        # 슬라이더로 프로그레스바 값 조절
        slider_label = ttb.Label(
            control_frame, text="🎚️ 프로그레스바 값 조절 (드래그하세요):", font=("Arial", 12))
        slider_label.pack(anchor="w", pady=(0, 8))

        self.progress_var = ttb.IntVar(value=0)

        # 슬라이더 프레임
        slider_frame = ttb.Frame(control_frame)
        slider_frame.pack(fill="x", pady=(0, 15))

        # 현재 값 표시 (왼쪽)
        self.current_value_label = ttb.Label(
            slider_frame, text="0%", font=("Arial", 14, "bold"))
        self.current_value_label.pack(side="left", padx=(0, 15))

        # 슬라이더 (중앙)
        self.slider = ttb.Scale(
            slider_frame,
            from_=0,
            to=100,
            orient="horizontal",
            variable=self.progress_var,
            command=self.on_slider_change,
            bootstyle="info",
            length=450
        )
        self.slider.pack(side="left", fill="x", expand=True)

        # 최대값 표시 (오른쪽)
        max_label = ttb.Label(slider_frame, text="100%", font=("Arial", 12))
        max_label.pack(side="left", padx=(15, 0))

        # 버튼들
        button_frame = ttb.Frame(control_frame)
        button_frame.pack(pady=10)

        # 자동 애니메이션 버튼
        start_btn = ttb.Button(
            button_frame,
            text="🎬 자동 애니메이션",
            command=self.start_progress,
            bootstyle="success",
            width=15
        )
        start_btn.pack(side="left", padx=8)

        # 25%, 50%, 75%, 100% 버튼들
        quick_buttons = [
            ("25%", 25, "info"),
            ("50%", 50, "warning"),
            ("75%", 75, "success"),
            ("100%", 100, "danger")
        ]

        for text, value, style in quick_buttons:
            btn = ttb.Button(
                button_frame,
                text=text,
                command=lambda v=value: self.set_progress(v),
                bootstyle=style,
                width=8
            )
            btn.pack(side="left", padx=3)

        # 리셋 버튼
        reset_btn = ttb.Button(
            button_frame,
            text="🔄 리셋",
            command=self.reset_progress,
            bootstyle="secondary",
            width=10
        )
        reset_btn.pack(side="left", padx=8)

        # 현재 값 표시 레이블
        self.status_label = ttb.Label(
            control_frame,
            text="준비됨 - 슬라이더나 버튼을 사용해보세요!",
            font=("Arial", 12),
            bootstyle="info"
        )
        self.status_label.pack(pady=10)

        # 다양한 스타일의 프로그레스바들
        styles = [
            ("Primary", "primary"),
            ("Success", "success"),
            ("Info", "info"),
            ("Warning", "warning"),
            ("Danger", "danger"),
            ("Success Striped", "success-striped"),
            ("Danger Striped", "danger-striped")
        ]

        # 프로그레스바들
        progressbar_frame = ttb.LabelFrame(
            self.container, text="📊 프로그레스바 스타일들", padding=15)
        progressbar_frame.pack(fill="x", padx=20, pady=15)

        for i, (name, style) in enumerate(styles):
            # 스타일별 컨테이너
            style_container = ttb.Frame(progressbar_frame)
            style_container.pack(fill="x", pady=8)

            # 스타일 이름과 설명
            if "striped" in style:
                icon = "🎪"
                description = f"{name} (줄무늬 패턴)"
            else:
                icon = "🎯"
                description = f"{name} (단색)"

            label = ttb.Label(
                style_container,
                text=f"{icon} {description}:",
                font=("Arial", 11, "bold")
            )
            label.pack(anchor="w", pady=(0, 5))

            # 프로그레스바
            pb = ttb.Progressbar(
                style_container,
                bootstyle=style,
                length=500,
                mode='determinate'
            )
            pb.pack(fill="x", pady=(0, 5))
            self.progressbars.append(pb)

            # 구분선 (마지막이 아닌 경우)
            if i < len(styles) - 1:
                separator = ttb.Separator(
                    progressbar_frame, orient="horizontal")
                separator.pack(fill="x", pady=5)

        # 설명 텍스트
        info_frame = ttb.LabelFrame(self.container, text="💡 사용법", padding=10)
        info_frame.pack(fill="x", padx=20, pady=10)

        info_text = ttb.Label(
            info_frame,
            text="• 슬라이더를 드래그하거나 버튼을 클릭해서 모든 프로그레스바를 동시에 제어하세요\n" +
                 "• 일반 스타일과 줄무늬(Striped) 스타일의 차이를 비교해보세요\n" +
                 "• 각 색상별로 다른 용도에 맞게 사용할 수 있습니다",
            font=("Arial", 10),
            justify="left"
        )
        info_text.pack(anchor="w")

    def on_slider_change(self, value):
        """슬라이더 값이 변경될 때 모든 프로그레스바 업데이트"""
        try:
            progress_value = int(float(value))

            # 현재 값 레이블 업데이트
            self.current_value_label.config(text=f"{progress_value}%")

            # 모든 프로그레스바 업데이트
            for pb in self.progressbars:
                pb['value'] = progress_value

            # 상태 표시
            if progress_value == 0:
                status = "시작점"
            elif progress_value < 25:
                status = "초기 단계"
            elif progress_value < 50:
                status = "진행 중"
            elif progress_value < 75:
                status = "절반 이상 완료"
            elif progress_value < 100:
                status = "거의 완료"
            else:
                status = "완료! 🎉"

            self.status_label.config(
                text=f"슬라이더: {progress_value}% - {status}")

        except Exception as e:
            print(f"슬라이더 오류: {e}")

    def set_progress(self, value):
        """특정 값으로 프로그레스바 설정"""
        self.progress_var.set(value)
        self.current_value_label.config(text=f"{value}%")

        # 직접 업데이트도 호출
        for pb in self.progressbars:
            pb['value'] = value

        self.status_label.config(text=f"버튼으로 설정: {value}% 완료")

    def start_progress(self):
        """프로그레스바 자동 애니메이션 시작"""
        def animate():
            self.status_label.config(text="자동 애니메이션 실행 중...")

            for i in range(101):
                # 슬라이더 값도 함께 업데이트
                self.progress_var.set(i)
                self.current_value_label.config(text=f"{i}%")

                # 모든 프로그레스바 업데이트
                for pb in self.progressbars:
                    pb['value'] = i

                # 상태 표시
                self.status_label.config(
                    text=f"자동 애니메이션: {i}% (각 스타일의 차이를 관찰해보세요!)")

                # UI 업데이트
                self.root.update()
                time.sleep(0.04)

            self.status_label.config(text="애니메이션 완료! 🎉 다시 테스트해보세요")

        # 별도 스레드에서 실행 (UI 블로킹 방지)
        thread = threading.Thread(target=animate)
        thread.daemon = True
        thread.start()

    def reset_progress(self):
        """모든 프로그레스바 리셋"""
        self.progress_var.set(0)
        self.current_value_label.config(text="0%")

        for pb in self.progressbars:
            pb['value'] = 0

        self.status_label.config(text="모든 프로그레스바가 리셋됨 - 다시 시작하세요!")

    def run(self):
        """프로그램 실행"""
        self.root.mainloop()


if __name__ == "__main__":
    # 프로그램 실행
    demo = ProgressBarDemo()
    demo.run()
