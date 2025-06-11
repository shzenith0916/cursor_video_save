import tkinter as tk
import tkinter.font as tkFont


def check_fonts():
    # tkinter 초기화
    root = tk.Tk()
    root.withdraw()  # 창 숨기기

    # 사용 가능한 폰트 목록 가져오기
    available_fonts = sorted(tkFont.families())

    print("=== 시스템에서 사용 가능한 폰트 목록 ===")
    print(f"총 {len(available_fonts)}개의 폰트가 설치되어 있습니다.\n")

    # Open Sans 관련 폰트 찾기
    open_sans_fonts = [
        font for font in available_fonts if 'open sans' in font.lower()]

    if open_sans_fonts:
        print("✅ Open Sans 관련 폰트가 발견되었습니다:")
        for font in open_sans_fonts:
            print(f"  - {font}")
    else:
        print("❌ Open Sans 폰트가 설치되어 있지 않습니다.")

    print("\n=== 추천 대체 폰트들 ===")
    recommended_fonts = [
        "Segoe UI",
        "Roboto",
        "Helvetica",
        "Calibri",
        "Verdana",
        "Tahoma",
        "DejaVu Sans",
        "Liberation Sans"
    ]

    available_recommended = []
    for font in recommended_fonts:
        if font in available_fonts:
            available_recommended.append(font)
            print(f"✅ {font}")
        else:
            print(f"❌ {font}")

    print(f"\n=== 사용 가능한 모든 폰트 (처음 20개) ===")
    for i, font in enumerate(available_fonts[:20]):
        print(f"{i+1:2d}. {font}")

    if len(available_fonts) > 20:
        print(f"... 그 외 {len(available_fonts) - 20}개 더")

    root.destroy()

    return open_sans_fonts, available_recommended


if __name__ == "__main__":
    open_sans_fonts, recommended = check_fonts()
