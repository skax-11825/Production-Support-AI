@echo off
chcp 65001 > nul

echo ============================================================
echo API 서버 + ngrok 통합 실행 스크립트 (Windows)
echo ============================================================

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

rem 가상환경 Python 경로 설정
set "VENV_PYTHON=%SCRIPT_DIR%venv\Scripts\python.exe"

if exist "%VENV_PYTHON%" (
    echo ✅ 가상환경 Python 사용: %VENV_PYTHON%
    set "PYTHON_EXEC=%VENV_PYTHON%"
) else (
    echo ⚠ 경고: 가상환경 Python을 찾을 수 없습니다. 시스템 Python을 사용합니다.
    echo ✅ 시스템 Python 사용
    set "PYTHON_EXEC=python"
)

rem .env 파일 확인
if not exist "%SCRIPT_DIR%.env" (
    echo ❌ 오류: .env 파일이 프로젝트 루트에 없습니다.
    echo      Oracle DB 연결 정보가 포함된 .env 파일을 생성해주세요.
    echo      자세한 내용은 README.md를 참조하세요.
    pause
    exit /b 1
)
echo ✅ .env 파일 확인: %SCRIPT_DIR%.env

rem 기존 서버 프로세스 종료
echo.
echo ============================================================
echo 1. 기존 프로세스 종료 중...
echo ============================================================
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
    echo 기존 서버 프로세스 종료: PID %%a
    taskkill /F /PID %%a > nul 2>&1
)

rem 기존 ngrok 프로세스 종료
taskkill /F /IM ngrok.exe > nul 2>&1

timeout /t 2 /nobreak > nul

rem 서버 시작
echo.
echo ============================================================
echo 2. API 서버 시작 중...
echo ============================================================
start "API Server" /MIN "%PYTHON_EXEC%" -c "import uvicorn; uvicorn.run('main:app', host='0.0.0.0', port=8000, log_level='info')"

rem 서버 시작 대기
echo 서버 시작 대기 중...
set "SERVER_READY=0"
for /L %%i in (1,1,30) do (
    timeout /t 1 /nobreak > nul
    curl -s http://localhost:8000/health > nul 2>&1
    if !errorlevel! == 0 (
        set "SERVER_READY=1"
        goto :server_ready
    )
    echo|set /p="."
)
:server_ready

if "%SERVER_READY%"=="0" (
    echo ❌ 서버가 시작되지 않았습니다. ngrok을 시작할 수 없습니다.
    pause
    exit /b 1
)
echo ✅ 서버 시작 완료

rem ngrok 시작
echo.
echo ============================================================
echo 3. ngrok 터널 시작 중...
echo ============================================================
start "ngrok" /MIN ngrok http 8000 --log=stdout

timeout /t 3 /nobreak > nul

echo.
echo ============================================================
echo ✅ 모든 서비스가 시작되었습니다!
echo ============================================================
echo.
echo 서버 URL: http://localhost:8000
echo ngrok 웹 UI: http://127.0.0.1:4040
echo.
echo 종료하려면 이 창을 닫으세요.
echo ============================================================
echo.
pause

rem 프로세스 종료
echo.
echo 모든 프로세스 종료 중...
taskkill /F /FI "WINDOWTITLE eq API Server*" > nul 2>&1
taskkill /F /FI "WINDOWTITLE eq ngrok*" > nul 2>&1
taskkill /F /IM ngrok.exe > nul 2>&1

echo ✅ 모든 서비스가 종료되었습니다.

