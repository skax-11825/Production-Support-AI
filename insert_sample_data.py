#!/usr/bin/env python3
"""
Inform Note Agent - 반도체 공정 다운타임 샘플 데이터 삽입 스크립트
테스트용 샘플 데이터를 생성합니다.
"""
from database import db
from config import settings
import logging
from datetime import datetime, timedelta
import random

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# 반도체 공정 샘플 데이터
SAMPLE_SITES = ['ICH', 'CJU', 'WUX']  # 이천, 청주, 우시
SAMPLE_FACTORIES = ['FAB1', 'FAB2', 'FAB3']
SAMPLE_LINES = ['LINE01', 'LINE02', 'LINE03', 'LINE04', 'LINE05']
SAMPLE_PROCESSES = ['PHOTO', 'ETCH', 'CVD', 'PVD', 'CMP', 'IMPLANT']
SAMPLE_EQUIPMENTS = ['EQP001', 'EQP002', 'EQP003', 'EQP004', 'EQP005']
SAMPLE_MODELS = ['MODEL-A', 'MODEL-B', 'MODEL-C']
SAMPLE_DOWN_TYPES = ['SCHEDULED', 'UNSCHEDULED']
SAMPLE_ERROR_CODES = ['ERR001', 'ERR002', 'ERR003', 'ERR004', 'ERR005', None]
SAMPLE_OPERATORS = ['OP001', 'OP002', 'OP003', 'OP004']
SAMPLE_DETECTORS = ['AUTO', 'MANUAL', 'SYSTEM']
SAMPLE_STATUSES = ['COMPLETED', 'IN_PROGRESS']

SAMPLE_PROB_REASONS = [
    '장비 부품 고장',
    '소재 공급 지연',
    '예방 정비',
    '전력 공급 문제',
    '환경 제어 문제',
    '소프트웨어 오류',
    '작업자 실수',
    '기타'
]

SAMPLE_ACT_CONTENTS = [
    '부품 교체 완료',
    '소재 재공급 완료',
    '정비 완료',
    '전력 복구 완료',
    '환경 제어 시스템 점검 완료',
    '소프트웨어 업데이트 완료',
    '재교육 실시',
    '조치 진행 중'
]


def generate_sample_data(count=10):
    """샘플 데이터 생성"""
    samples = []
    base_time = datetime.now() - timedelta(days=30)  # 30일 전부터
    
    for i in range(count):
        # 다운타임 시간 생성
        down_start = base_time + timedelta(
            days=random.randint(0, 29),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        # 다운 지속 시간 (분)
        down_minutes = random.randint(5, 480)  # 5분 ~ 8시간
        down_end = down_start + timedelta(minutes=down_minutes)
        
        # 조치 시간 (다운 종료 후 시작)
        act_start = down_end + timedelta(minutes=random.randint(0, 30))
        act_minutes = random.randint(10, 120)  # 10분 ~ 2시간
        act_end = act_start + timedelta(minutes=act_minutes)
        
        # 상태 결정 (조치 종료 시각이 현재보다 이전이면 COMPLETED)
        status = 'COMPLETED' if act_end < datetime.now() else 'IN_PROGRESS'
        
        sample = {
            'informnote_id': f'IN{str(i+1).zfill(6)}',
            'site_id': random.choice(SAMPLE_SITES),
            'factory_id': random.choice(SAMPLE_FACTORIES),
            'line_id': random.choice(SAMPLE_LINES),
            'process_id': random.choice(SAMPLE_PROCESSES),
            'eqp_id': random.choice(SAMPLE_EQUIPMENTS),
            'model_id': random.choice(SAMPLE_MODELS),
            'down_start_time': down_start,
            'down_end_time': down_end,
            'down_time_minutes': down_minutes,
            'down_type': random.choice(SAMPLE_DOWN_TYPES),
            'error_code': random.choice(SAMPLE_ERROR_CODES),
            'act_prob_reason': random.choice(SAMPLE_PROB_REASONS),
            'act_content': random.choice(SAMPLE_ACT_CONTENTS),
            'act_start_time': act_start,
            'act_end_time': act_end if status == 'COMPLETED' else None,
            'operator': random.choice(SAMPLE_OPERATORS),
            'first_detector': random.choice(SAMPLE_DETECTORS),
            'status_id': status
        }
        
        samples.append(sample)
    
    return samples


def insert_sample_data(count=10):
    """샘플 데이터 삽입"""
    logger.info("=" * 80)
    logger.info("샘플 데이터 삽입 시작")
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
    
    # 샘플 데이터 생성
    logger.info(f"샘플 데이터 {count}개 생성 중...")
    samples = generate_sample_data(count)
    logger.info("✓ 샘플 데이터 생성 완료")
    
    # 데이터 삽입
    try:
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
            
            for sample in samples:
                try:
                    cursor.execute(insert_sql, (
                        sample['informnote_id'],
                        sample['site_id'],
                        sample['factory_id'],
                        sample['line_id'],
                        sample['process_id'],
                        sample['eqp_id'],
                        sample['model_id'],
                        sample['down_start_time'],
                        sample['down_end_time'],
                        sample['down_time_minutes'],
                        sample['down_type'],
                        sample['error_code'],
                        sample['act_prob_reason'],
                        sample['act_content'],
                        sample['act_start_time'],
                        sample['act_end_time'],
                        sample['operator'],
                        sample['first_detector'],
                        sample['status_id']
                    ))
                    success_count += 1
                    logger.debug(f"✓ 삽입 완료: {sample['informnote_id']}")
                    
                except Exception as e:
                    error_count += 1
                    error_msg = str(e)
                    if 'unique constraint' in error_msg.lower():
                        logger.warning(f"  ⚠ 중복 데이터: {sample['informnote_id']} (건너뜀)")
                    else:
                        logger.error(f"  ✗ 삽입 실패: {sample['informnote_id']} - {error_msg[:100]}")
            
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
    print("Inform Note Agent - 샘플 데이터 삽입")
    print("=" * 80)
    print(f"데이터베이스: {settings.ORACLE_DSN}")
    print(f"사용자: {settings.ORACLE_USER}")
    print("=" * 80)
    
    try:
        count = int(input("\n삽입할 샘플 데이터 개수를 입력하세요 (기본값: 10): ").strip() or "10")
    except ValueError:
        count = 10
    
    if count <= 0:
        print("잘못된 입력입니다. 기본값 10을 사용합니다.")
        count = 10
    
    success = insert_sample_data(count)
    
    if success:
        print("\n" + "=" * 80)
        print("✓ 샘플 데이터 삽입 완료!")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("✗ 샘플 데이터 삽입 중 오류가 발생했습니다.")
        print("=" * 80)


if __name__ == '__main__':
    main()

