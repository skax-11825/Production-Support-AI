# 질문-답변 API 서버

Python FastAPI를 사용한 질문-답변 REST API 서버입니다. Oracle 데이터베이스와 연동되어 있으며, Dify 워크플로우와 통합되어 있습니다.

## 전체 시스템 흐름

```
사용자 질문 → Dify LLM이 내용 분석 및 키워드 추출
  ↓
Dify 워크플로우 → HTTP Request 노드 → 백엔드 서버 (/ask)
  ↓
백엔드에서 전달받은 키워드(공정 필터)로 Oracle DB 쿼리 실행
  ↓
결과를 Dify로 반환 → Dify가 최종 답변 생성
```

## 기능

- 질문을 받고 답변을 제공하는 REST API 엔드포인트
- Oracle 데이터베이스 연동
- Dify OpenAPI 연동 (선택 구성)
- Dify 제공 키워드 기반 Oracle DB 조회
- 헬스 체크 엔드포인트
- CORS 지원
- 별도 CLI로 질문 분석/쿼리 테스트 (question_analyzer 활용)

## 사전 요구사항

- Python 3.12 이상
- Oracle 데이터베이스 (로컬 또는 원격)
- Oracle Instant Client (oracledb 라이브러리 사용 시 필요할 수 있음)

## 설치 방법

### 1. Python 3.12 확인

- macOS: `python3.12 --version` 또는 `ls /Library/Frameworks/Python.framework/Versions/3.12`
- Windows: `py -3.12 --version`

### 2. 가상 환경 생성 및 활성화

```bash
# macOS/Linux
./setup_env.sh

# Windows (PowerShell 예시)
py -3.12 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

`setup_env.sh` 스크립트는 Python 3.12 전용 가상환경을 자동으로 재구성하고 의존성을 설치합니다.

### 3. 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 입력하세요:

**Oracle 연결 필수 값**
```env
ORACLE_USER=oracleuser
ORACLE_PASSWORD=oracle
ORACLE_DSN=localhost:1521/FREEPDB1
```

**Dify 연동 (선택사항)**
```env
DIFY_API_BASE=http://ai-platform-deploy.koreacentral.cloudapp.azure.com/v1
DIFY_API_KEY=<발급받은 API 키>
DIFY_USER_ID=oracle-agent-user
```

**참고**
- `DIFY_API_BASE`와 `DIFY_API_KEY` 중 하나라도 비어 있으면 Dify 호출은 자동으로 비활성화됩니다.
- `ORACLE_DSN` 형식 예시: `host:port/service_name` (XEPDB1, FREEPDB1 등) 또는 `host:port/SID`.

## 실행 방법

### 1. 연결 테스트 (선택사항)

Docker Oracle DB 연결을 먼저 테스트하려면:
```bash
python test_connection.py
```

### 2. 개발 모드로 실행

```bash
python main.py
```

또는 uvicorn을 직접 사용:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

서버가 실행되면 다음 주소에서 접근할 수 있습니다:
- API 서버: http://localhost:8000
- API 문서: http://localhost:8000/docs
- 대체 문서: http://localhost:8000/redoc

## API 엔드포인트

### 1. 루트 엔드포인트
- **GET** `/`
- 서버 정보 반환

### 2. 헬스 체크
- **GET** `/health`
- 서버 및 데이터베이스 연결 상태, Dify 활성화 여부 확인

### 3. 질문하기
- **POST** `/ask`
- 요청 본문:
```json
{
  "question": "ICH 사이트 FAC_M16 PROC_PH 다운타임 알려줘",
  "context": "추가 컨텍스트 (선택사항)",
  "filters": {
    "site_id": "ICH",
    "factory_id": "FAC_M16",
    "process_id": "PROC_PH",
    "down_type": "UNSCHEDULED",
    "down_time_min": 60
  }
}
```
- 응답:
```json
{
  "question": "질문 내용",
  "answer": "답변 내용",
  "success": true,
  "process_specific": true,
  "data_count": 15
}
```

## 시스템 아키텍처

### 주요 컴포넌트

1. **Dify 워크플로우**
   - 역할: 사용자 질문 수신 및 최종 답변 생성
   - HTTP Request 노드: 백엔드 서버 호출
   - 입력: `question` (필수), `context` (선택)
   - 출력: `answer` 필드를 사용하여 최종 답변 생성

2. **백엔드 서버 (FastAPI)**
   - 엔드포인트: `POST /ask`
   - 역할: 
     - Dify가 전달한 공정 필터(`filters`) 검증
     - Oracle DB 쿼리 실행
     - 결과 포맷팅 및 반환

3. **Question Analyzer**
   - 역할: 테스트용 CLI에서만 사용되는 정규식 기반 키워드 추출기
   - 제공 정보: `site_id`, `factory_id`, `process_id`, `model_id`, `eqp_id`, `down_type`, `status_id`, `error_code`, 다운타임/시간 범위 등

4. **Process Query Builder**
   - 역할: 추출된 공정정보로 Oracle DB 쿼리 생성 및 실행
   - 기능:
     - 동적 WHERE 절 생성
     - 통계 정보 조회
     - 결과 제한 및 포맷팅

5. **Oracle Database**
   - 테이블: `Inform_note`
   - 역할: 반도체 공정 다운타임 데이터 저장 및 조회

6. **Keyword Pipeline Tester (CLI)**
   - 위치: `scripts/keyword_pipeline_tester.py`
   - 역할: 백엔드 개발자가 질문-키워드-쿼리 파이프라인을 독립적으로 검증할 때 사용

## 키워드 파이프라인 테스트 CLI

Dify 없이도 질문 → 키워드 추출 → 쿼리 실행을 반복적으로 검증할 수 있는 스크립트를 제공합니다.

```bash
# 인터랙티브 모드 (무한 반복, exit 입력 시 종료)
python scripts/keyword_pipeline_tester.py

