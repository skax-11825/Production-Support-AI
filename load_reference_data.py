#!/usr/bin/env python3
"""
normalized_data.xlsx → 레퍼런스 테이블 데이터 적재 스크립트
"""
from pathlib import Path
import logging
from typing import Dict, Any

import pandas as pd

from database import db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

DATA_FILE = Path(__file__).parent / 'normalized_data.xlsx'

TABLE_CONFIG = {
    'site': {
        'table': 'SITE',
        'columns': {
            'site_id': 'site_id',
            'site_name': 'site_name',
        },
    },
    'factory': {
        'table': 'FACTORY',
        'columns': {
            'factory_id': 'factory_id',
            'factory_name': 'factory_name',
            'site_id': 'site_id',
        },
    },
    'line': {
        'table': 'LINE',
        'columns': {
            'line_id': 'line_id',
            'line_name': 'line_name',
            'factory_id': 'factory_id',
        },
    },
    'process': {
        'table': 'PROCESS',
        'columns': {
            'process_id': 'process_id',
            'process_name': 'process_name',
            'process_abbr': 'process_abbr',
        },
    },
    'model': {
        'table': 'MODEL',
        'columns': {
            'model_id': 'model_id',
            'model_name': 'model_name',
            'process_id': 'process_id',
            'vendor': 'vendor',
        },
    },
    'equipment': {
        'table': 'EQUIPMENT',
        'columns': {
            'eqp_id': 'eqp_id',
            'eqp_name': 'eqp_name',
            'model_id': 'model_id',
            'line_id': 'line_id',
        },
    },
    'error_code': {
        'table': 'ERROR_CODE',
        'columns': {
            'error_code': 'error_code',
            'error_desc': 'error_desc',
            'process_id': 'process_id',
        },
    },
    'status': {
        'table': 'STATUS',
        'columns': {
            'status_id': 'status_id',
            'status': 'status_name',
        },
    },
    'down_type': {
        'table': 'DOWN_TYPE',
        'columns': {
            'down_type_id': 'down_type_id',
            'down_type': 'down_type_name',
        },
    },
}


def _clean_value(value: Any):
    if isinstance(value, float) and pd.isna(value):
        return None
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value


def load_sheet(sheet_name: str) -> pd.DataFrame:
    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
    df.columns = [str(col).strip().lower() for col in df.columns]
    df = df.where(pd.notnull(df), None)
    return df


def upsert_table(sheet_name: str, config: Dict[str, Any]):
    table = config['table']
    columns = config['columns']
    df = load_sheet(sheet_name)

    if not df.empty:
        logger.info(f"{sheet_name} 시트 {len(df)}건 적재 준비")
    else:
        logger.warning(f"{sheet_name} 시트에 데이터가 없습니다. 건너뜀")
        return

    col_placeholders = ', '.join(columns.values())
    bind_placeholders = ', '.join([f":{col}" for col in columns.values()])
    insert_sql = f"INSERT INTO {table} ({col_placeholders}) VALUES ({bind_placeholders})"

    with db.get_connection() as conn:
        cursor = conn.cursor()
        logger.info(f"{table} 테이블 TRUNCATE")
        cursor.execute(f"TRUNCATE TABLE {table}")

        records = []
        for _, row in df.iterrows():
            record = {}
            for source, target in columns.items():
                record[target] = _clean_value(row.get(source))
            records.append(record)

        cursor.executemany(insert_sql, records)
        logger.info(f"{table} 테이블 {len(records)}건 삽입 완료")
        cursor.close()


def main():
    print("\n" + "=" * 80)
    print("normalized_data.xlsx → 레퍼런스 테이블 데이터 적재")
    print("=" * 80)
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"엑셀 파일을 찾을 수 없습니다: {DATA_FILE}")

    if not db.test_connection():
        raise RuntimeError("Oracle DB 연결 실패")

    for sheet_name, config in TABLE_CONFIG.items():
        try:
            upsert_table(sheet_name, config)
        except Exception as exc:
            logger.error(f"{sheet_name} 시트 적재 실패: {exc}", exc_info=True)
            raise

    print("✓ 모든 레퍼런스 테이블 적재 완료")


if __name__ == '__main__':
    main()

