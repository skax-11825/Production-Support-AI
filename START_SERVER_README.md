# 서버 시작 가이드

Windows와 macOS에서 간편하게 서버를 시작할 수 있는 스크립트입니다.

## 실행 방법

### Windows 사용자

1. **더블클릭 실행** (가장 간단)
   - `start_server.bat` 파일을 더블클릭
   - 또는 `start_server.py` 파일을 더블클릭

2. **명령어 실행**
   ```cmd
   start_server.bat
   ```
   또는
   ```cmd
   python start_server.py
   ```

### macOS/Linux 사용자

1. **더블클릭 실행** (Python이 기본 프로그램인 경우)
   - `start_server.py` 파일을 더블클릭

2. **터미널에서 실행**
   ```bash
   ./start_server.sh
   ```
   또는
   ```bash
   python3 start_server.py
   ```

## 스크립트 기능

- ✅ 가상환경 자동 감지 및 사용
- ✅ 환경 변수 파일(.env) 확인
- ✅ 서버 상태 및 URL 정보 표시
- ✅ 플랫폼별 최적화된 실행 방식
- ✅ 에러 메시지 및 안내 제공

## 서버 접속 정보

서버가 시작되면 다음 주소로 접속할 수 있습니다:

- **API 서버**: http://localhost:8000
- **헬스 체크**: http://localhost:8000/health
- **API 문서**: http://localhost:8000/docs

## 서버 종료

서버를 종료하려면:
- 터미널/명령 프롬프트에서 `Ctrl + C`를 누르세요
- 또는 터미널 창을 닫으세요

## 문제 해결

### 가상환경이 없다는 오류가 발생하는 경우

먼저 가상환경을 생성하세요:

**Windows:**
```cmd
py -3.12 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**macOS/Linux:**
```bash
./setup_env.sh
```

### .env 파일이 없다는 경고가 나타나는 경우

프로젝트 루트에 `.env` 파일을 생성하고 Oracle DB 연결 정보를 입력하세요.
