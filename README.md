# 질문-답변 API 서버

Python FastAPI를 사용한 질문-답변 REST API 서버입니다. Oracle 데이터베이스와 연동되어 있습니다.

## 기능

- 질문을 받고 답변을 제공하는 REST API 엔드포인트
- Oracle 데이터베이스 연동
- Dify OpenAPI 연동(선택 구성)
- 헬스 체크 엔드포인트
- CORS 지원

## 사전 요구사항

- Python 3.8 이상
- Oracle 데이터베이스 (로컬 또는 원격)
- Oracle Instant Client (oracledb 라이브러리 사용 시 필요할 수 있음)

## 설치 방법

1. Python 3.12 확인:
   - macOS: `python3.12 --version` 또는 `ls /Library/Frameworks/Python.framework/Versions/3.12`
   - Windows: `py -3.12 --version`

2. 가상 환경 생성 및 활성화:
```bash
# macOS/Linux
./setup_env.sh

# Windows (PowerShell 예시)
py -3.12 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

`setup_env.sh` 스크립트는 Python 3.12 전용 가상환경을 자동으로 재구성하고 의존성을 설치합니다.

3. 환경 변수 설정:
프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 입력하세요:

**Oracle 연결 필수 값**
```
ORACLE_USER=system
ORACLE_PASSWORD=oracle
ORACLE_DSN=localhost:1521/FREEPDB1
```

**Dify 연동(선택사항)**
```
DIFY_API_BASE=http://ai-platform-deploy.koreacentral.cloudapp.azure.com/v1
DIFY_API_KEY=<발급받은 API 키>
DIFY_USER_ID=oracle-agent-user
```

**참고**
- `DIFY_API_BASE` 와 `DIFY_API_KEY` 중 하나라도 비어 있으면 Dify 호출은 자동으로 비활성화되고 기존 Oracle 기반 답변 로직이 동작합니다.
- `ORACLE_DSN` 형식 예시: `host:port/service_name` (XEPDB1, FREEPDB1 등) 또는 `host:port/SID`.

> 💡 **Docker Oracle DB 연결 가이드**: 자세한 설정 방법은 `DOCKER_SETUP.md` 파일을 참고하세요.

## 실행 방법

### 1. 연결 테스트 (선택사항):
Docker Oracle DB 연결을 먼저 테스트하려면:
```bash
python test_connection.py
```

### 2. 개발 모드로 실행:
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
  "question": "질문 내용",
  "context": "추가 컨텍스트 (선택사항)"
}
```
- 응답:
```json
{
  "question": "질문 내용",
  "answer": "답변 내용",
  "success": true
}
```

## 사용 예시

### Dify 연동 테스트
1. `.env` 에 `DIFY_API_BASE` 와 `DIFY_API_KEY` 를 설정합니다.
2. 서버 실행 후 `/ask` 엔드포인트에 질문을 보내면 우선적으로 Dify에서 답변을 생성합니다.
3. Dify 호출에 실패하면 Oracle DB 기반 기본 답변으로 자동 대체됩니다.

### cURL을 사용한 요청:
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "현재 시간은 몇 시인가요?",
    "context": null
  }'
```

### Python을 사용한 요청:
```python
import requests

response = requests.post(
    "http://localhost:8000/ask",
    json={
        "question": "데이터베이스 연결 상태는 어떤가요?",
        "context": None
    }
)

print(response.json())
```

## 프로젝트 구조

```
.
├── main.py                  # FastAPI 애플리케이션 메인 파일
├── database.py              # Oracle DB 연결 관리
├── config.py                # 설정 관리
├── dify_client.py           # Dify OpenAPI 연동 모듈
├── test_connection.py       # DB 연결 테스트 스크립트
├── requirements.txt         # Python 패키지 의존성
├── build.spec               # PyInstaller 빌드 설정
├── build_windows.bat        # Windows 빌드 스크립트
├── build_macos.sh           # macOS/Linux 빌드 스크립트
├── setup_env.sh             # Python 3.12 전용 환경 설정 스크립트
├── BUILD_GUIDE.md           # 실행 파일 빌드 가이드
├── DOCKER_SETUP.md          # Docker Oracle DB 연결 가이드
├── DEPLOY_README.txt        # 배포용 사용 가이드
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

> 📖 **자세한 빌드 가이드**: `BUILD_GUIDE.md` 파일을 참고하세요.

## 향후 개선 사항

- [ ] AI 모델 통합 (예: OpenAI, Llama 등)
- [ ] 데이터베이스에서 지식 베이스 검색 기능
- [ ] 질문 히스토리 저장
- [ ] 인증 및 권한 관리
- [ ] 더 정교한 답변 생성 로직

## 라이선스

이 프로젝트는 개인 사용 목적으로 제작되었습니다.

