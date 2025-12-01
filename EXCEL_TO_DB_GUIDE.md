# 엑셀 파일 → Oracle DB 데이터 적재 가이드

## 개요

이 프로젝트에서는 `normalized_data_preprocessed.xlsx` 엑셀 파일의 데이터를 Oracle 데이터베이스에 자동으로 적재합니다.

## 사용되는 코드 파일

### 1. `load_data.py` - 데이터 적재 스크립트

**역할**: 엑셀 파일을 읽어서 Oracle DB 테이블에 데이터를 삽입합니다.

**주요 기능**:
- 엑셀 시트별 데이터 읽기 (`pandas.read_excel()`)
- 엑셀 컬럼명 → DB 컬럼명 매핑
- 데이터 정리 및 변환 (`_clean()`, `_clean_number()`)
- Oracle DB에 INSERT/MERGE 실행

**주요 함수**:
- `load_reference_dependencies()`: SITE, FACTORY, LINE 테이블 데이터 적재
- `load_reference_tables()`: 레퍼런스 테이블 데이터 적재 (PROCESS, MODEL, EQUIPMENT, ERROR_CODE, STATUS, DOWN_TYPE)
- `load_term_dictionary()`: FAB_TERMS_DICTIONARY 테이블 데이터 적재
- `load_inform_notes()`: INFORM_NOTE 테이블 데이터 적재

**사용 예시**:
```python
from load_data import (
    load_reference_dependencies,
    load_reference_tables,
    load_term_dictionary,
    load_inform_notes
)

# 1. 참조 테이블 먼저 적재
load_reference_dependencies()

# 2. 레퍼런스 테이블 적재
load_reference_tables()

# 3. 용어 사전 적재
load_term_dictionary(truncate=True)

# 4. Inform Note 데이터 적재
load_inform_notes()
```

### 2. `recreate_database.py` - 전체 DB 재구성 통합 스크립트

**역할**: 전체 데이터베이스를 초기화하고, 테이블을 재생성한 후, 데이터를 적재합니다.

**작업 순서**:
1. 기존 테이블 삭제 (외래키 제약조건 고려)
2. SQL 파일로 테이블 생성 (`create_reference_tables.sql`, `create_semicon_term_dict.sql`, `create_informnote_table.sql`)
3. 참조 테이블 데이터 적재 (SITE, FACTORY, LINE)
4. 레퍼런스 테이블 데이터 적재
5. 용어 사전 데이터 적재
6. Inform Note 데이터 적재

**사용 예시**:
```bash
# 확인 없이 자동 실행
python3 recreate_database.py --yes

# 또는 확인 후 실행
python3 recreate_database.py
```

## 엑셀 파일 구조

**파일명**: `normalized_data_preprocessed.xlsx`

**시트 구성**:
- `process`: 공정 정보
- `model`: 모델 정보
- `equipment`: 장비 정보
- `error_code`: 에러 코드 정보
- `status`: 상태 정보
- `down_type`: 다운 타입 정보
- `fab_terms_dictionary`: 반도체 용어 사전
- `inform_note`: 작업 내역 정보

## 엑셀 → DB 매핑 규칙

### 시트명 → 테이블명
- 엑셀 시트명을 대문자로 변환하여 테이블명으로 사용
- 예: `process` → `PROCESS`, `inform_note` → `INFORM_NOTE`

### 컬럼명 매핑
`load_data.py`의 `REFERENCE_TABLE_CONFIG`에 정의된 매핑 규칙을 따릅니다:

```python
REFERENCE_TABLE_CONFIG = {
    'process': {
        'table': 'PROCESS',
        'columns': {
            'process_id': 'PROCESS_ID',
            'process_name': 'PROCESS_NAME',
            'process_abbr': 'PROCESS_ABBR'
        }
    },
    # ... 기타 시트 매핑
}
```

**중요**: 엑셀 파일의 시트명과 컬럼명은 절대 변경하지 않고 그대로 사용합니다.

## 데이터 정리 로직

### `_clean()` 함수
- `None` 값 처리
- `NaN` 값 제거
- 문자열 공백 제거
- `pd.Timestamp` → `datetime` 변환

### `_clean_number()` 함수
- 숫자 값 정리 및 검증
- 문자열 숫자 변환 시도

## 특수 처리

### 1. SITE, FACTORY, LINE 테이블
- 엑셀 파일에 별도 시트가 없음
- `inform_note` 시트에서 관련 데이터를 추출하여 자동 생성
- `load_reference_dependencies()` 함수에서 처리

### 2. FAB_TERMS_DICTIONARY 테이블
- MERGE SQL 사용 (INSERT OR UPDATE)
- `term_id`를 기준으로 중복 처리
- `meaning_short ` (공백 포함) 컬럼명 자동 처리

### 3. INFORM_NOTE 테이블
- 대량 데이터 처리 (배치 INSERT)
- `inform_note_id` → `informnote_id` 매핑 (언더스코어 제거)
- 외래키 관계 고려하여 참조 테이블 먼저 적재

## 실행 방법

### 전체 DB 재구성 및 데이터 적재
```bash
# 가상환경 활성화
source venv/bin/activate  # macOS/Linux
# 또는
venv\Scripts\activate  # Windows

# 전체 재구성 실행
python3 recreate_database.py --yes
```

### 개별 데이터 적재 (테이블은 이미 존재하는 경우)
```python
from load_data import load_reference_tables, load_term_dictionary, load_inform_notes

load_reference_tables()
load_term_dictionary(truncate=True)
load_inform_notes()
```

## 주의사항

1. **데이터 백업**: `recreate_database.py`는 모든 기존 테이블과 데이터를 삭제합니다. 실행 전 백업을 권장합니다.

2. **외래키 제약조건**: 테이블 삭제 시 외래키 제약조건을 고려한 순서로 진행됩니다.

3. **엑셀 파일 위치**: `normalized_data_preprocessed.xlsx` 파일이 프로젝트 루트에 있어야 합니다.

4. **데이터 타입**: 엑셀의 날짜/시간 데이터는 자동으로 변환되지만, 형식이 맞지 않으면 오류가 발생할 수 있습니다.

## 관련 파일

- `load_data.py`: 데이터 적재 로직
- `recreate_database.py`: 전체 재구성 통합 스크립트
- `create_reference_tables.sql`: 레퍼런스 테이블 스키마
- `create_semicon_term_dict.sql`: 용어 사전 테이블 스키마
- `create_informnote_table.sql`: Inform Note 테이블 스키마
- `database.py`: Oracle DB 연결 관리
- `normalized_data_preprocessed.xlsx`: 원본 엑셀 데이터 파일

