import sys
import pandas as pd
import oracledb
from pathlib import Path
import math
import traceback
import datetime

# 로그 파일 설정
LOG_FILE = Path("loader_log.txt")

def log(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_msg + "\n")
    except:
        pass
    # 터미널 출력도 시도 (보이면 좋고 안보이면 로그 파일로)
    try:
        print(log_msg, flush=True)
    except:
        pass

# 기본 설정 (config.py에서 못 읽을 경우 대비)
ORACLE_USER = "oracleuser"
ORACLE_PASSWORD = "oracleuser" 
ORACLE_DSN = "localhost:1521/FREEPDB1"

# 설정 불러오기 시도
try:
    from config import settings
    ORACLE_USER = settings.ORACLE_USER
    ORACLE_PASSWORD = settings.ORACLE_PASSWORD
    ORACLE_DSN = settings.ORACLE_DSN
    log("Loaded settings from config.py")
except Exception as e:
    log(f"Failed to load settings from config.py: {e}")
    log("Using hardcoded settings (May fail if password is wrong)")

DATA_FILE = Path('normalized_data_preprocessed.xlsx').absolute()

def get_connection():
    log(f"Connecting to {ORACLE_DSN} as {ORACLE_USER}...")
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

# 테이블별 컬럼 매핑 정의
TABLE_MAPPINGS = {
    'process': {
        'table': 'PROCESS',
        'cols': ['process_id', 'process_name', 'process_abbr']
    },
    'model': {
        'table': 'MODEL',
        'cols': ['model_id', 'model_name', 'process_id', 'vendor']
    },
    'equipment': {
        'table': 'EQUIPMENT',
        'cols': ['eqp_id', 'eqp_name', 'model_id', 'line_id']
    },
    'error_code': {
        'table': 'ERROR_CODE',
        'cols': ['error_code', 'error_desc', 'process_id']
    },
    'status': {
        'table': 'STATUS',
        'cols': ['status_id', 'status'], 
        'db_cols': ['STATUS_ID', 'STATUS_NAME']
    },
    'down_type': {
        'table': 'DOWN_TYPE',
        'cols': ['down_type_id', 'down_type'],
        'db_cols': ['DOWN_TYPE_ID', 'DOWN_TYPE_NAME']
    }
}

def load_reference_tables(conn, cursor):
    log("\n=== Loading Reference Tables ===")
    
    for sheet_name, config in TABLE_MAPPINGS.items():
        table_name = config['table']
        excel_cols = config['cols']
        # DB 컬럼명은 별도 정의 없으면 엑셀 컬럼명의 대문자
        db_cols = config.get('db_cols', [c.upper() for c in excel_cols])
        
        try:
            log(f"Loading {table_name} from sheet '{sheet_name}'...")
            df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
            
            # 엑셀 컬럼명 정규화
            df.columns = [str(col).strip().lower() for col in df.columns]
            
            records = []
            for _, row in df.iterrows():
                record = []
                for col in excel_cols:
                    val = row.get(col.lower()) # 소문자로 매칭
                    record.append(_clean(val))
                records.append(tuple(record))
                
            if records:
                cursor.execute(f"TRUNCATE TABLE {table_name}")
                placeholders = ",".join([f":{i+1}" for i in range(len(db_cols))])
                col_names = ",".join(db_cols)
                sql = f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})"
                
                cursor.executemany(sql, records)
                log(f"Inserted {len(records)} rows into {table_name}")
            else:
                log(f"No records for {table_name}")
                
        except Exception as e:
            log(f"Error loading {table_name}: {e}")

def load_dependencies(conn, cursor):
    log("\n=== Loading Dependencies (SITE, FACTORY, LINE) ===")
    try:
        df = pd.read_excel(DATA_FILE, sheet_name='inform_note')
        
        # SITE
        site_ids = sorted(df['site_id'].dropna().unique())
        if site_ids:
            cursor.execute("TRUNCATE TABLE SITE")
            data = [(str(s), str(s)) for s in site_ids]
            cursor.executemany("INSERT INTO SITE (SITE_ID, SITE_NAME) VALUES (:1, :2)", data)
            log(f"Inserted {len(data)} sites")

        # FACTORY (site_id는 첫번째 site로 가정 - 로직 단순화)
        factory_ids = sorted(df['factory_id'].dropna().unique())
        if factory_ids and site_ids:
            cursor.execute("TRUNCATE TABLE FACTORY")
            default_site = str(site_ids[0])
            data = [(str(f), str(f), default_site) for f in factory_ids]
            cursor.executemany("INSERT INTO FACTORY (FACTORY_ID, FACTORY_NAME, SITE_ID) VALUES (:1, :2, :3)", data)
            log(f"Inserted {len(data)} factories")

        # LINE (factory_id는 첫번째 factory로 가정)
        line_ids = sorted(df['line_id'].dropna().unique())
        if line_ids and factory_ids:
            cursor.execute("TRUNCATE TABLE LINE")
            default_factory = str(factory_ids[0])
            data = [(str(l), str(l), default_factory) for l in line_ids]
            cursor.executemany("INSERT INTO LINE (LINE_ID, LINE_NAME, FACTORY_ID) VALUES (:1, :2, :3)", data)
            log(f"Inserted {len(data)} lines")
            
    except Exception as e:
        log(f"Error loading dependencies: {e}")

