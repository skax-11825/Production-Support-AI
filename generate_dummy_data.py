#!/usr/bin/env python3
"""
Inform Note Agent - data_table.csv 기반 더미 데이터 생성 및 Oracle DB 삽입
"""
import pandas as pd
import random
from datetime import datetime, timedelta
from database import db
import logging
from typing import List, Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# data_table.csv 기반 데이터 레이블 정의
DATA_LABELS = {
    'site_id': ['ICH', 'CJU', 'WUX'],
    'factory_id': {
        'ICH': ['FAC_M14', 'FAC_M16'],
        'CJU': ['FAC_M12', 'FAC_M15'],
        'WUX': ['FAC_C2F']
    },
    'line_id': {
        'FAC_M14': ['LN_M14_PH1', 'LN_M14_PH2', 'LN_M14_ET1', 'LN_M14_ET2'],
        'FAC_M16': ['LN_M16_PH1', 'LN_M16_PH2', 'LN_M16_TF1'],
        'FAC_M12': ['LN_M12_PH1', 'LN_M12_ET1', 'LN_M12_CM1'],
        'FAC_M15': ['LN_M15_PH1', 'LN_M15_ET1', 'LN_M15_IMP1'],
        'FAC_C2F': ['LN_C2F_PH1', 'LN_C2F_ET1']
    },
    'process_id': ['PROC_PH', 'PROC_ET', 'PROC_TF', 'PROC_DF', 'PROC_CM', 'PROC_IMP', 'PROC_CLN', 'PROC_MI'],
    'eqp_id': {
        'PROC_PH': [f'M{i//10}-PH-{i%10:03d}' for i in range(1, 31)],
        'PROC_ET': [f'M{i//10}-ET-{i%10:03d}' for i in range(1, 31)],
        'PROC_TF': [f'M{i//10}-TF-{i%10:03d}' for i in range(1, 31)],
        'PROC_DF': [f'M{i//10}-DF-{i%10:03d}' for i in range(1, 31)],
        'PROC_CM': [f'M{i//10}-CM-{i%10:03d}' for i in range(1, 31)],
        'PROC_IMP': [f'M{i//10}-IMP-{i%10:03d}' for i in range(1, 31)],
        'PROC_CLN': [f'M{i//10}-CLN-{i%10:03d}' for i in range(1, 31)],
        'PROC_MI': [f'M{i//10}-MI-{i%10:03d}' for i in range(1, 31)],
    },
    'model_id': ['MDL_KE_VER', 'MDL_KE_EDGE', 'MDL_KE_PRO', 'MDL_KE_LITE'],
    'down_type': ['SCHEDULED', 'UNSCHEDULED'],
    'error_code': {
        'PROC_PH': ['PH_ERR_2001', 'PH_ERR_3040', 'PH_STG_901', 'PH_VAC_102'],
        'PROC_ET': ['ET_ERR_1001', 'ET_TMP_301', 'ET_VAC_099'],
        'PROC_TF': ['TF_ERR_2001', 'TF_TMP_401'],
        'PROC_DF': ['DF_TMP_800', 'DF_ERR_500'],
        'PROC_CM': ['CM_HED_105', 'CM_MOT_300'],
        'PROC_IMP': ['IMP_BEAM_01', 'IMP_ARC_005'],
        'PROC_CLN': ['CLN_WET_200', 'CLN_DRY_300'],
        'PROC_MI': ['MI_IMG_404', 'MI_STG_100'],
    },
    'act_prob_reason': {
        'PROC_PH': ['노광 강도 불안정', '스테이지 위치 오차', '진공 시스템 이상'],
        'PROC_ET': ['에칭 속도 이상', '온도 제어 불안정', '가스 공급 문제'],
        'PROC_TF': ['증착 속도 이상', '온도 제어 문제'],
        'PROC_DF': ['TC 위치 변화로 온도 측정 부정확', '가스 유량 이상'],
        'PROC_CM': ['연마 속도 이상', '모터 이상'],
        'PROC_IMP': ['이온 빔 불안정', '아크 발생'],
        'PROC_CLN': ['세정액 공급 문제', '건조 시스템 이상'],
        'PROC_MI': ['이미지 센서 이상', '스테이지 문제'],
    },
    'act_content': {
        'PROC_PH': ['노광 강도 재조정', '스테이지 캘리브레이션', '진공 시스템 점검'],
        'PROC_ET': ['에칭 파라미터 조정', '온도 제어 시스템 점검', '가스 공급 라인 점검'],
        'PROC_TF': ['증착 파라미터 조정', '온도 제어 시스템 점검'],
        'PROC_DF': ['TC 재조정으로 측정 정확도 향상', '가스 유량 조정'],
        'PROC_CM': ['연마 파라미터 조정', '모터 교체'],
        'PROC_IMP': ['이온 빔 파라미터 조정', '아크 방지 시스템 점검'],
        'PROC_CLN': ['세정액 공급 라인 점검', '건조 시스템 점검'],
        'PROC_MI': ['이미지 센서 교체', '스테이지 캘리브레이션'],
    },
    'operator': ['김철수 책임', '이영희 선임', '박민수 책임', '정수진 책임', '최지영 선임'],
    'first_detector': ['RMS_System', 'FDC_System', 'Operator', 'Maintenance'],
    'status_id': ['COMPLETED', 'IN_PROGRESS'],
}


