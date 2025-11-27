#!/usr/bin/env python3
"""
Inform Note Agent - 반도체 공정 다운타임 관리 테이블 생성 스크립트
Oracle DB에 테이블을 생성하고 설정합니다.
"""
import sys
import os
from pathlib import Path
from database import db
from config import settings
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def read_sql_file(file_path):
    """SQL 파일 읽기"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        logger.error(f"SQL 파일 읽기 실패: {e}")
        return None


def split_sql_statements(sql_content):
    """SQL 문을 개별 명령어로 분리"""
    # 주석 제거 및 SQL 문 분리
    statements = []
    current_statement = []
    
    inside_plsql = False
    for line in sql_content.split('\n'):
        line = line.strip()
        
        # 빈 줄이나 주석만 있는 줄 건너뛰기
        if not line or line.startswith('--'):
            continue
        
        # 주석 제거 (라인 내 주석)
        if '--' in line:
            line = line[:line.index('--')].strip()
        upper_line = line.upper()

        if upper_line.startswith('CREATE OR REPLACE TRIGGER') or upper_line.startswith('CREATE TRIGGER'):
            inside_plsql = True
        
        if line:
            current_statement.append(line)
            
            # PL/SQL 블록은 END; 까지 하나의 문장으로 취급
            if inside_plsql:
                if upper_line.startswith('END'):
                    statement = ' '.join(current_statement)
                    statement = statement.rstrip(';').rstrip('/').strip()
                    if statement:
                        statements.append(statement)
                    current_statement = []
                    inside_plsql = False
                continue
            
            # 일반 SQL 문장의 종료 여부 확인
            if line.endswith(';') or line.endswith('/'):
                statement = ' '.join(current_statement)
                statement = statement.rstrip(';').rstrip('/').strip()
                if statement:
                    statements.append(statement)
                current_statement = []
    
    # 마지막 문장 처리
    if current_statement:
        statement = ' '.join(current_statement).strip()
        if statement:
            statements.append(statement)
    
    return statements


def execute_sql_file(file_path, drop_existing=False):
    """SQL 파일 실행"""
    logger.info("=" * 80)
    logger.info("Inform Note Agent 테이블 생성 시작")
    logger.info("=" * 80)
    
    # 데이터베이스 연결 확인
    if not db.test_connection():
        logger.error("데이터베이스 연결 실패")
        return False
    
    logger.info("✓ 데이터베이스 연결 성공")
    
    # SQL 파일 읽기
    sql_content = read_sql_file(file_path)
    if not sql_content:
        return False
    
    logger.info(f"✓ SQL 파일 읽기 완료: {file_path}")
    
    # SQL 문 분리
    statements = split_sql_statements(sql_content)
    logger.info(f"✓ 총 {len(statements)}개의 SQL 문 확인")
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 기존 테이블 삭제 (옵션)
            if drop_existing:
                logger.info("기존 테이블 삭제 중...")
                for table_name in ["INFORM_NOTE", "INFORMNOTE_TABLE"]:
                    try:
                        cursor.execute(f"DROP TABLE {table_name} CASCADE CONSTRAINTS")
                        logger.info(f"✓ 기존 테이블 삭제 완료: {table_name}")
                    except Exception as e:
                        logger.warning(f"{table_name} 삭제 실패 (없을 수 있음): {e}")
            
            # SQL 문 실행
            success_count = 0
            error_count = 0
            
            for i, statement in enumerate(statements, 1):
                try:
                    # 빈 문장 건너뛰기
                    if not statement.strip():
                        continue
                    
                    logger.info(f"[{i}/{len(statements)}] SQL 실행 중...")
                    logger.debug(f"SQL: {statement[:100]}...")
                    
                    cursor.execute(statement)
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    error_msg = str(e)
                    # 이미 존재하는 객체는 경고만 출력
                    if 'already exists' in error_msg.lower() or 'name is already used' in error_msg.lower():
                        logger.warning(f"  ⚠ 객체가 이미 존재합니다: {error_msg[:100]}")
                    else:
                        logger.error(f"  ✗ SQL 실행 실패: {error_msg[:200]}")
                        logger.debug(f"  실패한 SQL: {statement[:200]}")
            
            conn.commit()
            logger.info("=" * 80)
            logger.info(f"SQL 실행 완료: 성공 {success_count}개, 실패 {error_count}개")
            logger.info("=" * 80)
            
            # 테이블 생성 확인
            logger.info("\n테이블 생성 확인 중...")
            cursor.execute("""
                SELECT 
                    table_name,
                    num_rows,
                    TO_CHAR(last_analyzed, 'YYYY-MM-DD HH24:MI:SS') as last_analyzed
                FROM user_tables
                WHERE table_name = 'INFORM_NOTE'
            """)
            result = cursor.fetchone()
            
            if result:
                logger.info(f"✓ 테이블 생성 확인: {result[0]}")
                logger.info(f"  - 행 수: {result[1] if result[1] else 0}")
                logger.info(f"  - 최종 분석: {result[2] if result[2] else 'N/A'}")
            else:
                logger.warning("⚠ 테이블이 생성되지 않았을 수 있습니다.")
            
            # 인덱스 확인
            cursor.execute("""
                SELECT 
                    index_name,
                    COUNT(*) as column_count
                FROM user_ind_columns
                WHERE table_name = 'INFORM_NOTE'
                GROUP BY index_name
                ORDER BY index_name
            """)
            indexes = cursor.fetchall()
            
            if indexes:
                logger.info(f"\n✓ 생성된 인덱스: {len(indexes)}개")
                for idx_name, col_count in indexes:
                    logger.info(f"  - {idx_name} ({col_count}개 컬럼)")
            
            cursor.close()
            
            return error_count == 0
            
    except Exception as e:
        logger.error(f"테이블 생성 중 오류 발생: {e}", exc_info=True)
        return False


def verify_table_structure():
    """테이블 구조 검증"""
    logger.info("\n" + "=" * 80)
    logger.info("테이블 구조 검증")
    logger.info("=" * 80)
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 컬럼 정보 조회
            cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    data_length,
                    nullable,
                    data_default
                FROM user_tab_columns
                WHERE table_name = 'INFORM_NOTE'
                ORDER BY column_id
            """)
            columns = cursor.fetchall()
            
            logger.info(f"\n✓ 총 {len(columns)}개 컬럼 확인:")
            for col_name, data_type, data_length, nullable, data_default in columns:
                null_str = "NULL 허용" if nullable == 'Y' else "NOT NULL"
                length_str = f"({data_length})" if data_length else ""
                default_str = f" DEFAULT {data_default}" if data_default else ""
                logger.info(f"  - {col_name}: {data_type}{length_str} {null_str}{default_str}")
            
            # 제약조건 확인
            cursor.execute("""
                SELECT 
                    constraint_name,
                    constraint_type
                FROM user_constraints
                WHERE table_name = 'INFORM_NOTE'
                ORDER BY constraint_type, constraint_name
            """)
            constraints = cursor.fetchall()
            
            if constraints:
                logger.info(f"\n✓ 제약조건: {len(constraints)}개")
                for const_name, const_type in constraints:
                    const_type_name = {
                        'P': 'Primary Key',
                        'C': 'Check',
                        'U': 'Unique',
                        'R': 'Foreign Key'
                    }.get(const_type, const_type)
                    logger.info(f"  - {const_name}: {const_type_name}")
            
            cursor.close()
            return True
            
    except Exception as e:
        logger.error(f"테이블 구조 검증 실패: {e}", exc_info=True)
        return False


