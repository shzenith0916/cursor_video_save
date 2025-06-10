import ttkbootstrap as ttk
from ttkbootstrap import Window
from utils.styles import AppStyles

# 테스트 윈도우 생성 (ttkbootstrap 방식)
root = Window(themename="flatly")  # 또는 "litera", "journal", "darkly" 등
root.title('버튼 색상 테스트 - 기본 vs AppStyles vs TTKBootstrap ')
root.geometry('800x700')

style = ttk.Style()

# utils/styles.py의 스타일 적용
AppStyles.configure_styles(style)

# ======= 스크롤 가능한 프레임 생성 =======

# 메인 프레임과 스크롤바 생성
main_frame = ttk.Frame(root)
main_frame.pack(fill='both', expand=True, padx=10, pady=10)

# 캔버스와 스크롤바 생성
canvas = ttk.Canvas(main_frame)
scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
scrollable_frame = ttk.Frame(canvas)

scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

# 레이아웃 배치
canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# 마우스 휠 스크롤 바인딩


def _on_mousewheel(event):
    canvas.yview_scroll(int(-1*(event.delta/120)), "units")


canvas.bind_all("<MouseWheel>", _on_mousewheel)


# ======= 버튼들 생성 (scrollable_frame에 추가) =======

# ============ AppStyles 테스트 ============
ttk.Label(scrollable_frame, text='=== AppStyles 스타일 ===',
          font=('Arial', 12, 'bold')).pack(pady=(20, 10))

pastel_btn1 = ttk.Button(
    scrollable_frame, text='1Pastel.TButton ⚠️', style='1Pastel.TButton')
pastel_btn1.pack(pady=5)

pastel_btn2 = ttk.Button(
    scrollable_frame, text='2Pastel.TButton 🚀', style='2Pastel.TButton')
pastel_btn2.pack(pady=5)

pastel_btn3 = ttk.Button(
    scrollable_frame, text='3Pastel.TButton ⏯️', style='3Pastel.TButton')
pastel_btn3.pack(pady=5)

# ========= 파스텔 스타일들 =========
ttk.Label(scrollable_frame, text='=== 파스텔 스타일 ===',
          font=('Arial', 12, 'bold')).pack(pady=(20, 10))

pastel_outline_btn = ttk.Button(
    scrollable_frame, text='PastelGreenOutline.TButton 🌿', style='PastelGreenOutline.TButton')
pastel_outline_btn.pack(pady=5)

deep_teal_btn = ttk.Button(
    scrollable_frame, text='DeepTeal.TButton 🌊', style='DeepTeal.TButton')
deep_teal_btn.pack(pady=5)

forest_green_btn = ttk.Button(
    scrollable_frame, text='ForestGreen.TButton 🌲', style='ForestGreen.TButton')
forest_green_btn.pack(pady=5)


# ========= 새로운 재생/정지 아웃라인 스타일들 =========
ttk.Label(scrollable_frame, text='=== 새로운 재생/정지 아웃라인 스타일 ===',
          font=('Arial', 12, 'bold')).pack(pady=(20, 10))

play_outline_btn = ttk.Button(
    scrollable_frame, text='▶ 재생 (PlayOutline.TButton)', style='PlayOutline.TButton')
play_outline_btn.pack(pady=5)

stop_outline_btn = ttk.Button(
    scrollable_frame, text='■ 정지 (StopOutline.TButton)', style='StopOutline.TButton')
stop_outline_btn.pack(pady=5)

# 아이콘 크기 비교용 추가 버튼들
ttk.Label(scrollable_frame, text='=== 아이콘 크기/스타일 비교 ===',
          font=('Arial', 10, 'bold')).pack(pady=(10, 5))

icon_test_frame = ttk.Frame(scrollable_frame)
icon_test_frame.pack(pady=5)

# 다양한 아이콘 옵션들
play_options = ['▶', '⏵', '▷', '►']
stop_options = ['■', '⏹', '◼', '⬛']
temp_stop_options = ['⏸', '||', '⏸', '❚❚']

for i, play_icon in enumerate(play_options):
    btn = ttk.Button(
        icon_test_frame, text=f'{play_icon} 재생{i+1}', style='PlayOutline.TButton', width=10)
    btn.grid(row=0, column=i, padx=2, pady=2)

for i, stop_icon in enumerate(stop_options):
    btn = ttk.Button(
        icon_test_frame, text=f'{stop_icon} 정지{i+1}', style='StopOutline.TButton', width=10)
    btn.grid(row=1, column=i, padx=2, pady=2)

for i, temp_stop_icon in enumerate(temp_stop_options):
    btn = ttk.Button(
        icon_test_frame, text=f'{temp_stop_icon} 일시정지{i+1}', style='WarningOutline.TButton', width=10)
    btn.grid(row=2, column=i, padx=2, pady=2)

# 일시정지 아이콘 테스트
ttk.Label(scrollable_frame, text='=== 일시정지 아이콘 옵션들 ===',
          font=('Arial', 10, 'bold')).pack(pady=(15, 5))

pause_test_frame = ttk.Frame(scrollable_frame)
pause_test_frame.pack(pady=5)

# 다양한 일시정지 아이콘 옵션들
pause_options = [
    ('❚❚ 일시정지', '현재 사용'),
    ('|| 일시정지', '얇은 세로선'),
    ('▐▌ 일시정지', '블록 형태'),
    ('∥ 일시정지', '평행선'),
    ('⏯ 일시정지', '토글 아이콘'),
    ('⫸ 일시정지', '더블바'),
    ('⊡⊡ 일시정지', '사각 점들'),
    ('⦀⦀ 일시정지', '원형 점들'),
    ('⏮⏸ 일시정지', '이전+정지'),
    ('일시정지', '텍스트만')
]

