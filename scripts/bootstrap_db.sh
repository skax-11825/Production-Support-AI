#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

log() {
  echo "[bootstrap] $1"
}

# Python 경로 확인 (Docker에서는 시스템 Python 사용, 로컬에서는 venv 우선)
if [ -f "${PROJECT_ROOT}/venv/bin/python" ]; then
  PYTHON="${PROJECT_ROOT}/venv/bin/python"
  log "venv Python 사용: ${PYTHON}"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON="python3"
  log "시스템 python3 사용: ${PYTHON}"
elif command -v python >/dev/null 2>&1; then
  PYTHON="python"
  log "시스템 python 사용: ${PYTHON}"
else
  log "오류: Python을 찾을 수 없습니다."
  exit 1
fi

# DB 재구성 및 데이터 적재 (--yes 플래그로 자동 실행)
log "DB 재구성 및 데이터 적재 시작..."
"${PYTHON}" "${PROJECT_ROOT}/recreate_database.py" --yes

log "Oracle DB 초기화 및 데이터 적재 완료"


