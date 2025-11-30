#!/usr/bin/env python3
"""
모든 데이터 적재 스크립트 통합
- 레퍼런스 테이블 데이터
- 반도체 용어 사전 데이터
- Inform Note 데이터
"""
from pathlib import Path
import logging
from typing import Dict, Any, List
import math
import pandas as pd
from database import db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

DATA_FILE = Path(__file__).parent / 'normalized_data.xlsx'

# 레퍼런스 테이블 설정
# 테이블 이름은 엑셀 시트 이름의 대문자 버전과 정확히 일치합니다
# 예: 'site' 시트 -> 'SITE' 테이블, 'error_code' 시트 -> 'ERROR_CODE' 테이블
REFERENCE_TABLE_CONFIG = {
    'site': {'columns': {'site_id': 'site_id', 'site_name': 'site_name'}},
    'factory': {'columns': {'factory_id': 'factory_id', 'factory_name': 'factory_name', 'site_id': 'site_id'}},
    'line': {'columns': {'line_id': 'line_id', 'line_name': 'line_name', 'factory_id': 'factory_id'}},
    'process': {'columns': {'process_id': 'process_id', 'process_name': 'process_name', 'process_abbr': 'process_abbr'}},
    'model': {'columns': {'model_id': 'model_id', 'model_name': 'model_name', 'process_id': 'process_id', 'vendor': 'vendor'}},
    'equipment': {'columns': {'eqp_id': 'eqp_id', 'eqp_name': 'eqp_name', 'model_id': 'model_id', 'line_id': 'line_id'}},
    'error_code': {'columns': {'error_code': 'error_code', 'error_desc': 'error_desc', 'process_id': 'process_id'}},
    'status': {'columns': {'status_id': 'status_id', 'status': 'status_name'}},
    'down_type': {'columns': {'down_type_id': 'down_type_id', 'down_type': 'down_type_name'}},
}

# 용어 사전 MERGE SQL (테이블 이름은 동적으로 생성)
def get_term_dict_merge_sql(table_name: str) -> str:
    """용어 사전 MERGE SQL 생성 (테이블 이름 동적)"""
    return f"""
MERGE INTO {table_name} dst
USING (SELECT :term_id AS term_id FROM dual) src
ON (dst.term_id = src.term_id)
WHEN MATCHED THEN UPDATE SET
    term_en = :term_en,
    term_kor_reading = :term_kor_reading,
    meaning_short = :meaning_short,
    meaning_field = :meaning_field,
    search_keywords = :search_keywords,
    updated_at = SYSDATE
WHEN NOT MATCHED THEN INSERT (
    term_id, term_en, term_kor_reading, meaning_short, meaning_field,
    search_keywords, created_at, updated_at
) VALUES (
    :term_id, :term_en, :term_kor_reading, :meaning_short, :meaning_field,
    :search_keywords, SYSDATE, SYSDATE
)
"""

DOWN_TYPE_MAP = {0: 'SCHEDULED', 1: 'UNSCHEDULED'}
STATUS_MAP = {0: 'IN_PROGRESS', 1: 'COMPLETED'}


def _clean(value: Any):
    """값 정리"""
    if value is None:
        return None
    if isinstance(value, float):
        if math.isnan(value):
            return None
        return value
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    if pd.isna(value):
        return None
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value


def _clean_number(value: Any):
    """숫자 값 정리"""
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        return float(value)
    return value


def load_reference_tables():
    """레퍼런스 테이블 데이터 적재"""
    logger.info("레퍼런스 테이블 데이터 적재 시작")
    
    for sheet_name, config in REFERENCE_TABLE_CONFIG.items():
        # 테이블 이름은 엑셀 시트 이름의 대문자 버전과 정확히 일치
        table = sheet_name.upper()
        columns = config['columns']
        
        try:
            df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
            df.columns = [str(col).strip().lower() for col in df.columns]
            df = df.where(pd.notnull(df), None)
            
            if df.empty:
                logger.warning(f"{sheet_name} 시트에 데이터가 없습니다.")
                continue
            
            logger.info(f"{sheet_name} 시트 {len(df)}건 적재 준비")
            
            col_placeholders = ', '.join(columns.values())
            bind_placeholders = ', '.join([f":{col}" for col in columns.values()])
            insert_sql = f"INSERT INTO {table} ({col_placeholders}) VALUES ({bind_placeholders})"
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"TRUNCATE TABLE {table}")
                
                records = []
                for _, row in df.iterrows():
                    record = {}
                    for source, target in columns.items():
                        record[target] = _clean(row.get(source))
                    records.append(record)
                
                cursor.executemany(insert_sql, records)
                logger.info(f"{table} 테이블 {len(records)}건 삽입 완료")
                cursor.close()
                
        except Exception as e:
            logger.error(f"{sheet_name} 시트 적재 실패: {e}", exc_info=True)
            raise


