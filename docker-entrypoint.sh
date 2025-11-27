#!/usr/bin/env bash
set -euo pipefail

cd /app

if [ "${SKIP_DB_BOOTSTRAP:-0}" != "1" ]; then
  ./scripts/bootstrap_db.sh
else
  echo "[entrypoint] SKIP_DB_BOOTSTRAP=1 → DB 부트스트랩 생략"
fi

exec python -m uvicorn main:app --host 0.0.0.0 --port 8000