# 단일 질문만 테스트
python scripts/keyword_pipeline_tester.py --question "ICH FAC_M16 PROC_PH 다운 2시간"

# 실제 Oracle DB까지 실행 (환경변수 필요)
python scripts/keyword_pipeline_tester.py --execute-query --limit 5
```

- `question_analyzer`가 내부에서 정규식 기반으로 필터를 추출합니다.
- `--execute-query` 옵션을 사용하면 Oracle DB 연결을 확인 후 실제 결과를 확인할 수 있습니다.
- CLI는 오직 개발/테스트 용도로만 사용하며, 운영 `/ask` 엔드포인트는 Dify가 제공한 `filters`만 신뢰합니다.

### 처리 흐름

#### 케이스 1: 공정정보 특정 가능

1. **질문 예시**: "ICH 사이트의 FAC_M16 공장에서 PROC_PH 공정 다운타임 알려줘"
2. **처리 과정**:
   ```
   Dify LLM이 키워드를 추출하여 filters에 포함
   → 백엔드가 filters로 SQL 쿼리 생성 및 실행
   → 결과 포맷팅 (통계 + 상세 정보)
   → Dify로 반환
   ```
3. **응답 예시**:
   ```json
   {
     "answer": "다운타임 정보 조회 결과\n[통계 정보]\n- 총 건수: 15건\n...",
     "question": "ICH 사이트의 FAC_M16 공장에서 PROC_PH 공정 다운타임 알려줘",
     "success": true,
     "process_specific": true,
     "data_count": 15
   }
   ```

#### 케이스 2: 공정정보 특정 불가능

1. **질문 예시**: "반도체 공정이 뭐야?"
2. **처리 과정**:
   ```
   Dify LLM이 filters를 제공하지 않음 또는 필터 값이 없음
   → 백엔드는 DB 조회를 건너뛰고 Dify API (또는 기본 답변)로 처리
   → Dify로 반환
   ```

## 데이터베이스 설정

### Oracle DB 테이블 생성

#### 방법 1: 통합 스크립트 사용 (권장)

모든 테이블을 한 번에 생성:

```bash
./venv/bin/python3 setup_tables.py
```

스크립트 실행 시:
- 데이터베이스 연결 확인
- 레퍼런스 테이블 생성 (SITE, FACTORY, LINE 등)
- 반도체 용어 사전 테이블 생성 (FAB_TERMS_DICTIONARY)
- Inform Note 테이블 생성 (INFORM_NOTE)
- SQL 파일 자동 실행

**옵션**:
- 기존 테이블 삭제 후 재생성: `y` 입력 (주의: 모든 데이터 삭제됨)

#### 방법 2: SQL 파일 직접 실행

```bash
# SQL*Plus 또는 SQL Developer에서 실행
sqlplus user/password@database < create_informnote_table.sql
```

또는 Oracle SQL Developer에서 `create_informnote_table.sql` 파일을 열어 실행

### 테이블 구조

주요 컬럼:
- **기본 정보**: `informnote_id`, `site_id`, `factory_id`, `line_id`, `process_id`
- **장비 정보**: `eqp_id`, `model_id`
- **다운타임 정보**: `down_start_time`, `down_end_time`, `down_time_minutes`, `down_type`, `error_code`
- **조치 정보**: `act_prob_reason`, `act_content`, `act_start_time`, `act_end_time`
- **담당자 정보**: `operator`, `first_detector`
- **상태 정보**: `status_id`
- **메타데이터**: `created_at`, `updated_at`

### 데이터 적재

엑셀 파일(`normalized_data.xlsx`)에서 모든 데이터를 한 번에 적재:

```bash
./venv/bin/python3 load_data.py
```

스크립트 실행 시:
- 레퍼런스 테이블 데이터 적재
- 반도체 용어 사전 데이터 적재
- Inform Note 데이터 적재

## Docker로 전체 시스템 실행 (권장)

Docker Compose를 사용하면 Oracle DB와 애플리케이션을 한 번에 올릴 수 있습니다.

### 빠른 시작

```bash
# 1. Docker Compose로 전체 시스템 실행
docker compose up --build

