#!/usr/bin/env python3
"""
모든 테이블 생성 스크립트 통합
- 레퍼런스 테이블 (SITE, FACTORY, LINE 등)
- 반도체 용어 사전 (FAB_TERMS_DICTIONARY)
- Inform Note 테이블 (INFORM_NOTE)
"""
import sys
from pathlib import Path
import logging
from database import db
from config import settings
from utils import read_sql_file, split_sql_statements

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 테이블 설정
# 테이블 이름은 엑셀 시트 이름의 대문자 버전과 정확히 일치합니다
# 예: 'site' 시트 -> 'SITE' 테이블, 'fab_terms_dictionary' 시트 -> 'FAB_TERMS_DICTIONARY' 테이블
TABLE_CONFIGS = [
    {
        'name': '레퍼런스 테이블',
        'sql_file': 'create_reference_tables.sql',
        # 엑셀 시트 이름: site, factory, line, process, model, equipment, error_code, status, down_type
        'tables_to_drop': ['DOWN_TYPE', 'STATUS', 'ERROR_CODE', 'EQUIPMENT', 'MODEL', 'PROCESS', 'LINE', 'FACTORY', 'SITE'],
    },
    {
        'name': 'FAB_TERMS_DICTIONARY',
        'sql_file': 'create_semicon_term_dict.sql',
        # 엑셀 시트 이름: fab_terms_dictionary -> 테이블: FAB_TERMS_DICTIONARY
        'tables_to_drop': ['FAB_TERMS_DICTIONARY'],
    },
    {
        'name': 'INFORM_NOTE',
        'sql_file': 'create_informnote_table.sql',
        # 엑셀 시트 이름: Inform_note -> 테이블: INFORM_NOTE
        'tables_to_drop': ['INFORM_NOTE', 'INFORMNOTE_TABLE'],
    },
]


def execute_sql_file(sql_file: Path, drop_tables: list = None, drop_existing: bool = False) -> bool:
    """SQL 파일 실행"""
    if not sql_file.exists():
        logger.error(f"SQL 파일을 찾을 수 없습니다: {sql_file}")
        return False

    sql_content = read_sql_file(sql_file)
    if not sql_content:
        return False

    statements = split_sql_statements(sql_content)
    logger.info(f"SQL 문 {len(statements)}개 확인")

    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()

            # 기존 테이블 삭제
            if drop_existing and drop_tables:
                logger.info("기존 테이블 삭제 중...")
                for table_name in drop_tables:
                    try:
                        # VIEW 먼저 삭제 시도
                        try:
                            cursor.execute(f"DROP VIEW {table_name} CASCADE CONSTRAINTS")
                            logger.info(f"  - VIEW {table_name} 삭제 완료")
                        except Exception:
                            pass
                        # TABLE 삭제
                        cursor.execute(f"DROP TABLE {table_name} CASCADE CONSTRAINTS")
                        logger.info(f"  - TABLE {table_name} 삭제 완료")
                    except Exception as e:
                        logger.warning(f"  - {table_name} 삭제 실패 (없을 수 있음): {e}")

            # SQL 문 실행
            success_count = 0
            for idx, statement in enumerate(statements, 1):
                if not statement.strip():
                    continue
                try:
                    cursor.execute(statement)
                    success_count += 1
                    logger.info(f"[{idx}/{len(statements)}] 실행 완료")
                except Exception as e:
                    error_msg = str(e)
                    if 'already exists' in error_msg.lower() or 'name is already used' in error_msg.lower():
                        logger.warning(f"  ⚠ 객체가 이미 존재합니다")
                    else:
                        logger.error(f"  ✗ SQL 실행 실패: {error_msg[:200]}")
                        raise

            cursor.close()
            logger.info(f"✓ SQL 실행 완료: {success_count}개")
            return True

    except Exception as e:
        logger.error(f"테이블 생성 중 오류 발생: {e}", exc_info=True)
        return False


def main():
    """메인 함수"""
    print("\n" + "=" * 80)
    print("모든 테이블 생성 스크립트")
    print("=" * 80)
    print(f"데이터베이스: {settings.ORACLE_DSN}")
    print(f"사용자: {settings.ORACLE_USER}")
    print("=" * 80)

    if not db.test_connection():
        logger.error("데이터베이스 연결 실패")
        sys.exit(1)

    drop_existing = input("\n기존 테이블을 삭제하고 재생성할까요? (y/N): ").strip().lower() == 'y'
    if drop_existing:
        confirm = input("정말 진행하려면 'yes'를 입력하세요: ").strip().lower()
        if confirm != 'yes':
            print("취소되었습니다.")
            sys.exit(0)

    # 각 테이블 생성
    success_count = 0
    for config in TABLE_CONFIGS:
        print(f"\n[{config['name']}] 생성 중...")
        sql_file = Path(__file__).parent / config['sql_file']
        
        if execute_sql_file(sql_file, config['tables_to_drop'], drop_existing):
            logger.info(f"✓ {config['name']} 생성 완료")
            success_count += 1
        else:
            logger.error(f"✗ {config['name']} 생성 실패")
            sys.exit(1)

    print("\n" + "=" * 80)
    print(f"✓ 모든 테이블 생성 완료 ({success_count}/{len(TABLE_CONFIGS)})")
    print("=" * 80)


if __name__ == '__main__':
    main()

