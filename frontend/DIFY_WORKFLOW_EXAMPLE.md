# Dify 워크플로우 구성 예시

이 문서는 Dify 워크플로우를 실제로 구성하는 방법을 단계별로 보여줍니다.

## 워크플로우 구조

```
┌─────────────┐
│  시작 노드  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│  LLM 노드 (질문 분석)            │
│  - 사용자 질문 분석              │
│  - 필요한 Tool 결정              │
│  - 파라미터 추출                 │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│  HTTP Request 노드 (Tool)        │
│  - FastAPI 서버 호출             │
│  - 데이터 조회                   │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│  LLM 노드 (응답 생성)            │
│  - 데이터를 자연어로 변환        │
│  - 사용자에게 설명               │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────┐
│  종료 노드  │
└─────────────┘
```

## 상세 설정

### 1. 시작 노드 (Start)

**변수 설정**:
- `query` (Text): 사용자 질문

### 2. 첫 번째 LLM 노드: 질문 분석

**노드 타입**: LLM

**모델 선택**: 
- GPT-4
- Claude 3
- 또는 원하는 모델

**시스템 프롬프트**:
```
당신은 반도체 공정 데이터 조회 시스템의 전문 어시스턴트입니다.

사용자의 질문을 분석하여 적절한 Tool을 호출해야 합니다.

사용 가능한 Tool:
1. lookup_ids - 공정/모델/장비의 ID를 조회합니다
   파라미터: process_id, process_name, model_id, model_name, eqp_id, eqp_name
   
2. get_error_code_stats - 에러 코드별 통계를 조회합니다
   파라미터: start_date, end_date, process_id, model_id, eqp_id, error_code, group_by
   
3. get_pm_history - PM(점검) 이력을 조회합니다
   파라미터: start_date, end_date, process_id, eqp_id, operator, limit
   
4. search_inform_notes - 상세 조치 내역을 검색합니다
   파라미터: start_date, end_date, process_id, eqp_id, operator, status_id, limit

작업 순서:
1. 사용자 질문을 분석하여 어떤 Tool이 필요한지 결정
2. 질문에서 필요한 파라미터를 추출
3. Tool을 호출하여 데이터 조회
4. 조회된 데이터를 다음 단계로 전달

질문 예시:
- "ETCH 공정의 에러 코드 통계를 보여줘"
  → get_error_code_stats Tool 사용, process_name="ETCH" 추출
  
- "2024년 1월부터 3월까지의 PM 이력을 조회해줘"
  → get_pm_history Tool 사용, start_date="2024-01-01", end_date="2024-03-31" 추출
  
- "EQP_001 장비의 상세 내역을 검색해줘"
  → search_inform_notes Tool 사용, eqp_id="EQP_001" 추출
```

**입력 변수**:
- `query`: `{{#start.query}}{{start.query}}{{/start.query}}`

**출력 변수**:
- `tool_name`: 호출할 Tool 이름 (예: "get_error_code_stats")
- `tool_params`: Tool 파라미터 (JSON 문자열)

**출력 예시**:
```json
{
  "tool_name": "get_error_code_stats",
  "tool_params": {
    "process_name": "ETCH",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31"
  }
}
```

### 3. HTTP Request 노드: FastAPI 서버 호출

**중요**: 이 노드를 **Tool로 등록**해야 LLM이 자동으로 호출할 수 있습니다.

#### Tool 등록 방법

1. HTTP Request 노드를 생성
2. 노드 설정에서 "Tool" 옵션 활성화
3. Tool 이름 입력 (예: "get_error_code_stats")
4. Tool 설명 입력

#### 노드 설정

**노드 타입**: HTTP Request

**Tool 이름**: `get_error_code_stats`

**Tool 설명**: 
```
에러 코드별 통계를 조회합니다. 공정, 모델, 장비, 날짜 범위, 에러 코드로 필터링할 수 있습니다.
```

**HTTP Method**: `POST`

**URL**: 
```
https://your-ngrok-url.ngrok-free.dev/api/v1/informnote/stats/error-code
```

**Headers**:
```json
{
  "Content-Type": "application/json"
}
```

**Request Body** (템플릿):
```json
{
  "start_date": "{{#start_date}}{{start_date}}{{/start_date}}",
  "end_date": "{{#end_date}}{{end_date}}{{/end_date}}",
  "process_id": "{{#process_id}}{{process_id}}{{/process_id}}",
  "model_id": "{{#model_id}}{{model_id}}{{/model_id}}",
  "eqp_id": "{{#eqp_id}}{{eqp_id}}{{/eqp_id}}",
  "error_code": "{{#error_code}}{{error_code}}{{/error_code}}",
  "group_by": "{{#group_by}}{{group_by}}{{/group_by}}"
}
```

