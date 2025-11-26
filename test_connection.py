"""
Oracle 데이터베이스 연결 테스트 스크립트
Docker Oracle DB 연결을 테스트합니다.
"""
import sys
from database import db
from config import settings
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_connection():
    """데이터베이스 연결 테스트"""
    print("=" * 50)
    print("Oracle DB 연결 테스트")
    print("=" * 50)
    print(f"DSN: {settings.ORACLE_DSN}")
    print(f"User: {settings.ORACLE_USER}")
    print(f"Password: {'*' * len(settings.ORACLE_PASSWORD)}")
    print("-" * 50)
    
    try:
        # 연결 풀 생성
        db.create_pool()
        print("✓ 연결 풀 생성 성공")
        
        # 연결 테스트
        if db.test_connection():
            print("✓ 데이터베이스 연결 성공!")
            
            # 추가 정보 조회
            try:
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # 현재 사용자 정보
                    cursor.execute("SELECT USER FROM DUAL")
                    current_user = cursor.fetchone()[0]
                    print(f"✓ 현재 사용자: {current_user}")
                    
                    # 데이터베이스 이름
                    cursor.execute("SELECT NAME FROM V$DATABASE")
                    db_name = cursor.fetchone()[0]
                    print(f"✓ 데이터베이스 이름: {db_name}")
                    
                    # 테이블 목록 조회 (예시)
                    cursor.execute("""
                        SELECT table_name 
                        FROM user_tables 
                        WHERE ROWNUM <= 5
                    """)
                    tables = cursor.fetchall()
                    if tables:
                        print(f"✓ 사용자 테이블 (최대 5개): {[t[0] for t in tables]}")
                    else:
                        print("✓ 사용자 테이블 없음 (정상)")
                    
                    cursor.close()
            except Exception as e:
                logger.warning(f"추가 정보 조회 중 오류: {e}")
            
            print("=" * 50)
            print("연결 테스트 완료!")
            return True
        else:
            print("✗ 데이터베이스 연결 실패")
            return False
            
    except Exception as e:
        print(f"✗ 오류 발생: {e}")
        print("\n문제 해결 방법:")
        print("1. Docker 컨테이너가 실행 중인지 확인: docker ps")
        print("2. .env 파일의 설정이 올바른지 확인")
        print("3. ORACLE_DSN 형식 확인:")
        print("   - Service Name 사용: localhost:1521/FREEPDB1")
        print("   - SID 사용: localhost:1521/XE")
        print("4. Oracle Instant Client 설치 여부 확인")
        return False
    finally:
        db.close_pool()


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)

