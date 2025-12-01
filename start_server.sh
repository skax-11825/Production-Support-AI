#!/bin/bash
# 서버 시작 스크립트 (macOS/Linux)
# 더블클릭으로 실행 가능

cd "$(dirname "$0")"

echo "============================================================"
echo "질문-답변 API 서버 시작"
echo "============================================================"
echo ""

# 가상환경 확인
if [ ! -f "venv/bin/python3" ]; then
    echo "❌ 가상환경을 찾을 수 없습니다."
    echo "먼저 다음 명령어를 실행하세요:"
    echo "  ./setup_env.sh"
    echo ""
    read -p "아무 키나 눌러 종료하세요..."
    exit 1
fi

# 환경 변수 파일 확인
if [ ! -f ".env" ]; then
    echo "⚠️  .env 파일을 찾을 수 없습니다."
    echo "서버 시작을 계속합니다..."
    echo ""
fi

echo "============================================================"
echo "서버 시작 중..."
echo "============================================================"
echo ""
echo "서버 URL: http://localhost:8000"
echo "헬스 체크: http://localhost:8000/health"
echo "API 문서: http://localhost:8000/docs"
echo ""
echo "서버를 종료하려면 Ctrl+C를 누르세요."
echo "============================================================"
echo ""

# 서버 실행
source venv/bin/activate
python3 main.py
