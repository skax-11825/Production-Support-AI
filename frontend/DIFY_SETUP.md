# Dify 연동 설정 가이드

이 문서는 Dify AI 플랫폼과 FastAPI 서버를 연동하는 방법을 설명합니다.

## 전체 시스템 흐름

```
[사용자] 
  ↓ 질문 입력
[웹 UI (frontend)]
  ↓ HTTP Request (Dify Chat API)
[Dify AI]
  ↓ HTTP Request (Tool 호출)
[FastAPI Server]
  ↓ SQL Query
[Oracle Database]
  ↓ 결과 반환
[FastAPI Server]
  ↓ 응답 반환
[Dify AI]
  ↓ 자연어 응답 생성
[웹 UI]
  ↓ 결과 표시
[사용자]
```

## 1단계: Dify 워크플로우 생성

### 1.1 Dify 접속 및 워크플로우 생성

1. Dify 웹사이트에 로그인
2. "워크플로우" 메뉴로 이동
3. "새 워크플로우 생성" 클릭

### 1.2 워크플로우 구조

다음과 같은 구조로 워크플로우를 구성합니다:

```
[시작] 
  ↓
[LLM 노드] (질문 분석 및 Tool 호출 결정)
  ↓
[HTTP Request 노드들] (FastAPI 서버 호출)
  ↓
[LLM 노드] (결과를 자연어로 변환)
  ↓
[종료]
```

## 2단계: HTTP Request Tool 설정

### 2.1 ID 조회 Tool

**Tool 이름**: `lookup_ids`

**HTTP Method**: `POST`

**URL**: `https://your-ngrok-url.ngrok-free.dev/lookup/ids`

**Headers**:
```
Content-Type: application/json
```

**Request Body**:
```json
{
  "process": {
    "id": "{{process_id}}",
    "name": "{{process_name}}"
  },
  "model": {
    "id": "{{model_id}}",
    "name": "{{model_name}}"
  },
  "equipment": {
    "id": "{{eqp_id}}",
    "name": "{{eqp_name}}"
  }
}
```

**Response Schema**:
```json
{
  "process_id": "string",
  "model_id": "string",
  "eqp_id": "string"
}
```

### 2.2 에러 코드 통계 Tool

**Tool 이름**: `get_error_code_stats`

**HTTP Method**: `POST`

**URL**: `https://your-ngrok-url.ngrok-free.dev/api/v1/informnote/stats/error-code`

**Request Body**:
```json
{
  "start_date": "{{start_date}}",
  "end_date": "{{end_date}}",
  "process_id": "{{process_id}}",
  "model_id": "{{model_id}}",
  "eqp_id": "{{eqp_id}}",
  "error_code": "{{error_code}}",
  "group_by": "{{group_by}}"
}
```

**Response Schema**:
```json
{
  "list": [
    {
      "period": "string",
      "process_id": "string",
      "process_name": "string",
      "model_id": "string",
      "model_name": "string",
      "eqp_id": "string",
      "eqp_name": "string",
      "error_code": "string",
      "error_des": "string",
      "event_cnt": "number",
      "total_down_time_minutes": "number"
    }
  ]
}
```

### 2.3 PM 이력 조회 Tool

**Tool 이름**: `get_pm_history`

**HTTP Method**: `POST`

**URL**: `https://your-ngrok-url.ngrok-free.dev/api/v1/informnote/history/pm`

**Request Body**:
```json
{
  "start_date": "{{start_date}}",
  "end_date": "{{end_date}}",
  "process_id": "{{process_id}}",
  "eqp_id": "{{eqp_id}}",
  "operator": "{{operator}}",
  "limit": 10
}
```

### 2.4 상세 검색 Tool

**Tool 이름**: `search_inform_notes`

**HTTP Method**: `POST`

**URL**: `https://your-ngrok-url.ngrok-free.dev/api/v1/informnote/search`

