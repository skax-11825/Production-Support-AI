#!/bin/bash
# Inform Note API 서버 - 통합 시작 스크립트 (macOS/Linux)

cd "$(dirname "$0")"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

show_menu() {
    clear
    echo "============================================================"
    echo "  Inform Note API 서버 - 시작 메뉴"
    echo "============================================================"
    echo ""
    echo "  1. 서버 실행 (Docker Compose 또는 로컬 서버)"
    echo "  2. Ngrok 터널 실행"
    echo "  3. 기타 도구 (DB 상태 확인 등)"
    echo "  4. 통합 실행 (서버 + Ngrok)"
    echo "  5. 종료"
    echo ""
    echo "============================================================"
}

start_server() {
    clear
    echo "============================================================"
    echo "  서버 실행"
    echo "============================================================"
    echo ""
    
    # Docker Compose 확인
    if command -v docker-compose &> /dev/null || command -v docker &> /dev/null; then
        echo "Docker Compose를 사용하여 서버를 시작합니다..."
        echo ""
        
        if command -v docker-compose &> /dev/null; then
            docker-compose up -d
        elif command -v docker &> /dev/null; then
            docker compose up -d
        fi
        
        if [ $? -eq 0 ]; then
            echo ""
            echo -e "${GREEN}✓ Docker Compose로 서버가 시작되었습니다.${NC}"
            echo "  서버 URL: http://localhost:8000"
            echo "  API 문서: http://localhost:8000/docs"
            echo ""
            read -p "계속하려면 Enter를 누르세요..."
            return
        else
            echo ""
            echo -e "${YELLOW}⚠ Docker Compose 실행 실패. 로컬 서버를 시작합니다...${NC}"
            echo ""
        fi
    else
        echo "Docker Compose를 찾을 수 없습니다. 로컬 서버를 시작합니다..."
        echo ""
    fi
    
    # 로컬 서버 시작
    if [ ! -f "venv/bin/python3" ]; then
        echo -e "${RED}❌ 가상환경을 찾을 수 없습니다.${NC}"
        echo "  먼저 가상환경을 생성하세요: python3 -m venv venv"
        echo ""
        read -p "계속하려면 Enter를 누르세요..."
        return
    fi
    
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}⚠️  .env 파일을 찾을 수 없습니다.${NC}"
        echo "  서버 시작을 계속합니다..."
        echo ""
    fi
    
    echo "서버 시작 중..."
    echo ""
    
    # 백그라운드로 서버 실행
    source venv/bin/activate
    nohup python3 main.py > server.log 2>&1 &
    SERVER_PID=$!
    
    echo -e "${GREEN}✓ 서버가 시작되었습니다 (PID: $SERVER_PID)${NC}"
    echo "  서버 URL: http://localhost:8000"
    echo "  API 문서: http://localhost:8000/docs"
    echo "  로그 파일: server.log"
    echo ""
    echo "서버를 종료하려면: kill $SERVER_PID"
    echo ""
    read -p "계속하려면 Enter를 누르세요..."
}

start_ngrok() {
    clear
    echo "============================================================"
    echo "  Ngrok 터널 실행"
    echo "============================================================"
    echo ""
    
    # Ngrok 확인
    if ! command -v ngrok &> /dev/null; then
        echo -e "${RED}❌ Ngrok을 찾을 수 없습니다.${NC}"
        echo "  Ngrok을 설치하고 PATH에 추가하세요."
        echo "  다운로드: https://ngrok.com/download"
        echo "  또는: brew install ngrok/ngrok/ngrok"
        echo ""
        read -p "계속하려면 Enter를 누르세요..."
        return
    fi
    
    # 포트 확인 (기본값 8000)
    NGROK_PORT=8000
    
    echo "Ngrok 터널 시작 중 (포트 $NGROK_PORT)..."
    echo "  로컬 서버가 실행 중이어야 합니다."
    echo ""
    
    # 백그라운드로 Ngrok 실행
    nohup ngrok http $NGROK_PORT > ngrok.log 2>&1 &
    NGROK_PID=$!
    
    echo -e "${GREEN}✓ Ngrok이 시작되었습니다 (PID: $NGROK_PID)${NC}"
    echo "  Ngrok 대시보드: http://localhost:4040"
    echo "  로그 파일: ngrok.log"
    echo ""
    echo "Ngrok을 종료하려면: kill $NGROK_PID"
    echo ""
    read -p "계속하려면 Enter를 누르세요..."
}