# 백그라운드 실행
docker compose up -d --build
```

이 명령어는 다음을 자동으로 수행합니다:
1. Oracle Database Express Edition (XE) 컨테이너 생성 및 시작
2. 애플리케이션 컨테이너 빌드 및 시작
3. Oracle DB가 준비될 때까지 대기
4. DB 부트스트랩 실행 (테이블 생성 및 데이터 적재)
5. FastAPI 서버 시작 (포트 8000)

### Docker Compose 관리 명령어

```bash
# 전체 시스템 시작
docker compose up -d

# 전체 시스템 중지
docker compose down

# 전체 시스템 중지 및 볼륨 삭제 (주의: 데이터 삭제됨)
docker compose down -v

# 로그 확인
docker compose logs -f

# 특정 서비스 로그만 확인
docker compose logs -f question-answer-api
docker compose logs -f oracle-db

# 컨테이너 상태 확인
docker compose ps

# 컨테이너 재시작
docker compose restart

# 특정 서비스만 재시작
docker compose restart question-answer-api
```

### 환경 변수 설정

Docker Compose 사용 시 기본 설정:
- Oracle DB: `oracle-db:1521/FREEPDB1`
- 사용자: `oracleuser`
- 비밀번호: `oracle`

`.env` 파일을 생성하여 다른 설정을 사용할 수 있습니다:

```env
ORACLE_USER=oracleuser
ORACLE_PASSWORD=oracle
ORACLE_DSN=oracle-db:1521/FREEPDB1
SKIP_DB_BOOTSTRAP=0  # 0: 실행, 1: 생략
```

### DB 부트스트랩 건너뛰기

이미 데이터가 있는 경우 부트스트랩을 건너뛸 수 있습니다:

```bash
SKIP_DB_BOOTSTRAP=1 docker compose up
```

또는 `.env` 파일에 `SKIP_DB_BOOTSTRAP=1` 추가

### 데이터 영구 저장

Oracle DB 데이터는 Docker 볼륨(`oracle-data`)에 저장되어 컨테이너를 재시작해도 데이터가 유지됩니다.

볼륨 확인:
```bash
docker volume ls | grep oracle-data
```

볼륨 삭제 (주의: 모든 데이터 삭제):
```bash
docker volume rm agent_oracle-data
```

## Docker Oracle DB 연결 (수동 설정)

### Docker Oracle 컨테이너 확인

현재 실행 중인 Oracle 컨테이너:
- 컨테이너 이름: `oracle-db` (Docker Compose 사용 시)
- 이미지: `gvenzl/oracle-xe:23-slim`
- 포트: `1521:1521`

### DSN 형식

1. **Service Name 사용** (권장):
   ```
   ORACLE_DSN=localhost:1521/FREEPDB1
   ```

2. **SID 사용**:
   ```
   ORACLE_DSN=localhost:1521/XE
   ```

3. **TNS 형식** (tnsnames.ora 사용 시):
   ```
   ORACLE_DSN=ORCL
   ```

### Docker 컨테이너 관리 명령어

```bash
# 컨테이너 상태 확인
docker ps | grep oracle

# 컨테이너 로그 확인
docker logs oracle

# 컨테이너 재시작
docker restart oracle

# 컨테이너 중지
docker stop oracle

# 컨테이너 시작
docker start oracle

# SQL*Plus로 직접 연결 테스트
docker exec -it oracle sqlplus oracleuser/oracle@FREEPDB1
```

### 문제 해결

#### 연결 오류: ORA-12541: TNS:no listener
**원인**: Oracle 리스너가 실행되지 않음
**해결**:
```bash
# 컨테이너 상태 확인
docker ps

# 컨테이너 재시작
docker restart oracle

