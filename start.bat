@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

cd /d "%~dp0"

:MENU
cls
echo ============================================================
echo   Inform Note API 서버 - 시작 메뉴
echo ============================================================
echo.
echo   1. 서버 실행 (Docker Compose 또는 로컬 서버)
echo   2. Ngrok 터널 실행
echo   3. 기타 도구 (DB 상태 확인 등)
echo   4. 통합 실행 (서버 + Ngrok)
echo   5. 종료
echo.
echo ============================================================
set /p choice="선택하세요 (1-5): "

if "%choice%"=="1" goto START_SERVER
if "%choice%"=="2" goto START_NGROK
if "%choice%"=="3" goto TOOLS
if "%choice%"=="4" goto START_ALL
if "%choice%"=="5" goto EXIT
goto MENU

:START_SERVER
cls
echo ============================================================
echo   서버 실행
echo ============================================================
echo.

REM Docker Compose 확인
where docker-compose >nul 2>&1
if %errorlevel%==0 (
    echo Docker Compose를 사용하여 서버를 시작합니다...
    echo.
    docker-compose up -d
    if %errorlevel%==0 (
        echo.
        echo ✓ Docker Compose로 서버가 시작되었습니다.
        echo   서버 URL: http://localhost:8000
        echo   API 문서: http://localhost:8000/docs
        echo.
        pause
    ) else (
        echo.
        echo ⚠ Docker Compose 실행 실패. 로컬 서버를 시작합니다...
        echo.
        goto START_LOCAL_SERVER
    )
) else (
    echo Docker Compose를 찾을 수 없습니다. 로컬 서버를 시작합니다...
    echo.
    goto START_LOCAL_SERVER
)

goto MENU

:START_LOCAL_SERVER
REM 가상환경 확인
if not exist "venv\Scripts\python.exe" (
    echo ❌ 가상환경을 찾을 수 없습니다.
    echo    먼저 가상환경을 생성하세요: python -m venv venv
    echo.
    pause
    goto MENU
)

REM 환경 변수 파일 확인
if not exist ".env" (
    echo ⚠️  .env 파일을 찾을 수 없습니다.
    echo    서버 시작을 계속합니다...
    echo.
)

echo 서버 시작 중...
echo.
start "API Server" cmd /k "venv\Scripts\python.exe main.py"
echo.
echo ✓ 서버가 새 창에서 시작되었습니다.
echo   서버 URL: http://localhost:8000
echo   API 문서: http://localhost:8000/docs
echo.
pause
goto MENU

:START_NGROK
cls
echo ============================================================
echo   Ngrok 터널 실행
echo ============================================================
echo.

REM Ngrok 확인
where ngrok >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Ngrok을 찾을 수 없습니다.
    echo    Ngrok을 설치하고 PATH에 추가하세요.
    echo    다운로드: https://ngrok.com/download
    echo.
    pause
    goto MENU
)

REM Ngrok 설정 확인
if not exist ".env" (
    echo ⚠️  .env 파일을 찾을 수 없습니다.
    echo    기본 포트 8000을 사용합니다.
    set NGROK_PORT=8000
) else (
    REM .env에서 포트 읽기 (기본값 8000)
    set NGROK_PORT=8000
)

echo Ngrok 터널 시작 중 (포트 %NGROK_PORT%)...
echo   로컬 서버가 실행 중이어야 합니다.
echo.
start "Ngrok Tunnel" cmd /k "ngrok http %NGROK_PORT%"
echo.
echo ✓ Ngrok이 새 창에서 시작되었습니다.
echo   Ngrok 대시보드: http://localhost:4040
echo.
pause
goto MENU

:TOOLS
cls
echo ============================================================
echo   기타 도구
echo ============================================================
echo.
echo   1. DB 연결 상태 확인
echo   2. Docker Compose 상태 확인
echo   3. 서버 로그 확인
echo   4. 뒤로 가기
echo.
set /p tool_choice="선택하세요 (1-4): "

if "%tool_choice%"=="1" goto CHECK_DB
if "%tool_choice%"=="2" goto CHECK_DOCKER
if "%tool_choice%"=="3" goto CHECK_LOGS
if "%tool_choice%"=="4" goto MENU
goto TOOLS

:CHECK_DB
cls
echo ============================================================
echo   DB 연결 상태 확인
echo ============================================================
echo.

if not exist "venv\Scripts\python.exe" (
    echo ❌ 가상환경을 찾을 수 없습니다.
    pause
    goto TOOLS
)

venv\Scripts\python.exe test_connection.py
echo.
pause
goto TOOLS

:CHECK_DOCKER
cls
echo ============================================================
echo   Docker Compose 상태 확인
echo ============================================================
echo.

where docker-compose >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose를 찾을 수 없습니다.
    pause
    goto TOOLS
)

docker-compose ps
echo.
pause
goto TOOLS

:CHECK_LOGS
cls
echo ============================================================
echo   서버 로그 확인
echo ============================================================
echo.

if exist "server.log" (
    echo 서버 로그 (마지막 50줄):
    echo.
    powershell -Command "Get-Content server.log -Tail 50"
) else (
    echo 서버 로그 파일을 찾을 수 없습니다.
)

echo.
pause
goto TOOLS

:START_ALL
cls
echo ============================================================
echo   통합 실행 (서버 + Ngrok)
echo ============================================================
echo.
echo   모든 서비스를 순차적으로 시작합니다...
echo.

REM 1. 서버 시작
echo [1/2] 서버 시작 중...
call :START_SERVER_QUIET
timeout /t 3 /nobreak >nul

REM 2. Ngrok 시작
echo [2/2] Ngrok 시작 중...
call :START_NGROK_QUIET

echo.
echo ============================================================
echo   ✓ 모든 서비스가 시작되었습니다!
echo ============================================================
echo   서버 URL: http://localhost:8000
echo   API 문서: http://localhost:8000/docs
echo   Ngrok 대시보드: http://localhost:4040
echo.
echo   서비스를 종료하려면 각 창을 닫으세요.
echo.
pause
goto MENU

:START_SERVER_QUIET
where docker-compose >nul 2>&1
if %errorlevel%==0 (
    docker-compose up -d >nul 2>&1
    if %errorlevel%==0 (
        echo   ✓ Docker Compose 서버 시작 완료
        exit /b
    )
)
if exist "venv\Scripts\python.exe" (
    start "API Server" cmd /k "venv\Scripts\python.exe main.py"
    echo   ✓ 로컬 서버 시작 완료
)
exit /b

:START_NGROK_QUIET
where ngrok >nul 2>&1
if %errorlevel%==0 (
    start "Ngrok Tunnel" cmd /k "ngrok http 8000"
    echo   ✓ Ngrok 시작 완료
) else (
    echo   ⚠ Ngrok을 찾을 수 없습니다. 건너뜀
)
exit /b

:EXIT
echo.
echo 프로그램을 종료합니다.
timeout /t 2 >nul
exit

