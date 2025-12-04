# Inform Note API Server

Oracle Database와 연동된 반도체 공정 데이터 조회 및 통계 API 서버입니다. FastAPI 기반으로 RESTful API를 제공하며, Dify AI와의 연동을 지원합니다.

## 주요 기능

- **에러 코드 통계**: Error Code별 발생 건수 및 다운타임 집계
- **PM 이력 조회**: 장비 점검(PM) 이력 조회
- **상세 내역 검색**: 조치 내역 상세 정보 검색
- **ID 조회**: 공정/모델/장비 ID 조회 (ID 또는 NAME으로 검색)
- **Dify AI 연동**: 자연어 질의-응답 지원 (선택사항)

---

## 전체 구조

### 프로젝트 구조

```
Agent/
├── 📁 핵심 애플리케이션
│   ├── main.py                    # FastAPI 메인 애플리케이션 (API 엔드포인트)
│   ├── database.py                # Oracle DB 연결 관리 (연결 풀)
│   ├── config.py                  # 설정 관리 (.env 파일 읽기)
│   └── utils.py                   # 유틸리티 함수 (SQL 파일 읽기 등)
│
├── 📁 데이터베이스 관리
│   ├── recreate_database.py       # DB 전체 재구성 스크립트
│   ├── load_data.py               # Excel 파일에서 DB로 데이터 적재
│   ├── test_connection.py         # DB 연결 테스트
│   └── create_*.sql              # DB 스키마 생성 SQL 파일
│
├── 📁 SQL 템플릿
│   └── sql_templates/
│       ├── error_code_stats.sql   # 에러 코드 통계 쿼리
│       ├── pm_history.sql         # PM 이력 조회 쿼리
│       ├── search_inform_notes.sql # 상세 검색 쿼리
│       └── lookup_id.sql          # ID/NAME 조회 쿼리
│
├── 📁 서버 시작 스크립트
│   ├── start.sh / start.bat       # 통합 시작 스크립트 (메뉴 방식) ⭐ 권장
│   ├── start_server.sh / .py      # 간단한 서버 시작
│   └── start_ngrok.sh / .bat     # Ngrok 터널 시작
│
├── 📁 Docker
│   ├── docker-compose.yml         # Docker Compose 설정 (Oracle DB + API 서버)
│   ├── Dockerfile                 # API 서버 이미지 정의
│   └── docker-entrypoint.sh       # Docker 진입점 스크립트
│
├── 📁 설정 파일
│   ├── .env                       # 환경 변수 (생성 필요)
│   ├── requirements.txt           # Python 패키지 의존성
│   └── build.spec                 # PyInstaller 빌드 설정
│
└── 📁 데이터 파일
    └── normalized_data_preprocessed_251203.xlsx  # 데이터 적재용 Excel 파일
```

### 시스템 아키텍처

```
┌─────────────────┐
│   Dify AI       │  ← 자연어 질의 입력
└────────┬────────┘
         │ HTTP Request
         ▼
┌─────────────────┐
│  FastAPI Server │  ← REST API 엔드포인트
│   (main.py)     │
└────────┬────────┘
         │ SQL Query
         ▼
┌─────────────────┐
│  Oracle Database│  ← 데이터 저장소
│  (FREEPDB1)     │
└─────────────────┘

┌─────────────────┐
│   Ngrok Tunnel  │  ← 외부 접근용 (선택사항)
└─────────────────┘
```

### 주요 컴포넌트

| 컴포넌트 | 파일 | 역할 |
|---------|------|------|
| **API 서버** | `main.py` | FastAPI 기반 REST API 엔드포인트 제공 |
| **DB 연결** | `database.py` | Oracle DB 연결 풀 관리 |
| **설정 관리** | `config.py` | 환경 변수 읽기 및 설정 관리 |
| **데이터 적재** | `load_data.py` | Excel 파일 → Oracle DB 데이터 적재 |
| **DB 초기화** | `recreate_database.py` | 테이블 생성 및 데이터 적재 통합 |

---

## 시스템 및 서버 시작

### 사전 요구사항

- **Python 3.12+**
- **Oracle Database** (로컬 또는 원격)
  - Docker 사용 시: 자동으로 Oracle DB 컨테이너 실행
  - 로컬 실행 시: Oracle Instant Client 설치 필요
