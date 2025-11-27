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

run_with_prompt "y\nyes\n" "setup_reference_tables.py"
run_plain "load_reference_data.py"

run_with_prompt "y\nyes\n" "setup_semicon_term_dict.py"
run_with_prompt "y\n" "load_semicon_term_dict.py"

run_with_prompt "y\nyes\n" "setup_informnote_table.py"
run_plain "load_inform_note_from_excel.py"

log "Oracle DB 초기화 및 데이터 적재 완료"


