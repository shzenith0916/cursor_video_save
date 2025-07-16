#!/bin/bash

echo "🚀 비디오 플레이어 실행파일 빌드 시작"
echo "======================================"

echo
echo "1. PyInstaller 설치 확인 중..."
if python -c "import PyInstaller; print('✓ PyInstaller 설치됨')" 2>/dev/null; then
    echo "✓ PyInstaller 설치됨"
else
    echo "❌ PyInstaller가 설치되지 않았습니다."
    echo "PyInstaller를 설치합니다..."
    pip install pyinstaller
    if [ $? -ne 0 ]; then
        echo "❌ PyInstaller 설치 실패"
        exit 1
    fi
fi

echo
echo "2. 빌드 스크립트 실행 중..."
python build.py

echo
echo "빌드 완료!"
echo "dist 폴더에서 실행파일을 확인하세요." 