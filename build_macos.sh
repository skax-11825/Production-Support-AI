#!/bin/bash
# macOS/Linux용 실행 파일 빌드 스크립트

set -e  # 오류 발생 시 즉시 종료

echo "========================================"
echo "macOS/Linux 실행 파일 빌드 시작"
echo "========================================"

# 가상 환경 활성화 확인
if [ -f "venv/bin/activate" ]; then
    echo "[1/6] 가상 환경 활성화 중..."
    source venv/bin/activate
else
    echo "[ERROR] 가상 환경을 찾을 수 없습니다."
    echo "        가상 환경을 새로 생성하려면 ./setup_env.sh 를 실행하세요."
    exit 1
fi

# Python 버전 확인
PY_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
if [ "$PY_VERSION" != "3.12" ]; then
    echo "[ERROR] 현재 가상환경 Python 버전이 3.12가 아닙니다. (현재: $PY_VERSION)"
    echo "        ./setup_env.sh 를 실행해 Python 3.12 기반 환경을 재구성하세요."
    exit 1
fi
echo "[2/6] Python 버전 확인: $PY_VERSION ✓"

# PyInstaller 설치 확인
if ! python -c "import PyInstaller" 2>/dev/null; then
    echo "[ERROR] PyInstaller가 설치되지 않았습니다."
    echo "        pip install pyinstaller 실행 후 다시 시도하세요."
    exit 1
fi
PYINSTALLER_VERSION=$(python -c "import PyInstaller; print(PyInstaller.__version__)")
echo "[3/6] PyInstaller 버전: $PYINSTALLER_VERSION ✓"

# 필요한 패키지 설치 확인
echo "[4/6] 필요한 패키지 설치 확인 중..."
pip install -q -r requirements.txt
echo "        패키지 설치 완료 ✓"

# 기존 빌드 폴더 삭제
echo "[5/6] 기존 빌드 폴더 정리 중..."
[ -d "dist" ] && rm -rf dist
[ -d "build" ] && rm -rf build
echo "        정리 완료 ✓"

# PyInstaller로 실행 파일 빌드
echo "[6/6] 실행 파일 빌드 중..."
if pyinstaller build.spec --clean --noconfirm; then
    echo "        빌드 성공 ✓"
else
    echo ""
    echo "========================================"
    echo "[ERROR] 빌드 실패!"
    echo "========================================"
    echo "오류 로그를 확인하세요."
    exit 1
fi

# 빌드 결과 확인
if [ -f "dist/question-answer-api" ]; then
    # 실행 권한 부여
    chmod +x dist/question-answer-api
    
    # 파일 크기 확인
    FILE_SIZE=$(du -h "dist/question-answer-api" | cut -f1)
    
    echo ""
    echo "========================================"
    echo "✓ 빌드 완료!"
    echo "========================================"
    echo "실행 파일 위치: dist/question-answer-api"
    echo "파일 크기: $FILE_SIZE"
    echo ""
    echo "사용 방법:"
    echo "  1. dist 폴더로 이동: cd dist"
    echo "  2. .env 파일 복사: cp ../.env ."
    echo "  3. 실행: ./question-answer-api"
    echo ""
    echo "주의사항:"
    echo "  - .env 파일에 Oracle DB 연결 정보가 설정되어 있어야 합니다."
    echo "  - 실행 파일과 같은 디렉토리에 .env 파일이 있어야 합니다."
    echo ""
else
    echo ""
    echo "========================================"
    echo "[ERROR] 빌드된 실행 파일을 찾을 수 없습니다!"
    echo "========================================"
    exit 1
fi

