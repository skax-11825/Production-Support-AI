"""
Oracle 데이터베이스 연결 및 관리 모듈
"""
import oracledb
from contextlib import contextmanager
from typing import Optional
from config import settings
import logging

logger = logging.getLogger(__name__)


class Database:
    """Oracle 데이터베이스 연결 관리 클래스"""
    
    def __init__(self):
        self.pool: Optional[oracledb.ConnectionPool] = None
    
    def create_pool(self):
        """연결 풀 생성"""
        try:
            logger.info(f"Oracle DB 연결 시도 중...")
            logger.info(f"DSN: {settings.ORACLE_DSN}, User: {settings.ORACLE_USER}")
            
            self.pool = oracledb.create_pool(
                user=settings.ORACLE_USER,
                password=settings.ORACLE_PASSWORD,
                dsn=settings.ORACLE_DSN,
                min=1,
                max=5,
                increment=1
            )
            logger.info("Oracle DB 연결 풀이 생성되었습니다.")
            
            # 연결 풀 생성 시 한 번만 버전 정보 조회
            try:
                with self.pool.acquire() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT BANNER FROM V$VERSION WHERE ROWNUM = 1")
                    version = cursor.fetchone()
                    if version:
                        logger.info(f"Oracle DB 버전: {version[0]}")
                    cursor.close()
            except Exception:
                pass  # 버전 조회 실패해도 연결 풀 생성은 성공한 것으로 간주
        except oracledb.Error as e:
            error, = e.args
            logger.error(f"Oracle DB 연결 풀 생성 실패: {error.message}")
            logger.error(f"오류 코드: {error.code}")
            raise
        except Exception as e:
            logger.error(f"Oracle DB 연결 풀 생성 실패: {e}")
            raise
    
    def close_pool(self):
        """연결 풀 종료"""
        if self.pool:
            self.pool.close()
            logger.info("Oracle DB 연결 풀이 종료되었습니다.")
    
    @contextmanager
    def get_connection(self):
        """데이터베이스 연결 컨텍스트 매니저"""
        if not self.pool:
            self.create_pool()
        
        conn = self.pool.acquire()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"데이터베이스 작업 중 오류 발생: {e}")
            raise
        finally:
            self.pool.release(conn)
    
    def test_connection(self) -> bool:
        """데이터베이스 연결 테스트"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM DUAL")
                result = cursor.fetchone()
                cursor.close()
                return result is not None
        except oracledb.Error as e:
            error, = e.args
            logger.error(f"연결 테스트 실패: {error.message}")
            logger.error(f"오류 코드: {error.code}")
            return False
        except Exception as e:
            logger.error(f"연결 테스트 실패: {e}")
            return False


# 전역 데이터베이스 인스턴스
db = Database()

