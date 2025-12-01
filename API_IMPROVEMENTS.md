# API 개선 사항 요약

## 개선된 API 엔드포인트

### 1. `/lookup/ids` - ID 조회 API
**개선 사항:**
- Dify 변수 참조 패턴 자동 감지 및 처리
- OR 연산자(`||`) 처리: 실제 값 추출
- 상세 로깅 추가

**처리 로직:**
- `"{{ http7.response.process_id }}"` → `None` 처리
- `"에칭 || 변수참조"` → `"에칭"` 추출
- 변수 참조 문자열 자동 감지 및 무시

### 2. `/api/v1/informnote/stats/error-code` - 에러 통계 API
**개선 사항:**
- 변수 참조 패턴 감지 및 처리
- 잘못된 필드 값 감지 (error_code에 장비명/공정명)
- 모든 필터가 None인 경우 경고 로그
- 상세 로깅 추가

**처리 로직:**
- `process_id: "{{ http7.response.process_id }}"` → `None` 처리
- `error_code: "ASML_PH_#001"` (장비명) → `None` 처리
- 모든 필터가 None이면 경고 로그 출력

### 3. `/api/v1/informnote/search` - 작업 내역 검색 API
**개선 사항:**
- 변수 참조 패턴 감지 및 처리
- 모든 필터가 None인 경우 경고 로그
- 상세 로깅 추가

**처리 로직:**
- `process_id: "{{ http7.response.process_id }}"` → `None` 처리
- `eqp_id: "{{ http7.response.eqp_id }}"` → `None` 처리
- 모든 필터가 None이면 경고 로그 출력

### 4. `/api/v1/informnote/history/pm` - PM 이력 API
**개선 사항:**
- 변수 참조 패턴 감지 및 처리
- 모든 필터가 None인 경우 경고 로그
- 상세 로깅 추가

## 공통 개선 사항

### `clean_request_value()` 함수 추가
```python
def clean_request_value(value: Optional[str], field_name: str = "") -> Optional[str]:
    """요청 값 정리: 변수 참조 패턴, null 문자열 처리"""
    # Dify 변수 참조 패턴 감지 ({{ ... }}, http7.response.xxx)
    # null 문자열 처리
    # 빈 문자열 처리
```

**감지하는 패턴:**
- `{{ ... }}` (중괄호 포함)
- `http7.response.xxx` (변수 참조)
- `null` (문자열)

### 로깅 개선
- 요청 수신 시 전체 파라미터 로깅
- 변수 참조 감지 시 경고 로그
- 모든 필터가 None인 경우 경고 로그
- 조회 결과 건수 로깅

## 현재 문제점

### Dify 워크플로우 설정 문제
1. **변수 참조가 문자열로 전송됨:**
   - `"process_id": "{{ http7.response.process_id }}"`
   - 올바른 형식: `"process_id": "{{#http7.response.process_id#}}"`

2. **결과:**
   - 모든 필터가 `None`이 되어 전체 데이터 조회
   - 의도한 필터링이 작동하지 않음

### 해결 방법

**Dify HTTP Request 노드 설정 수정:**

**잘못된 설정 (현재):**
```json
{
  "process_id": "{{ http7.response.process_id }}",
  "eqp_id": "{{ http7.response.eqp_id }}"
}
```

**올바른 설정 (권장):**
```json
{
  "structured_output": "{{#http7.response#}}"
}
```

또는:

```json
{
  "process_id": "{{#http7.response.process_id#}}",
  "eqp_id": "{{#http7.response.eqp_id#}}"
}
```

## 테스트 결과

### 정상 작동 케이스
```bash
# 실제 값 전달
{"process_id": "PROC_CLN"}
→ 정상 조회 (115건 - 에러 통계, 3건 - 작업 내역)

{"eqp_name": "ASML_PH_#001"}
→ 정상 매핑 (M14-PH-001)
```

### 문제 케이스 (변수 참조 문자열)
```bash
{"process_id": "{{ http7.response.process_id }}"}
→ None 처리 → 전체 데이터 조회 (1522건)
```

## 다음 단계

1. ✅ API 개선 완료
2. ⚠️ Dify 워크플로우 수정 필요:
   - HTTP Request 노드의 변수 참조 형식 확인
   - `{{#...#}}` 형식 사용
   - 또는 `structured_output` 객체 전체 전송

3. 📝 로깅 확인:
   - 서버 로그에서 변수 참조 감지 여부 확인
   - 실제 전달되는 값 확인

