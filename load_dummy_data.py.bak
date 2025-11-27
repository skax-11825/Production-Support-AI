#!/usr/bin/env python3
"""
Inform Note Agent - Dummy 폴더의 더미 데이터 생성 코드를 사용하여 Oracle DB에 데이터 삽입
"""
import sys
import os
from pathlib import Path
import pandas as pd

# 상위 폴더의 Dummy 폴더 경로 추가
current_dir = Path(__file__).parent
dummy_dir = current_dir.parent / "Dummy"
sys.path.insert(0, str(dummy_dir))

# Dummy 폴더의 data_gen.py 임포트
try:
    from data_gen import generate_inform_notes
except ImportError as e:
    print(f"오류: Dummy 폴더의 data_gen.py를 임포트할 수 없습니다: {e}")
    print(f"Dummy 폴더 경로: {dummy_dir}")
    sys.exit(1)

from database import db
from config import settings
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def convert_to_oracle_format(df_row, index):
    """
    Dummy 폴더의 데이터 형식을 Oracle DB 형식으로 변환
    
    Args:
        df_row: pandas DataFrame의 한 행
        index: 행 인덱스 (고유 ID 생성용)
    
    Returns:
        Oracle DB에 삽입할 딕셔너리
    """
    # informnote_id 생성 (VARCHAR2(10) 제약)
    # 형식: IN + 인덱스 (최대 10자)
    # IN(2자) + 숫자(8자) = 최대 10자
    # 10만개까지: IN00000001 ~ IN00099999 (9자)
    # 100만개까지: IN0000001 ~ IN00999999 (9자)
    # 1000만개까지: IN00000001 ~ IN09999999 (10자)
    informnote_id = f"IN{str(index + 1).zfill(8)}"[:10]  # 최대 10자로 제한
    
    # down_type 변환 (Unscheduled -> UNSCHEDULED)
    down_type = df_row.get('down_type', 'UNSCHEDULED')
    if down_type == 'Unscheduled':
        down_type = 'UNSCHEDULED'
    elif down_type == 'Scheduled':
        down_type = 'SCHEDULED'
    else:
        down_type = 'UNSCHEDULED'  # 기본값
    
    # status_id 변환 (In_Progress -> IN_PROGRESS, Completed -> COMPLETED)
    status = df_row.get('status', 'Completed')
    if status == 'In_Progress':
        status_id = 'IN_PROGRESS'
    elif status == 'Completed':
        status_id = 'COMPLETED'
    else:
        status_id = 'COMPLETED'  # 기본값
    
    # down_time_minutes 변환 (down_time_period 사용)
    down_time_minutes = df_row.get('down_time_period')
    if down_time_minutes is None or pd.isna(down_time_minutes):
        down_time_minutes = None
    
    # 날짜 문자열을 datetime으로 변환
    def parse_datetime(dt_str):
        if dt_str is None or pd.isna(dt_str):
            return None
        try:
            return datetime.strptime(str(dt_str), "%Y-%m-%d %H:%M:%S")
        except:
            return None
    
    down_start_time = parse_datetime(df_row.get('down_start_time'))
    down_end_time = parse_datetime(df_row.get('down_end_time'))
    act_start_time = parse_datetime(df_row.get('act_start_time'))
    act_end_time = parse_datetime(df_row.get('act_end_time'))
    
    return {
        'informnote_id': informnote_id,
        'site_id': df_row.get('site_id'),
        'factory_id': df_row.get('factory_id'),
        'line_id': df_row.get('line_id'),
        'process_id': df_row.get('process_id'),
        'eqp_id': df_row.get('eqp_id'),
        'model_id': df_row.get('model_id'),
        'down_start_time': down_start_time,
        'down_end_time': down_end_time,
        'down_time_minutes': down_time_minutes,
        'down_type': down_type,
        'error_code': df_row.get('error_code'),
        'act_prob_reason': df_row.get('act_prob_reason'),
        'act_content': df_row.get('act_content'),
        'act_start_time': act_start_time,
        'act_end_time': act_end_time,
        'operator': df_row.get('operator'),
        'first_detector': df_row.get('first_detector'),
        'status_id': status_id
    }


