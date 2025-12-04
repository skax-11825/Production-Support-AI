# Inform Note API Server

Oracle Database와 Dify AI를 연동한 질문-답변 API 서버입니다. 반도체 공정 데이터를 조회하고 통계를 제공합니다.

## 주요 기능

- **에러 코드 통계**: Error Code별 발생 건수 및 다운타임 집계
- **PM 이력 조회**: 장비 점검(PM) 이력 조회
- **상세 내역 검색**: 조치 내역 상세 정보 검색
- **ID 조회**: 공정/모델/장비 ID 조회
- **Dify AI 연동**: 자연어 질의-응답 지원

## 사전 요구사항

- **Python 3.12+**
- **Oracle Database** (로컬 또는 원격)
- **Oracle Instant Client** (로컬 실행 시)
- **Docker & Docker Compose** (Docker 사용 시, 선택사항)

## 빠른 시작

### 방법 1: Docker Compose (권장)

Docker를 사용하면 Oracle Database와 API 서버를 함께 실행할 수 있습니다.

```bash
# 1. 저장소 클론
git clone <repository-url>
cd Agent

# 2. 환경 변수 파일 생성
cp .env.example .env
# .env 파일을 열어 Oracle DB 연결 정보 수정

# 3. Docker Compose로 실행
docker-compose up -d

# 4. 서버 상태 확인
curl http://localhost:8000/health
```

### 방법 2: 로컬 설치 (Windows/Mac)

#### Windows

1. **Python 설치 확인**
```powershell
python --version  # Python 3.12 이상이어야 함
```

2. **가상환경 생성 및 활성화**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

3. **패키지 설치**
```powershell
pip install -r requirements.txt
```

4. **환경 변수 파일 생성**
```powershell
# .env 파일을 생성하고 다음 내용 입력
ORACLE_USER=your_username
ORACLE_PASSWORD=your_password
ORACLE_DSN=localhost:1521/XEPDB1
DIFY_API_BASE=https://api.dify.ai/v1
DIFY_API_KEY=your_dify_api_key
DIFY_USER_ID=oracle-agent-user
```

5. **서버 실행**
```powershell
# 방법 1: 통합 시작 스크립트 (권장) - 메뉴 방식
start.bat

# 방법 2: 직접 실행
python main.py

# 방법 3: Python 스크립트 실행 (더블클릭 가능)
python start_server.py

# 방법 4: Ngrok만 실행
start_ngrok.bat
```

#### macOS/Linux

1. **Python 설치 확인**
```bash
python3 --version  # Python 3.12 이상이어야 함
```

2. **가상환경 생성**
```bash
python3 -m venv venv
source venv/bin/activate
```

3. **패키지 설치**
```bash
pip install -r requirements.txt
```

4. **환경 변수 파일 생성**
```bash
# .env 파일을 생성하고 다음 내용 입력
ORACLE_USER=your_username
ORACLE_PASSWORD=your_password
ORACLE_DSN=localhost:1521/XEPDB1
DIFY_API_BASE=https://api.dify.ai/v1
DIFY_API_KEY=your_dify_api_key
DIFY_USER_ID=oracle-agent-user
```

5. **서버 실행**
```bash
# 방법 1: 통합 시작 스크립트 (권장) - 메뉴 방식
chmod +x start.sh
./start.sh

# 방법 2: 직접 실행
python3 main.py

# 방법 3: 간단한 서버 시작 스크립트
chmod +x start_server.sh
./start_server.sh

# 방법 4: Ngrok만 실행
chmod +x start_ngrok.sh
./start_ngrok.sh
```

## 환경 변수 설정

`.env` 파일에 다음 환경 변수를 설정하세요:

```env
# Oracle Database 연결 정보
ORACLE_USER=your_username
ORACLE_PASSWORD=your_password
ORACLE_DSN=localhost:1521/XEPDB1

# Dify AI 설정 (선택사항)
DIFY_API_BASE=https://api.dify.ai/v1
DIFY_API_KEY=your_dify_api_key
DIFY_USER_ID=oracle-agent-user

# 애플리케이션 설정
APP_NAME=Question Answer API
APP_VERSION=1.0.0
```

## 데이터베이스 초기화

처음 사용 시 데이터베이스를 초기화해야 합니다:

```bash
# 가상환경 활성화 후
python recreate_database.py

# 데이터 로드 (Excel 파일에서)
python load_data.py
```

## API 엔드포인트

서버 실행 후 `http://localhost:8000/docs`에서 Swagger UI를 통해 API 문서를 확인할 수 있습니다.

### 주요 엔드포인트

- `GET /` - 서버 정보
- `GET /health` - 헬스 체크
- `POST /lookup/ids` - ID 조회 (공정/모델/장비)
- `POST /api/v1/informnote/stats/error-code` - 에러 코드 통계
- `POST /api/v1/informnote/history/pm` - PM 이력 조회
- `POST /api/v1/informnote/search` - 상세 내역 검색
- `POST /ask` - 질문-답변 (Dify 연동)

## Docker 사용

### Docker Compose로 전체 시스템 실행

```bash
# 전체 시스템 시작 (Oracle DB + API 서버)
docker-compose up -d

# 로그 확인
docker-compose logs -f question-answer-api

# 시스템 중지
docker-compose down

# 데이터 포함 완전 삭제
docker-compose down -v
```

### Docker 이미지 직접 빌드

```bash
# 이미지 빌드
docker build -t question-answer-api .

# 컨테이너 실행
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  --name question-answer-api \
  question-answer-api
```

## 개발 가이드

### 프로젝트 구조

```
Agent/
├── main.py                 # FastAPI 메인 애플리케이션
├── database.py             # Oracle DB 연결 관리
├── config.py               # 설정 관리
├── recreate_database.py    # DB 초기화 스크립트
├── load_data.py            # 데이터 로딩 스크립트
├── utils.py                # 유틸리티 함수
├── requirements.txt        # Python 패키지 의존성
├── Dockerfile              # Docker 이미지 정의
├── docker-compose.yml      # Docker Compose 설정
├── create_*.sql            # DB 스키마 SQL 파일
├── start.sh / start.bat    # 통합 시작 스크립트 (메뉴 방식, 권장)
├── start_server.sh/.py     # 간단한 서버 시작 스크립트
└── start_ngrok.sh/.bat     # Ngrok 터널 시작 스크립트
```

### 로컬 개발 환경 설정

1. 가상환경 생성 및 활성화
2. 패키지 설치: `pip install -r requirements.txt`
3. `.env` 파일 생성 및 설정
4. DB 초기화: `python recreate_database.py`
5. 서버 실행: `python main.py`

## 트러블슈팅

### Oracle Database 연결 오류

- **ORA-12154: TNS:could not resolve the connect identifier**
  - `ORACLE_DSN` 형식 확인: `hostname:port/service_name`
  - Oracle Instant Client 설치 확인

- **ORA-01017: invalid username/password**
  - `.env` 파일의 사용자명/비밀번호 확인

### 포트 충돌

- 포트 8000이 이미 사용 중인 경우:
  ```bash
  # macOS/Linux
  lsof -ti:8000 | xargs kill -9
  
  # Windows
  netstat -ano | findstr :8000
  taskkill /PID <PID> /F
  ```

### Dify 연동 문제

- Dify 설정이 없어도 기본 API는 작동합니다
- Dify를 사용하려면 `.env`에 `DIFY_API_BASE`와 `DIFY_API_KEY` 설정

## 라이선스

이 프로젝트는 내부 사용 목적으로 개발되었습니다.

## 문의

문제가 발생하거나 질문이 있으시면 이슈를 등록해 주세요.

