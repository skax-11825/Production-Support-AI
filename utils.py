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
    """SQL 문을 개별 명령어로 분리 (PL/SQL 블록 포함)"""
    statements = []
    current_statement = []
    
    inside_plsql = False
    
    for line in sql_content.split('\n'):
        original_line = line
        line = line.strip()
        
        # 빈 줄 건너뛰기
        if not line:
            continue
        
        # 주석 줄 건너뛰기
        if line.startswith('--'):
            continue
        
        # 라인 내 주석 제거 (문자열 내부가 아닌 경우만)
        comment_pos = line.find('--')
        if comment_pos >= 0:
            # 문자열 내부에 있는지 확인
            before_comment = line[:comment_pos]
            quote_count = before_comment.count("'") - before_comment.count("''")
            if quote_count % 2 == 0:  # 짝수면 문자열 밖
                line = before_comment.strip()
        
        if not line:
            continue
            
        upper_line = line.upper()

        # PL/SQL 블록 시작 감지
        if 'TRIGGER' in upper_line and ('CREATE' in upper_line or 'CREATE OR REPLACE' in upper_line):
            inside_plsql = True
        
        if line:
            current_statement.append(original_line)  # 원본 라인 사용 (들여쓰기 보존)
            
            # PL/SQL 블록은 END; 또는 END / 까지 하나의 문장으로 취급
            if inside_plsql:
                if upper_line.strip().startswith('END') and (';' in line or '/' in line):
                    statement = '\n'.join(current_statement)
                    # 끝의 ; 또는 / 제거
                    statement = statement.rstrip().rstrip(';').rstrip('/').strip()
                    if statement:
                        statements.append(statement)
                    current_statement = []
                    inside_plsql = False
                continue
            
            # 일반 SQL 문장의 종료 여부 확인
            if line.endswith(';') or line.endswith('/'):
                statement = '\n'.join(current_statement)
                statement = statement.rstrip().rstrip(';').rstrip('/').strip()
                if statement:
                    statements.append(statement)
                current_statement = []
    
    # 마지막 문장 처리
    if current_statement:
        statement = '\n'.join(current_statement).strip()
        if statement:
            statements.append(statement)
    
    return statements

