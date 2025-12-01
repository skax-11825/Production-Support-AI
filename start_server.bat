@echo off
REM 서버 시작 스크립트 (Windows)
REM 더블클릭으로 실행 가능

chcp 65001 >nul
cd /d "%~dp0"

echo ============================================================
echo 질문-답변 API 서버 시작
echo ============================================================
echo.

REM 가상환경 확인
if not exist "venv\Scripts\python.exe" (
    echo ❌ 가상환경을 찾을 수 없습니다.
    echo 먼저 다음 명령어를 실행하세요:
    echo   setup_env.bat 또는 수동으로 가상환경을 설정하세요
    echo.
    pause
    exit /b 1
)

REM 환경 변수 파일 확인
if not exist ".env" (
    echo ⚠️  .env 파일을 찾을 수 없습니다.
    echo 서버 시작을 계속합니다...
    echo.
)

echo ============================================================
echo 서버 시작 중...
echo ============================================================
echo.
echo 서버 URL: http://localhost:8000
echo 헬스 체크: http://localhost:8000/health
echo API 문서: http://localhost:8000/docs
echo.
echo 서버를 종료하려면 Ctrl+C를 누르세요.
echo ============================================================
echo.

REM 서버 실행
call venv\Scripts\python.exe main.py

if errorlevel 1 (
    echo.
    echo ❌ 서버 시작 중 오류가 발생했습니다.
    pause
)

