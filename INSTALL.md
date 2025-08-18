# 비디오 플레이어 설치 가이드

## 📋 시스템 요구사항

### 운영체제
- Windows 10 이상 (64비트 권장)
- Windows 11 지원

### 필수 소프트웨어
- **VLC Media Player** (필수)
- **FFmpeg** (필수)
---

## 🚀 설치 방법

### 1단계: VLC Media Player 설치 (필수)

**⚠️ 중요: VLC가 설치되지 않으면 비디오 재생이 작동하지 않습니다.**

#### VLC 다운로드 및 설치
1. [VLC 공식 웹사이트](https://www.videolan.org/vlc/)에서 VLC Media Player 다운로드
2. **Windows 버전 선택**: "Download VLC" 클릭
3. 다운로드된 설치 파일 실행
4. 설치 마법사의 지시에 따라 설치 완료

#### VLC 설치 확인
- 설치 후 시작 메뉴에서 "VLC Media Player" 검색하여 실행 가능한지 확인
- 또는 명령 프롬프트에서 `vlc --version` 명령으로 확인

### 2단계: FFmpeg 설치 (필수)

**⚠️ 중요: FFmpeg가 설치되지 않으면 비디오/오디오/이미지 추출 기능이 작동하지 않습니다.**

FFmpeg는 다음 핵심 기능들을 위해 필요합니다:
- 비디오 구간 추출
- 오디오 추출  
- 이미지 프레임 추출

#### FFmpeg 설치 방법
1. [FFmpeg 공식 웹사이트](https://ffmpeg.org/download.html)에서 Windows 빌드 다운로드
2. 압축 해제 후 적절한 위치에 저장 (예: `C:\ffmpeg\`)
3. 시스템 PATH에 FFmpeg bin 폴더 추가:
   - 시스템 속성 → 고급 → 환경 변수
   - 시스템 변수에서 "Path" 선택 → 편집
   - `C:\ffmpeg\bin` 경로 추가

#### 방법 2: Chocolatey 사용
```bash
choco install ffmpeg
```

#### 방법 3: Winget 사용
```bash
winget install ffmpeg
```

#### FFmpeg 설치 확인
- 명령 프롬프트에서 `ffmpeg -version` 명령으로 확인

### 3단계: 비디오 플레이어 설치

1. `VideoPlayer_Setup.exe` 실행
2. 설치 마법사의 지시에 따라 진행
3. 설치 완료 후 바탕화면 또는 시작 메뉴에서 실행



## 문제 해결

### VLC 관련 오류
**증상**: 프로그램 실행 시 "VLC 초기화 실패" 오류
**해결**: 
1. VLC Media Player가 제대로 설치되었는지 확인
2. VLC를 한 번 실행하여 정상 작동하는지 확인
3. 프로그램 재시작

### FFmpeg 관련 오류  
**증상**: 추출 기능 사용 시 "FFmpeg를 찾을 수 없습니다" 메시지
**해결**:
1. FFmpeg가 설치되었는지 확인 (`ffmpeg -version`)
2. PATH 환경 변수에 FFmpeg가 추가되었는지 확인
3. 컴퓨터 재시작 후 다시 시도

### 일반적인 문제
**증상**: 프로그램이 실행되지 않음
**해결**:
1. Windows Defender나 백신 프로그램에서 차단하지 않는지 확인
2. 관리자 권한으로 실행 시도
3. 최신 Windows 업데이트 설치


## 📄 라이선스

이 소프트웨어는 다음 오픈소스 라이브러리를 사용합니다:
- VLC Media Player (GPL 라이선스)
- FFmpeg (GPL/LGPL 라이선스)
- OpenCV (Apache 2.0 라이선스)