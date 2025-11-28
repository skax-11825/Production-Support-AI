"""
공통 유틸리티 함수
"""
import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


def read_sql_file(file_path: Path) -> str:
    """SQL 파일 읽기"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        logger.error(f"SQL 파일 읽기 실패: {e}")
        return ""


def split_sql_statements(sql_content: str) -> List[str]:
    """SQL 문을 개별 명령어로 분리"""
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

