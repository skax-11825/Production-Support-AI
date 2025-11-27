# Inform Note Agent - 반도체 공정 다운타임 관리 테이블 설정 가이드

## 개요

이 가이드는 반도체 공정에서 발생하는 장비 다운타임 정보를 관리하는 `INFORMNOTE_TABLE` 테이블을 Oracle DB에 생성하고 설정하는 방법을 설명합니다.

## 테이블 구조

### 주요 컬럼

- **기본 정보**
  - `informnote_id`: 다운타임 정보 고유 ID (Primary Key)
  - `site_id`: 사이트 ID (ICH: 이천, CJU: 청주, WUX: 우시 등)
  - `factory_id`: FAB/공장 ID
  - `line_id`: 라인 ID
  - `process_id`: 공정 ID

- **장비 정보**
  - `eqp_id`: 장비 ID (Equipment ID)
  - `model_id`: 장비 모델 ID

- **다운타임 정보**
  - `down_start_time`: 다운 시작 시각
  - `down_end_time`: 다운 종료 시각
  - `down_time_minutes`: 다운 지속 시간(분)
  - `down_type`: 다운 유형 (SCHEDULED / UNSCHEDULED)
  - `error_code`: 에러 코드

- **조치 정보**
  - `act_prob_reason`: 추정 원인
  - `act_content`: 조치 내용
  - `act_start_time`: 조치 시작 시각
  - `act_end_time`: 조치 종료 시각

- **담당자 정보**
  - `operator`: 작업자
  - `first_detector`: 최초 감지 주체

- **상태 정보**
  - `status_id`: 상태 (COMPLETED / IN_PROGRESS)

- **메타데이터**
  - `created_at`: 레코드 생성 시각 (자동)
  - `updated_at`: 레코드 수정 시각 (자동)

### 제약조건

- **Primary Key**: `informnote_id`
- **Check 제약조건**:
  - `down_type`: SCHEDULED 또는 UNSCHEDULED만 허용
  - `status_id`: COMPLETED 또는 IN_PROGRESS만 허용
  - `down_time_minutes`: 0 이상
  - 시간 순서 검증 (종료 시각 >= 시작 시각)

### 인덱스

반도체 공정 조회 최적화를 위한 인덱스:

- `IDX_INFORMNOTE_SITE`: 사이트별 조회
- `IDX_INFORMNOTE_FACTORY`: 공장별 조회
- `IDX_INFORMNOTE_LINE`: 라인별 조회
- `IDX_INFORMNOTE_EQP`: 장비별 조회 (가장 빈번)
- `IDX_INFORMNOTE_DOWN_TIME`: 다운타임 기간 조회
- `IDX_INFORMNOTE_STATUS`: 상태별 조회
- `IDX_INFORMNOTE_SITE_FACTORY_LINE`: 복합 조회
- `IDX_INFORMNOTE_ERROR_CODE`: 에러 코드 조회
- `IDX_INFORMNOTE_CREATED_AT`: 생성일 조회

## 설치 방법

### 1. 사전 요구사항

- Python 3.12
- Oracle 데이터베이스 연결 설정 (`.env` 파일)
- 필요한 패키지 설치 완료

### 2. 테이블 생성

#### 방법 1: Python 스크립트 사용 (권장)

```bash
./venv/bin/python3 setup_informnote_table.py
```

스크립트 실행 시:
- 데이터베이스 연결 확인
- SQL 파일 자동 실행
- 테이블 생성 확인
- 구조 검증

**옵션**:
- 기존 테이블 삭제 후 재생성: `y` 입력 (주의: 모든 데이터 삭제됨)

#### 방법 2: SQL 파일 직접 실행

```bash
# SQL*Plus 또는 SQL Developer에서 실행
sqlplus user/password@database < create_informnote_table.sql
```

또는 Oracle SQL Developer에서 `create_informnote_table.sql` 파일을 열어 실행

### 3. 샘플 데이터 삽입 (선택사항)

테스트를 위한 샘플 데이터 삽입:

```bash
./venv/bin/python3 insert_sample_data.py
```

실행 시 삽입할 데이터 개수 입력 (기본값: 10개)

## 사용 예시

