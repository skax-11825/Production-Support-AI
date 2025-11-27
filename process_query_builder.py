"""
공정정보 기반 Oracle DB 쿼리 생성 모듈
추출된 공정정보로 데이터베이스 쿼리를 생성하고 실행합니다.
"""
import logging
from typing import Dict, List, Optional, Any
from database import db
from question_analyzer import ProcessInfo

logger = logging.getLogger(__name__)


class ProcessQueryBuilder:
    """공정정보 기반 쿼리 빌더"""
    
    def __init__(self):
        """초기화"""
        pass
    
    def build_query(self, process_info: ProcessInfo, question_type: str = "general") -> tuple:
        """
        공정정보를 기반으로 SQL 쿼리 생성
        
        Args:
            process_info: 추출된 공정정보
            question_type: 질문 유형 (general, statistics, details 등)
        
        Returns:
            SQL 쿼리 문자열
        """
        logger.info(f"[쿼리 생성] 시작 - 질문 유형: {question_type}")
        
        # 기본 SELECT 절
        select_clause = """
            SELECT 
                informnote_id,
                site_id,
                factory_id,
                line_id,
                process_id,
                eqp_id,
                model_id,
                down_start_time,
                down_end_time,
                down_time_minutes,
                down_type,
                error_code,
                act_prob_reason,
                act_content,
                act_start_time,
                act_end_time,
                operator,
                first_detector,
                status_id,
                created_at
            FROM INFORM_NOTE
        """
        
        # WHERE 절 생성
        where_conditions = []
        bind_params = []
        param_index = 1
        
        if process_info.site_id:
            where_conditions.append(f"site_id = :{param_index}")
            bind_params.append(process_info.site_id)
            param_index += 1
        
        if process_info.factory_id:
            where_conditions.append(f"factory_id = :{param_index}")
            bind_params.append(process_info.factory_id)
            param_index += 1
        
        if process_info.process_id:
            where_conditions.append(f"process_id = :{param_index}")
            bind_params.append(process_info.process_id)
            param_index += 1
        
        if process_info.model_id:
            where_conditions.append(f"model_id = :{param_index}")
            bind_params.append(process_info.model_id)
            param_index += 1
        
        if process_info.down_type:
            where_conditions.append(f"down_type = :{param_index}")
            bind_params.append(process_info.down_type)
            param_index += 1
        
        if process_info.down_time_minutes is not None:
            # 다운타임 시간 범위 검색 (입력값의 ±10% 범위)
            tolerance = process_info.down_time_minutes * 0.1
            min_time = process_info.down_time_minutes - tolerance
            max_time = process_info.down_time_minutes + tolerance
            where_conditions.append(f"down_time_minutes BETWEEN :{param_index} AND :{param_index + 1}")
            bind_params.append(max(0, min_time))
            bind_params.append(max_time)
            param_index += 2
        
        # WHERE 절 조합
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # ORDER BY 절
        order_by_clause = "ORDER BY down_start_time DESC"
        
        # 최종 쿼리 조합
        query = f"{select_clause} {where_clause} {order_by_clause}"
        
        logger.info(f"[쿼리 생성] 완료")
        logger.debug(f"[쿼리 생성] 생성된 쿼리: {query}")
        logger.debug(f"[쿼리 생성] 바인드 파라미터: {bind_params}")
        
        return query, bind_params
    
    def execute_query(self, query: str, bind_params: List[Any], limit: int = 100) -> List[Dict]:
        """
        쿼리 실행 및 결과 반환
        
        Args:
            query: SQL 쿼리
            bind_params: 바인드 파라미터
            limit: 최대 반환 행 수
        
        Returns:
            쿼리 결과 리스트
        """
        logger.info(f"[쿼리 실행] 시작 - 최대 {limit}행 반환")
        
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # ROWNUM을 사용한 LIMIT 구현 (Oracle)
                limited_query = f"""
                    SELECT * FROM (
                        {query}
                    ) WHERE ROWNUM <= {limit}
                """
                
                # 바인드 파라미터 적용
                if bind_params:
                    cursor.execute(limited_query, bind_params)
                else:
                    cursor.execute(limited_query)
                
                # 컬럼명 가져오기
                columns = [desc[0] for desc in cursor.description]
                
                # 결과 가져오기
                rows = cursor.fetchall()
                
                # 딕셔너리 리스트로 변환
                results = []
                for row in rows:
                    result_dict = {}
                    for i, col in enumerate(columns):
                        value = row[i]
                        # TIMESTAMP를 문자열로 변환
                        if hasattr(value, 'strftime'):
                            value = value.strftime('%Y-%m-%d %H:%M:%S')
                        result_dict[col] = value
                    results.append(result_dict)
                
                cursor.close()
                
                logger.info(f"[쿼리 실행] 완료 - {len(results)}행 반환")
                return results
                
        except Exception as e:
            logger.error(f"[쿼리 실행] 오류 발생: {e}", exc_info=True)
            raise
    
    def get_statistics(self, process_info: ProcessInfo) -> Dict[str, Any]:
        """
        공정정보 기반 통계 조회
        
        Returns:
            통계 정보 딕셔너리
        """
        logger.info("[통계 조회] 시작")
        
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # WHERE 절 생성
                where_conditions = []
                bind_params = []  # 리스트로 변경
                param_index = 1
                
                if process_info.site_id:
                    where_conditions.append(f"site_id = :{param_index}")
                    bind_params.append(process_info.site_id)
                    param_index += 1
                
                if process_info.factory_id:
                    where_conditions.append(f"factory_id = :{param_index}")
                    bind_params.append(process_info.factory_id)
                    param_index += 1
                
                if process_info.process_id:
                    where_conditions.append(f"process_id = :{param_index}")
                    bind_params.append(process_info.process_id)
                    param_index += 1
                
                if process_info.model_id:
                    where_conditions.append(f"model_id = :{param_index}")
                    bind_params.append(process_info.model_id)
                    param_index += 1
                
                if process_info.down_type:
                    where_conditions.append(f"down_type = :{param_index}")
                    bind_params.append(process_info.down_type)
                    param_index += 1
                
                where_clause = ""
                if where_conditions:
                    where_clause = "WHERE " + " AND ".join(where_conditions)
                
                # 통계 쿼리
                stats_query = f"""
                    SELECT 
                        COUNT(*) as total_count,
                        SUM(down_time_minutes) as total_minutes,
                        AVG(down_time_minutes) as avg_minutes,
                        MIN(down_time_minutes) as min_minutes,
                        MAX(down_time_minutes) as max_minutes,
                        COUNT(CASE WHEN down_type = 'SCHEDULED' THEN 1 END) as scheduled_count,
                        COUNT(CASE WHEN down_type = 'UNSCHEDULED' THEN 1 END) as unscheduled_count,
                        COUNT(CASE WHEN status_id = 'COMPLETED' THEN 1 END) as completed_count,
                        COUNT(CASE WHEN status_id = 'IN_PROGRESS' THEN 1 END) as in_progress_count
                    FROM INFORM_NOTE
                    {where_clause}
                """
                
                # 바인드 파라미터 적용
                if bind_params:
                    cursor.execute(stats_query, bind_params)
                else:
                    cursor.execute(stats_query)
                
                row = cursor.fetchone()
                columns = [desc[0] for desc in cursor.description]
                
                stats = {}
                for i, col in enumerate(columns):
                    value = row[i]
                    # 숫자를 float로 변환
                    if isinstance(value, (int, float)):
                        stats[col.lower()] = float(value) if value is not None else 0
                    else:
                        stats[col.lower()] = value
                
                cursor.close()
                
                logger.info(f"[통계 조회] 완료: {stats}")
                return stats
                
        except Exception as e:
            logger.error(f"[통계 조회] 오류 발생: {e}", exc_info=True)
            raise


# 전역 인스턴스
query_builder = ProcessQueryBuilder()

