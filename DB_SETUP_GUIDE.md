# Oracle 데이터베이스 구축 가이드

`recreate_database.py`를 사용하여 Oracle 데이터베이스를 구축하는 방법입니다.

## 사전 준비

### 1. 환경 변수 확인

`.env` 파일에 다음 정보가 올바르게 설정되어 있어야 합니다:

```env
ORACLE_USER=oracleuser
ORACLE_PASSWORD=oracle
ORACLE_DSN=localhost:1521/FREEPDB1
```

### 2. 데이터베이스 연결 확인

```bash
source venv/bin/activate
python test_connection.py
```

연결이 성공하면 다음 단계로 진행합니다.

## 데이터베이스 구축 실행

### 자동 실행 (확인 없이)

```bash
source venv/bin/activate
python recreate_database.py --yes
```

### 인터랙티브 실행 (확인 필요)

```bash
source venv/bin/activate
python recreate_database.py
# "yes" 입력하여 확인
```

## 실행 과정

스크립트는 다음 순서로 작업을 수행합니다:

### 1단계: 기존 테이블 삭제
- 외래키 제약조건을 고려하여 자식 테이블부터 삭제
- 삭제 순서: INFORM_NOTE → EQUIPMENT → ERROR_CODE → MODEL → LINE → FACTORY → FAB_TERMS_DICTIONARY → SITE → PROCESS → STATUS → DOWN_TYPE

### 2단계: 새 테이블 생성
다음 순서로 테이블을 생성합니다:

1. **레퍼런스 테이블** (`create_reference_tables.sql`)
   - SITE, FACTORY, LINE, PROCESS, MODEL, EQUIPMENT, ERROR_CODE, STATUS, DOWN_TYPE

2. **FAB_TERMS_DICTIONARY** (`create_semicon_term_dict.sql`)
   - 반도체 용어 사전 테이블

3. **INFORM_NOTE** (`create_informnote_table.sql`)
   - 다운타임 정보 메인 테이블

### 3단계: 테이블 확인
생성된 테이블 목록과 행 수를 확인합니다.

### 4단계: 레퍼런스 테이블 데이터 적재
`normalized_data.xlsx`의 다음 시트에서 데이터를 적재합니다:
- site
- factory
- line
- process
- model
- equipment
- error_code
- status
- down_type

### 5단계: 용어 사전 데이터 적재
`normalized_data.xlsx`의 `fab_terms_dictionary` 시트에서 데이터를 적재합니다.

### 6단계: Inform Note 데이터 적재
`normalized_data.xlsx`의 `Inform_note` 시트에서 데이터를 적재합니다.

## 생성되는 테이블 구조

### 레퍼런스 테이블
- **SITE**: 사이트 정보
- **FACTORY**: 공장 정보 (SITE 참조)
- **LINE**: 라인 정보 (FACTORY 참조)
- **PROCESS**: 공정 정보
- **MODEL**: 장비 모델 정보 (PROCESS 참조)
- **EQUIPMENT**: 장비 정보 (MODEL, LINE 참조)
- **ERROR_CODE**: 에러 코드 정보 (PROCESS 참조)
- **STATUS**: 상태 정보
- **DOWN_TYPE**: 다운타임 유형 정보

### 메인 테이블
- **INFORM_NOTE**: 다운타임 정보 (DOWN_TYPE, STATUS 참조)
- **FAB_TERMS_DICTIONARY**: 반도체 용어 사전

## 문제 해결

### DB 연결 실패
- `.env` 파일의 인증 정보 확인
- Oracle DB가 실행 중인지 확인
- DSN 형식 확인 (예: `localhost:1521/FREEPDB1`)

### 테이블 생성 실패
- SQL 파일이 올바른 위치에 있는지 확인
- 이전 실행의 잔여 객체가 있는지 확인
- 로그를 확인하여 구체적인 오류 메시지 확인

### 데이터 적재 실패
- `normalized_data.xlsx` 파일이 존재하는지 확인
- 엑셀 파일의 시트 이름이 정확한지 확인
- 외래키 제약조건 위반이 없는지 확인

## 로그 확인

실행 중 상세한 로그가 출력됩니다. 문제가 발생하면 로그를 확인하세요:

```bash
python recreate_database.py --yes 2>&1 | tee db_setup.log
```

## 완료 확인

스크립트 실행 후 다음 명령으로 테이블을 확인할 수 있습니다:

```sql
SELECT table_name, num_rows 
FROM user_tables 
ORDER BY table_name;
```