# 리스너 상태 확인
docker exec oracle lsnrctl status
```

#### 연결 오류: ORA-01017: invalid username/password
**원인**: 잘못된 사용자명 또는 비밀번호
**해결**:
- `.env` 파일의 `ORACLE_USER`와 `ORACLE_PASSWORD` 확인
- Docker 컨테이너 실행 시 설정한 비밀번호와 일치하는지 확인

#### 연결 오류: ORA-12514: TNS:listener does not currently know of service
**원인**: 잘못된 Service Name 또는 SID
**해결**:
```bash
# Service Name 확인
docker exec oracle sqlplus -s oracleuser/oracle <<EOF
SELECT name FROM v\$pdbs;
EXIT;
EOF
```

### DB 부트스트랩 프로세스

`docker-entrypoint.sh`가 Oracle 초기화 스크립트(`scripts/bootstrap_db.sh`)를 자동으로 호출합니다.

실행 순서:
1. Oracle DB 연결 대기 (최대 30회 시도)
2. `setup_tables.py` - 모든 테이블 생성 (레퍼런스, 용어 사전, Inform Note)
3. `load_data.py` - 모든 데이터 적재 (레퍼런스, 용어 사전, Inform Note)
4. FastAPI 서버 시작

## Dify 연동 설정

### Dify HTTP 노드 설정 방법

1. Dify 워크플로우 편집기에서 **HTTP Request** 노드를 추가합니다
2. 노드 설정을 엽니다

#### 기본 설정
- **Method**: `POST`
- **URL**: 
  - 로컬 테스트: `http://localhost:8000/ask`
  - 배포 환경: `https://your-domain.com/ask` (실제 배포 주소로 변경)

#### Headers 설정
```
Content-Type: application/json
```

#### Body 설정 (JSON)
```json
{
  "question": "{{#question#}}",
  "context": "{{#context#}}"
}
```

또는 Dify 변수 사용:
- `question`: 사용자 질문 변수
- `context`: (선택사항) 추가 컨텍스트 변수

#### 응답 처리
- `{{#response.answer#}}`: 답변 내용 추출
- `{{#response.success#}}`: 성공 여부 확인

### 테스트 예시

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "시스템 상태를 알려줘",
    "context": "테스트"
  }'
```

## ngrok 설정 (로컬 개발용)

ngrok은 로컬 컴퓨터에서 실행 중인 서버를 인터넷을 통해 접근할 수 있게 해주는 도구입니다.

### 1. ngrok 계정 만들기

1. https://dashboard.ngrok.com/signup 에서 계정 생성
2. 이메일 인증 완료

### 2. authtoken 받기

1. https://dashboard.ngrok.com/get-started/your-authtoken 에서 authtoken 복사

### 3. authtoken 설정하기

```bash
export PATH="$HOME/bin:$PATH"
ngrok config add-authtoken <여기에_복사한_authtoken_붙여넣기>
```

### 4. ngrok 실행하기

로컬 서버(포트 8000)를 외부에 노출:
```bash
export PATH="$HOME/bin:$PATH"
ngrok http 8000
```

실행하면 `Forwarding` 줄에 있는 주소를 복사하여 Dify HTTP 노드의 URL로 사용하세요.

**주의사항**:
- ngrok 무료 버전은 종료하면 주소가 변경됩니다
- 매번 실행할 때마다 새로운 주소가 생성됩니다
- 세션이 2시간 후 자동 종료될 수 있습니다

## 배포

### Azure 배포

#### 방법 1: Azure Container Instances (ACI) 사용

1. Azure CLI 로그인
```bash
az login
```

2. 리소스 그룹 생성
```bash
az group create --name question-answer-api-rg --location koreacentral
```

3. Azure Container Registry (ACR) 생성
```bash
az acr create --resource-group question-answer-api-rg \
  --name questionanswerapiacr \
  --sku Basic
```

4. 이미지 빌드 및 푸시
```bash
az acr login --name questionanswerapiacr
az acr build --registry questionanswerapiacr \
  --image question-answer-api:latest .
```

5. Container Instance 배포
```bash
az container create \
  --resource-group question-answer-api-rg \
  --name question-answer-api \
  --image questionanswerapiacr.azurecr.io/question-answer-api:latest \
  --registry-login-server questionanswerapiacr.azurecr.io \
  --registry-username questionanswerapiacr \
  --registry-password <ACR_PASSWORD> \
  --dns-name-label question-answer-api \
  --ports 8000 \
  --environment-variables \
    ORACLE_USER=oracleuser \
    ORACLE_PASSWORD=oracle \
    ORACLE_DSN=your-oracle-host:1521/FREEPDB1 \
    DIFY_API_BASE=https://ai-platform-deploy.koreacentral.cloudapp.azure.com:3000/v1 \
    DIFY_API_KEY=your-dify-api-key \
    DIFY_USER_ID=oracle-agent-user \
    DEBUG=False