def load_term_dictionary(truncate: bool = False):
    """반도체 용어 사전 데이터 적재"""
    sheet_name = 'fab_terms_dictionary'
    # 테이블 이름은 엑셀 시트 이름의 대문자 버전과 정확히 일치
    table_name = sheet_name.upper()
    
    logger.info(f"{table_name} 데이터 적재 시작")
    
    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
    df.columns = [str(col).strip().lower() for col in df.columns]
    
    records = []
    for _, row in df.iterrows():
        term_en = _clean(row.get('term_en'))
        kor = _clean(row.get('term_kor_reading'))
        meaning_short = _clean(row.get('meaning_short'))
        meaning_field = _clean(row.get('meaning_field'))
        
        keywords = ' '.join(filter(None, [
            term_en.lower() if term_en else None,
            kor,
            meaning_short.lower() if meaning_short else None,
        ]))
        
        records.append({
            'term_id': _clean(row.get('term_id')),
            'term_en': term_en,
            'term_kor_reading': kor,
            'meaning_short': meaning_short,
            'meaning_field': meaning_field,
            'search_keywords': keywords[:600] if keywords else None,
        })
    
    logger.info(f"{sheet_name} 시트 {len(records)}건 로드 완료")
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        if truncate:
            cursor.execute(f"TRUNCATE TABLE {table_name}")
        
        merge_sql = get_term_dict_merge_sql(table_name)
        for idx, record in enumerate(records, 1):
            if not record['term_id']:
                logger.warning(f"{idx}번째 행: term_id 없음, 건너뜀")
                continue
            cursor.execute(merge_sql, record)
            if idx % 50 == 0:
                logger.info(f"{idx}건 처리")
        
        cursor.close()
    logger.info(f"{table_name} {len(records)}건 upsert 완료")


def _dedup_columns(columns):
    """중복 컬럼명 처리"""
    seen = {}
    result = []
    for col in columns:
        key = str(col).strip().lower()
        count = seen.get(key, 0) + 1
        seen[key] = count
        if count == 1:
            result.append(key)
        else:
            result.append(f"{key}_{count}")
    return result


def _normalize_times(start_raw, end_raw, label: str):
    """시간 정규화"""
    start = _clean(start_raw)
    end = _clean(end_raw)
    if start and end and end < start:
        logger.warning(f"{label}: end({end}) < start({start}), end를 start와 동일하게 조정")
        end = start
    return start, end


def load_inform_notes():
    """Inform Note 데이터 적재"""
    sheet_name = 'Inform_note'
    # 테이블 이름은 엑셀 시트 이름의 대문자 버전과 정확히 일치
    table_name = sheet_name.upper()
    
    logger.info(f"{table_name} 데이터 적재 시작")
    
    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
    df.columns = _dedup_columns(df.columns)
    df = df.where(pd.notnull(df), None)
    
    if df.empty:
        logger.warning(f"{sheet_name} 시트에 데이터가 없습니다.")
        return
    
    insert_sql = f"""
        INSERT INTO {table_name} (
            informnote_id, site_id, factory_id, line_id, process_id,
            eqp_id, model_id, down_start_time, down_end_time, down_time_minutes,
            down_type_id, error_code, act_prob_reason, act_content,
            act_start_time, act_end_time, operator, first_detector, status_id, link
        ) VALUES (
            :informnote_id, :site_id, :factory_id, :line_id, :process_id,
            :eqp_id, :model_id, :down_start_time, :down_end_time, :down_time_minutes,
            :down_type_id, :error_code, :act_prob_reason, :act_content,
            :act_start_time, :act_end_time, :operator, :first_detector, :status_id, :link
        )
    """
    
    records = []
    for idx, row in df.iterrows():
        down_start, down_end = _normalize_times(row.get('down_start_time'), row.get('down_end_time'), f"row {idx} down")
        act_start, act_end = _normalize_times(row.get('act_start_time'), row.get('act_end_time'), f"row {idx} act")
        
        # 엑셀의 ID 값을 그대로 사용 (매핑 제거)
        down_type_val = _clean_number(row.get('down_type_id'))
        status_val = _clean_number(row.get('status_id'))

        record = {
            'informnote_id': _clean(row.get('inform_note_id')),
            'site_id': _clean(row.get('site_id')),
            'factory_id': _clean(row.get('factory_id')),
            'line_id': _clean(row.get('line_id')),
            'process_id': _clean(row.get('process_id')),
            'eqp_id': _clean(row.get('eqp_id')),
            'model_id': _clean(row.get('model_id')),
            'down_start_time': down_start,
            'down_end_time': down_end,
            'down_time_minutes': _clean_number(row.get('down_time_minutes')),
            'down_type_id': int(down_type_val) if down_type_val is not None else None,
            'error_code': _clean(row.get('error_code')),
            'act_prob_reason': _clean(row.get('act_prob_reason')),
            'act_content': _clean(row.get('act_content')),
            'act_start_time': act_start,
            'act_end_time': act_end,
            'operator': _clean(row.get('operator')),
            'first_detector': _clean(row.get('first_detector')),
            'status_id': int(status_val) if status_val is not None else None,
            'link': f"https://gipms.com/reference/{idx + 1}",
        }
        records.append(record)
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"TRUNCATE TABLE {table_name}")
        cursor.executemany(insert_sql, records)
        logger.info(f"{table_name} {len(records)}건 삽입 완료")
        cursor.close()


def main():
    """메인 함수"""
    print("\n" + "=" * 80)
    print("모든 데이터 적재 스크립트")
    print("=" * 80)
    
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"엑셀 파일을 찾을 수 없습니다: {DATA_FILE}")
    
    if not db.test_connection():
        raise RuntimeError("Oracle DB 연결 실패")
    
    # 레퍼런스 테이블 데이터 적재
    print("\n[1/3] 레퍼런스 테이블 데이터 적재...")
    load_reference_tables()
    print("✓ 레퍼런스 테이블 데이터 적재 완료")
    
    # 용어 사전 데이터 적재
    print("\n[2/3] fab_terms_dictionary 데이터 적재...")
    load_term_dictionary(truncate=True)  # 자동 실행 시 항상 TRUNCATE
    print("✓ fab_terms_dictionary 데이터 적재 완료")
    
    # Inform Note 데이터 적재
    print("\n[3/3] Inform_note 데이터 적재...")
    load_inform_notes()
    print("✓ Inform_note 데이터 적재 완료")
    
    print("\n" + "=" * 80)
    print("✓ 모든 데이터 적재 완료")
    print("=" * 80)


if __name__ == '__main__':
    main()

