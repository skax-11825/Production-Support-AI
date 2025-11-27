#!/usr/bin/env python3
"""
normalized_data.xlsx → FAB_TERMS_DICTIONARY 적재 스크립트
"""
from pathlib import Path
import logging
from typing import Dict, Any, List

import pandas as pd

from database import db

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DATA_FILE = Path(__file__).parent / 'normalized_data.xlsx'
SHEET_NAME = 'fab_terms_dictionary'
TABLE_NAME = 'FAB_TERMS_DICTIONARY'

MERGE_SQL = """
MERGE INTO FAB_TERMS_DICTIONARY dst
USING (
    SELECT :term_id AS term_id FROM dual
) src
ON (dst.term_id = src.term_id)
WHEN MATCHED THEN UPDATE SET
    term_en = :term_en,
    term_kor_reading = :term_kor_reading,
    meaning_short = :meaning_short,
    meaning_field = :meaning_field,
    search_keywords = :search_keywords,
    updated_at = SYSDATE
WHEN NOT MATCHED THEN INSERT (
    term_id,
    term_en,
    term_kor_reading,
    meaning_short,
    meaning_field,
    search_keywords,
    created_at,
    updated_at
) VALUES (
    :term_id,
    :term_en,
    :term_kor_reading,
    :meaning_short,
    :meaning_field,
    :search_keywords,
    SYSDATE,
    SYSDATE
)
"""


def _normalize_record(row: Dict[str, Any]) -> Dict[str, Any]:
    """엑셀 행을 DB 적재용 딕셔너리로 변환"""
    def _clean(value: Any) -> str:
        if value is None:
            return None
        value = str(value).strip()
        return value or None

    term_en = _clean(row.get('term_en'))
    kor = _clean(row.get('term_kor_reading'))
    meaning_short = _clean(row.get('meaning_short'))
    meaning_field = _clean(row.get('meaning_field'))

    keywords = ' '.join(
        filter(
            None,
            [
                term_en.lower() if term_en else None,
                kor,
                meaning_short.lower() if meaning_short else None,
            ],
        )
    )

    return {
        'term_id': _clean(row.get('term_id')),
        'term_en': term_en,
        'term_kor_reading': kor,
        'meaning_short': meaning_short,
        'meaning_field': meaning_field,
        'search_keywords': keywords[:600] if keywords else None,
    }


def load_dataframe() -> List[Dict[str, Any]]:
    """엑셀 파일을 읽어 레코드 목록으로 반환"""
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"엑셀 파일을 찾을 수 없습니다: {DATA_FILE}")

    df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)
    df.columns = [str(col).strip().lower() for col in df.columns]
    records = [_normalize_record(rec) for rec in df.to_dict(orient='records')]
    logger.info(f"{SHEET_NAME} 시트 {len(records)}건 로드 완료")
    return records


def upsert_terms(records: List[Dict[str, Any]], truncate: bool = False):
    """레코드를 DB에 적재"""
    if not db.test_connection():
        raise RuntimeError("Oracle DB 연결에 실패했습니다.")

    with db.get_connection() as conn:
        cursor = conn.cursor()
        if truncate:
            logger.info(f"{TABLE_NAME} 테이블 TRUNCATE")
            cursor.execute(f"TRUNCATE TABLE {TABLE_NAME}")

        for idx, record in enumerate(records, 1):
            if not record['term_id']:
                logger.warning(f"{idx}번째 행: term_id 없음, 건너뜀")
                continue
            cursor.execute(MERGE_SQL, record)
            if idx % 50 == 0:
                logger.info(f"{idx}건 처리")

        cursor.close()
    logger.info(f"{len(records)}건 upsert 완료")


def main():
    print("\n" + "=" * 80)
    print("FAB_TERMS_DICTIONARY 데이터 적재")
    print("=" * 80)
    truncate = input("적재 전 테이블을 비울까요? (y/N): ").strip().lower() == 'y'

    records = load_dataframe()
    upsert_terms(records, truncate=truncate)
    print("✓ 데이터 적재 완료")


if __name__ == '__main__':
    main()