```

#### 방법 2: Azure App Service 사용

```bash
az webapp create \
  --resource-group question-answer-api-rg \
  --plan question-answer-api-plan \
  --name question-answer-api-app \
  --deployment-container-image-name questionanswerapiacr.azurecr.io/question-answer-api:latest

az webapp config appsettings set \
  --resource-group question-answer-api-rg \
  --name question-answer-api-app \
  --settings \
    ORACLE_USER=oracleuser \
    ORACLE_PASSWORD=oracle \
    ORACLE_DSN=your-oracle-host:1521/FREEPDB1 \
    DIFY_API_BASE=https://ai-platform-deploy.koreacentral.cloudapp.azure.com:3000/v1 \
    DIFY_API_KEY=your-dify-api-key \
    DIFY_USER_ID=oracle-agent-user \
    DEBUG=False \
    WEBSITES_PORT=8000
```

### 배포 후 Dify HTTP 노드 설정

- Azure Container Instances: `http://question-answer-api.koreacentral.azurecontainer.io/ask`
- Azure App Service: `https://question-answer-api-app.azurewebsites.net/ask`

## 실행 파일 빌드

Windows와 macOS에서 실행 가능한 실행 파일을 만들 수 있습니다.

### 빠른 빌드

**Windows:**
```cmd
build_windows.bat
```

**macOS/Linux:**
```bash
./build_macos.sh
```

빌드된 실행 파일은 `dist` 폴더에 생성됩니다.

## 프로젝트 구조

```
.
├── main.py                  # FastAPI 애플리케이션 메인 파일
├── question_analyzer.py     # 질문 분석 및 공정정보 추출 모듈
├── process_query_builder.py # Oracle DB 쿼리 생성 및 실행 모듈
├── database.py              # Oracle DB 연결 관리
├── config.py                # 설정 관리
├── dify_client.py           # Dify OpenAPI 연동 모듈
├── test_connection.py       # DB 연결 테스트 스크립트
├── setup_tables.py          # 통합 테이블 생성 스크립트
├── load_data.py             # 통합 데이터 적재 스크립트
├── utils.py                 # 공통 유틸리티 함수
├── create_informnote_table.sql # 테이블 생성 SQL
├── requirements.txt         # Python 패키지 의존성
├── build.spec               # PyInstaller 빌드 설정
├── build_windows.bat        # Windows 빌드 스크립트
├── build_macos.sh           # macOS/Linux 빌드 스크립트
├── setup_env.sh             # Python 3.12 전용 환경 설정 스크립트
├── Dockerfile               # Docker 이미지 빌드 설정
├── docker-compose.yml       # Docker Compose 설정
└── README.md                # 프로젝트 문서
```

## 문제 해결

### Oracle DB 연결 오류
1. Oracle 데이터베이스가 실행 중인지 확인
2. `.env` 파일의 DSN 형식이 올바른지 확인
3. 방화벽 설정 확인 (원격 DB인 경우)
4. Oracle Instant Client 설치 여부 확인

### 포트 충돌
기본 포트 8000이 사용 중인 경우, `main.py`의 포트 번호를 변경하거나 uvicorn 실행 시 `--port` 옵션 사용

### 에러 처리

#### 데이터베이스 연결 실패
```json
{
  "answer": "데이터베이스에 연결할 수 없습니다. 시스템 관리자에게 문의하세요.",
  "success": false
}
```

#### 쿼리 실행 오류
```json
{
  "answer": "공정정보 기반 답변 생성 중 오류가 발생했습니다: ...",
  "success": false
}
```

## 성능 최적화

1. **쿼리 결과 제한**: 최대 50건으로 제한
2. **인덱스 활용**: 사이트, 공장, 라인, 장비별 인덱스 사용
3. **로깅**: 상세한 로깅으로 디버깅 용이

## 보안 고려사항

1. **SQL Injection 방지**: 바인드 파라미터 사용
2. **입력 검증**: 질문 필수 검증
3. **에러 메시지**: 상세한 에러 정보는 로그에만 기록
4. **CORS**: 프로덕션에서는 특정 도메인으로 제한 권장

## 라이선스

이 프로젝트는 개인 사용 목적으로 제작되었습니다.