**입력 변수 연결**:
- `start_date`: 이전 LLM 노드에서 추출한 값
- `end_date`: 이전 LLM 노드에서 추출한 값
- `process_id`: 이전 LLM 노드에서 추출한 값
- 등등...

**Response Schema** (선택사항):
```json
{
  "list": [
    {
      "period": "string",
      "process_id": "string",
      "process_name": "string",
      "error_code": "string",
      "event_cnt": "number",
      "total_down_time_minutes": "number"
    }
  ]
}
```

### 4. 두 번째 LLM 노드: 응답 생성

**노드 타입**: LLM

**시스템 프롬프트**:
```
당신은 반도체 공정 데이터 분석 전문가입니다.

조회된 데이터를 사용자에게 이해하기 쉽게 설명하세요.

규칙:
1. 통계 데이터는 주요 인사이트를 강조
2. 숫자는 읽기 쉽게 포맷팅 (예: 1,234건)
3. 테이블 데이터는 핵심 정보를 요약
4. 사용자가 이해하기 쉬운 언어로 설명
5. 필요시 데이터를 표 형식으로 정리

응답 형식:
- 먼저 조회된 데이터의 요약 설명
- 주요 인사이트나 패턴
- 상세 데이터 (표 형식으로 정리 가능)
```

**입력 변수**:
- `query`: `{{#start.query}}{{start.query}}{{/start.query}}`
- `tool_result`: `{{#http_request.response}}{{http_request.response}}{{/http_request.response}}`

**출력 변수**:
- `answer`: 최종 자연어 응답

### 5. 종료 노드 (End)

**출력 변수**:
- `answer`: `{{#llm2.answer}}{{llm2.answer}}{{/llm2.answer}}`

## 여러 Tool을 사용하는 경우

여러 Tool을 사용하려면:

1. **각 Tool마다 별도의 HTTP Request 노드 생성**
   - `lookup_ids` Tool
   - `get_error_code_stats` Tool
   - `get_pm_history` Tool
   - `search_inform_notes` Tool

2. **LLM 노드에서 Tool 선택**
   - 첫 번째 LLM 노드가 질문을 분석하여 어떤 Tool을 호출할지 결정
   - 조건 분기 노드나 Switch 노드를 사용하여 Tool 선택

3. **또는 LLM이 자동으로 Tool 선택**
   - 모든 HTTP Request 노드를 Tool로 등록
   - LLM 노드의 시스템 프롬프트에 모든 Tool 정보 제공
   - LLM이 자동으로 적절한 Tool 선택 및 호출

## 실제 구성 예시

### 예시 1: 단순한 질문 분석

```
[시작] → [LLM: 질문 분석] → [HTTP Request: Tool 호출] → [LLM: 응답 생성] → [종료]
```

### 예시 2: 조건부 Tool 선택

```
[시작] 
  ↓
[LLM: 질문 분석]
  ↓
[Switch 노드: Tool 선택]
  ├─→ [HTTP Request: lookup_ids]
  ├─→ [HTTP Request: get_error_code_stats]
  ├─→ [HTTP Request: get_pm_history]
  └─→ [HTTP Request: search_inform_notes]
  ↓
[LLM: 응답 생성]
  ↓
[종료]
```

### 예시 3: 여러 Tool 순차 호출

```
[시작]
  ↓
[LLM: 질문 분석]
  ↓
[HTTP Request: lookup_ids] → ID 조회
  ↓
[HTTP Request: get_error_code_stats] → 통계 조회 (ID 사용)
  ↓
[LLM: 응답 생성]
  ↓
[종료]
```

## 테스트 방법

1. **워크플로우 편집기에서 테스트**
   - "Run" 또는 "Test" 버튼 클릭
   - 샘플 입력: `{"query": "ETCH 공정의 에러 코드 통계를 보여줘"}`
   - 각 노드의 실행 결과 확인

2. **Chat 애플리케이션에서 테스트**
   - Chat 애플리케이션으로 이동
   - 질문 입력: "ETCH 공정의 에러 코드 통계를 보여줘"
   - 응답 확인

3. **웹 UI에서 테스트**
   - 웹 UI에서 동일한 질문 입력
   - 최종 응답 확인

## 주의사항

1. **Tool 등록 필수**: HTTP Request 노드를 Tool로 등록해야 LLM이 호출할 수 있습니다.

2. **URL 확인**: Ngrok URL이 변경되면 모든 HTTP Request 노드의 URL을 업데이트해야 합니다.

3. **파라미터 매핑**: LLM 노드에서 추출한 파라미터를 HTTP Request 노드의 입력 변수에 올바르게 연결해야 합니다.

4. **에러 처리**: HTTP Request 노드에서 에러가 발생할 경우를 대비한 에러 처리 로직 추가 권장.

5. **응답 형식**: FastAPI 서버의 응답 형식과 Dify 워크플로우의 기대 형식이 일치하는지 확인.

