import sys
import pandas as pd
import oracledb
from pathlib import Path
import math
import traceback

# 하드코딩된 설정 (문제 해결을 위해 임시 사용)
ORACLE_USER = "oracleuser"
ORACLE_PASSWORD = "oracleuser"  # 비밀번호는 보통 계정과 동일하거나 1234 등으로 설정됨. 
# setup_tables.py 로그에 따르면 DSN은 localhost:1521/FREEPDB1
ORACLE_DSN = "localhost:1521/FREEPDB1"

DATA_FILE = Path('normalized_data_preprocessed.xlsx').absolute()

def get_connection():
    print(f"Connecting to {ORACLE_DSN} as {ORACLE_USER}...", flush=True)
    return oracledb.connect(
        user=ORACLE_USER,
        password=ORACLE_PASSWORD,
        dsn=ORACLE_DSN
    )

def _clean(value):
    if value is None: return None
    if isinstance(value, float) and math.isnan(value): return None
    if pd.isna(value): return None
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value

def _clean_number(value):
    if value is None: return None
    if isinstance(value, float) and math.isnan(value): return None
    if isinstance(value, (int, float)): return float(value)
    if isinstance(value, str):
        value = value.strip()
        if not value: return None
        try: return float(value)
        except: return None
    return value

def load_inform_notes_simple():
    print("=" * 50)
    print("SIMPLE DATA LOADER STARTED")
    print("=" * 50)
    
    if not DATA_FILE.exists():
        print(f"ERROR: File not found: {DATA_FILE}")
        return

    try:
        conn = get_connection()
        cursor = conn.cursor()
        print("DB Connected successfully.")
        
        print("Reading Excel file...", flush=True)
        df = pd.read_excel(DATA_FILE, sheet_name='inform_note')
        print(f"Excel loaded: {len(df)} rows", flush=True)
        
        # 컬럼명 정규화
        df.columns = [str(col).strip().lower() for col in df.columns]
        
        # 데이터 준비
        records = []
        for idx, row in df.iterrows():
            # 필수 컬럼 매핑
            informnote_id = _clean(row.get('inform_note_id'))
            if not informnote_id: continue
            
            records.append((
                informnote_id,
                _clean(row.get('site_id')),
                _clean(row.get('factory_id')),
                _clean(row.get('line_id')),
                _clean(row.get('process_id')),
                _clean(row.get('eqp_id')),
                _clean(row.get('model_id')),
                # 시간은 일단 생략하거나 문자열로 처리될 수 있음
                None, None, # down_start, down_end
                _clean_number(row.get('down_time_minutes')),
                # ... 나머지 컬럼 생략 (테스트 목적)
            ))
            
        print(f"Prepared {len(records)} records.")
        
        # 간단히 INSERT 테스트 (전체 컬럼 매핑은 복잡하므로, 
        # load_data.py가 왜 안되는지 알기 위해 여기까지 실행되는지 확인이 목표)
        # 만약 여기까지 실행된다면 load_data.py의 특정 모듈 문제임.
        
        cursor.close()
        conn.close()
        print("Process finished successfully.")
        
    except Exception as e:
        print(f"ERROR: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    load_inform_notes_simple()

