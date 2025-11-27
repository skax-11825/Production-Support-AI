-- ============================================================
-- Inform Note Agent - 반도체 공정 다운타임 관리 테이블
-- 생성일: 2025-01-27
-- 설명: 반도체 공정에서 발생하는 장비 다운타임 정보를 관리하는 테이블
-- ============================================================

-- 기존 테이블이 있으면 삭제 (주의: 데이터도 함께 삭제됨)
-- DROP TABLE INFORMNOTE_TABLE CASCADE CONSTRAINTS;

-- 테이블 생성
CREATE TABLE INFORMNOTE_TABLE (
    -- Primary Key
    informnote_id VARCHAR2(10) NOT NULL,
    
    -- 사이트/공장/라인 정보 (반도체 공정 계층 구조)
    site_id VARCHAR2(10),           -- 사이트 ID (ICH, CJU, WUX 등)
    factory_id VARCHAR2(20),        -- FAB/공장 ID
    line_id VARCHAR2(30),            -- 라인 ID
    process_id VARCHAR2(20),        -- 공정 ID
    
    -- 장비 정보
    eqp_id VARCHAR2(50),            -- 장비 ID (Equipment ID)
    model_id VARCHAR2(50),          -- 장비 모델 ID
    
    -- 다운타임 정보
    down_start_time TIMESTAMP,      -- 다운 시작 시각
    down_end_time TIMESTAMP,        -- 다운 종료 시각
    down_time_minutes NUMBER(10,2), -- 다운 지속 시간(분) - 소수점 허용
    down_type VARCHAR2(20),         -- 다운 유형 (SCHEDULED / UNSCHEDULED)
    error_code VARCHAR2(50),       -- 에러 코드
    
    -- 조치 정보
    act_prob_reason VARCHAR2(200), -- 추정 원인
    act_content VARCHAR2(200),      -- 조치 내용
    act_start_time TIMESTAMP,       -- 조치 시작 시각
    act_end_time TIMESTAMP,         -- 조치 종료 시각
    
    -- 담당자 정보
    operator VARCHAR2(50),          -- 작업자
    first_detector VARCHAR2(50),    -- 최초 감지 주체
    
    -- 상태 정보
    status_id VARCHAR2(20),         -- 상태 (COMPLETED / IN_PROGRESS)
    
    -- 메타데이터
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 생성 시각
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 수정 시각
    
    -- Primary Key 제약조건
    CONSTRAINT INFORMNOTE_TABLE_PK PRIMARY KEY (informnote_id),
    
    -- 체크 제약조건
    CONSTRAINT CHK_DOWN_TYPE CHECK (down_type IN ('SCHEDULED', 'UNSCHEDULED', NULL)),
    CONSTRAINT CHK_STATUS_ID CHECK (status_id IN ('COMPLETED', 'IN_PROGRESS', NULL)),
    CONSTRAINT CHK_DOWN_TIME CHECK (down_time_minutes >= 0 OR down_time_minutes IS NULL),
    CONSTRAINT CHK_TIME_ORDER CHECK (
        (down_start_time IS NULL AND down_end_time IS NULL) OR
        (down_start_time IS NOT NULL AND down_end_time IS NOT NULL AND down_end_time >= down_start_time) OR
        (down_start_time IS NULL OR down_end_time IS NULL)
    ),
    CONSTRAINT CHK_ACT_TIME_ORDER CHECK (
        (act_start_time IS NULL AND act_end_time IS NULL) OR
        (act_start_time IS NOT NULL AND act_end_time IS NOT NULL AND act_end_time >= act_start_time) OR
        (act_start_time IS NULL OR act_end_time IS NULL)
    )
);

-- 인덱스 생성 (반도체 공정 조회 최적화)
-- 사이트별 조회
CREATE INDEX IDX_INFORMNOTE_SITE ON INFORMNOTE_TABLE(site_id);

-- 공장별 조회
CREATE INDEX IDX_INFORMNOTE_FACTORY ON INFORMNOTE_TABLE(factory_id);

-- 라인별 조회
CREATE INDEX IDX_INFORMNOTE_LINE ON INFORMNOTE_TABLE(line_id);

-- 장비별 조회 (가장 빈번한 조회)
CREATE INDEX IDX_INFORMNOTE_EQP ON INFORMNOTE_TABLE(eqp_id);