- **Docker & Docker Compose** (Docker 사용 시, 선택사항)

### 1단계: 프로젝트 클론 및 환경 설정

```bash
# 저장소 클론
git clone <repository-url>
cd Agent

# 가상환경 생성
python3 -m venv venv  # 또는 python -m venv venv (Windows)

# 가상환경 활성화
# macOS/Linux:
source venv/bin/activate
# Windows:
.\venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

### 2단계: 환경 변수 설정

`.env` 파일을 프로젝트 루트에 생성하고 다음 내용을 입력하세요:

```env
# Oracle Database 연결 정보 (필수)
ORACLE_USER=oracleuser
ORACLE_PASSWORD=oracle
ORACLE_DSN=localhost:1521/FREEPDB1

# Dify AI 설정 (선택사항)
DIFY_API_BASE=https://api.dify.ai/v1
DIFY_API_KEY=your_dify_api_key
DIFY_USER_ID=oracle-agent-user

# 애플리케이션 설정
APP_NAME=Question Answer API
APP_VERSION=1.0.0
```

### 3단계: 데이터베이스 초기화

처음 사용 시 데이터베이스를 초기화해야 합니다:

```bash
# 가상환경 활성화 후

# 1. DB 테이블 생성 및 데이터 적재 (통합)
python recreate_database.py

# 또는 단계별 실행:
# 2. DB 테이블 생성만
python recreate_database.py --skip-data

# 3. 데이터 적재만 (테이블이 이미 있는 경우)
python load_data.py
```

**주의**: `normalized_data_preprocessed_251203.xlsx` 파일이 프로젝트 루트에 있어야 합니다.

### 4단계: 서버 시작

#### 방법 1: 통합 시작 스크립트 (권장) ⭐

메뉴 방식으로 서버, Ngrok, 도구를 선택할 수 있습니다.

**macOS/Linux:**
```bash
chmod +x start.sh
./start.sh
```

**Windows:**
```cmd
start.bat
```

**메뉴 옵션:**
1. 서버 실행 (Docker Compose 또는 로컬 서버)
2. Ngrok 터널 실행
3. 기타 도구 (DB 상태 확인 등)
4. 통합 실행 (서버 + Ngrok)

#### 방법 2: Docker Compose (권장 - 처음 사용자)

Oracle Database와 API 서버를 함께 실행합니다.

```bash
# 전체 시스템 시작 (Oracle DB + API 서버)
docker-compose up -d

# 서버 상태 확인
curl http://localhost:8000/health

# 로그 확인
docker-compose logs -f question-answer-api

# 시스템 중지
docker-compose down
```

#### 방법 3: 로컬 서버 직접 실행

**macOS/Linux:**
```bash
# 방법 A: Python 직접 실행
python3 main.py

# 방법 B: 간단한 시작 스크립트
chmod +x start_server.sh
./start_server.sh

# 방법 C: Python 스크립트 (더블클릭 가능)
python3 start_server.py
```

**Windows:**
```powershell
# 방법 A: Python 직접 실행
python main.py

# 방법 B: Python 스크립트 (더블클릭 가능)
python start_server.py
```

#### 방법 4: Ngrok 터널 (외부 접근용)

로컬 서버를 외부에서 접근 가능하게 합니다.

**macOS/Linux:**
```bash
chmod +x start_ngrok.sh
./start_ngrok.sh
```

**Windows:**
```cmd
start_ngrok.bat
```

Ngrok 대시보드: http://localhost:4040

### 5단계: 서버 확인

서버가 정상적으로 시작되었는지 확인하세요:

```bash
# 헬스 체크
curl http://localhost:8000/health

# API 문서 확인
# 브라우저에서 http://localhost:8000/docs 접속
```

---

## API 엔드포인트

서버 실행 후 `http://localhost:8000/docs`에서 Swagger UI를 통해 API 문서를 확인할 수 있습니다.

### 주요 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `GET` | `/` | 서버 정보 |
| `GET` | `/health` | 헬스 체크 (DB 연결 상태 포함) |
| `POST` | `/lookup/ids` | ID 조회 (공정/모델/장비) |
| `POST` | `/api/v1/informnote/stats/error-code` | 에러 코드 통계 |
| `POST` | `/api/v1/informnote/history/pm` | PM 이력 조회 |
| `POST` | `/api/v1/informnote/search` | 상세 내역 검색 |

