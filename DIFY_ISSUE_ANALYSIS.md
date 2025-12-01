# Dify LLM 키워드 추출 문제 분석 및 해결

## 문제 분석

### 작동하지 않는 질문들

#### 1. "2025년 5월 Cleaning 공정 에러 건수 보여줘"
**로그 분석:**
```
[ID 조회] 요청 수신 - 전체 요청: {
  "process_name": "1764575467466.structured_output.process_keyword",
  "model_name": "",
  "eqp_name": ""
}
[키워드 추출] 변수 참조 패턴 감지, 무시: 1764575467466.structured_output.process_keyword
[ID 조회] 최종 결과: {'process_id': None, 'model_id': None, 'eqp_id': None}
```

**문제점:**
- Dify가 변수 참조 문자열을 그대로 전송
- 실제 "Cleaning" 값이 전달되지 않음
- 변수 참조 패턴으로 감지되어 무시됨

**DB 확인 결과:**
- "Cleaning" → "PROC_CLN" 매핑은 정상 작동 ✅
- 테스트: `{"process_name": "Cleaning"}` → `{"process_id": "PROC_CLN"}` ✅

#### 2. "ASML_PH_#001 에러의 월별 발생 추이 보여줘"
**문제점:**
- 비슷한 문제 (변수 참조 문자열 전송)

**DB 확인 결과:**
- "ASML_PH_#001" → "M14-PH-001" 매핑은 정상 작동 ✅
- 테스트: `{"eqp_name": "ASML_PH_#001"}` → `{"eqp_id": "M14-PH-001"}` ✅

### 작동하는 질문

#### 3. "M14-PH-008 장비의 에러 내역 알려줘"
**로그 분석:**
```
[ID 조회] 요청 수신 - 전체 요청: {
  "process_name": "1764575467466.structured_output.process_keyword",
  "model_name": "",
  "eqp_name": "M14-PH-008"
}
[ID 조회] 최종 결과: {'process_id': None, 'model_id': None, 'eqp_id': 'M14-PH-008'}
```

**성공 이유:**
- `eqp_name`에 이미 ID 형식("M14-PH-008")이 직접 전달됨
- 변수 참조가 아닌 실제 값이라 바로 매칭됨

## 핵심 문제점

### 1. Dify가 변수 참조를 문자열로 전송
- Dify 워크플로우에서 변수 참조(`1764575467466.structured_output.process_keyword`)가 실제 값 대신 전송됨
- API는 이를 변수 참조 패턴으로 감지하여 무시함

### 2. OR 연산자(||)가 포함된 경우
- 예: `"에칭 || 1764575467466.structured_output.process_keyword"`
- 실제 값("에칭")이 있지만 전체가 변수 참조로 감지되어 무시됨

### 3. Dify 워크플로우 설정 문제 가능성
- LLM이 키워드를 추출했지만, HTTP Request 노드에서 변수 참조가 제대로 해석되지 않음
- 구조화된 출력(Structured Output)이 제대로 파싱되지 않음

## 해결 방법

### 1. 코드 개선 (완료)

#### OR 연산자 처리 추가
```python
def clean_value(value):
    # OR 연산자(||)로 분리되어 있는 경우 처리
    if '||' in str_val:
        parts = [part.strip() for part in str_val.split('||')]
        # 변수 참조가 아닌 실제 값만 추출
        for part in parts:
            if part and not is_variable_reference(part):
                return part
```

#### 변수 참조 감지 개선
```python
def is_variable_reference(value: str) -> bool:
    """변수 참조 패턴인지 확인"""
    # 숫자.structured_output.keyword 패턴 감지
    if '.' in value_lower:
        if value_lower.startswith('.') or (
            any(char.isdigit() for char in value_lower[:10]) and 
            any(kw in value_lower for kw in ['structured_output', 'keyword', 'output'])
        ):
            return True
    return False
```

### 2. Dify 워크플로우 수정 필요

#### HTTP Request 노드 설정 확인
1. **Request Body** 설정 확인:
   - 변수 참조가 아닌 실제 값이 전달되도록 설정
   - 예: `{{#1764575467466.structured_output.process_keyword#}}` 형식 사용

2. **Structured Output** 사용:
   - LLM 노드에서 Structured Output을 사용하는 경우
   - HTTP Request 노드에서 `{{#노드ID.structured_output.필드명#}}` 형식 사용

3. **변수 참조 형식 확인:**
   ```json
   {
     "process_name": "{{#1764575467466.structured_output.proc_keyword#}}",
     "eqp_name": "{{#1764575467466.structured_output.eqp_keyword#}}"
   }
   ```

#### LLM 프롬프트 개선
- 키워드 추출 프롬프트에서 명확한 출력 형식 요구
- 예: "Cleaning", "ASML_PH_#001" 같은 실제 값만 출력

## 테스트 결과

### 정상 작동 케이스
```bash
# Cleaning → PROC_CLN
curl -X POST "http://localhost:8000/lookup/ids" \
  -H "Content-Type: application/json" \
  -d '{"process_name": "Cleaning"}'
# 결과: {"process_id": "PROC_CLN", "model_id": null, "eqp_id": null} ✅

# ASML_PH_#001 → M14-PH-001
curl -X POST "http://localhost:8000/lookup/ids" \
  -H "Content-Type: application/json" \
  -d '{"eqp_name": "ASML_PH_#001"}'
# 결과: {"process_id": null, "model_id": null, "eqp_id": "M14-PH-001"} ✅
```

### 문제 케이스
```bash
# 변수 참조 문자열 → 무시됨
{"process_name": "1764575467466.structured_output.process_keyword"}
# 결과: {"process_id": null, ...} ❌

# OR 연산자 포함 → 개선된 로직으로 실제 값 추출 가능
{"process_name": "에칭 || 1764575467466.structured_output.process_keyword"}
# 결과: "에칭" 추출 ✅
```

## 다음 단계

1. ✅ 코드 개선 완료 (OR 연산자 처리, 변수 참조 감지 개선)
2. ⚠️ Dify 워크플로우 수정 필요:
   - HTTP Request 노드의 Request Body 설정 확인
   - 변수 참조 형식 확인 (`{{#...#}}`)
   - Structured Output에서 실제 값이 전달되는지 확인

3. 🔍 추가 디버깅:
   - Dify 워크플로우 실행 로그 확인
   - HTTP Request 노드의 실제 전송 데이터 확인
   - LLM 출력 원본 확인

## 권장 조치사항

1. **Dify 워크플로우에서 변수 참조 확인:**
   - HTTP Request 노드의 Request Body에서 변수 참조가 올바른 형식인지 확인
   - 예: `{{#노드ID.structured_output.필드명#}}`

2. **LLM 출력 확인:**
   - LLM 노드에서 실제로 "Cleaning", "ASML_PH_#001" 같은 값을 출력하는지 확인

3. **API 로그 모니터링:**
   - 서버 로그에서 실제 수신 요청 확인
   - 변수 참조 패턴이 계속 나타나면 Dify 설정 문제

4. **대안 방법:**
   - Dify에서 `text` 필드나 `structured_output` 객체로 전체 데이터 전송
   - API에서 JSON 파싱하여 키워드 추출 (이미 구현됨)