def load_inform_notes(conn, cursor):
    log("\n=== Loading INFORM_NOTE ===")
    try:
        df = pd.read_excel(DATA_FILE, sheet_name='inform_note')
        df.columns = [str(col).strip().lower() for col in df.columns]
        
        records = []
        for idx, row in df.iterrows():
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
                # 시간 처리 (단순화)
                None, None, # down_start, down_end
                _clean_number(row.get('down_time_minutes')),
                _clean_number(row.get('down_type_id')),
                _clean(row.get('error_code')),
                _clean(row.get('act_prob_reason')),
                _clean(row.get('act_content')),
                None, None, # act_start, act_end
                _clean(row.get('operator')),
                _clean(row.get('first_detector')),
                _clean_number(row.get('status_id')),
                f"https://gipms.com/reference/{idx + 1}"
            ))
            
        if records:
            cursor.execute("TRUNCATE TABLE INFORM_NOTE")
            
            insert_sql = """
                INSERT INTO INFORM_NOTE (
                    informnote_id, site_id, factory_id, line_id, process_id, eqp_id, model_id, 
                    down_start_time, down_end_time, down_time_minutes, down_type_id, error_code,
                    act_prob_reason, act_content, act_start_time, act_end_time,
                    operator, first_detector, status_id, link
                ) VALUES (
                    :1, :2, :3, :4, :5, :6, :7, 
                    :8, :9, :10, :11, :12, 
                    :13, :14, :15, :16, 
                    :17, :18, :19, :20
                )
            """
            cursor.executemany(insert_sql, records)
            log(f"Inserted {len(records)} rows into INFORM_NOTE")
            
    except Exception as e:
        log(f"Error loading INFORM_NOTE: {e}")
        log(traceback.format_exc())

def load_terms(conn, cursor):
    log("\n=== Loading FAB_TERMS_DICTIONARY ===")
    try:
        df = pd.read_excel(DATA_FILE, sheet_name='fab_terms_dictionary')
        df.columns = [str(col).strip().lower() for col in df.columns]
        
        records = []
        for _, row in df.iterrows():
            term_id = _clean(row.get('term_id'))
            if not term_id: continue
            
            term_en = _clean(row.get('term_en'))
            term_kor = _clean(row.get('term_kor_reading'))
            meaning_short = _clean(row.get('meaning_short'))
            
            keywords = f"{term_en} {term_kor} {meaning_short}"
            
            records.append((
                term_id, term_en, term_kor, meaning_short, 
                _clean(row.get('meaning_field')), keywords[:600]
            ))
            
        if records:
            # 트리거 비활성화
            try: cursor.execute("ALTER TRIGGER TRG_FAB_TERMS_DICTIONARY_UPD DISABLE")
            except: pass
            
            cursor.execute("TRUNCATE TABLE FAB_TERMS_DICTIONARY")
            
            sql = """
                INSERT INTO FAB_TERMS_DICTIONARY (
                    term_id, term_en, term_kor_reading, meaning_short, meaning_field, search_keywords, 
                    created_at, updated_at
                ) VALUES (:1, :2, :3, :4, :5, :6, SYSDATE, SYSDATE)
            """
            cursor.executemany(sql, records)
            log(f"Inserted {len(records)} terms")
            
            try: cursor.execute("ALTER TRIGGER TRG_FAB_TERMS_DICTIONARY_UPD ENABLE")
            except: pass
            
    except Exception as e:
        log(f"Error loading terms: {e}")

def main():
    log("=" * 50)
    log("FULL DATA LOADER STARTED")
    log("=" * 50)
    
    if not DATA_FILE.exists():
        log(f"ERROR: File not found: {DATA_FILE}")
        return

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        log("DB Connected.")
        
        # 1. 의존성 테이블 (SITE, FACTORY, LINE)
        load_dependencies(conn, cursor)
        
        # 2. 레퍼런스 테이블
        load_reference_tables(conn, cursor)
        
        # 3. 용어 사전
        load_terms(conn, cursor)
        
        # 4. Inform Note
        load_inform_notes(conn, cursor)
        
        conn.commit()
        log("\nALL DATA COMMITTED SUCCESSFULLY")
        
    except Exception as e:
        if conn: conn.rollback()
        log(f"FATAL ERROR: {e}")
        log(traceback.format_exc())
    finally:
        if conn: conn.close()
        log("Process finished.")

if __name__ == "__main__":
    if LOG_FILE.exists():
        try: LOG_FILE.unlink()
        except: pass
    main()
