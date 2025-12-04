@echo off
chcp 65001 >nul
cd /d "%~dp0"

set PORT=%1
if "%PORT%"=="" set PORT=8000

echo ============================================================
echo   Ngrok 터널 시작
echo ============================================================
echo.

REM Ngrok 확인
where ngrok >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Ngrok을 찾을 수 없습니다.
    echo    Ngrok을 설치하고 PATH에 추가하세요.
    echo    다운로드: https://ngrok.com/download
    pause
    exit /b 1
)

echo Ngrok 터널 시작 중 (포트 %PORT%)...
echo   로컬 서버가 http://localhost:%PORT% 에서 실행 중이어야 합니다.
echo.
echo Ngrok 대시보드: http://localhost:4040
echo 종료하려면 Ctrl+C를 누르세요.
echo ============================================================
echo.

ngrok http %PORT%

