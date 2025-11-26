#!/bin/bash
# Python 3.12 전용 가상환경 생성/재생성 스크립트
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

PYTHON_BIN="${PYTHON_BIN:-python3.12}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "[ERROR] '$PYTHON_BIN' 실행 파일을 찾을 수 없습니다."
  echo "        PYTHON_BIN=/절대/경로/python3.12 형태로 지정해 주세요."
  exit 1
fi

echo "[INFO] Python 실행 파일: $PYTHON_BIN"
echo "[INFO] 기존 가상환경 제거..."
rm -rf venv

echo "[INFO] 새 가상환경 생성..."
"$PYTHON_BIN" -m venv venv
source venv/bin/activate

echo "[INFO] pip 업그레이드..."
python -m pip install --upgrade pip

echo "[INFO] 의존성 설치..."
python -m pip install -r requirements.txt

echo "[INFO] 설치 검증..."
python -c "import sys; print('Python version:', sys.version)"
python -m pip show oracledb >/dev/null 2>&1 && echo "[INFO] oracledb 설치 확인 완료"

echo "[INFO] 가상환경이 Python 3.12 기반으로 준비되었습니다."

