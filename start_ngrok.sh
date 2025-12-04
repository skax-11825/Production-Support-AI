#!/bin/bash
# Ngrok 터널 시작 스크립트 (macOS/Linux)

cd "$(dirname "$0")"

PORT=${1:-8000}

echo "============================================================"
echo "  Ngrok 터널 시작"
echo "============================================================"
echo ""

# Ngrok 확인
if ! command -v ngrok &> /dev/null; then
    echo "❌ Ngrok을 찾을 수 없습니다."
    echo "  Ngrok을 설치하고 PATH에 추가하세요."
    echo "  다운로드: https://ngrok.com/download"
    echo "  또는: brew install ngrok/ngrok/ngrok"
    exit 1
fi

echo "Ngrok 터널 시작 중 (포트 $PORT)..."
echo "  로컬 서버가 http://localhost:$PORT 에서 실행 중이어야 합니다."
echo ""
echo "Ngrok 대시보드: http://localhost:4040"
echo "종료하려면 Ctrl+C를 누르세요."
echo "============================================================"
echo ""

ngrok http $PORT

