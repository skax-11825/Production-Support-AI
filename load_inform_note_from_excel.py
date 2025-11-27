#!/usr/bin/env python3
"""
normalized_data.xlsx → INFORM_NOTE 적재
"""
from pathlib import Path
import logging
from typing import Dict, Any
import math

import pandas as pd

from database import db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

DATA_FILE = Path(__file__).parent / 'normalized_data.xlsx'
SHEET_NAME = 'Inform_note'

DOWN_TYPE_MAP = {
    0: 'SCHEDULED',
    1: 'UNSCHEDULED',
}

STATUS_MAP = {
    0: 'IN_PROGRESS',
    1: 'COMPLETED',
}


def _clean(value: Any):
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


def _dedup_columns(columns):
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
    start = _clean(start_raw)
    end = _clean(end_raw)

    if start and end and end < start:
        logger.warning("%s: end(%s) < start(%s), end를 start와 동일하게 조정합니다.", label, end, start)
        end = start
    return start, end


def load_dataframe() -> pd.DataFrame:
    df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)
    df.columns = _dedup_columns(df.columns)
    df = df.where(pd.notnull(df), None)
    return df


def upsert_inform_notes(df: pd.DataFrame, truncate: bool = True):
    insert_sql = """
        INSERT INTO INFORM_NOTE (
            informnote_id, site_id, factory_id, line_id, process_id,
            eqp_id, model_id, down_start_time, down_end_time, down_time_minutes,
            down_type, error_code, act_prob_reason, act_content,
            act_start_time, act_end_time, operator, first_detector, status_id, link
        ) VALUES (
            :informnote_id, :site_id, :factory_id, :line_id, :process_id,
            :eqp_id, :model_id, :down_start_time, :down_end_time, :down_time_minutes,
            :down_type, :error_code, :act_prob_reason, :act_content,
            :act_start_time, :act_end_time, :operator, :first_detector, :status_id, :link
        )
    """

    records = []
    for idx, row in df.iterrows():
        down_start, down_end = _normalize_times(row.get('down_start_time'), row.get('down_end_time'), f"row {idx} down")
        act_start, act_end = _normalize_times(row.get('act_start_time'), row.get('act_end_time'), f"row {idx} act")
        link_value = f"https://gipms.com/reference/{idx + 1}"

        record: Dict[str, Any] = {
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
            'down_type': DOWN_TYPE_MAP.get(int(_clean_number(row.get('down_type_id')))) if _clean_number(row.get('down_type_id')) is not None else None,
            'error_code': _clean(row.get('error_code')),
            'act_prob_reason': _clean(row.get('act_prob_reason')),
            'act_content': _clean(row.get('act_content')),
            'act_start_time': act_start,
            'act_end_time': act_end,
            'operator': _clean(row.get('operator')),
            'first_detector': _clean(row.get('first_detector')),
            'status_id': STATUS_MAP.get(int(_clean_number(row.get('status_id')))) if _clean_number(row.get('status_id')) is not None else None,
            'link': link_value,
        }
        records.append(record)

    with db.get_connection() as conn:
        cursor = conn.cursor()
        if truncate:
            logger.info("INFORM_NOTE TRUNCATE")
            cursor.execute("TRUNCATE TABLE INFORM_NOTE")

        cursor.executemany(insert_sql, records)
        logger.info(f"INFORM_NOTE {len(records)}건 삽입 완료")
        cursor.close()


def main():
    print("\n" + "=" * 80)
    print("normalized_data.xlsx → INFORM_NOTE 적재")
    print("=" * 80)

    if not DATA_FILE.exists():
        raise FileNotFoundError(f"엑셀 파일을 찾을 수 없습니다: {DATA_FILE}")

    if not db.test_connection():
        raise RuntimeError("Oracle DB 연결 실패")

    df = load_dataframe()
    if df.empty:
        print("시트에 데이터가 없습니다.")
        return

    upsert_inform_notes(df)
    print("✓ INFORM_NOTE 적재 완료")


if __name__ == '__main__':
    main()

