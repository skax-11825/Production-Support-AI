# 실행 파일 빌드 가이드

이 가이드는 Windows와 macOS에서 실행 가능한 실행 파일을 만드는 방법을 설명합니다.

## 사전 요구사항

- Python 3.12.x 설치 (macOS: python.org 설치본, Windows: `py -3.12`)
- 필요한 Python 패키지 설치

## 빌드 방법

### Windows에서 빌드

1. **가상 환경 생성 및 활성화** (PowerShell 예시):
```cmd
py -3.12 -m venv venv
venv\Scripts\activate
```

2. **빌드 스크립트 실행**:
```cmd
build_windows.bat
```

또는 수동으로:
```cmd
py -3.12 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pyinstaller build.spec --clean
```

3. **빌드 결과**:
   - 실행 파일: `dist\question-answer-api.exe`
   - 실행 파일과 같은 폴더에 `.env` 파일을 복사해야 합니다.

### macOS/Linux에서 빌드

1. **가상 환경 생성 및 활성화**:
```bash
./setup_env.sh
source venv/bin/activate
```

2. **빌드 스크립트 실행 권한 부여 및 실행**:
```bash
chmod +x build_macos.sh
./build_macos.sh
```

또는 수동으로:
```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pyinstaller build.spec --clean
```

3. **빌드 결과**:
   - 실행 파일: `dist/question-answer-api`
   - 실행 파일과 같은 폴더에 `.env` 파일을 복사해야 합니다.

## 실행 파일 사용 방법

### 1. 환경 변수 파일 준비

실행 파일과 같은 폴더에 `.env` 파일을 생성하세요:

```env
ORACLE_USER=system
ORACLE_PASSWORD=oracle
ORACLE_DSN=localhost:1521/FREEPDB1

APP_NAME=Question Answer API
APP_VERSION=1.0.0
DEBUG=True
```

### 2. 실행 파일 실행

**Windows:**
```cmd
cd dist
copy ..\.env .
question-answer-api.exe
```

**macOS/Linux:**
```bash
cd dist
cp ../.env .
./question-answer-api
```

### 3. 서버 접속

실행 파일을 실행하면 서버가 시작됩니다:
- API 서버: http://localhost:8000
- API 문서: http://localhost:8000/docs
- 헬스 체크: http://localhost:8000/health

## 배포 패키지 만들기

배포할 때는 다음 파일들을 함께 배포하세요:

```
배포_폴더/
├── question-answer-api.exe (또는 question-answer-api)
├── .env (사용자가 설정해야 함)
└── README.txt (사용 가이드)
```

### 배포용 README.txt 예시

```
질문-답변 API 서버 실행 가이드

1. .env 파일을 열어서 Oracle 데이터베이스 정보를 입력하세요:
   ORACLE_USER=your_username
   ORACLE_PASSWORD=your_password
   ORACLE_DSN=localhost:1521/FREEPDB1

2. 실행 파일을 더블클릭하거나 명령줄에서 실행하세요.

3. 브라우저에서 http://localhost:8000/docs 접속하여 API 문서를 확인하세요.

4. 서버를 중지하려면 Ctrl+C를 누르세요.
```

## 문제 해결

### 빌드 오류: "ModuleNotFoundError"

필요한 패키지가 설치되지 않았을 수 있습니다:
```bash
pip install -r requirements.txt
```

### 실행 파일이 작동하지 않음

1. `.env` 파일이 실행 파일과 같은 폴더에 있는지 확인
2. 명령줄에서 실행하여 오류 메시지 확인
3. Oracle DB 연결 정보가 올바른지 확인

### Windows에서 "바이러스로 인식됨"

PyInstaller로 만든 실행 파일이 일부 안티바이러스에서 오탐지될 수 있습니다. 
- 실행 파일에 디지털 서명을 추가하거나
- 안티바이러스 예외 목록에 추가

### macOS에서 "개발자를 확인할 수 없음" 오류

macOS에서 처음 실행 시 보안 경고가 나타날 수 있습니다:
1. 시스템 설정 > 보안 및 개인 정보 보호
2. "확인 없이 열기" 클릭

또는 명령줄에서:
```bash
xattr -cr dist/question-answer-api
```

## 빌드 옵션 커스터마이징

`build.spec` 파일을 수정하여 빌드 옵션을 변경할 수 있습니다:

- **단일 파일 vs 폴더 구조**: `onefile=True` 또는 `onedir=True`
- **콘솔 창 표시**: `console=True` (로그 확인용) 또는 `console=False` (GUI 앱처럼)
- **아이콘 추가**: `icon='path/to/icon.ico'` (Windows) 또는 `icon='path/to/icon.icns'` (macOS)

## 크로스 플랫폼 빌드

**중요**: PyInstaller는 각 플랫폼에서 해당 플랫폼용 실행 파일만 생성합니다.
- Windows에서 빌드 → Windows용 .exe 파일
- macOS에서 빌드 → macOS용 실행 파일
- Linux에서 빌드 → Linux용 실행 파일

따라서 각 플랫폼에서 해당 플랫폼용 빌드 스크립트를 실행해야 합니다.

## 추가 리소스

- [PyInstaller 공식 문서](https://pyinstaller.org/)
- [PyInstaller 사용법](https://pyinstaller.org/en/stable/usage.html)

