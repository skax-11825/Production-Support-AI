# API 서버 엔드포인트 및 Ngrok URI

## 서버 상태
- ✅ **API 서버**: 정상 작동 중 (http://localhost:8000)
- ✅ **Ngrok**: 정상 작동 중
- ✅ **데이터베이스**: 연결됨

## Ngrok Public URL
**Base URL**: `https://youlanda-unconciliatory-unmirthfully.ngrok-free.dev`

---

## API 엔드포인트 목록

### 1. 기본 엔드포인트

#### GET `/`
- **설명**: 루트 엔드포인트 (서버 정보)
- **로컬**: `http://localhost:8000/`
- **Ngrok**: `https://youlanda-unconciliatory-unmirthfully.ngrok-free.dev/`
- **응답 예시**:
  ```json
  {
    "message": "데이터 조회 API 서버에 오신 것을 환영합니다.",
    "version": "1.0.0"
  }
  ```

#### GET `/health`
- **설명**: 헬스 체크 엔드포인트
- **로컬**: `http://localhost:8000/health`
- **Ngrok**: `https://youlanda-unconciliatory-unmirthfully.ngrok-free.dev/health`
- **응답 예시**:
  ```json
  {
    "status": "healthy",
    "database_connected": true
  }
  ```

#### GET `/docs`
- **설명**: Swagger UI 문서
- **로컬**: `http://localhost:8000/docs`
- **Ngrok**: `https://youlanda-unconciliatory-unmirthfully.ngrok-free.dev/docs`

#### GET `/openapi.json`
- **설명**: OpenAPI 스키마
- **로컬**: `http://localhost:8000/openapi.json`
- **Ngrok**: `https://youlanda-unconciliatory-unmirthfully.ngrok-free.dev/openapi.json`

---

### 2. 조회 API

#### POST `/lookup/ids`
- **설명**: ID 조회 API (process/model/equipment)
- **로컬**: `http://localhost:8000/lookup/ids`
- **Ngrok**: `https://youlanda-unconciliatory-unmirthfully.ngrok-free.dev/lookup/ids`
- **요청 본문 예시**:
  ```json
  {
    "process": {
      "id": "PROC001",
      "name": "공정명"
    },
    "model": {
      "id": "MODEL001",
      "name": "모델명"
    },
    "equipment": {
      "id": "EQP001",
      "name": "장비명"
    }
  }
  ```

#### POST `/api/v1/informnote/search`
- **설명**: 상세 조치 내역 검색
- **로컬**: `http://localhost:8000/api/v1/informnote/search`
- **Ngrok**: `https://youlanda-unconciliatory-unmirthfully.ngrok-free.dev/api/v1/informnote/search`
- **요청 본문 예시**:
  ```json
  {
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "process_id": "PROC001",
    "eqp_id": "EQP001",
    "operator": "운영자명",
    "status_id": 1,
    "limit": 20
  }
  ```

---

### 3. 통계 API

#### POST `/api/v1/informnote/stats/error-code`
- **설명**: Error Code별 건수·Down Time 집계
- **로컬**: `http://localhost:8000/api/v1/informnote/stats/error-code`
- **Ngrok**: `https://youlanda-unconciliatory-unmirthfully.ngrok-free.dev/api/v1/informnote/stats/error-code`
- **요청 본문 예시**:
  ```json
  {
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "process_id": "PROC001",
    "model_id": "MODEL001",
    "eqp_id": "EQP001",
    "error_code": "ERR001",
    "group_by": "error_code"
  }
  ```

#### POST `/api/v1/informnote/history/pm`
- **설명**: PM(장비 점검) 이력 조회
- **로컬**: `http://localhost:8000/api/v1/informnote/history/pm`
- **Ngrok**: `https://youlanda-unconciliatory-unmirthfully.ngrok-free.dev/api/v1/informnote/history/pm`
- **요청 본문 예시**:
  ```json
  {
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "process_id": "PROC001",
    "eqp_id": "EQP001",
    "operator": "운영자명",
    "limit": 10
  }
  ```

---

## Ngrok 통계
- **총 연결 수**: 318건
- **HTTP 요청 수**: 334건
- **터널 상태**: 활성

---

## 테스트 명령어 예시

### 로컬 테스트
```bash
# 헬스 체크
curl http://localhost:8000/health

# ID 조회
curl -X POST http://localhost:8000/lookup/ids \
  -H "Content-Type: application/json" \
  -d '{"process": {"name": "공정명"}}'
```

### Ngrok 테스트
```bash
# 헬스 체크
curl https://youlanda-unconciliatory-unmirthfully.ngrok-free.dev/health

# ID 조회
curl -X POST https://youlanda-unconciliatory-unmirthfully.ngrok-free.dev/lookup/ids \
  -H "Content-Type: application/json" \
  -d '{"process": {"name": "공정명"}}'
```

---

**생성일**: 2025-12-03
**Ngrok URL**: `https://youlanda-unconciliatory-unmirthfully.ngrok-free.dev`

