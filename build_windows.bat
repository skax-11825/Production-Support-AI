@echo off
REM Windows용 실행 파일 빌드 스크립트

setlocal enabledelayedexpansion

echo ========================================
echo Windows 실행 파일 빌드 시작
echo ========================================

set PYTHON_BIN=%PYTHON_BIN%
if "%PYTHON_BIN%"=="" set PYTHON_BIN=python

REM 가상 환경 활성화 확인
if exist "venv\Scripts\activate.bat" (
    echo [1/6] 가상 환경 활성화 중...
    call venv\Scripts\activate.bat
) else (
    echo [ERROR] 가상 환경을 찾을 수 없습니다.
    echo         가상 환경을 생성하려면 PowerShell에서: %PYTHON_BIN% -m venv venv
    echo         혹은 WSL/macOS에서는 ./setup_env.sh 실행
    pause
    exit /b 1
)

REM Python 버전 확인
for /f "tokens=1* delims=." %%a in ('python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}') "') do set CUR_PY=%%a.%%b
if not "%CUR_PY%"=="3.12" (
    echo [ERROR] 가상환경 Python 버전이 3.12가 아닙니다. (현재: %CUR_PY%)
    echo         setup_env.sh 또는 %PYTHON_BIN% -m venv venv 로 3.12 환경을 다시 구성하세요.
    pause
    exit /b 1
)
echo [2/6] Python 버전 확인: %CUR_PY% ✓

REM PyInstaller 설치 확인
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] PyInstaller가 설치되지 않았습니다.
    echo         pip install pyinstaller 실행 후 다시 시도하세요.
    pause
    exit /b 1
)
for /f "delims=" %%i in ('python -c "import PyInstaller; print(PyInstaller.__version__)"') do set PYINSTALLER_VERSION=%%i
echo [3/6] PyInstaller 버전: %PYINSTALLER_VERSION% ✓

REM 필요한 패키지 설치 확인
echo [4/6] 필요한 패키지 설치 확인 중...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo [ERROR] 패키지 설치 실패
    pause
    exit /b 1
)
echo         패키지 설치 완료 ✓

REM 기존 빌드 폴더 삭제
echo [5/6] 기존 빌드 폴더 정리 중...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build
echo         정리 완료 ✓

REM PyInstaller로 실행 파일 빌드
echo [6/6] 실행 파일 빌드 중...
pyinstaller build.spec --clean --noconfirm
if errorlevel 1 (
    echo.
    echo ========================================
    echo [ERROR] 빌드 실패!
    echo ========================================
    echo 오류 로그를 확인하세요.
    pause
    exit /b 1
)
echo         빌드 성공 ✓

REM 빌드 결과 확인
if exist "dist\question-answer-api.exe" (
    echo.
    echo ========================================
    echo ✓ 빌드 완료!
    echo ========================================
    echo 실행 파일 위치: dist\question-answer-api.exe
    echo.
    echo 사용 방법:
    echo   1. dist 폴더로 이동: cd dist
    echo   2. .env 파일 복사: copy ..\\.env .
    echo   3. 실행: question-answer-api.exe
    echo.
    echo 주의사항:
    echo   - .env 파일에 Oracle DB 연결 정보가 설정되어 있어야 합니다.
    echo   - 실행 파일과 같은 디렉토리에 .env 파일이 있어야 합니다.
    echo.
) else (
    echo.
    echo ========================================
    echo [ERROR] 빌드된 실행 파일을 찾을 수 없습니다!
    echo ========================================
    pause
    exit /b 1
)

pause

