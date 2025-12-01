#!/usr/bin/env python3
"""
모든 데이터 적재 스크립트 통합
- 레퍼런스 테이블 데이터
- 반도체 용어 사전 데이터
- Inform Note 데이터

중요: 엑셀 파일의 시트명과 컬럼명을 토시 하나 바꾸지 않고 그대로 사용합니다.
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

DATA_FILE = Path(__file__).parent / 'normalized_data_preprocessed.xlsx'

# 레퍼런스 테이블 설정
# 테이블 이름은 엑셀 시트 이름을 대문자로 변환한 것과 정확히 일치합니다
# 컬럼 매핑: {엑셀_컬럼명: DB_컬럼명}
# 엑셀 컬럼명은 정확히 그대로 사용 (공백 포함)
REFERENCE_TABLE_CONFIG = {
    'process': {
        'table': 'PROCESS',
        'columns': {
            'process_id': 'PROCESS_ID',
            'process_name': 'PROCESS_NAME',
            'process_abbr': 'PROCESS_ABBR'
        }
    },
    'model': {
        'table': 'MODEL',
        'columns': {
            'model_id': 'MODEL_ID',
            'model_name': 'MODEL_NAME',
            'process_id': 'PROCESS_ID',
            'vendor': 'VENDOR'
        }
    },
    'equipment': {
        'table': 'EQUIPMENT',
        'columns': {
            'eqp_id': 'EQP_ID',
            'eqp_name': 'EQP_NAME',
            'model_id': 'MODEL_ID',
            'line_id': 'LINE_ID'
        }
    },
    'error_code': {
        'table': 'ERROR_CODE',
        'columns': {
            'error_code': 'ERROR_CODE',
            'error_desc': 'ERROR_DESC',
            'process_id': 'PROCESS_ID'
        }
    },
    'status': {
        'table': 'STATUS',
        'columns': {
            'status_id': 'STATUS_ID',
            'status': 'STATUS_NAME'  # 엑셀의 'status' 컬럼 -> DB의 'STATUS_NAME' 컬럼
        }
    },
    'down_type': {
        'table': 'DOWN_TYPE',
        'columns': {
            'down_type_id': 'DOWN_TYPE_ID',
            'down_type': 'DOWN_TYPE_NAME'  # 엑셀의 'down_type' 컬럼 -> DB의 'DOWN_TYPE_NAME' 컬럼
        }
    },
}

# 용어 사전 MERGE SQL (테이블 이름은 동적으로 생성)
def get_term_dict_merge_sql(table_name: str) -> str:
    """용어 사전 MERGE SQL 생성 (테이블 이름 동적) - term_id 기준"""
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
        try:
            return float(value)
        except ValueError:
            return None
    return value


def load_reference_tables():
    """레퍼런스 테이블 데이터 적재"""
    logger.info("=" * 80)
    logger.info("레퍼런스 테이블 데이터 적재 시작")
    logger.info("=" * 80)
    
    for sheet_name, config in REFERENCE_TABLE_CONFIG.items():
        table_name = config['table']
        columns_map = config['columns']
        
        try:
            # 엑셀 시트 읽기 (컬럼명은 그대로 유지)
            df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
            
            # 컬럼명 정확히 확인 및 매핑
            # 엑셀 컬럼명을 소문자로 정규화하여 매핑 (공백 제거)
            df.columns = [str(col).strip() for col in df.columns]
            
            # 빈 행 제거
            df = df.dropna(how='all')
            
            if df.empty:
                logger.warning(f"{sheet_name} 시트에 데이터가 없습니다.")
                continue
            
            logger.info(f"\n[{sheet_name} 시트 -> {table_name} 테이블]")
            logger.info(f"  데이터 행 수: {len(df)}")
            logger.info(f"  엑셀 컬럼: {list(df.columns)}")
            
            # 매핑 검증
            excel_cols_lower = {col.lower(): col for col in df.columns}
            missing_cols = []
            for excel_col_key in columns_map.keys():
                if excel_col_key.lower() not in excel_cols_lower:
                    missing_cols.append(excel_col_key)
            
            if missing_cols:
                logger.error(f"  ✗ 필수 컬럼이 없습니다: {missing_cols}")
                raise ValueError(f"{sheet_name} 시트에 필수 컬럼이 없습니다: {missing_cols}")
            
            # INSERT SQL 생성
            db_columns = list(columns_map.values())
            col_placeholders = ', '.join(db_columns)
            bind_placeholders = ', '.join([f":{col}" for col in db_columns])
            insert_sql = f"INSERT INTO {table_name} ({col_placeholders}) VALUES ({bind_placeholders})"
            
            # 데이터 준비
            records = []
            for idx, row in df.iterrows():
                record = {}
                for excel_col, db_col in columns_map.items():
                    # 엑셀 컬럼명을 소문자로 정규화하여 찾기
                    excel_col_normalized = excel_col.lower()
                    if excel_col_normalized in excel_cols_lower:
                        actual_excel_col = excel_cols_lower[excel_col_normalized]
                        value = row.get(actual_excel_col)
                        record[db_col] = _clean(value)
                    else:
                        logger.warning(f"  행 {idx+2}: 컬럼 '{excel_col}'를 찾을 수 없습니다.")
                        record[db_col] = None
                
                records.append(record)
            
            logger.info(f"  준비된 레코드: {len(records)}개")
            
            # 데이터베이스에 삽입
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"TRUNCATE TABLE {table_name}")
                logger.info(f"  ✓ {table_name} 테이블 TRUNCATE 완료")
                
                cursor.executemany(insert_sql, records)
                logger.info(f"  ✓ {table_name} 테이블 {len(records)}건 삽입 완료")
                
                # 검증: 삽입된 행 수 확인
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                inserted_count = cursor.fetchone()[0]
                logger.info(f"  ✓ 검증: {table_name} 테이블에 {inserted_count}건 확인")
                
                if inserted_count != len(records):
                    logger.warning(f"  ⚠ 경고: 삽입된 행 수({inserted_count})와 준비된 행 수({len(records)})가 다릅니다.")
                
                cursor.close()
                
        except Exception as e:
            logger.error(f"✗ {sheet_name} 시트 적재 실패: {e}", exc_info=True)
            raise


def load_term_dictionary(truncate: bool = False):
    """반도체 용어 사전 데이터 적재"""
    sheet_name = 'fab_terms_dictionary'
    table_name = 'FAB_TERMS_DICTIONARY'
    
    logger.info("=" * 80)
    logger.info(f"{table_name} 데이터 적재 시작")
    logger.info("=" * 80)
    
    try:
        # 엑셀 시트 읽기
        df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
        
        # 컬럼명 정확히 확인 (공백 포함)
        # 'meaning_short ' 뒤에 공백이 있을 수 있으므로 strip()을 사용하되, 매핑은 명확히
        df.columns = [str(col).strip() for col in df.columns]
        
        # 빈 행 제거
        df = df.dropna(how='all')
        
        logger.info(f"\n[{sheet_name} 시트 -> {table_name} 테이블]")
        logger.info(f"  데이터 행 수: {len(df)}")
        logger.info(f"  엑셀 컬럼: {list(df.columns)}")
        
        # 필수 컬럼 확인
        required_cols = ['term_id', 'term_en', 'term_kor_reading', 'meaning_short', 'meaning_field']
        excel_cols_lower = {col.lower(): col for col in df.columns}
        
        missing_cols = [col for col in required_cols if col.lower() not in excel_cols_lower]
        if missing_cols:
            logger.error(f"  ✗ 필수 컬럼이 없습니다: {missing_cols}")
            raise ValueError(f"{sheet_name} 시트에 필수 컬럼이 없습니다: {missing_cols}")
        
        # 데이터 준비
        records = []
        for idx, row in df.iterrows():
            # 엑셀 컬럼명에서 실제 컬럼 찾기 (소문자 정규화)
            term_id = _clean(row.get(excel_cols_lower.get('term_id', 'term_id')))
            term_en = _clean(row.get(excel_cols_lower.get('term_en', 'term_en')))
            term_kor_reading = _clean(row.get(excel_cols_lower.get('term_kor_reading', 'term_kor_reading')))
            meaning_short = _clean(row.get(excel_cols_lower.get('meaning_short', 'meaning_short')))
            meaning_field = _clean(row.get(excel_cols_lower.get('meaning_field', 'meaning_field')))
            
            # 필수 필드 검증
            if not term_id:
                logger.warning(f"  행 {idx+2}: term_id 없음, 건너뜀")
                continue
            if not term_en:
                logger.warning(f"  행 {idx+2}: term_en 없음, 건너뜀")
                continue
            
            # 검색 키워드 생성
            keywords = ' '.join(filter(None, [
                term_en.lower() if term_en else None,
                term_kor_reading,
                meaning_short.lower() if meaning_short else None,
            ]))
            
            records.append({
                'term_id': term_id,
                'term_en': term_en,
                'term_kor_reading': term_kor_reading,
                'meaning_short': meaning_short,
                'meaning_field': meaning_field,
                'search_keywords': keywords[:600] if keywords else None,
            })
        
        logger.info(f"  준비된 레코드: {len(records)}개")
        
        # 데이터베이스에 MERGE
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 트리거 비활성화 (데이터 적재 중 오류 방지)
            try:
                cursor.execute(f"ALTER TRIGGER TRG_FAB_TERMS_DICTIONARY_UPD DISABLE")
                logger.debug("  트리거 비활성화 완료")
            except Exception as e:
                logger.debug(f"  트리거 비활성화 실패 (무시): {e}")
            
            if truncate:
                cursor.execute(f"TRUNCATE TABLE {table_name}")
                logger.info(f"  ✓ {table_name} 테이블 TRUNCATE 완료")
            
            merge_sql = get_term_dict_merge_sql(table_name)
            
            success_count = 0
            for idx, record in enumerate(records, 1):
                try:
                    cursor.execute(merge_sql, record)
                    success_count += 1
                except Exception as e:
                    error_msg = str(e)
                    # 중복된 term_en이 있는 경우, term_en 기준으로 DELETE 후 INSERT
                    if 'unique constraint' in error_msg.lower() and 'term_en' in error_msg.lower():
                        try:
                            cursor.execute(f"DELETE FROM {table_name} WHERE term_en = :term_en", {'term_en': record['term_en']})
                            cursor.execute(merge_sql, record)
                            success_count += 1
                            logger.debug(f"  행 {idx+1}: term_en 중복으로 기존 레코드 삭제 후 재삽입")
                        except Exception as e2:
                            logger.warning(f"  행 {idx+1} 처리 실패 (중복 처리 시도 후 실패): {e2}")
                    else:
                        logger.warning(f"  행 {idx+1} 처리 실패: {error_msg[:100]}")
                
                if idx % 50 == 0:
                    logger.info(f"  {idx}건 처리 중...")
            
            # 트리거 재활성화
            try:
                cursor.execute(f"ALTER TRIGGER TRG_FAB_TERMS_DICTIONARY_UPD ENABLE")
                logger.debug("  트리거 재활성화 완료")
            except Exception as e:
                logger.warning(f"  트리거 재활성화 실패: {e}")
                # 트리거가 유효하지 않으면 삭제하고 재생성
                try:
                    cursor.execute(f"DROP TRIGGER TRG_FAB_TERMS_DICTIONARY_UPD")
                    logger.info("  유효하지 않은 트리거 삭제 완료")
                    # 트리거 재생성
                    trigger_sql = """
                    CREATE OR REPLACE TRIGGER TRG_FAB_TERMS_DICTIONARY_UPD
                    BEFORE UPDATE ON FAB_TERMS_DICTIONARY
                    FOR EACH ROW
                    BEGIN
                        :NEW.UPDATED_AT := SYSDATE;
                    END;
                    """
                    cursor.execute(trigger_sql)
                    logger.info("  트리거 재생성 완료")
                except Exception as e2:
                    logger.warning(f"  트리거 재생성 실패: {e2}")
            
            # 검증: 삽입된 행 수 확인
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            inserted_count = cursor.fetchone()[0]
            logger.info(f"  ✓ 검증: {table_name} 테이블에 {inserted_count}건 확인")
            
            cursor.close()
        
        logger.info(f"✓ {table_name} {success_count}건 upsert 완료")
        
    except Exception as e:
        logger.error(f"✗ {table_name} 데이터 적재 실패: {e}", exc_info=True)
        raise


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
    sheet_name = 'inform_note'
    table_name = 'INFORM_NOTE'
    
    logger.info("=" * 80)
    logger.info(f"{table_name} 데이터 적재 시작")
    logger.info("=" * 80)
    
    try:
        # 엑셀 시트 읽기
        df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
        
        # 중복 컬럼명 처리
        df.columns = _dedup_columns(df.columns)
        
        # 빈 행 제거
        df = df.dropna(how='all')
        
        logger.info(f"\n[{sheet_name} 시트 -> {table_name} 테이블]")
        logger.info(f"  데이터 행 수: {len(df)}")
        logger.info(f"  엑셀 컬럼: {list(df.columns)}")
        
        # 컬럼 매핑: 엑셀 컬럼명 -> DB 컬럼명
        column_mapping = {
            'inform_note_id': 'INFORMNOTE_ID',  # 언더스코어 제거
            'site_id': 'SITE_ID',
            'factory_id': 'FACTORY_ID',
            'line_id': 'LINE_ID',
            'process_id': 'PROCESS_ID',
            'eqp_id': 'EQP_ID',
            'model_id': 'MODEL_ID',
            'down_start_time': 'DOWN_START_TIME',
            'down_end_time': 'DOWN_END_TIME',
            'down_time_minutes': 'DOWN_TIME_MINUTES',
            'down_type_id': 'DOWN_TYPE_ID',
            'error_code': 'ERROR_CODE',
            'act_prob_reason': 'ACT_PROB_REASON',
            'act_content': 'ACT_CONTENT',
            'act_start_time': 'ACT_START_TIME',
            'act_end_time': 'ACT_END_TIME',
            'operator': 'OPERATOR',
            'first_detector': 'FIRST_DETECTOR',
            'status_id': 'STATUS_ID',
        }
        
        # INSERT SQL 생성
        db_columns = list(column_mapping.values()) + ['LINK']  # LINK는 생성
        col_placeholders = ', '.join(db_columns)
        bind_placeholders = ', '.join([f":{col}" for col in db_columns])
        insert_sql = f"""
            INSERT INTO {table_name} ({col_placeholders}) 
            VALUES ({bind_placeholders})
        """
        
        # 데이터 준비
        records = []
        excel_cols_lower = {col.lower(): col for col in df.columns}
        
        for idx, row in df.iterrows():
            # 시간 정규화
            down_start, down_end = _normalize_times(
                row.get(excel_cols_lower.get('down_start_time', 'down_start_time')),
                row.get(excel_cols_lower.get('down_end_time', 'down_end_time')),
                f"행 {idx+2} down"
            )
            act_start, act_end = _normalize_times(
                row.get(excel_cols_lower.get('act_start_time', 'act_start_time')),
                row.get(excel_cols_lower.get('act_end_time', 'act_end_time')),
                f"행 {idx+2} act"
            )
            
            # 숫자 값 정리
            down_type_val = _clean_number(row.get(excel_cols_lower.get('down_type_id', 'down_type_id')))
            status_val = _clean_number(row.get(excel_cols_lower.get('status_id', 'status_id')))
            
            record = {
                'INFORMNOTE_ID': _clean(row.get(excel_cols_lower.get('inform_note_id', 'inform_note_id'))),
                'SITE_ID': _clean(row.get(excel_cols_lower.get('site_id', 'site_id'))),
                'FACTORY_ID': _clean(row.get(excel_cols_lower.get('factory_id', 'factory_id'))),
                'LINE_ID': _clean(row.get(excel_cols_lower.get('line_id', 'line_id'))),
                'PROCESS_ID': _clean(row.get(excel_cols_lower.get('process_id', 'process_id'))),
                'EQP_ID': _clean(row.get(excel_cols_lower.get('eqp_id', 'eqp_id'))),
                'MODEL_ID': _clean(row.get(excel_cols_lower.get('model_id', 'model_id'))),
                'DOWN_START_TIME': down_start,
                'DOWN_END_TIME': down_end,
                'DOWN_TIME_MINUTES': _clean_number(row.get(excel_cols_lower.get('down_time_minutes', 'down_time_minutes'))),
                'DOWN_TYPE_ID': int(down_type_val) if down_type_val is not None else None,
                'ERROR_CODE': _clean(row.get(excel_cols_lower.get('error_code', 'error_code'))),
                'ACT_PROB_REASON': _clean(row.get(excel_cols_lower.get('act_prob_reason', 'act_prob_reason'))),
                'ACT_CONTENT': _clean(row.get(excel_cols_lower.get('act_content', 'act_content'))),
                'ACT_START_TIME': act_start,
                'ACT_END_TIME': act_end,
                'OPERATOR': _clean(row.get(excel_cols_lower.get('operator', 'operator'))),
                'FIRST_DETECTOR': _clean(row.get(excel_cols_lower.get('first_detector', 'first_detector'))),
                'STATUS_ID': int(status_val) if status_val is not None else None,
                'LINK': f"https://gipms.com/reference/{idx + 1}",
            }
            
            # 필수 필드 검증
            if not record['INFORMNOTE_ID']:
                logger.warning(f"  행 {idx+2}: inform_note_id 없음, 건너뜀")
                continue
            
            records.append(record)
        
        logger.info(f"  준비된 레코드: {len(records)}개")
        
        # 데이터베이스에 삽입
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"TRUNCATE TABLE {table_name}")
            logger.info(f"  ✓ {table_name} 테이블 TRUNCATE 완료")
            
            cursor.executemany(insert_sql, records)
            logger.info(f"  ✓ {table_name} 테이블 {len(records)}건 삽입 완료")
            
            # 검증: 삽입된 행 수 확인
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            inserted_count = cursor.fetchone()[0]
            logger.info(f"  ✓ 검증: {table_name} 테이블에 {inserted_count}건 확인")
            
            if inserted_count != len(records):
                logger.warning(f"  ⚠ 경고: 삽입된 행 수({inserted_count})와 준비된 행 수({len(records)})가 다릅니다.")
            
            cursor.close()
        
    except Exception as e:
        logger.error(f"✗ {table_name} 데이터 적재 실패: {e}", exc_info=True)
        raise


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
    load_term_dictionary(truncate=True)
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
