-- ============================================================
-- Inform Note Agent - 반도체 공정 다운타임 관리 테이블
-- 생성일: 2025-01-27
-- 설명: 반도체 공정에서 발생하는 장비 다운타임 정보를 관리하는 테이블
-- normalized_data.xlsx의 'Inform_note' 시트 기반
-- 테이블 이름: INFORM_NOTE (엑셀 시트 이름의 대문자 버전)
-- ============================================================

-- 기존 테이블이 있으면 삭제 (주의: 데이터도 함께 삭제됨)
-- DROP TABLE INFORM_NOTE CASCADE CONSTRAINTS;

-- 테이블 생성
CREATE TABLE INFORM_NOTE (
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
    down_type_id NUMBER(5),         -- 다운 유형 (FK)
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
    status_id NUMBER(5),            -- 상태 (FK)
    link VARCHAR2(200),             -- 참고 링크
    
    -- 메타데이터
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 생성 시각
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 수정 시각
    
    -- Primary Key 제약조건
    CONSTRAINT PK_INFORM_NOTE_TBL PRIMARY KEY (informnote_id),
    
    -- Foreign Key 제약조건
    CONSTRAINT FK_INFORM_NOTE_DOWN_TYPE FOREIGN KEY (down_type_id) REFERENCES DOWN_TYPE(DOWN_TYPE_ID),
    CONSTRAINT FK_INFORM_NOTE_STATUS FOREIGN KEY (status_id) REFERENCES STATUS(STATUS_ID),
    
    -- 체크 제약조건
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
CREATE INDEX IDX_INFORM_NOTE_SITE_COL ON INFORM_NOTE(site_id);

-- 공장별 조회
CREATE INDEX IDX_INFORM_NOTE_FACTORY_COL ON INFORM_NOTE(factory_id);

-- 라인별 조회
CREATE INDEX IDX_INFORM_NOTE_LINE_COL ON INFORM_NOTE(line_id);

-- 장비별 조회 (가장 빈번한 조회)
CREATE INDEX IDX_INFORM_NOTE_EQP_COL ON INFORM_NOTE(eqp_id);

-- 다운타임 기간 조회 (시간 범위 검색용)
CREATE INDEX IDX_INFORM_NOTE_DOWN_TIME_COL ON INFORM_NOTE(down_start_time, down_end_time);

-- 상태별 조회
CREATE INDEX IDX_INFORM_NOTE_STATUS_COL ON INFORM_NOTE(status_id);

-- 다운 유형별 조회
CREATE INDEX IDX_INFORM_NOTE_DOWN_TYPE_COL ON INFORM_NOTE(down_type_id);

-- 복합 인덱스 (사이트-공장-라인 조회)
CREATE INDEX IDX_INFORM_NOTE_SFL_COL ON INFORM_NOTE(site_id, factory_id, line_id);

-- 에러 코드 조회
CREATE INDEX IDX_INFORM_NOTE_ERROR_COL ON INFORM_NOTE(error_code);

-- 생성일 조회
CREATE INDEX IDX_INFORM_NOTE_CREATED_COL ON INFORM_NOTE(created_at);

-- 코멘트 추가 (테이블 및 컬럼 설명)
COMMENT ON TABLE INFORM_NOTE IS 'normalized_data.xlsx Inform_note 시트 기반 테이블';
COMMENT ON COLUMN INFORM_NOTE.informnote_id IS '다운타임 정보 고유 ID (Primary Key)';
COMMENT ON COLUMN INFORM_NOTE.site_id IS '사이트 ID (ICH: 이천, CJU: 청주, WUX: 우시 등)';
COMMENT ON COLUMN INFORM_NOTE.factory_id IS 'FAB/공장 ID';
COMMENT ON COLUMN INFORM_NOTE.line_id IS '라인 ID';
COMMENT ON COLUMN INFORM_NOTE.process_id IS '공정 ID';
COMMENT ON COLUMN INFORM_NOTE.eqp_id IS '장비 ID (Equipment ID)';
COMMENT ON COLUMN INFORM_NOTE.model_id IS '장비 모델 ID';
COMMENT ON COLUMN INFORM_NOTE.down_start_time IS '다운 시작 시각';
COMMENT ON COLUMN INFORM_NOTE.down_end_time IS '다운 종료 시각';
COMMENT ON COLUMN INFORM_NOTE.down_time_minutes IS '다운 지속 시간(분)';
COMMENT ON COLUMN INFORM_NOTE.down_type_id IS '다운 유형 ID (FK)';
COMMENT ON COLUMN INFORM_NOTE.error_code IS '에러 코드';
COMMENT ON COLUMN INFORM_NOTE.act_prob_reason IS '추정 원인';
COMMENT ON COLUMN INFORM_NOTE.act_content IS '조치 내용';
COMMENT ON COLUMN INFORM_NOTE.act_start_time IS '조치 시작 시각';
COMMENT ON COLUMN INFORM_NOTE.act_end_time IS '조치 종료 시각';
COMMENT ON COLUMN INFORM_NOTE.operator IS '작업자';
COMMENT ON COLUMN INFORM_NOTE.first_detector IS '최초 감지 주체';
COMMENT ON COLUMN INFORM_NOTE.status_id IS '상태 ID (FK)';
COMMENT ON COLUMN INFORM_NOTE.link IS '참조 링크 (https://gipms.com/reference/번호)';
COMMENT ON COLUMN INFORM_NOTE.created_at IS '레코드 생성 시각';
COMMENT ON COLUMN INFORM_NOTE.updated_at IS '레코드 수정 시각';

-- 업데이트 시각 자동 갱신 트리거 생성
CREATE OR REPLACE TRIGGER TRG_INFORM_NOTE_UPDATE
BEFORE UPDATE ON INFORM_NOTE
FOR EACH ROW
BEGIN
    :NEW.updated_at := SYSTIMESTAMP;
END;

-- 시퀀스 생성 (informnote_id 자동 생성용 - 필요시 사용)
-- CREATE SEQUENCE SEQ_INFORMNOTE_ID
-- START WITH 1
-- INCREMENT BY 1
-- NOCACHE
-- NOCYCLE;

-- 테이블 생성 확인