### API 사용 예시

```bash
# 헬스 체크
curl http://localhost:8000/health

# ID 조회
curl -X POST http://localhost:8000/lookup/ids \
  -H "Content-Type: application/json" \
  -d '{
    "process": {"name": "ETCH"},
    "model": {"id": "MDL_KE_PRO"},
    "equipment": {"name": "EQP_001"}
  }'
```

자세한 API 문서는 `API_ENDPOINTS.md`를 참조하세요.

---

## 데이터베이스 관리

### 데이터베이스 구조

주요 테이블:
- `INFORM_NOTE`: 조치 내역 메인 테이블
- `PROCESS`: 공정 정보
- `MODEL`: 모델 정보
- `EQUIPMENT`: 장비 정보
- `ERROR_CODE`: 에러 코드 정보
- `FAB_TERMS_DICTIONARY`: 반도체 용어 사전

### 데이터 적재

Excel 파일(`normalized_data_preprocessed_251203.xlsx`)에서 데이터를 적재합니다:

```bash
# 전체 데이터 적재 (레퍼런스 테이블 + Inform Note)
python load_data.py
```

적재 순서:
1. 참조 테이블 (SITE, FACTORY, LINE)
2. 레퍼런스 테이블 (PROCESS, MODEL, EQUIPMENT, ERROR_CODE, STATUS, DOWN_TYPE)
3. 용어 사전 (FAB_TERMS_DICTIONARY)
4. Inform Note 데이터

### DB 연결 테스트

```bash
python test_connection.py
```

---

## 개발 가이드

### 로컬 개발 환경 설정

1. 가상환경 생성 및 활성화
2. 패키지 설치: `pip install -r requirements.txt`
3. `.env` 파일 생성 및 설정
4. DB 초기화: `python recreate_database.py`
5. 서버 실행: `python main.py`

### 코드 구조

- **main.py**: FastAPI 앱, API 엔드포인트 정의
- **database.py**: Oracle DB 연결 풀 관리
- **config.py**: 환경 변수 관리 (pydantic-settings)
- **utils.py**: SQL 파일 읽기, SQL 문 분리
- **sql_templates/**: SQL 쿼리 템플릿 (보안 강화)

### 보안 기능

- **SQL Injection 방지**: 모든 SQL 쿼리를 템플릿 파일로 분리
- **화이트리스트 검증**: 테이블/컬럼명 화이트리스트로 검증
- **파라미터 바인딩**: 모든 사용자 입력은 파라미터 바인딩 사용

---

## 트러블슈팅

### Oracle Database 연결 오류

**ORA-12154: TNS:could not resolve the connect identifier**
- `ORACLE_DSN` 형식 확인: `hostname:port/service_name`
- Oracle Instant Client 설치 확인
- Docker 사용 시: `oracle-db:1521/FREEPDB1` 형식 사용

**ORA-01017: invalid username/password**
- `.env` 파일의 사용자명/비밀번호 확인
- Docker 사용 시: 기본값은 `oracleuser/oracle`

### 포트 충돌

포트 8000이 이미 사용 중인 경우:

**macOS/Linux:**
```bash
lsof -ti:8000 | xargs kill -9
```

**Windows:**
```cmd
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### 서버 시작 실패

1. 가상환경이 활성화되어 있는지 확인
2. `.env` 파일이 존재하는지 확인
3. Oracle DB가 실행 중인지 확인
4. 로그 파일 확인: `server.log`

### 데이터 적재 실패

1. Excel 파일 경로 확인: `normalized_data_preprocessed_251203.xlsx`
2. DB 테이블이 생성되어 있는지 확인
3. DB 연결 상태 확인: `python test_connection.py`

### Docker 관련

**컨테이너가 시작되지 않음:**
```bash
# 로그 확인
docker-compose logs

# 컨테이너 재시작
docker-compose restart
```

**데이터 초기화:**
```bash
# 모든 데이터 삭제 후 재시작
docker-compose down -v
docker-compose up -d
```

---

## 라이선스

이 프로젝트는 내부 사용 목적으로 개발되었습니다.

## 문의

문제가 발생하거나 질문이 있으시면 이슈를 등록해 주세요.