-- 다운타임 기간 조회 (시간 범위 검색용)
CREATE INDEX IDX_INFORMNOTE_DOWN_TIME ON INFORMNOTE_TABLE(down_start_time, down_end_time);

-- 상태별 조회
CREATE INDEX IDX_INFORMNOTE_STATUS ON INFORMNOTE_TABLE(status_id);

-- 복합 인덱스 (사이트-공장-라인 조회)
CREATE INDEX IDX_INFORMNOTE_SITE_FACTORY_LINE ON INFORMNOTE_TABLE(site_id, factory_id, line_id);

-- 에러 코드 조회
CREATE INDEX IDX_INFORMNOTE_ERROR_CODE ON INFORMNOTE_TABLE(error_code);

-- 생성일 조회
CREATE INDEX IDX_INFORMNOTE_CREATED_AT ON INFORMNOTE_TABLE(created_at);

-- 코멘트 추가 (테이블 및 컬럼 설명)
COMMENT ON TABLE INFORMNOTE_TABLE IS '반도체 공정 장비 다운타임 관리 테이블';
COMMENT ON COLUMN INFORMNOTE_TABLE.informnote_id IS '다운타임 정보 고유 ID (Primary Key)';
COMMENT ON COLUMN INFORMNOTE_TABLE.site_id IS '사이트 ID (ICH: 이천, CJU: 청주, WUX: 우시 등)';
COMMENT ON COLUMN INFORMNOTE_TABLE.factory_id IS 'FAB/공장 ID';
COMMENT ON COLUMN INFORMNOTE_TABLE.line_id IS '라인 ID';
COMMENT ON COLUMN INFORMNOTE_TABLE.process_id IS '공정 ID';
COMMENT ON COLUMN INFORMNOTE_TABLE.eqp_id IS '장비 ID (Equipment ID)';
COMMENT ON COLUMN INFORMNOTE_TABLE.model_id IS '장비 모델 ID';
COMMENT ON COLUMN INFORMNOTE_TABLE.down_start_time IS '다운 시작 시각';
COMMENT ON COLUMN INFORMNOTE_TABLE.down_end_time IS '다운 종료 시각';
COMMENT ON COLUMN INFORMNOTE_TABLE.down_time_minutes IS '다운 지속 시간(분)';
COMMENT ON COLUMN INFORMNOTE_TABLE.down_type IS '다운 유형: SCHEDULED(계획), UNSCHEDULED(비계획)';
COMMENT ON COLUMN INFORMNOTE_TABLE.error_code IS '에러 코드';
COMMENT ON COLUMN INFORMNOTE_TABLE.act_prob_reason IS '추정 원인';
COMMENT ON COLUMN INFORMNOTE_TABLE.act_content IS '조치 내용';
COMMENT ON COLUMN INFORMNOTE_TABLE.act_start_time IS '조치 시작 시각';
COMMENT ON COLUMN INFORMNOTE_TABLE.act_end_time IS '조치 종료 시각';
COMMENT ON COLUMN INFORMNOTE_TABLE.operator IS '작업자';
COMMENT ON COLUMN INFORMNOTE_TABLE.first_detector IS '최초 감지 주체';
COMMENT ON COLUMN INFORMNOTE_TABLE.status_id IS '상태: COMPLETED(완료), IN_PROGRESS(진행중)';
COMMENT ON COLUMN INFORMNOTE_TABLE.created_at IS '레코드 생성 시각';
COMMENT ON COLUMN INFORMNOTE_TABLE.updated_at IS '레코드 수정 시각';

-- 업데이트 시각 자동 갱신 트리거 생성
CREATE OR REPLACE TRIGGER TRG_INFORMNOTE_UPDATE
BEFORE UPDATE ON INFORMNOTE_TABLE
FOR EACH ROW
BEGIN
    :NEW.updated_at := SYSTIMESTAMP;
END;
/

-- 시퀀스 생성 (informnote_id 자동 생성용 - 필요시 사용)
-- CREATE SEQUENCE SEQ_INFORMNOTE_ID
-- START WITH 1
-- INCREMENT BY 1
-- NOCACHE
-- NOCYCLE;

-- 테이블 생성 확인
SELECT 
    table_name,
    num_rows,
    last_analyzed
FROM user_tables
WHERE table_name = 'INFORMNOTE_TABLE';

-- 인덱스 확인
SELECT 
    index_name,
    column_name,
    column_position
FROM user_ind_columns
WHERE table_name = 'INFORMNOTE_TABLE'
ORDER BY index_name, column_position;

