# 빠른 시작 가이드: UI와 Dify 연결하기

## 전체 연결 구조 이해하기

```
[웹 UI (frontend/index.html)]
    ↓ 사용자가 질문 입력
    ↓ Dify Chat API 호출 (POST /chat-messages)
[Dify 워크플로우]
    ↓ LLM이 질문 분석
    ↓ 필요한 Tool 결정
    ↓ HTTP Request 노드 실행
[FastAPI 서버 (main.py)]
    ↓ SQL 쿼리 실행
[Oracle Database]
    ↓ 데이터 반환
[FastAPI 서버]
    ↓ JSON 응답
[Dify 워크플로우]
    ↓ LLM이 결과를 자연어로 변환
    ↓ 최종 응답 생성
[웹 UI]
    ↓ 사용자에게 결과 표시
```

## 단계별 설정 가이드

### 1단계: Dify에서 Chat 애플리케이션 생성

#### 방법 A: Chat 애플리케이션 사용 (가장 간단)

1. **Dify 웹사이트 접속**
   - https://dify.ai 접속 및 로그인

2. **Chat 애플리케이션 생성**
   - 좌측 메뉴에서 "Chat" 클릭
   - "Create Chat App" 클릭
   - 애플리케이션 이름 입력 (예: "Inform Note Assistant")

3. **워크플로우 선택**
   - "Select Workflow" 클릭
   - 아래에서 생성할 워크플로우를 선택

#### 방법 B: 워크플로우를 Chat 모드로 설정

1. **워크플로우 생성**
   - 좌측 메뉴에서 "Workflow" 클릭
   - "Create Workflow" 클릭
   - 워크플로우 이름 입력

2. **Chat 모드 활성화**
   - 워크플로우 설정에서 "Chat" 모드 선택
   - 또는 Chat 애플리케이션에서 이 워크플로우를 연결

---

### 2단계: Dify 워크플로우 구성

워크플로우 편집기에서 다음과 같이 노드를 구성합니다:

```
[시작 노드]
    ↓
[LLM 노드] - 질문 분석 및 Tool 호출 결정
    ↓
[HTTP Request 노드] - FastAPI 서버 호출 (Tool)
    ↓
[LLM 노드] - 결과를 자연어로 변환
    ↓
[종료 노드]
```

#### 2.1 첫 번째 LLM 노드 설정

**노드 타입**: LLM

**모델**: GPT-4, Claude 등 원하는 모델 선택

**시스템 프롬프트**:
```
당신은 반도체 공정 데이터 조회 시스템의 어시스턴트입니다.
사용자의 질문을 분석하여 필요한 데이터를 조회해야 합니다.

사용 가능한 Tool:
1. lookup_ids - 공정/모델/장비 ID 조회
2. get_error_code_stats - 에러 코드 통계 조회
3. get_pm_history - PM(점검) 이력 조회
4. search_inform_notes - 상세 조치 내역 검색

사용자 질문을 분석하여:
1. 어떤 Tool을 사용해야 하는지 결정
2. 필요한 파라미터를 추출 (공정명, 날짜 범위, 장비명 등)
3. Tool을 호출하여 데이터를 조회
4. 조회된 데이터를 사용자에게 설명

질문 예시:
- "ETCH 공정의 에러 코드 통계를 보여줘" → get_error_code_stats Tool 사용
- "최근 PM 이력을 조회해줘" → get_pm_history Tool 사용
- "특정 장비의 상세 내역을 검색해줘" → search_inform_notes Tool 사용
```

**입력 변수**:
- `query`: 사용자 질문 (시작 노드에서 전달)

**출력 변수**:
- `tool_name`: 호출할 Tool 이름
- `tool_params`: Tool에 전달할 파라미터 (JSON 형식)

#### 2.2 HTTP Request 노드 설정 (Tool)

**노드 타입**: HTTP Request

**이 노드는 Tool로 등록되어 LLM이 자동으로 호출할 수 있습니다.**

각 API 엔드포인트마다 별도의 HTTP Request 노드를 만들어야 합니다:

##### Tool 1: ID 조회

**Tool 이름**: `lookup_ids`

**HTTP Method**: `POST`

**URL**: 
```
https://your-ngrok-url.ngrok-free.dev/lookup/ids
```
또는 로컬 테스트 시:
```
http://localhost:8000/lookup/ids
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
  "process": {
    "id": "{{#process_id}}{{process_id}}{{/process_id}}",
    "name": "{{#process_name}}{{process_name}}{{/process_name}}"
  },
  "model": {
    "id": "{{#model_id}}{{model_id}}{{/model_id}}",
    "name": "{{#model_name}}{{model_name}}{{/model_name}}"
  },
  "equipment": {
    "id": "{{#eqp_id}}{{eqp_id}}{{/eqp_id}}",
    "name": "{{#eqp_name}}{{eqp_name}}{{/eqp_name}}"
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

##### Tool 2: 에러 코드 통계

**Tool 이름**: `get_error_code_stats`

**URL**: 
```
https://your-ngrok-url.ngrok-free.dev/api/v1/informnote/stats/error-code
```

**Request Body**:
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

##### Tool 3: PM 이력 조회

**Tool 이름**: `get_pm_history`

**URL**: 
```
https://your-ngrok-url.ngrok-free.dev/api/v1/informnote/history/pm
```

**Request Body**:
```json
{
  "start_date": "{{#start_date}}{{start_date}}{{/start_date}}",
  "end_date": "{{#end_date}}{{end_date}}{{/end_date}}",
  "process_id": "{{#process_id}}{{process_id}}{{/process_id}}",
  "eqp_id": "{{#eqp_id}}{{eqp_id}}{{/eqp_id}}",
  "operator": "{{#operator}}{{operator}}{{/operator}}",
  "limit": 10
}
```

##### Tool 4: 상세 검색

**Tool 이름**: `search_inform_notes`

**URL**: 
```
https://your-ngrok-url.ngrok-free.dev/api/v1/informnote/search
```

**Request Body**:
```json
{
  "start_date": "{{#start_date}}{{start_date}}{{/start_date}}",
  "end_date": "{{#end_date}}{{end_date}}{{/end_date}}",
  "process_id": "{{#process_id}}{{process_id}}{{/process_id}}",
  "eqp_id": "{{#eqp_id}}{{eqp_id}}{{/eqp_id}}",
  "operator": "{{#operator}}{{operator}}{{/operator}}",
  "status_id": "{{#status_id}}{{status_id}}{{/status_id}}",
  "limit": 20
}
```

**중요**: 각 HTTP Request 노드를 **Tool로 등록**해야 LLM이 자동으로 호출할 수 있습니다.

#### 2.3 두 번째 LLM 노드 설정

**역할**: 조회된 데이터를 자연어로 변환

**시스템 프롬프트**:
```
당신은 반도체 공정 데이터 분석 전문가입니다.
조회된 데이터를 사용자에게 이해하기 쉽게 설명하세요.