for i, (pause_text, description) in enumerate(pause_options):
    row = i // 5  # 5개씩 한 줄
    col = i % 5
    btn = ttk.Button(
        pause_test_frame, text=pause_text, style='PlayOutline.TButton', width=12)
    btn.grid(row=row, column=col, padx=2, pady=2)

    # 설명 레이블 (작게)
    desc_label = ttk.Label(
        pause_test_frame, text=description, font=('Arial', 8))
    desc_label.grid(row=row+2, column=col, padx=2, pady=(0, 5))


# ========= TTKBootstrap 기본 스타일들 =========
ttk.Label(scrollable_frame, text='=== TTKBootstrap 기본 스타일 ===',
          font=('Arial', 12, 'bold')).pack(pady=(20, 10))

primary_btn = ttk.Button(
    scrollable_frame, text='Primary 버튼 💙', bootstyle="primary")
primary_btn.pack(pady=3)

secondary_btn = ttk.Button(
    scrollable_frame, text='Secondary 버튼 🩶', bootstyle="secondary")
secondary_btn.pack(pady=3)

success_bootstrap_btn = ttk.Button(
    scrollable_frame, text='Success 버튼 💚', bootstyle="success")
success_bootstrap_btn.pack(pady=3)

info_btn = ttk.Button(scrollable_frame, text='Info 버튼 💎', bootstyle="info")
info_btn.pack(pady=3)

warning_btn = ttk.Button(
    scrollable_frame, text='Warning 버튼 ⚠️', bootstyle="warning")
warning_btn.pack(pady=3)

danger_bootstrap_btn = ttk.Button(
    scrollable_frame, text='Danger 버튼 ❤️', bootstyle="danger")
danger_bootstrap_btn.pack(pady=3)

light_btn = ttk.Button(scrollable_frame, text='Light 버튼 🤍', bootstyle="light")
light_btn.pack(pady=3)

dark_btn = ttk.Button(scrollable_frame, text='Dark 버튼 🖤', bootstyle="dark")
dark_btn.pack(pady=3)

# ========= Outline 스타일들도 추가 =========
ttk.Label(scrollable_frame, text='=== TTKBootstrap Outline 스타일 ===',
          font=('Arial', 12, 'bold')).pack(pady=(20, 10))

primary_outline_btn = ttk.Button(
    scrollable_frame, text='Primary Outline 💙', bootstyle="primary-outline")
primary_outline_btn.pack(pady=3)

success_outline_btn = ttk.Button(
    scrollable_frame, text='Success Outline 💚', bootstyle="success-outline")
success_outline_btn.pack(pady=3)

danger_outline_btn = ttk.Button(
    scrollable_frame, text='Danger Outline ❤️', bootstyle="danger-outline")
danger_outline_btn.pack(pady=3)

warning_outline_btn = ttk.Button(
    scrollable_frame, text='Warning Outline ⚠️', bootstyle="warning-outline")
warning_outline_btn.pack(pady=3)

info_outline_btn = ttk.Button(
    scrollable_frame, text='Info Outline 💎', bootstyle="info-outline")
info_outline_btn.pack(pady=3)

# 상태 표시 (고정 위치)
status_frame = ttk.Frame(root, style='info.TFrame')
status_frame.pack(fill='x', side='bottom', padx=10, pady=5)

status_label = ttk.Label(
    status_frame, text='클릭한 버튼이 여기에 표시됩니다. 마우스 휠로 스크롤하세요!', font=('Arial', 11, 'bold'))
status_label.pack(pady=10)


def on_button_click(button_name):
    status_label.config(text=f'✅ {button_name} 클릭됨!')


# 모든 버튼에 클릭 이벤트 추가\
buttons_info = [
    (pastel_btn1, '1Pastel.TButton'),
    (pastel_btn2, '2Pastel.TButton'),
    (pastel_btn3, '3Pastel.TButton'),
    (pastel_outline_btn, 'PastelGreenOutline.TButton'),
    (deep_teal_btn, 'DeepTeal.TButton'),        # 새로 추가
    (forest_green_btn, 'ForestGreen.TButton'),  # 새로 추가
    (play_outline_btn, 'PlayOutline.TButton'),  # 새로 추가 ⭐
    (stop_outline_btn, 'StopOutline.TButton'),  # 새로 추가 ⭐
    (primary_btn, 'Bootstrap Primary'),
    (secondary_btn, 'Bootstrap Secondary'),
    (success_bootstrap_btn, 'Bootstrap Success'),
    (info_btn, 'Bootstrap Info'),
    (warning_btn, 'Bootstrap Warning'),
    (danger_bootstrap_btn, 'Bootstrap Danger'),
    (light_btn, 'Bootstrap Light'),
    (dark_btn, 'Bootstrap Dark'),
    (primary_outline_btn, 'Bootstrap Primary Outline'),
    (success_outline_btn, 'Bootstrap Success Outline'),
    (danger_outline_btn, 'Bootstrap Danger Outline'),
    (warning_outline_btn, 'Bootstrap Warning Outline'),
    (info_outline_btn, 'Bootstrap Info Outline')
]

for btn, name in buttons_info:
    btn.config(command=lambda n=name: on_button_click(n))

print('=== TTKBootstrap 버튼 색상 테스트 ===')
print('1. AppStyles 커스텀 스타일들')
print('2. 파스텔 스타일들')
print('3. TTKBootstrap 기본 스타일들')
print('4. TTKBootstrap Outline 스타일들')
print('🖱️ 각 버튼을 클릭해보세요!')
print(f'현재 테마: flatly')

root.mainloop()
