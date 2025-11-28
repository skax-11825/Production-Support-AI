#!/usr/bin/env bash
set -euo pipefail

cd /app

# Oracle DB 연결 대기
wait_for_db() {
  echo "[entrypoint] Oracle DB 연결 대기 중..."
  local max_attempts=30
  local attempt=1
  
  while [ $attempt -le $max_attempts ]; do
    if python -c "
import oracledb
import os
import sys

try:
    conn = oracledb.connect(
        user=os.getenv('ORACLE_USER', 'system'),
        password=os.getenv('ORACLE_PASSWORD', 'oracle'),
        dsn=os.getenv('ORACLE_DSN', 'oracle-db:1521/FREEPDB1')
    )
    conn.close()
    sys.exit(0)
except:
    sys.exit(1)
" 2>/dev/null; then
      echo "[entrypoint] Oracle DB 연결 성공!"
      return 0
    fi
    
    echo "[entrypoint] 시도 $attempt/$max_attempts - DB 연결 대기 중..."
    sleep 2
    attempt=$((attempt + 1))
  done
  
  echo "[entrypoint] 오류: Oracle DB 연결 실패 (최대 시도 횟수 초과)"
  return 1
}

# DB 연결 대기
wait_for_db

# DB 부트스트랩 실행
if [ "${SKIP_DB_BOOTSTRAP:-0}" != "1" ]; then
  echo "[entrypoint] DB 부트스트랩 시작..."
  ./scripts/bootstrap_db.sh
else
  echo "[entrypoint] SKIP_DB_BOOTSTRAP=1 → DB 부트스트랩 생략"
fi

# 애플리케이션 시작
echo "[entrypoint] FastAPI 서버 시작..."
exec python -m uvicorn main:app --host 0.0.0.0 --port 8000