- 통계 데이터는 주요 인사이트를 강조
- 테이블 데이터는 핵심 정보를 요약
- 사용자가 이해하기 쉬운 언어로 설명
- 필요시 데이터를 표 형식으로 정리
```

**입력 변수**:
- `query`: 원본 사용자 질문
- `tool_result`: HTTP Request 노드에서 반환된 데이터

**출력 변수**:
- `answer`: 최종 자연어 응답

---

### 3단계: Dify API Key 발급

1. **Chat 애플리케이션 설정**
   - 생성한 Chat 애플리케이션으로 이동
   - "API" 또는 "Settings" 탭 클릭

2. **API Key 생성**
   - "API Keys" 섹션에서 "Create API Key" 클릭
   - Key 이름 입력 (예: "Web UI Key")
   - 생성된 Key 복사 (형식: `app-xxxxxxxx`)

3. **API Base URL 확인**
   - 일반적으로: `https://api.dify.ai/v1`
   - 또는 자체 호스팅 시: `https://your-dify-domain.com/v1`

---

### 4단계: 웹 UI 설정 및 실행

1. **웹 UI 열기**
   ```bash
   # 방법 1: 직접 파일 열기
   open frontend/index.html
   
   # 방법 2: 로컬 서버 실행 (권장)
   cd frontend
   python3 -m http.server 8080
   # 브라우저에서 http://localhost:8080 접속
   ```

2. **Dify 설정 입력**
   - 사이드바에서 다음 정보 입력:
     - **Dify API Base URL**: `https://api.dify.ai/v1` (또는 자체 호스팅 URL)
     - **Dify API Key**: 3단계에서 발급한 Key
     - **API 서버 URL**: `http://localhost:8000` (또는 Ngrok URL)
   - "설정 저장" 클릭

3. **시스템 상태 확인**
   - "상태 확인" 버튼 클릭
   - API 서버와 Dify 연결 상태 확인

---

### 5단계: 테스트

1. **Dify 워크플로우 테스트**
   - Dify 워크플로우 편집기에서 "Run" 또는 "Test" 클릭
   - 샘플 질문 입력: "ETCH 공정의 에러 코드 통계를 보여줘"
   - 각 노드가 올바르게 실행되는지 확인

2. **웹 UI 테스트**
   - 웹 UI에서 동일한 질문 입력
   - 응답이 올바르게 표시되는지 확인

---

## 문제 해결

### Q: "Dify API 오류"가 발생합니다

**A**: 다음을 확인하세요:
1. Dify API Key가 올바른지 확인
2. Chat 애플리케이션이 올바른 워크플로우를 사용하는지 확인
3. 워크플로우가 Chat 모드로 설정되어 있는지 확인

### Q: Tool이 호출되지 않습니다

**A**: 다음을 확인하세요:
1. HTTP Request 노드가 Tool로 등록되어 있는지 확인
2. LLM 노드의 시스템 프롬프트에 Tool 사용 방법이 명시되어 있는지 확인
3. Tool 이름이 정확한지 확인

### Q: FastAPI 서버 연결 실패

**A**: 다음을 확인하세요:
1. FastAPI 서버가 실행 중인지 확인 (`http://localhost:8000/health`)
2. Ngrok을 사용하는 경우 URL이 올바른지 확인
3. CORS 설정이 올바른지 확인 (이미 설정됨)

### Q: 데이터가 표시되지 않습니다

**A**: 다음을 확인하세요:
1. Dify 워크플로우에서 데이터가 올바르게 반환되는지 확인
2. 두 번째 LLM 노드가 데이터를 올바르게 처리하는지 확인
3. 웹 UI의 JavaScript 콘솔에서 오류 확인 (F12)

---

## 요약

1. **Dify에서 Chat 애플리케이션 생성** → 워크플로우 연결
2. **워크플로우 구성** → LLM 노드 + HTTP Request 노드 (Tool) + LLM 노드
3. **API Key 발급** → Chat 애플리케이션에서 Key 생성
4. **웹 UI 설정** → API Key 입력 및 저장
5. **테스트** → 질문 입력하여 동작 확인

이제 UI → Dify 워크플로우 → FastAPI 서버 → 데이터베이스가 모두 연결됩니다!

