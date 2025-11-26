@echo off
REM Windows용 실행 파일 빌드 스크립트

echo ========================================
echo Windows 실행 파일 빌드 시작
echo ========================================

set PYTHON_BIN=%PYTHON_BIN%
if "%PYTHON_BIN%"=="" set PYTHON_BIN=python

REM 가상 환경 활성화 확인
if exist "venv\Scripts\activate.bat" (
    echo 가상 환경 활성화 중...
    call venv\Scripts\activate.bat
) else (
    echo 경고: 가상 환경을 찾을 수 없습니다.
    echo 가상 환경을 생성하려면 PowerShell에서: %PYTHON_BIN% -m venv venv
    echo 혹은 WSL/macOS에서는 ./setup_env.sh 실행
    pause
    exit /b 1
)

for /f "tokens=1* delims=." %%a in ('python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}') "') do set CUR_PY=%%a.%%b
if not "%CUR_PY%"=="3.12" (
    echo [ERROR] 가상환경 Python 버전이 3.12가 아닙니다. (현재: %CUR_PY%)
    echo         setup_env.sh 또는 %PYTHON_BIN% -m venv venv 로 3.12 환경을 다시 구성하세요.
    pause
    exit /b 1
)

REM 필요한 패키지 설치 확인
echo 필요한 패키지 설치 확인 중...
pip install -r requirements.txt

REM 기존 빌드 폴더 삭제
if exist "dist" (
    echo 기존 빌드 폴더 삭제 중...
    rmdir /s /q dist
)
if exist "build" (
    echo 기존 빌드 임시 폴더 삭제 중...
    rmdir /s /q build
)

REM PyInstaller로 실행 파일 빌드
echo 실행 파일 빌드 중...
pyinstaller build.spec --clean

if exist "dist\question-answer-api.exe" (
    echo.
    echo ========================================
    echo 빌드 완료!
    echo ========================================
    echo 실행 파일 위치: dist\question-answer-api.exe
    echo.
    echo 사용 방법:
    echo 1. dist 폴더로 이동
    echo 2. .env 파일을 dist 폴더에 복사
    echo 3. question-answer-api.exe 실행
    echo.
) else (
    echo.
    echo ========================================
    echo 빌드 실패!
    echo ========================================
    echo 오류 로그를 확인하세요.
    echo.
)

pause