def main():
    """메인 함수"""
    sql_file = Path(__file__).parent / 'create_informnote_table.sql'
    
    if not sql_file.exists():
        logger.error(f"SQL 파일을 찾을 수 없습니다: {sql_file}")
        sys.exit(1)
    
    # 사용자 확인
    print("\n" + "=" * 80)
    print("Inform Note Agent - 반도체 공정 다운타임 관리 테이블 생성")
    print("=" * 80)
    print(f"데이터베이스: {settings.ORACLE_DSN}")
    print(f"사용자: {settings.ORACLE_USER}")
    print(f"SQL 파일: {sql_file}")
    print("=" * 80)
    
    drop_existing = input("\n기존 테이블을 삭제하고 새로 생성하시겠습니까? (y/N): ").strip().lower() == 'y'
    
    if drop_existing:
        print("⚠ 경고: 기존 테이블의 모든 데이터가 삭제됩니다!")
        confirm = input("정말 진행하시겠습니까? (yes 입력): ").strip().lower()
        if confirm != 'yes':
            print("취소되었습니다.")
            sys.exit(0)
    
    # SQL 파일 실행
    success = execute_sql_file(sql_file, drop_existing=drop_existing)
    
    if success:
        # 테이블 구조 검증
        verify_table_structure()
        
        print("\n" + "=" * 80)
        print("✓ 테이블 생성 완료!")
        print("=" * 80)
        print("\n다음 단계:")
        print("1. 테이블이 정상적으로 생성되었는지 확인하세요.")
        print("2. 샘플 데이터를 삽입하여 테스트하세요.")
        print("3. 애플리케이션에서 테이블을 사용할 수 있습니다.")
    else:
        print("\n" + "=" * 80)
        print("✗ 테이블 생성 중 오류가 발생했습니다.")
        print("=" * 80)
        sys.exit(1)


if __name__ == '__main__':
    main()

