#!/usr/bin/env python3
"""
Oracle DB 전체 재구성 및 데이터 적재 통합 스크립트
1. 기존 테이블 삭제 (외래키 제약조건 고려)
2. 새 스키마로 테이블 생성
3. 데이터 적재
"""
import sys
from pathlib import Path
import logging
from database import db
from config import settings
from utils import read_sql_file, split_sql_statements

# load_data.py의 함수들 import
from load_data import (
    load_reference_dependencies,
    load_reference_tables,
    load_term_dictionary,
    load_inform_notes,
    DATA_FILE
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 테이블 삭제 순서 (자식 테이블부터, 외래키 제약조건 고려)
# normalized_data_preprocessed.xlsx에는 site, factory, line 시트가 없으므로 제외
DROP_ORDER = [
    'INFORM_NOTE',           # 가장 많은 참조를 하는 테이블
    'EQUIPMENT',            # MODEL 참조 (LINE은 엑셀에 없음)
    'ERROR_CODE',           # PROCESS 참조
    'MODEL',                # PROCESS 참조
    'FAB_TERMS_DICTIONARY', # 독립적
    'PROCESS',              # 독립적
    'STATUS',               # 독립적
    'DOWN_TYPE',            # 독립적
]

# 테이블 생성 설정
TABLE_CONFIGS = [
    {
        'name': '레퍼런스 테이블',
        'sql_file': 'create_reference_tables.sql',
    },
    {
        'name': 'FAB_TERMS_DICTIONARY',
        'sql_file': 'create_semicon_term_dict.sql',
    },
    {
        'name': 'INFORM_NOTE',
        'sql_file': 'create_informnote_table.sql',
    },
]


def drop_all_tables():
    """모든 테이블 삭제 (외래키 제약조건 고려)"""
    logger.info("=" * 80)
    logger.info("기존 테이블 삭제 시작")
    logger.info("=" * 80)
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 외래키 제약조건 비활성화를 위해 먼저 모든 외래키 확인
            cursor.execute("""
                SELECT constraint_name, table_name
                FROM user_constraints
                WHERE constraint_type = 'R'
                ORDER BY table_name
            """)
            foreign_keys = cursor.fetchall()
            
            if foreign_keys:
                logger.info(f"외래키 제약조건 {len(foreign_keys)}개 발견")
                for fk_name, table_name in foreign_keys:
                    try:
                        cursor.execute(f"ALTER TABLE {table_name} DROP CONSTRAINT {fk_name}")
                        logger.debug(f"  - {table_name}.{fk_name} 제약조건 삭제")
                    except Exception as e:
                        logger.warning(f"  - {table_name}.{fk_name} 제약조건 삭제 실패: {e}")
            
            # 테이블 삭제 (순서 중요)
            dropped_count = 0
            for table_name in DROP_ORDER:
                try:
                    # VIEW 먼저 삭제 시도
                    try:
                        cursor.execute(f"DROP VIEW {table_name} CASCADE CONSTRAINTS")
                        logger.info(f"  ✓ VIEW {table_name} 삭제 완료")
                    except Exception:
                        pass
                    
                    # TABLE 삭제
                    cursor.execute(f"DROP TABLE {table_name} CASCADE CONSTRAINTS")
                    logger.info(f"  ✓ TABLE {table_name} 삭제 완료")
                    dropped_count += 1
                except Exception as e:
                    error_msg = str(e)
                    if 'does not exist' in error_msg.lower() or 'table or view does not exist' in error_msg.lower():
                        logger.debug(f"  - {table_name} 테이블 없음 (건너뜀)")
                    else:
                        logger.warning(f"  - {table_name} 삭제 실패: {error_msg[:100]}")
            
            # 시퀀스도 삭제 (있다면)
            cursor.execute("""
                SELECT sequence_name
                FROM user_sequences
            """)
            sequences = cursor.fetchall()
            for (seq_name,) in sequences:
                try:
                    cursor.execute(f"DROP SEQUENCE {seq_name}")
                    logger.info(f"  ✓ SEQUENCE {seq_name} 삭제 완료")
                except Exception as e:
                    logger.warning(f"  - {seq_name} 시퀀스 삭제 실패: {e}")
            
            cursor.close()
            logger.info(f"✓ 테이블 삭제 완료: {dropped_count}개")
            return True
            
    except Exception as e:
        logger.error(f"테이블 삭제 중 오류 발생: {e}", exc_info=True)
        return False


def create_all_tables():
    """모든 테이블 생성"""
    logger.info("=" * 80)
    logger.info("새 테이블 생성 시작")
    logger.info("=" * 80)
    
    success_count = 0
    for config in TABLE_CONFIGS:
        logger.info(f"\n[{config['name']}] 생성 중...")
        sql_file = Path(__file__).parent / config['sql_file']
        
        if not sql_file.exists():
            logger.error(f"SQL 파일을 찾을 수 없습니다: {sql_file}")
            return False
        
        sql_content = read_sql_file(sql_file)
        if not sql_content:
            logger.error(f"SQL 파일 읽기 실패: {sql_file}")
            return False
        
        statements = split_sql_statements(sql_content)
        logger.info(f"SQL 문 {len(statements)}개 확인")
        
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                success = 0
                for idx, statement in enumerate(statements, 1):
                    if not statement.strip():
                        continue
                    try:
                        # PL/SQL 블록(TRIGGER 등)은 그대로 실행
                        # 일반 SQL도 execute()로 실행
                        cursor.execute(statement)
                        success += 1
                        if idx <= 3 or idx % 10 == 0:  # 처음 3개와 10개마다 로그
                            logger.info(f"  [{idx}/{len(statements)}] 실행 완료")
                    except Exception as e:
                        error_msg = str(e)
                        error_upper = error_msg.upper()
                        # 이미 존재하는 객체는 경고만 출력하고 계속 진행
                        if any(keyword in error_upper for keyword in ['ALREADY EXISTS', 'NAME IS ALREADY USED', 'ORA-00955', 'ORA-00942']):
                            logger.warning(f"  ⚠ [{idx}/{len(statements)}] 객체가 이미 존재하거나 없음: {error_msg[:100]}")
                            success += 1  # 경고지만 성공으로 카운트
                        else:
                            logger.error(f"  ✗ [{idx}/{len(statements)}] SQL 실행 실패")
                            logger.error(f"     SQL 미리보기: {statement[:150]}...")
                            logger.error(f"     오류: {error_msg[:400]}")
                            raise
                
                cursor.close()
                logger.info(f"✓ {config['name']} 생성 완료: {success}개 SQL 실행")
                success_count += 1
                
        except Exception as e:
            logger.error(f"{config['name']} 생성 중 오류 발생: {e}", exc_info=True)
            return False
    
    logger.info(f"\n✓ 모든 테이블 생성 완료 ({success_count}/{len(TABLE_CONFIGS)})")
    return True


def verify_tables():
    """생성된 테이블 확인"""
    logger.info("=" * 80)
    logger.info("생성된 테이블 확인")
    logger.info("=" * 80)
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 모든 테이블 조회
            cursor.execute("""
                SELECT table_name, num_rows
                FROM user_tables
                ORDER BY table_name
            """)
            tables = cursor.fetchall()
            
            if tables:
                logger.info(f"\n생성된 테이블 ({len(tables)}개):")
                for table_name, num_rows in tables:
                    logger.info(f"  - {table_name}: {num_rows if num_rows else 0}행")
            else:
                logger.warning("생성된 테이블이 없습니다.")
            
            cursor.close()
            return True
            
    except Exception as e:
        logger.error(f"테이블 확인 중 오류 발생: {e}", exc_info=True)
        return False


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Oracle DB 전체 재구성 및 데이터 적재')
    parser.add_argument('--yes', '-y', action='store_true', help='확인 없이 자동 실행')
    args = parser.parse_args()
    
    print("\n" + "=" * 80)
    print("Oracle DB 전체 재구성 및 데이터 적재")
    print("=" * 80)
    print(f"데이터베이스: {settings.ORACLE_DSN}")
    print(f"사용자: {settings.ORACLE_USER}")
    print("=" * 80)
    print("\n⚠ 경고: 이 작업은 모든 기존 테이블과 데이터를 삭제합니다!")
    print("\n작업 순서:")
    print("  1. 기존 테이블 삭제")
    print("  2. 새 스키마로 테이블 생성")
    print("  3. 테이블 확인")
    print("  4. 데이터 적재 (참조 테이블: SITE, FACTORY, LINE)")
    print("  5. 데이터 적재 (레퍼런스 테이블)")
    print("  6. 데이터 적재 (용어 사전)")
    print("  7. 데이터 적재 (Inform Note)")
    print("=" * 80)
    
    if not args.yes:
        try:
            confirm = input("\n정말 진행하시겠습니까? (yes 입력): ").strip().lower()
            if confirm != 'yes':
                print("취소되었습니다.")
                sys.exit(0)
        except (EOFError, KeyboardInterrupt):
            print("\n입력이 중단되었습니다. --yes 플래그를 사용하여 자동 실행하세요.")
            sys.exit(1)
    else:
        print("\n[--yes 플래그 사용] 확인 없이 자동 실행합니다...")
    
    # DB 연결 확인
    if not db.test_connection():
        logger.error("데이터베이스 연결 실패")
        sys.exit(1)
    
    # 엑셀 파일 확인
    if not DATA_FILE.exists():
        logger.error(f"엑셀 파일을 찾을 수 없습니다: {DATA_FILE}")
        sys.exit(1)
    
    # 1단계: 기존 테이블 삭제
    print("\n[1/7] 기존 테이블 삭제 중...")
    if not drop_all_tables():
        logger.error("테이블 삭제 실패")
        sys.exit(1)
    print("✓ 기존 테이블 삭제 완료")
    
    # 2단계: 새 테이블 생성
    print("\n[2/7] 새 테이블 생성 중...")
    if not create_all_tables():
        logger.error("테이블 생성 실패")
        sys.exit(1)
    print("✓ 새 테이블 생성 완료")
    
    # 3단계: 테이블 확인
    print("\n[3/7] 생성된 테이블 확인 중...")
    if not verify_tables():
        logger.error("테이블 확인 실패")
        sys.exit(1)
    print("✓ 테이블 확인 완료")
    
    # 4단계: 참조 테이블 (SITE, FACTORY, LINE) 데이터 적재
    print("\n[4/7] 참조 테이블 (SITE, FACTORY, LINE) 데이터 적재 중...")
    try:
        load_reference_dependencies()
        print("✓ 참조 테이블 데이터 적재 완료")
    except Exception as e:
        logger.error(f"참조 테이블 데이터 적재 실패: {e}", exc_info=True)
        sys.exit(1)
    
    # 5단계: 레퍼런스 테이블 데이터 적재
    print("\n[5/7] 레퍼런스 테이블 데이터 적재 중...")
    try:
        load_reference_tables()
        print("✓ 레퍼런스 테이블 데이터 적재 완료")
    except Exception as e:
        logger.error(f"레퍼런스 테이블 데이터 적재 실패: {e}", exc_info=True)
        sys.exit(1)
    
    # 6단계: 용어 사전 데이터 적재
    print("\n[6/7] fab_terms_dictionary 데이터 적재 중...")
    try:
        load_term_dictionary(truncate=True)
        print("✓ fab_terms_dictionary 데이터 적재 완료")
    except Exception as e:
        logger.error(f"용어 사전 데이터 적재 실패: {e}", exc_info=True)
        sys.exit(1)
    
    # 7단계: Inform Note 데이터 적재
    print("\n[7/7] Inform_note 데이터 적재 중...")
    try:
        load_inform_notes()
        print("✓ Inform_note 데이터 적재 완료")
    except Exception as e:
        logger.error(f"Inform Note 데이터 적재 실패: {e}", exc_info=True)
        sys.exit(1)
    
    # 최종 확인
    print("\n" + "=" * 80)
    print("✓ DB 재구성 및 데이터 적재 완료!")
    print("=" * 80)
    verify_tables()
    print("=" * 80)


if __name__ == '__main__':
    main()

