#!/usr/bin/env python3
"""
normalized_data.xlsx 기반 레퍼런스 테이블(사이트/공장/라인 등) 생성 스크립트
"""
import sys
import logging
from pathlib import Path

from database import db
from config import settings
from setup_informnote_table import read_sql_file, split_sql_statements

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

SQL_FILE = Path(__file__).parent / 'create_reference_tables.sql'


def execute_sql(drop_existing: bool = False) -> bool:
    if not db.test_connection():
        logger.error("데이터베이스 연결 실패")
        return False

    sql_content = read_sql_file(SQL_FILE)
    if not sql_content:
        return False

    statements = split_sql_statements(sql_content)
    logger.info(f"레퍼런스 테이블 DDL {len(statements)}건 실행 예정")

    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()

            if drop_existing:
                logger.info("기존 레퍼런스 테이블 삭제")
                for table in [
                    'DOWN_TYPE',
                    'STATUS',
                    'ERROR_CODE',
                    'EQUIPMENT',
                    'MODEL',
                    'PROCESS',
                    'LINE',
                    'FACTORY',
                    'SITE',
                ]:
                    try:
                        cursor.execute(f"DROP TABLE {table} CASCADE CONSTRAINTS")
                        logger.info(f" - {table} 삭제 완료")
                    except Exception as exc:
                        logger.warning(f" - {table} 삭제 실패 (없을 수 있음): {exc}")

            success = 0
            for idx, statement in enumerate(statements, 1):
                if not statement.strip():
                    continue
                cursor.execute(statement)
                success += 1
                logger.info(f"[{idx}/{len(statements)}] 실행 완료")

            logger.info(f"DDL 실행 성공 {success}건")
            cursor.close()
        return True
    except Exception as exc:
        logger.error(f"레퍼런스 테이블 생성 중 오류: {exc}", exc_info=True)
        return False


def main():
    if not SQL_FILE.exists():
        logger.error(f"SQL 파일을 찾을 수 없습니다: {SQL_FILE}")
        sys.exit(1)

    print("\n" + "=" * 80)
    print("normalized_data.xlsx → 레퍼런스 테이블 생성")
    print("=" * 80)
    print(f"데이터베이스: {settings.ORACLE_DSN}")
    print(f"사용자: {settings.ORACLE_USER}")
    print(f"SQL 파일: {SQL_FILE}")
    print("=" * 80)

    drop_existing = input("기존 레퍼런스 테이블을 삭제하고 재생성할까요? (y/N): ").strip().lower() == 'y'
    if drop_existing:
        confirm = input("정말 진행하려면 'yes'를 입력하세요: ").strip().lower()
        if confirm != 'yes':
            print("취소되었습니다.")
            sys.exit(0)

    if execute_sql(drop_existing=drop_existing):
        print("\n✓ 레퍼런스 테이블 생성 완료")
    else:
        print("\n✗ 레퍼런스 테이블 생성 실패")
        sys.exit(1)


if __name__ == '__main__':
    main()

