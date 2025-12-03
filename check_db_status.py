import oracledb
from config import settings
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_tables():
    try:
        dsn = settings.ORACLE_DSN
        user = settings.ORACLE_USER
        password = settings.ORACLE_PASSWORD
        
        logger.info(f"Connecting to DB: {dsn} as {user}")
        
        connection = oracledb.connect(
            user=user,
            password=password,
            dsn=dsn
        )
        
        cursor = connection.cursor()
        
        # 테이블 목록 조회
        cursor.execute("SELECT table_name FROM user_tables ORDER BY table_name")
        tables = cursor.fetchall()
        
        print("\n=== 현재 생성된 테이블 목록 ===")
        if not tables:
            print("생성된 테이블이 없습니다.")
        else:
            for table in tables:
                # 각 테이블의 데이터 개수 조회
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                    count = cursor.fetchone()[0]
                    print(f"- {table[0]}: {count} 행")
                except Exception as e:
                    print(f"- {table[0]}: 조회 실패 ({e})")
                    
        print("==============================\n")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        logger.error(f"DB 연결 또는 조회 실패: {e}")

if __name__ == "__main__":
    check_tables()

