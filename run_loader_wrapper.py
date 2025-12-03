import sys
import pandas as pd
import oracledb
from config import settings
from pathlib import Path
import logging

# 로깅 설정 (화면 출력 강제)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

DATA_FILE = Path('normalized_data_preprocessed.xlsx')

def get_connection():
    return oracledb.connect(
        user=settings.ORACLE_USER,
        password=settings.ORACLE_PASSWORD,
        dsn=settings.ORACLE_DSN
    )

def load_inform_notes():
    logger.info("INFORM_NOTE 데이터 적재 시작...")
    try:
        df = pd.read_excel(DATA_FILE, sheet_name='inform_note')
        logger.info(f"엑셀 읽기 성공: {len(df)}행")
        
        # 컬럼명 소문자 변환 및 공백 제거
        df.columns = [str(col).strip().lower() for col in df.columns]
        
        records = []
        for idx, row in df.iterrows():
            # 간단하게 필수 데이터만 매핑 테스트
            informnote_id = row.get('inform_note_id')
            if pd.isna(informnote_id):
                continue
                
            records.append({
                'informnote_id': str(informnote_id),
                'site_id': str(row.get('site_id', '')),
                'factory_id': str(row.get('factory_id', '')),
                'line_id': str(row.get('line_id', '')),
                'process_id': str(row.get('process_id', '')),
                'eqp_id': str(row.get('eqp_id', '')),
                'model_id': str(row.get('model_id', '')),
                # 필요한 다른 컬럼들도 추가해야 함
            })
            
        logger.info(f"변환된 레코드: {len(records)}건")
        
        # 일단 1건만이라도 들어가는지 테스트
        if not records:
            logger.warning("적재할 데이터가 없습니다.")
            return

        conn = get_connection()
        cursor = conn.cursor()
        
        # TRUNCATE
        cursor.execute("TRUNCATE TABLE INFORM_NOTE")
        logger.info("INFORM_NOTE 테이블 비움")
        
        # INSERT (일부 컬럼만)
        # 실제로는 모든 컬럼을 넣어야 하지만, 테스트를 위해 간단히
        # load_data.py의 로직을 그대로 가져오는 게 낫겠음
        pass 
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"에러 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("스크립트 시작", flush=True)
    if not DATA_FILE.exists():
        print(f"파일 없음: {DATA_FILE}")
    else:
        # 기존 load_data.py를 호출하는 방식으로 변경 (래퍼 스크립트)
        # 왜냐하면 로직을 다 옮기기엔 복잡함
        try:
            import load_data
            print("load_data 모듈 임포트 성공")
            load_data.main()
        except Exception as e:
            print(f"load_data 실행 실패: {e}")
            import traceback
            traceback.print_exc()