show_tools() {
    clear
    echo "============================================================"
    echo "  기타 도구"
    echo "============================================================"
    echo ""
    echo "  1. DB 연결 상태 확인"
    echo "  2. Docker Compose 상태 확인"
    echo "  3. 서버 로그 확인"
    echo "  4. Ngrok 로그 확인"
    echo "  5. 뒤로 가기"
    echo ""
    read -p "선택하세요 (1-5): " tool_choice
    
    case $tool_choice in
        1)
            clear
            echo "============================================================"
            echo "  DB 연결 상태 확인"
            echo "============================================================"
            echo ""
            if [ -f "venv/bin/python3" ]; then
                source venv/bin/activate
                python3 test_connection.py
            else
                echo -e "${RED}❌ 가상환경을 찾을 수 없습니다.${NC}"
            fi
            echo ""
            read -p "계속하려면 Enter를 누르세요..."
            show_tools
            ;;
        2)
            clear
            echo "============================================================"
            echo "  Docker Compose 상태 확인"
            echo "============================================================"
            echo ""
            if command -v docker-compose &> /dev/null; then
                docker-compose ps
            elif command -v docker &> /dev/null; then
                docker compose ps
            else
                echo -e "${RED}❌ Docker Compose를 찾을 수 없습니다.${NC}"
            fi
            echo ""
            read -p "계속하려면 Enter를 누르세요..."
            show_tools
            ;;
        3)
            clear
            echo "============================================================"
            echo "  서버 로그 확인 (마지막 50줄)"
            echo "============================================================"
            echo ""
            if [ -f "server.log" ]; then
                tail -n 50 server.log
            else
                echo "서버 로그 파일을 찾을 수 없습니다."
            fi
            echo ""
            read -p "계속하려면 Enter를 누르세요..."
            show_tools
            ;;
        4)
            clear
            echo "============================================================"
            echo "  Ngrok 로그 확인 (마지막 50줄)"
            echo "============================================================"
            echo ""
            if [ -f "ngrok.log" ]; then
                tail -n 50 ngrok.log
            else
                echo "Ngrok 로그 파일을 찾을 수 없습니다."
            fi
            echo ""
            read -p "계속하려면 Enter를 누르세요..."
            show_tools
            ;;
        5)
            return
            ;;
        *)
            show_tools
            ;;
    esac
}

start_all() {
    clear
    echo "============================================================"
    echo "  통합 실행 (서버 + Ngrok)"
    echo "============================================================"
    echo ""
    echo "  모든 서비스를 순차적으로 시작합니다..."
    echo ""
    
    # 1. 서버 시작
    echo "[1/2] 서버 시작 중..."
    if command -v docker-compose &> /dev/null || command -v docker &> /dev/null; then
        if command -v docker-compose &> /dev/null; then
            docker-compose up -d > /dev/null 2>&1
        else
            docker compose up -d > /dev/null 2>&1
        fi
        if [ $? -eq 0 ]; then
            echo -e "  ${GREEN}✓ Docker Compose 서버 시작 완료${NC}"
        else
            if [ -f "venv/bin/python3" ]; then
                source venv/bin/activate
                nohup python3 main.py > server.log 2>&1 &
                echo -e "  ${GREEN}✓ 로컬 서버 시작 완료${NC}"
            fi
        fi
    elif [ -f "venv/bin/python3" ]; then
        source venv/bin/activate
        nohup python3 main.py > server.log 2>&1 &
        echo -e "  ${GREEN}✓ 로컬 서버 시작 완료${NC}"
    else
        echo -e "  ${RED}❌ 서버를 시작할 수 없습니다.${NC}"
    fi
    
    sleep 3
    
    # 2. Ngrok 시작
    echo "[2/2] Ngrok 시작 중..."
    if command -v ngrok &> /dev/null; then
        nohup ngrok http 8000 > ngrok.log 2>&1 &
        echo -e "  ${GREEN}✓ Ngrok 시작 완료${NC}"
    else
        echo -e "  ${YELLOW}⚠ Ngrok을 찾을 수 없습니다. 건너뜀${NC}"
    fi
    
    echo ""
    echo "============================================================"
    echo -e "  ${GREEN}✓ 모든 서비스가 시작되었습니다!${NC}"
    echo "============================================================"
    echo "  서버 URL: http://localhost:8000"
    echo "  API 문서: http://localhost:8000/docs"
    echo "  Ngrok 대시보드: http://localhost:4040"
    echo ""
    echo "  서비스를 종료하려면:"
    echo "    - Docker: docker-compose down"
    echo "    - 로컬 서버: pkill -f 'python3 main.py'"
    echo "    - Ngrok: pkill ngrok"
    echo ""
    read -p "계속하려면 Enter를 누르세요..."
}

# 메인 루프
while true; do
    show_menu
    read -p "선택하세요 (1-5): " choice
    
    case $choice in
        1)
            start_server
            ;;
        2)
            start_ngrok
            ;;
        3)
            show_tools
            ;;
        4)
            start_all
            ;;
        5)
            echo ""
            echo "프로그램을 종료합니다."
            exit 0
            ;;
        *)
            echo ""
            echo -e "${RED}잘못된 선택입니다. 다시 선택하세요.${NC}"
            sleep 1
            ;;
    esac
done

