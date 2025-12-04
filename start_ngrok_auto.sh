#!/bin/bash
# Ngrok 자동 재시작 스크립트
# Ngrok 세션이 만료되면 자동으로 재시작

NGROK_PORT=8000
NGROK_LOG="/tmp/ngrok.log"

echo "Ngrok 자동 재시작 스크립트 시작"
echo "포트: $NGROK_PORT"
echo "로그: $NGROK_LOG"
echo ""

# Ngrok 프로세스 확인 및 종료
kill_ngrok() {
    pkill -f "ngrok http" || true
    sleep 2
}

# Ngrok 시작
start_ngrok() {
    echo "$(date): Ngrok 시작 중..." >> "$NGROK_LOG"
    ngrok http $NGROK_PORT > /dev/null 2>&1 &
    sleep 3
    echo "$(date): Ngrok 시작 완료" >> "$NGROK_LOG"
}

# Ngrok 상태 확인
check_ngrok() {
    curl -s http://localhost:4040/api/tunnels > /dev/null 2>&1
    return $?
}

# 메인 루프
while true; do
    if ! check_ngrok; then
        echo "$(date): Ngrok 연결 끊김, 재시작 중..." | tee -a "$NGROK_LOG"
        kill_ngrok
        start_ngrok
        
        # 새 URL 출력
        sleep 5
        NEW_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o 'https://[^"]*\.ngrok[^"]*' | head -1)
        if [ ! -z "$NEW_URL" ]; then
            echo "$(date): 새 Ngrok URL: $NEW_URL" | tee -a "$NGROK_LOG"
            echo "새 URL: $NEW_URL"
        fi
    fi
    
    # 5분마다 체크
    sleep 300
done

