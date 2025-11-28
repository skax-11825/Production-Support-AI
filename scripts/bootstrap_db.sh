#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

log() {
  echo "[bootstrap] $1"
}

run_with_prompt() {
  local prompt="$1"
  local script="$2"
  log "실행: ${script}"
  printf "%b" "${prompt}" | "${PROJECT_ROOT}/venv/bin/python" "${PROJECT_ROOT}/${script}"
}

run_plain() {
  local script="$1"
  log "실행: ${script}"
  "${PROJECT_ROOT}/venv/bin/python" "${PROJECT_ROOT}/${script}"
}

# 통합된 스크립트 사용
run_with_prompt "y\nyes\n" "setup_tables.py"
run_plain "load_data.py"

log "Oracle DB 초기화 및 데이터 적재 완료"


