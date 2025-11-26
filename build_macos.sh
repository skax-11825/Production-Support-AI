#!/bin/bash
# macOS/Linux용 실행 파일 빌드 스크립트

echo "========================================"
echo "macOS/Linux 실행 파일 빌드 시작"
echo "========================================"

# 가상 환경 활성화 확인
if [ -f "venv/bin/activate" ]; then
    echo "가상 환경 활성화 중..."
    source venv/bin/activate
else
    echo "경고: 가상 환경을 찾을 수 없습니다."
    echo "가상 환경을 새로 생성하려면 ./setup_env.sh 를 실행하세요."
    exit 1
fi

PY_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
if [ "$PY_VERSION" != "3.12" ]; then
    echo "[ERROR] 현재 가상환경 Python 버전이 3.12가 아닙니다. (현재: $PY_VERSION)"
    echo "        ./setup_env.sh 를 실행해 Python 3.12 기반 환경을 재구성하세요."
    exit 1
fi

# 필요한 패키지 설치 확인
echo "필요한 패키지 설치 확인 중..."
pip install -r requirements.txt

# 기존 빌드 폴더 삭제
if [ -d "dist" ]; then
    echo "기존 빌드 폴더 삭제 중..."
    rm -rf dist
fi

if [ -d "build" ]; then
    echo "기존 빌드 임시 폴더 삭제 중..."
    rm -rf build
fi

# PyInstaller로 실행 파일 빌드
echo "실행 파일 빌드 중..."
pyinstaller build.spec --clean

if [ -f "dist/question-answer-api" ]; then
    echo ""
    echo "========================================"
    echo "빌드 완료!"
    echo "========================================"
    echo "실행 파일 위치: dist/question-answer-api"
    echo ""
    echo "사용 방법:"
    echo "1. dist 폴더로 이동"
    echo "2. .env 파일을 dist 폴더에 복사"
    echo "3. ./question-answer-api 실행"
    echo ""
    
    # 실행 권한 부여
    chmod +x dist/question-answer-api
    echo "실행 권한이 부여되었습니다."
else
    echo ""
    echo "========================================"
    echo "빌드 실패!"
    echo "========================================"
    echo "오류 로그를 확인하세요."
    echo ""
    exit 1
fi