def generate_inform_note(index: int, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """
    단일 Inform Note 데이터 생성
    
    Args:
        index: 인덱스 (informnote_id 생성용)
        start_date: 시작 날짜 범위
        end_date: 종료 날짜 범위
    
    Returns:
        Inform Note 딕셔너리
    """
    # 사이트 선택
    site_id = random.choice(DATA_LABELS['site_id'])
    
    # 공장 선택 (사이트에 따라)
    factory_id = random.choice(DATA_LABELS['factory_id'][site_id])
    
    # 라인 선택 (공장에 따라)
    line_id = random.choice(DATA_LABELS['line_id'][factory_id])
    
    # 공정 선택
    process_id = random.choice(DATA_LABELS['process_id'])
    
    # 장비 선택 (공정에 따라)
    eqp_id = random.choice(DATA_LABELS['eqp_id'][process_id])
    
    # 모델 선택
    model_id = random.choice(DATA_LABELS['model_id'])
    
    # 다운타임 유형
    down_type = random.choice(DATA_LABELS['down_type'])
    
    # 다운타임 시간 생성 (30분 ~ 480분)
    down_time_minutes = random.randint(30, 480)
    
    # 다운 시작 시간 (랜덤)
    time_range = (end_date - start_date).total_seconds()
    random_seconds = random.randint(0, int(time_range))
    down_start_time = start_date + timedelta(seconds=random_seconds)
    
    # 다운 종료 시간
    down_end_time = down_start_time + timedelta(minutes=down_time_minutes)
    
    # 에러 코드 (공정에 따라)
    error_code = random.choice(DATA_LABELS['error_code'][process_id])
    
    # 추정 원인 (공정에 따라)
    act_prob_reason = random.choice(DATA_LABELS['act_prob_reason'][process_id])
    
    # 조치 내용 (공정에 따라)
    act_content = random.choice(DATA_LABELS['act_content'][process_id])
    
    # 조치 시작 시간 (다운 시작 후 10~60분)
    act_start_delay = random.randint(10, 60)
    act_start_time = down_start_time + timedelta(minutes=act_start_delay)
    
    # 조치 종료 시간 (조치 시작 후 다운타임의 70~90%)
    act_duration = int(down_time_minutes * random.uniform(0.7, 0.9))
    act_end_time = act_start_time + timedelta(minutes=act_duration)
    
    # 작업자
    operator = random.choice(DATA_LABELS['operator'])
    
    # 최초 감지 주체
    first_detector = random.choice(DATA_LABELS['first_detector'])
    
    # 상태 (90% 확률로 완료, 10% 확률로 진행중)
    status_id = 'COMPLETED' if random.random() < 0.9 else 'IN_PROGRESS'
    
    # informnote_id 생성 (VARCHAR(10) 제약)
    informnote_id = f"IN{str(index + 1).zfill(8)}"[:10]
    
    return {
        'informnote_id': informnote_id,
        'site_id': site_id,
        'factory_id': factory_id,
        'line_id': line_id,
        'process_id': process_id,
        'eqp_id': eqp_id,
        'model_id': model_id,
        'down_start_time': down_start_time,
        'down_end_time': down_end_time if status_id == 'COMPLETED' else None,
        'down_time_minutes': down_time_minutes if status_id == 'COMPLETED' else None,
        'down_type': down_type,
        'error_code': error_code,
        'act_prob_reason': act_prob_reason,
        'act_content': act_content,
        'act_start_time': act_start_time,
        'act_end_time': act_end_time if status_id == 'COMPLETED' else None,
        'operator': operator,
        'first_detector': first_detector,
        'status_id': status_id,
        'link': f"https://dummy.reference/{index + 1}",
    }


def insert_data_to_oracle(data_list: List[Dict[str, Any]]) -> tuple[int, int]:
    """
    Oracle DB에 데이터 삽입
    
    Returns:
        (성공 건수, 실패 건수)
    """
    db.create_pool()
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            insert_sql = """
                INSERT INTO INFORM_NOTE (
                    informnote_id, site_id, factory_id, line_id, process_id,
                    eqp_id, model_id, down_start_time, down_end_time, down_time_minutes,
                    down_type, error_code, act_prob_reason, act_content,
                    act_start_time, act_end_time, operator, first_detector, status_id, link
                ) VALUES (
                    :1, :2, :3, :4, :5, :6, :7, :8, :9, :10,
                    :11, :12, :13, :14, :15, :16, :17, :18, :19, :20
                )
            """
            
            success_count = 0
            error_count = 0
            
            for idx, data in enumerate(data_list):
                try:
                    cursor.execute(insert_sql, (
                        data['informnote_id'],
                        data['site_id'],
                        data['factory_id'],
                        data['line_id'],
                        data['process_id'],
                        data['eqp_id'],
                        data['model_id'],
                        data['down_start_time'],
                        data['down_end_time'],
                        data['down_time_minutes'],
                        data['down_type'],
                        data['error_code'],
                        data['act_prob_reason'],
                        data['act_content'],
                        data['act_start_time'],
                        data['act_end_time'],
                        data['operator'],
                        data['first_detector'],
                        data['status_id'],
                        data['link'],
                    ))
                    success_count += 1
                    
                    if (idx + 1) % 100 == 0:
                        logger.info(f"진행 중... {idx + 1}/{len(data_list)}건 삽입 완료")
                        conn.commit()
                except Exception as e:
                    error_count += 1
                    logger.error(f"✗ 삽입 실패 (행 {idx + 1}): {e}")
            
            conn.commit()
            cursor.close()
            
            return success_count, error_count
            
    except Exception as e:
        logger.error(f"데이터베이스 작업 중 오류 발생: {e}")
        raise
    finally:
        db.close_pool()


def main():
    """메인 함수"""
    print("=" * 80)
    print("Inform Note Agent - data_table.csv 기반 더미 데이터 생성")
    print("=" * 80)
    
    # 생성할 데이터 개수 입력
    try:
        num_records = int(input("\n생성할 데이터 개수를 입력하세요 (기본값: 1000): ") or "1000")
    except ValueError:
        num_records = 1000
    
    # 날짜 범위 설정 (최근 90일)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    logger.info(f"데이터 생성 시작: {num_records}건")
    logger.info(f"날짜 범위: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
    
    # 데이터 생성
    data_list = []
    for i in range(num_records):
        data = generate_inform_note(i, start_date, end_date)
        data_list.append(data)
    
    logger.info(f"데이터 생성 완료: {len(data_list)}건")
    
    # Oracle DB에 삽입
    logger.info("Oracle DB에 데이터 삽입 중...")
    success_count, error_count = insert_data_to_oracle(data_list)
    
    print("\n" + "=" * 80)
    print(f"데이터 삽입 완료: 성공 {success_count}개, 실패 {error_count}개")
    print("=" * 80)
    
    # 통계 정보 출력
    if success_count > 0:
        db.create_pool()
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM INFORM_NOTE')
                total = cursor.fetchone()[0]
                print(f"✓ 현재 테이블 총 행 수: {total}")
                
                # 사이트별 통계
                cursor.execute('''
                    SELECT site_id, COUNT(*) as cnt, 
                           ROUND(SUM(down_time_minutes)/60, 2) as total_hours
                    FROM INFORM_NOTE
                    GROUP BY site_id
                    ORDER BY site_id
                ''')
                print("\n사이트별 통계:")
                for row in cursor.fetchall():
                    print(f"  - {row[0]}: {row[1]}건, 총 다운타임 {row[2]}시간")
                
                cursor.close()
        except Exception as e:
            logger.error(f"통계 조회 중 오류: {e}")
        finally:
            db.close_pool()
    
    print("\n" + "=" * 80)
    print("✓ 더미 데이터 생성 및 삽입 완료!")
    print("=" * 80)


if __name__ == '__main__':
    main()

