#!/bin/bash

# API 서버 + ngrok 통합 실행 스크립트 (macOS/Linux)

# 스크립트가 위치한 디렉토리로 이동
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================================"
echo "API 서버 + ngrok 통합 실행 스크립트 (macOS/Linux)"
echo "============================================================"

# 가상환경 Python 경로 설정
VENV_PYTHON="$SCRIPT_DIR/venv/bin/python3"

if [ -f "$VENV_PYTHON" ]; then
    echo "✅ 가상환경 Python 사용: $VENV_PYTHON"
    PYTHON_EXEC="$VENV_PYTHON"
else
    echo "⚠ 경고: 가상환경 Python을 찾을 수 없습니다. 시스템 Python을 사용합니다."
    echo "✅ 시스템 Python 사용"
    PYTHON_EXEC="python3"
fi

# .env 파일 확인
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo "❌ 오류: .env 파일이 프로젝트 루트에 없습니다."
    echo "     Oracle DB 연결 정보가 포함된 .env 파일을 생성해주세요."
    echo "     자세한 내용은 README.md를 참조하세요."
    exit 1
fi
echo "✅ .env 파일 확인: $SCRIPT_DIR/.env"

# 기존 프로세스 종료
echo ""
echo "============================================================"
echo "1. 기존 프로세스 종료 중..."
echo "============================================================"

# 기존 서버 프로세스 종료
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "기존 서버 프로세스 종료 중..."
    lsof -ti:8000 | xargs kill -9 > /dev/null 2>&1
    sleep 2
fi

# 기존 ngrok 프로세스 종료
pkill -f "ngrok http 8000" > /dev/null 2>&1
sleep 2

# 서버 시작
echo ""
echo "============================================================"
echo "2. API 서버 시작 중..."
echo "============================================================"
"$PYTHON_EXEC" -c "import uvicorn; uvicorn.run('main:app', host='0.0.0.0', port=8000, log_level='info')" > server.log 2>&1 &
SERVER_PID=$!

echo "서버 프로세스 ID: $SERVER_PID"

# 서버 시작 대기
echo "서버 시작 대기 중..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo " ✅"
        SERVER_READY=1
        break
    fi
    echo -n "."
    sleep 1
done

if [ "$SERVER_READY" != "1" ]; then
    echo " ❌ (타임아웃)"
    echo "서버가 시작되지 않았습니다. 로그를 확인하세요: server.log"
    kill $SERVER_PID 2>/dev/null
    exit 1
fi

# ngrok 경로 찾기
echo ""
echo "============================================================"
echo "3. ngrok 터널 시작 중..."
echo "============================================================"

NGROK_PATH=""
if [ -f "$HOME/bin/ngrok" ]; then
    NGROK_PATH="$HOME/bin/ngrok"
elif [ -f "/usr/local/bin/ngrok" ]; then
    NGROK_PATH="/usr/local/bin/ngrok"
elif [ -f "/usr/bin/ngrok" ]; then
    NGROK_PATH="/usr/bin/ngrok"
else
    NGROK_PATH="ngrok"
fi

echo "ngrok 경로: $NGROK_PATH"

# ngrok 시작
export PATH="$HOME/bin:$PATH"
"$NGROK_PATH" http 8000 --log=stdout > ngrok.log 2>&1 &
NGROK_PID=$!

echo "ngrok 프로세스 ID: $NGROK_PID"

sleep 3

echo ""
echo "============================================================"
echo "✅ 모든 서비스가 시작되었습니다!"
echo "============================================================"
echo ""
echo "서버 URL: http://localhost:8000"
echo "ngrok 웹 UI: http://127.0.0.1:4040"
echo ""
echo "서버 로그: server.log"
echo "ngrok 로그: ngrok.log"
echo ""
echo "종료하려면 Ctrl+C를 누르세요..."
echo "============================================================"

# 종료 핸들러
cleanup() {
    echo ""
    echo "종료 신호 수신..."
    echo "모든 프로세스 종료 중..."
    
    kill $SERVER_PID 2>/dev/null
    kill $NGROK_PID 2>/dev/null
    pkill -f "ngrok http 8000" > /dev/null 2>&1
    lsof -ti:8000 | xargs kill -9 > /dev/null 2>&1
    
    sleep 2
    
    echo "✅ 모든 서비스가 종료되었습니다."
    exit 0
}

trap cleanup SIGINT SIGTERM

# 대기
wait

