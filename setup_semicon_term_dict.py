#!/usr/bin/env python3
"""
FAB_TERMS_DICTIONARY 테이블 생성 스크립트
normalized_data.xlsx 기반 용어 사전 테이블을 Oracle DB에 생성합니다.
"""
import sys
from pathlib import Path
import logging

from database import db
from config import settings
from setup_informnote_table import read_sql_file, split_sql_statements

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

TABLE_NAME = 'FAB_TERMS_DICTIONARY'
SQL_FILE = Path(__file__).parent / 'create_semicon_term_dict.sql'


def execute_sql(drop_existing: bool = False) -> bool:
    """DDL 스크립트를 실행해 용어 사전 테이블을 생성한다."""
    if not db.test_connection():
        logger.error("데이터베이스 연결 실패")
        return False

    sql_content = read_sql_file(SQL_FILE)
    if not sql_content:
        return False

    statements = split_sql_statements(sql_content)
    logger.info(f"{TABLE_NAME} 생성용 SQL 문 {len(statements)}개 발견")

    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()

            if drop_existing:
                logger.info(f"{TABLE_NAME} 기존 객체 삭제 시도")
                try:
                    cursor.execute(f"DROP VIEW {TABLE_NAME}")
                    logger.info("기존 뷰 삭제 완료")
                except Exception:
                    logger.debug("삭제할 기존 뷰가 없거나 이미 삭제됨")
                try:
                    cursor.execute(f"DROP TABLE {TABLE_NAME} CASCADE CONSTRAINTS")
                    logger.info("기존 테이블 삭제 완료")
                except Exception as exc:
                    logger.warning(f"기존 테이블 삭제 실패(없을 수 있음): {exc}")

            success = 0
            for idx, statement in enumerate(statements, 1):
                if not statement.strip():
                    continue

                try:
                    logger.info(f"[{idx}/{len(statements)}] SQL 실행")
                    cursor.execute(statement)
                    success += 1
                except Exception as exc:
                    logger.error(f"SQL 실행 실패: {exc}")
                    raise

            logger.info(f"{TABLE_NAME} 생성 SQL 실행 완료 (성공 {success}건)")

            cursor.execute(
                """
                SELECT column_name, data_type, data_length
                FROM user_tab_columns
                WHERE table_name = :table_name
                ORDER BY column_id
                """,
                {'table_name': TABLE_NAME}
            )
            columns = cursor.fetchall()
            if columns:
                logger.info(f"{TABLE_NAME} 컬럼 {len(columns)}개 확인")
                for name, data_type, length in columns:
                    logger.info(f" - {name}: {data_type}({length})")

            cursor.close()
        return True
    except Exception as exc:
        logger.error(f"{TABLE_NAME} 생성 중 오류: {exc}", exc_info=True)
        return False


def main():
    if not SQL_FILE.exists():
        logger.error(f"SQL 파일을 찾을 수 없습니다: {SQL_FILE}")
        sys.exit(1)

    print("\n" + "=" * 80)
    print("FAB_TERMS_DICTIONARY 용어 사전 테이블 생성")
    print("=" * 80)
    print(f"데이터베이스: {settings.ORACLE_DSN}")
    print(f"사용자: {settings.ORACLE_USER}")
    print(f"SQL 파일: {SQL_FILE}")
    print("=" * 80)

    drop_existing = input("기존 테이블을 삭제하고 재생성할까요? (y/N): ").strip().lower() == 'y'
    if drop_existing:
        confirm = input("정말 진행하려면 'yes'를 입력하세요: ").strip().lower()
        if confirm != 'yes':
            print("취소되었습니다.")
            sys.exit(0)

    if execute_sql(drop_existing=drop_existing):
        print("\n✓ FAB_TERMS_DICTIONARY 생성 완료")
    else:
        print("\n✗ 테이블 생성 실패")
        sys.exit(1)


if __name__ == '__main__':
    main()

