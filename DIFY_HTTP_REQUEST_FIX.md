# Dify HTTP Request 노드 설정 수정 가이드

## 현재 문제점

현재 JSON 본문에 다음과 같이 설정되어 있습니다:
```json
{
  "process_name": "① 최종 키워... / {x} process_keyword",
  "eqp_name": "① 키워드 추... / ... / {x} eqp_keyword",
  "model_name": "① 키워드 추... / ... / {x} model_keyword"
}
```

이 형식은 **변수 참조가 제대로 작동하지 않아** 문자열로 그대로 전송됩니다.

## 올바른 설정 방법

### 방법 1: 변수 삽입 기능 사용 (권장)

1. **JSON 본문의 각 값 필드에서 변수 삽입:**

   - `process_name` 값 필드 클릭
   - 오른쪽에 나타나는 **변수 선택 버튼** 클릭 (보통 `/` 또는 `{x}` 아이콘)
   - 변수 목록에서 다음 중 하나 선택:
     - `① 최종 키워드` 노드의 `structured_output.process_keyword`
     - 또는 `① 키워드 추출` 노드의 `structured_output.proc_keyword`

2. **올바른 JSON 형태:**
   ```json
   {
     "process_name": "{{#①최종키워드.structured_output.process_keyword#}}",
     "eqp_name": "{{#①최종키워드.structured_output.eqp_keyword#}}",
     "model_name": "{{#①최종키워드.structured_output.model_keyword#}}"
   }
   ```

### 방법 2: 직접 변수 참조 입력

JSON 본문을 다음과 같이 수정하세요:

```json
{
  "process_name": "{{#노드ID.structured_output.proc_keyword#}}",
  "eqp_name": "{{#노드ID.structured_output.eqp_keyword#}}",
  "model_name": "{{#노드ID.structured_output.model_keyword#}}"
}
```

**주의:** `노드ID`는 실제 LLM 노드의 ID로 변경해야 합니다.

### 방법 3: structured_output 객체 전체 전송 (더 안정적)

```json
{
  "structured_output": "{{#①최종키워드.structured_output#}}"
}
```

이렇게 하면 API에서 `structured_output` 객체 전체를 받아서 처리할 수 있습니다.

## 단계별 수정 방법

### 1단계: LLM 노드 확인
- LLM 노드에서 Structured Output 설정 확인
- 출력 필드명 확인: `proc_keyword`, `eqp_keyword`, `model_keyword` 등

### 2단계: HTTP Request 노드 수정

#### Option A: 개별 필드 사용 (권장)
```json
{
  "process_name": "{{#①최종키워드.structured_output.proc_keyword#}}",
  "eqp_name": "{{#①최종키워드.structured_output.eqp_keyword#}}",
  "model_name": "{{#①최종키워드.structured_output.model_keyword#}}"
}
```

#### Option B: structured_output 전체 전송
```json
{
  "text": null,
  "structured_output": "{{#①최종키워드.structured_output#}}"
}
```

### 3단계: 변수 참조 형식 확인

Dify에서 변수 참조는 다음 형식 중 하나를 사용합니다:
- `{{#노드ID.출력필드#}}`
- `{{노드ID.출력필드}}`
- 또는 UI에서 선택 시 자동 생성

## 현재 문제 해결

### 문제 1: 변수 참조가 문자열로 전송됨
**원인:** 변수 참조 형식이 잘못됨
**해결:** 올바른 변수 참조 형식 사용

### 문제 2: "Cleaning" 같은 실제 값이 전달되지 않음
**원인:** LLM 노드의 Structured Output에서 실제 값을 출력하지만, HTTP Request에서 변수 참조가 작동하지 않음
**해결:** 변수 삽입 기능을 사용하여 올바르게 연결

## 테스트 방법

1. 워크플로우 실행 후 HTTP Request의 "마지막 실행" 탭 확인
2. 실제 전송된 요청 본문 확인
3. 다음 중 하나가 되어야 함:
   - `"process_name": "Cleaning"` (실제 값)
   - `"structured_output": {"proc_keyword": "Cleaning", ...}` (객체)

다음은 **절대 안 됨**:
   - `"process_name": "1764575467466.structured_output.process_keyword"` (변수 참조 문자열)

## 참고: API에서 지원하는 형식

API는 다음 형식을 모두 지원합니다:

1. **직접 필드:**
   ```json
   {
     "process_name": "Cleaning",
     "eqp_name": "ASML_PH_#001"
   }
   ```

2. **structured_output 객체:**
   ```json
   {
     "structured_output": {
       "proc_keyword": "Cleaning",
       "eqp_keyword": "ASML_PH_#001"
     }
   }
   ```

3. **text 필드 (JSON 문자열):**
   ```json
   {
     "text": "{\"proc_keyword\": \"Cleaning\", \"eqp_keyword\": \"ASML_PH_#001\"}"
   }
   ```

가장 안정적인 방법은 **structured_output 객체 전체를 전송**하는 것입니다.

