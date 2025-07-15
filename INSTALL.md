# 설치 가이드

## Python 패키지 설치
```bash
pip install -r requirements.txt
```

## FFmpeg 설치

이 프로젝트는 비디오 편집을 위해 FFmpeg가 필요합니다.

### Windows에서 FFmpeg 설치

#### 방법 1: 공식 웹사이트에서 다운로드
1. https://ffmpeg.org/download.html 방문
2. Windows builds 다운로드
3. 압축 해제 후 원하는 폴더에 저장
4. 시스템 환경변수 PATH에 FFmpeg bin 폴더 경로 추가

#### 방법 2: Chocolatey 사용
```bash
choco install ffmpeg
```

#### 방법 3: Winget 사용
```bash
winget install ffmpeg
```

### 설치 확인
설치 후 터미널에서 다음 명령어로 확인:
```bash
ffmpeg -version
```

### 문제 해결
- FFmpeg가 설치되었는데도 "FFmpeg가 설치되지 않았습니다" 오류가 발생하면 PATH 환경변수를 확인하세요.
- 시스템 재시작 후 다시 시도해보세요. 