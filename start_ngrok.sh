#!/bin/bash

# ngrok 자동 실행 스크립트

# PATH 설정
export PATH="$HOME/bin:$PATH"

# 서버가 실행 중인지 확인 (최대 30초 대기)
for i in {1..30}; do
    if lsof -ti:8000 > /dev/null 2>&1; then
        break
    fi
    sleep 1
done

# 서버가 실행 중이 아니면 종료
if ! lsof -ti:8000 > /dev/null 2>&1; then
    echo "$(date): 서버가 실행 중이 아닙니다. ngrok을 시작할 수 없습니다." >> /tmp/ngrok.log
    exit 1
fi

# 기존 ngrok 프로세스 종료
pkill -f "ngrok http 8000" 2>/dev/null
sleep 2

# ngrok 실행
echo "$(date): ngrok을 시작합니다." >> /tmp/ngrok.log
export PATH="$HOME/bin:$PATH"
ngrok http 8000 --log=stdout >> /tmp/ngrok.log 2>&1