### 데이터 조회

```sql
-- 특정 사이트의 다운타임 조회
SELECT * FROM INFORMNOTE_TABLE
WHERE site_id = 'ICH'
ORDER BY down_start_time DESC;

-- 특정 장비의 다운타임 조회
SELECT 
    informnote_id,
    down_start_time,
    down_end_time,
    down_time_minutes,
    down_type,
    status_id
FROM INFORMNOTE_TABLE
WHERE eqp_id = 'EQP001'
ORDER BY down_start_time DESC;

-- 기간별 다운타임 통계
SELECT 
    site_id,
    factory_id,
    COUNT(*) as downtime_count,
    SUM(down_time_minutes) as total_minutes,
    AVG(down_time_minutes) as avg_minutes
FROM INFORMNOTE_TABLE
WHERE down_start_time >= SYSDATE - 30
GROUP BY site_id, factory_id
ORDER BY total_minutes DESC;

-- 진행 중인 다운타임 조회
SELECT 
    informnote_id,
    eqp_id,
    down_start_time,
    down_time_minutes,
    status_id
FROM INFORMNOTE_TABLE
WHERE status_id = 'IN_PROGRESS'
ORDER BY down_start_time;
```

### 데이터 삽입

```sql
INSERT INTO INFORMNOTE_TABLE (
    informnote_id, site_id, factory_id, line_id, process_id,
    eqp_id, model_id, down_start_time, down_end_time, down_time_minutes,
    down_type, error_code, act_prob_reason, act_content,
    act_start_time, act_end_time, operator, first_detector, status_id
) VALUES (
    'IN000001', 'ICH', 'FAB1', 'LINE01', 'PHOTO',
    'EQP001', 'MODEL-A', 
    TIMESTAMP '2025-01-27 10:00:00',
    TIMESTAMP '2025-01-27 11:30:00',
    90,
    'UNSCHEDULED', 'ERR001', '장비 부품 고장', '부품 교체 완료',
    TIMESTAMP '2025-01-27 11:30:00',
    TIMESTAMP '2025-01-27 12:00:00',
    'OP001', 'AUTO', 'COMPLETED'
);
```

## 파일 설명

- `create_informnote_table.sql`: 테이블 생성 SQL 스크립트
- `setup_informnote_table.py`: 테이블 생성 자동화 Python 스크립트
- `insert_sample_data.py`: 샘플 데이터 삽입 스크립트
- `data_table.csv`: 테이블 정의서 (원본)

## 주의사항

1. **데이터 백업**: 기존 테이블을 삭제하기 전에 반드시 데이터를 백업하세요.
2. **권한 확인**: 테이블 생성 및 인덱스 생성 권한이 필요합니다.
3. **공간 확인**: 인덱스 생성 시 충분한 테이블스페이스가 필요합니다.
4. **성능**: 대용량 데이터 삽입 시 배치 처리 방식을 고려하세요.

## 문제 해결

### 테이블이 생성되지 않는 경우

1. 데이터베이스 연결 확인:
   ```bash
   python test_connection.py
   ```

2. 권한 확인:
   ```sql
   SELECT * FROM user_sys_privs WHERE privilege LIKE '%CREATE%';
   ```

3. SQL 파일 직접 실행하여 오류 메시지 확인

### 인덱스 생성 실패

- 테이블스페이스 공간 확인
- 인덱스 이름 충돌 확인 (이미 존재하는 경우)

### 데이터 삽입 실패

- 제약조건 위반 확인 (CHECK 제약조건, NOT NULL 등)
- 데이터 타입 불일치 확인
- Primary Key 중복 확인

## 추가 기능

### 시퀀스 사용 (자동 ID 생성)

테이블 생성 스크립트에 포함된 시퀀스를 활성화하려면:

```sql
-- 시퀀스 활성화
ALTER SEQUENCE SEQ_INFORMNOTE_ID START WITH 1;

-- 사용 예시
INSERT INTO INFORMNOTE_TABLE (informnote_id, ...)
VALUES (SEQ_INFORMNOTE_ID.NEXTVAL, ...);
```

## 지원

문제가 발생하거나 질문이 있으시면 프로젝트 관리자에게 문의하세요.