def insert_to_oracle(df):
    """
    생성된 데이터를 Oracle DB에 삽입
    
    Args:
        df: pandas DataFrame (Dummy 폴더의 generate_inform_notes 결과)
    """
    logger.info("=" * 80)
    logger.info("Oracle DB 데이터 삽입 시작")
    logger.info("=" * 80)
    
    # 데이터베이스 연결 확인
    if not db.test_connection():
        logger.error("데이터베이스 연결 실패")
        return False
    
    logger.info("✓ 데이터베이스 연결 성공")
    
    # 테이블 존재 확인
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM user_tables 
                WHERE table_name = 'INFORMNOTE_TABLE'
            """)
            table_exists = cursor.fetchone()[0] > 0
            
            if not table_exists:
                logger.error("INFORMNOTE_TABLE 테이블이 존재하지 않습니다.")
                logger.error("먼저 setup_informnote_table.py를 실행하여 테이블을 생성하세요.")
                return False
            
            logger.info("✓ 테이블 존재 확인")
            cursor.close()
    except Exception as e:
        logger.error(f"테이블 확인 실패: {e}")
        return False
    
    # 데이터 변환 및 삽입
    try:
        logger.info(f"총 {len(df)}건의 데이터를 변환 중...")
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            insert_sql = """
                INSERT INTO INFORMNOTE_TABLE (
                    informnote_id, site_id, factory_id, line_id, process_id,
                    eqp_id, model_id, down_start_time, down_end_time, down_time_minutes,
                    down_type, error_code, act_prob_reason, act_content,
                    act_start_time, act_end_time, operator, first_detector, status_id
                ) VALUES (
                    :1, :2, :3, :4, :5, :6, :7, :8, :9, :10,
                    :11, :12, :13, :14, :15, :16, :17, :18, :19
                )
            """
            
            success_count = 0
            error_count = 0
            
            for idx, (_, row) in enumerate(df.iterrows()):
                try:
                    # 데이터 변환
                    oracle_data = convert_to_oracle_format(row, idx)
                    
                    # NULL 값 처리
                    cursor.execute(insert_sql, (
                        oracle_data['informnote_id'],
                        oracle_data['site_id'],
                        oracle_data['factory_id'],
                        oracle_data['line_id'],
                        oracle_data['process_id'],
                        oracle_data['eqp_id'],
                        oracle_data['model_id'],
                        oracle_data['down_start_time'],
                        oracle_data['down_end_time'],
                        oracle_data['down_time_minutes'],
                        oracle_data['down_type'],
                        oracle_data['error_code'],
                        oracle_data['act_prob_reason'],
                        oracle_data['act_content'],
                        oracle_data['act_start_time'],
                        oracle_data['act_end_time'],
                        oracle_data['operator'],
                        oracle_data['first_detector'],
                        oracle_data['status_id']
                    ))
                    success_count += 1
                    
                    if (idx + 1) % 100 == 0:
                        logger.info(f"진행 중... {idx + 1}/{len(df)}건 삽입 완료")
                    
                except Exception as e:
                    error_count += 1
                    error_msg = str(e)
                    if 'unique constraint' in error_msg.lower():
                        logger.warning(f"  ⚠ 중복 데이터: {oracle_data.get('informnote_id', 'N/A')} (건너뜀)")
                    else:
                        logger.error(f"  ✗ 삽입 실패 (행 {idx + 1}): {error_msg[:100]}")
            
            conn.commit()
            
            logger.info("=" * 80)
            logger.info(f"데이터 삽입 완료: 성공 {success_count}개, 실패 {error_count}개")
            logger.info("=" * 80)
            
            # 삽입된 데이터 확인
            cursor.execute("SELECT COUNT(*) FROM INFORMNOTE_TABLE")
            total_count = cursor.fetchone()[0]
            logger.info(f"✓ 현재 테이블 총 행 수: {total_count}")
            
            # 통계 정보
            cursor.execute("""
                SELECT 
                    site_id,
                    COUNT(*) as cnt,
                    SUM(down_time_minutes) as total_down_minutes
                FROM INFORMNOTE_TABLE
                GROUP BY site_id
                ORDER BY site_id
            """)
            stats = cursor.fetchall()
            
            if stats:
                logger.info("\n사이트별 통계:")
                for site, cnt, total_min in stats:
                    hours = (total_min or 0) / 60
                    logger.info(f"  - {site}: {cnt}건, 총 다운타임 {hours:.2f}시간")
            
            cursor.close()
            
            return error_count == 0
            
    except Exception as e:
        logger.error(f"데이터 삽입 중 오류 발생: {e}", exc_info=True)
        return False


def main():
    """메인 함수"""
    print("\n" + "=" * 80)
    print("Inform Note Agent - Dummy 데이터 로드")
    print("=" * 80)
    print(f"데이터베이스: {settings.ORACLE_DSN}")
    print(f"사용자: {settings.ORACLE_USER}")
    print(f"Dummy 폴더: {dummy_dir}")
    print("=" * 80)
    
    try:
        days = int(input("\n생성할 데이터 기간(일)을 입력하세요 (기본값: 180일): ").strip() or "180")
    except ValueError:
        days = 180
    
    if days <= 0:
        print("잘못된 입력입니다. 기본값 180을 사용합니다.")
        days = 180
    
    # Dummy 폴더로 이동하여 데이터 생성
    original_cwd = os.getcwd()
    try:
        os.chdir(dummy_dir)
        logger.info(f"Dummy 폴더로 이동: {dummy_dir}")
        
        logger.info(f"{days}일간의 더미 데이터 생성 중...")
        df = generate_inform_notes(days=days)
        
        logger.info(f"✓ {len(df)}건의 데이터 생성 완료")
        
    finally:
        os.chdir(original_cwd)
        logger.info(f"원래 디렉토리로 복귀: {original_cwd}")
    
    if df.empty:
        logger.error("생성된 데이터가 없습니다.")
        return
    
    # Oracle DB에 삽입
    success = insert_to_oracle(df)
    
    if success:
        print("\n" + "=" * 80)
        print("✓ 더미 데이터 삽입 완료!")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("✗ 더미 데이터 삽입 중 오류가 발생했습니다.")
        print("=" * 80)


if __name__ == '__main__':
    main()