**Request Body**:
```json
{
  "start_date": "{{start_date}}",
  "end_date": "{{end_date}}",
  "process_id": "{{process_id}}",
  "eqp_id": "{{eqp_id}}",
  "operator": "{{operator}}",
  "status_id": "{{status_id}}",
  "limit": 20
}
```

## 3단계: LLM 노드 설정

### 3.1 질문 분석 LLM

**역할**: 사용자 질문을 분석하여 필요한 Tool을 결정

**시스템 프롬프트 예시**:
```
당신은 반도체 공정 데이터 조회 시스템의 어시스턴트입니다.
사용자의 질문을 분석하여 적절한 Tool을 호출해야 합니다.

사용 가능한 Tool:
1. lookup_ids: 공정/모델/장비 ID 조회
2. get_error_code_stats: 에러 코드 통계 조회
3. get_pm_history: PM 이력 조회
4. search_inform_notes: 상세 내역 검색

사용자 질문을 분석하여 필요한 정보를 추출하고 적절한 Tool을 호출하세요.
```

### 3.2 응답 생성 LLM

**역할**: 조회된 데이터를 자연어로 변환

**시스템 프롬프트 예시**:
```
당신은 반도체 공정 데이터 분석 전문가입니다.
조회된 데이터를 사용자에게 이해하기 쉽게 설명하세요.

- 통계 데이터는 주요 인사이트를 강조
- 테이블 데이터는 핵심 정보를 요약
- 사용자가 이해하기 쉬운 언어로 설명
```

## 4단계: 워크플로우 변수 설정

Dify 워크플로우에서 다음 변수들을 설정할 수 있습니다:

- `process_id`, `process_name`: 공정 정보
- `model_id`, `model_name`: 모델 정보
- `eqp_id`, `eqp_name`: 장비 정보
- `start_date`, `end_date`: 날짜 범위
- `error_code`: 에러 코드
- `operator`: 운영자 이름
- `status_id`: 상태 ID

## 5단계: Chat API 설정

### 5.1 API Key 발급

1. Dify 워크플로우 설정으로 이동
2. "API Keys" 섹션에서 새 Key 생성
3. 생성된 Key를 복사 (형식: `app-xxxxxxxx`)

### 5.2 웹 UI에 API Key 입력

1. 웹 UI의 사이드바로 이동
2. "Dify API Key" 필드에 Key 입력
3. "설정 저장" 클릭

## 6단계: 테스트

### 6.1 Dify 워크플로우 테스트

1. Dify 워크플로우 편집기에서 "테스트" 버튼 클릭
2. 샘플 질문 입력: "ETCH 공정의 에러 코드 통계를 보여줘"
3. 각 노드의 실행 결과 확인

### 6.2 웹 UI 테스트

1. 웹 UI에서 동일한 질문 입력
2. 응답이 올바르게 표시되는지 확인
3. 데이터 테이블이 제대로 렌더링되는지 확인

## 문제 해결

### Tool 호출 실패

**증상**: Dify에서 Tool 호출이 실패함

**해결 방법**:
1. Ngrok URL이 올바른지 확인
2. FastAPI 서버가 실행 중인지 확인
3. CORS 설정 확인
4. HTTP Request 노드의 URL과 헤더 확인

### 응답 형식 오류

**증상**: Dify가 응답을 파싱하지 못함

**해결 방법**:
1. Response Schema가 올바른지 확인
2. FastAPI 서버의 응답 형식 확인
3. 실제 응답과 Schema가 일치하는지 확인

### 데이터가 표시되지 않음

**증상**: 웹 UI에 데이터가 표시되지 않음

**해결 방법**:
1. Dify 응답에 `metadata.data` 필드가 포함되어 있는지 확인
2. 웹 UI의 JavaScript 콘솔에서 오류 확인
3. Dify 워크플로우에서 데이터를 올바르게 반환하는지 확인

## 참고 자료

- [Dify 공식 문서](https://docs.dify.ai/)
- [FastAPI 서버 API 문서](./../API_ENDPOINTS.md)
- [프론트엔드 README](./README.md)

