"""
질문-답변 API 서버
FastAPI를 사용한 REST API 엔드포인트
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
import logging
import json
from database import db
from config import settings
from dify_client import is_dify_enabled, request_answer, DifyClientError
from utils import read_sql_file
from pathlib import Path

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="질문을 받고 답변을 제공하는 API 서버"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# 요청/응답 모델
# ============================================================================

class QuestionRequest(BaseModel):
    """질문 요청 모델"""
    question: Optional[str] = ""
    context: Optional[str] = None


class AnswerResponse(BaseModel):
    """답변 응답 모델"""
    answer: str
    question: str
    success: bool


class ProcessInfo(BaseModel):
    """Process 정보 모델"""
    id: Optional[str] = None
    name: Optional[str] = None


class ModelInfo(BaseModel):
    """Model 정보 모델"""
    id: Optional[str] = None
    name: Optional[str] = None


class EquipmentInfo(BaseModel):
    """Equipment 정보 모델"""
    id: Optional[str] = None
    name: Optional[str] = None


class IdLookupRequest(BaseModel):
    """ID 조회 요청 모델 - Dify 형식 및 단순 형식 모두 지원"""
    # Dify 형식: process/model/equipment 객체
    process: Optional[ProcessInfo] = None
    model: Optional[ModelInfo] = None
    equipment: Optional[EquipmentInfo] = None
    
    # 단순 형식: 직접 필드
    process_id: Optional[str] = None
    process_name: Optional[str] = None
    model_id: Optional[str] = None
    model_name: Optional[str] = None
    eqp_id: Optional[str] = None
    eqp_name: Optional[str] = None


class IdLookupResponse(BaseModel):
    """ID 조회 응답 모델"""
    process_id: Optional[str] = None
    model_id: Optional[str] = None
    eqp_id: Optional[str] = None


class HealthResponse(BaseModel):
    """헬스 체크 응답 모델"""
    status: str
    database_connected: bool
    dify_enabled: bool


class ErrorCodeStatsItem(BaseModel):
    """Error Code 통계 아이템 모델"""
    period: Optional[str] = None
    process_id: Optional[str] = None
    process_name: Optional[str] = None
    model_id: Optional[str] = None
    model_name: Optional[str] = None
    eqp_id: Optional[str] = None
    eqp_name: Optional[str] = None
    error_code: Optional[str] = None
    error_des: Optional[str] = None
    event_cnt: int
    total_down_time_minutes: Optional[float] = None


class ErrorCodeStatsResponse(BaseModel):
    """Error Code 통계 응답 모델"""
    list: List[ErrorCodeStatsItem]


class ErrorCodeStatsRequest(BaseModel):
    """Error Code 통계 요청 모델"""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    process_id: Optional[str] = None
    model_id: Optional[str] = None
    eqp_id: Optional[str] = None
    error_code: Optional[str] = None
    group_by: Optional[str] = "error_code"


class PMHistoryItem(BaseModel):
    """PM(점검) 이력 아이템 모델"""
    down_date: str
    down_type: str
    down_time_minutes: float
    operator: Optional[str] = None


class PMHistoryResponse(BaseModel):
    """PM 이력 응답 모델"""
    list: List[PMHistoryItem]


class PMHistoryRequest(BaseModel):
    """PM 이력 요청 모델"""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    process_id: Optional[str] = None
    eqp_id: Optional[str] = None
    operator: Optional[str] = None
    limit: Optional[int] = Field(default=10, ge=1, le=1000)


class SearchItem(BaseModel):
    """상세 내역 검색 아이템 모델"""
    informnote_id: str
    down_start_time: str
    process_name: Optional[str] = None
    eqp_name: Optional[str] = None
    error_code: Optional[str] = None
    error_desc: Optional[str] = None
    act_content: Optional[str] = None
    operator: Optional[str] = None
    status: str


class SearchResponse(BaseModel):
    """상세 내역 검색 응답 모델"""
    list: List[SearchItem]


class SearchRequest(BaseModel):
    """상세 내역 검색 요청 모델"""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    process_id: Optional[str] = None
    eqp_id: Optional[str] = None
    operator: Optional[str] = None
    status_id: Optional[int] = None
    limit: Optional[int] = Field(default=20, ge=1, le=1000)


# ============================================================================
# 공통 유틸리티 함수
# ============================================================================

def format_date_for_db(d: Optional[date]) -> Optional[str]:
    """날짜를 DB 형식 문자열로 변환"""
    return d.strftime('%Y-%m-%d') if d else None


def get_sql_template(filename: str) -> str:
    """SQL 템플릿 파일 읽기"""
    template_path = Path(__file__).parent / "sql_templates" / filename
    sql_content = read_sql_file(template_path)
    if not sql_content:
        logger.error(f"SQL 템플릿 파일을 읽을 수 없습니다: {template_path}")
        raise HTTPException(status_code=500, detail=f"SQL 템플릿 파일을 읽을 수 없습니다: {filename}")
    return sql_content.strip()




def lookup_id_by_name(table: str, id_col: str, name_col: str, search_value: str) -> Optional[str]:
    """테이블에서 이름으로 ID 조회"""
    if not search_value or not search_value.strip():
        return None
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            query = f"""
                SELECT {id_col} 
                FROM {table} 
                WHERE UPPER(TRIM({id_col})) LIKE UPPER('%' || TRIM(:1) || '%') 
                   OR UPPER(TRIM({name_col})) LIKE UPPER('%' || TRIM(:2) || '%')
                FETCH FIRST 1 ROWS ONLY
            """
            cursor.execute(query, [search_value.strip(), search_value.strip()])
            row = cursor.fetchone()
            cursor.close()
            return row[0] if row else None
    except Exception as e:
        logger.error(f"ID 조회 오류 ({table}): {e}")
        return None


# ============================================================================
# 데이터베이스 연결 초기화
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행"""
    try:
        db.create_pool()
        if db.test_connection():
            logger.info("데이터베이스 연결 성공")
    except Exception as e:
        logger.error(f"시작 시 오류 발생: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행"""
    db.close_pool()
    logger.info("애플리케이션 종료")


# ============================================================================
# 엔드포인트
# ============================================================================

@app.get("/", tags=["기본"])
async def root():
    """루트 엔드포인트"""
    return {
        "message": "질문-답변 API 서버에 오신 것을 환영합니다.",
        "version": settings.APP_VERSION
    }


@app.get("/health", response_model=HealthResponse, tags=["기본"])
async def health_check():
    """헬스 체크 엔드포인트"""
    db_connected = db.test_connection()
    return HealthResponse(
        status="healthy" if db_connected else "unhealthy",
        database_connected=db_connected,
        dify_enabled=is_dify_enabled(),
    )


@app.post("/lookup/ids", response_model=IdLookupResponse, tags=["조회"])
async def lookup_ids(request: IdLookupRequest):
    """
    ID 조회 API
    
    process_id/process_name, model_id/model_name, eqp_id/eqp_name 또는
    Dify 형식(process/model/equipment 객체)으로 ID 조회.
    
    - ID가 제공되면 그대로 반환
    - 이름만 제공되면 DB에서 ID 조회 후 반환
    """
    request_dict = request.model_dump(exclude_none=True)
    logger.info(f"[ID 조회] 요청 수신 - 전체 요청: {json.dumps(request_dict, ensure_ascii=False)}")
    
    # Process ID 처리
    process_id = None
    process_name = None
    
    # Dify 형식: process 객체
    if request.process:
        process_id = clean_request_value(request.process.id)
        process_name = clean_request_value(request.process.name)
    # 단순 형식: 직접 필드
    if not process_id:
        process_id = clean_request_value(request.process_id)
    if not process_name:
        process_name = clean_request_value(request.process_name)
    
    # Process ID 결정: ID가 있으면 사용, 없으면 이름으로 조회
    final_process_id = None
    if process_id:
        final_process_id = process_id
        logger.info(f"[ID 조회] process_id 직접 제공: {process_id}")
    elif process_name:
        final_process_id = lookup_id_by_name("PROCESS", "PROCESS_ID", "PROCESS_NAME", process_name)
        if final_process_id:
            logger.info(f"[ID 조회] process_name '{process_name}'을(를) ID '{final_process_id}'로 변환")
        else:
            logger.warning(f"[ID 조회] process_name '{process_name}'에 해당하는 ID를 찾을 수 없음")
    
    # Model ID 처리
    model_id = None
    model_name = None
    
    # Dify 형식: model 객체
    if request.model:
        model_id = clean_request_value(request.model.id)
        model_name = clean_request_value(request.model.name)
    # 단순 형식: 직접 필드
    if not model_id:
        model_id = clean_request_value(request.model_id)
    if not model_name:
        model_name = clean_request_value(request.model_name)
    
    # Model ID 결정
    final_model_id = None
    if model_id:
        final_model_id = model_id
        logger.info(f"[ID 조회] model_id 직접 제공: {model_id}")
    elif model_name:
        final_model_id = lookup_id_by_name("MODEL", "MODEL_ID", "MODEL_NAME", model_name)
        if final_model_id:
            logger.info(f"[ID 조회] model_name '{model_name}'을(를) ID '{final_model_id}'로 변환")
        else:
            logger.warning(f"[ID 조회] model_name '{model_name}'에 해당하는 ID를 찾을 수 없음")
    
    # Equipment ID 처리
    eqp_id = None
    eqp_name = None
    
    # Dify 형식: equipment 객체
    if request.equipment:
        eqp_id = clean_request_value(request.equipment.id)
        eqp_name = clean_request_value(request.equipment.name)
    # 단순 형식: 직접 필드
    if not eqp_id:
        eqp_id = clean_request_value(request.eqp_id)
    if not eqp_name:
        eqp_name = clean_request_value(request.eqp_name)
    
    # Equipment ID 결정
    final_eqp_id = None
    if eqp_id:
        final_eqp_id = eqp_id
        logger.info(f"[ID 조회] eqp_id 직접 제공: {eqp_id}")
    elif eqp_name:
        final_eqp_id = lookup_id_by_name("EQUIPMENT", "EQP_ID", "EQP_NAME", eqp_name)
        if final_eqp_id:
            logger.info(f"[ID 조회] eqp_name '{eqp_name}'을(를) ID '{final_eqp_id}'로 변환")
        else:
            logger.warning(f"[ID 조회] eqp_name '{eqp_name}'에 해당하는 ID를 찾을 수 없음")
    
    result = IdLookupResponse(
        process_id=final_process_id,
        model_id=final_model_id,
        eqp_id=final_eqp_id
    )
    
    logger.info(f"[ID 조회] 최종 결과: {result.model_dump()}")
    return result


def clean_request_value(value: Optional[str]) -> Optional[str]:
    """요청 값 정리: None, 빈 문자열, 'null' 문자열 처리"""
    if value is None:
        return None
    str_val = str(value).strip()
    if not str_val or str_val.lower() == 'null':
        return None
    return str_val


@app.post(
    "/api/v1/informnote/stats/error-code",
    response_model=ErrorCodeStatsResponse,
    tags=["통계"]
)
async def get_error_code_stats(request: ErrorCodeStatsRequest):
    """
    공정/장비 Error Code별 건수·Down Time 집계 엔드포인트
    """
    if not db.test_connection():
        raise HTTPException(status_code=503, detail="데이터베이스에 연결할 수 없습니다.")
    
    # 요청 값 정리 및 로깅
    cleaned_process_id = clean_request_value(request.process_id)
    cleaned_model_id = clean_request_value(request.model_id)
    cleaned_eqp_id = clean_request_value(request.eqp_id)
    cleaned_error_code = clean_request_value(request.error_code)
    
    logger.info(f"[Error Code 통계] 요청 수신 - process_id: {cleaned_process_id}, model_id: {cleaned_model_id}, eqp_id: {cleaned_eqp_id}, error_code: {cleaned_error_code}, group_by: {request.group_by}")
    
    try:
        # Period 처리
        if request.group_by == 'month':
            period_select = "TO_CHAR(n.down_start_time, 'YYYY-MM') AS period"
            period_group = "TO_CHAR(n.down_start_time, 'YYYY-MM')"
            period_order = "period ASC"
        elif request.group_by == 'day':
            period_select = "TO_CHAR(n.down_start_time, 'YYYY-MM-DD') AS period"
            period_group = "TO_CHAR(n.down_start_time, 'YYYY-MM-DD')"
            period_order = "period ASC"
        else:
            period_select = "NULL AS period"
            period_group = ""
            period_order = "n.process_id ASC"
        
        # GROUP BY 절 구성
        group_cols = [
            "n.process_id, p.process_name",
            "n.model_id, m.model_name",
            "n.eqp_id, e.eqp_name",
            "n.error_code, ec.error_desc"
        ]
        if period_group:
            group_cols.insert(0, period_group)
        
        # ORDER BY 절 구성
        order_cols = [
            period_order if period_group else "n.process_id ASC",
            "n.process_id ASC",
            "n.error_code ASC"
        ]
        
        # SQL 템플릿 파일 읽기 및 동적 부분 치환
        sql_template = get_sql_template("error_code_stats.sql")
        sql = sql_template.format(
            period_select=period_select,
            group_by_clause=', '.join(group_cols),
            order_by_clause=', '.join(order_cols)
        )
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, {
                "start_date": format_date_for_db(request.start_date),
                "end_date": format_date_for_db(request.end_date),
                "process_id": cleaned_process_id,
                "model_id": cleaned_model_id,
                "eqp_id": cleaned_eqp_id,
                "error_code": cleaned_error_code
            })
            
            rows = cursor.fetchall()
            cursor.close()
            
            result_list = [
                ErrorCodeStatsItem(
                    period=row[0],
                    process_id=row[1],
                    process_name=row[2],
                    model_id=row[3],
                    model_name=row[4],
                    eqp_id=row[5],
                    eqp_name=row[6],
                    error_code=row[7],
                    error_des=row[8],
                    event_cnt=row[9],
                    total_down_time_minutes=float(row[10]) if row[10] is not None else None
                )
                for row in rows
            ]
            
            logger.info(f"[Error Code 통계] 조회 결과: {len(result_list)}건")
            return ErrorCodeStatsResponse(list=result_list)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Error Code 통계] 조회 중 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"통계 조회 중 오류가 발생했습니다: {str(e)}")


@app.post(
    "/api/v1/informnote/history/pm",
    response_model=PMHistoryResponse,
    tags=["통계"]
)
async def get_pm_history(request: PMHistoryRequest):
    """
    PM(장비 점검) 이력 조회 엔드포인트 (down_type_id=0)
    """
    if not db.test_connection():
        raise HTTPException(status_code=503, detail="데이터베이스에 연결할 수 없습니다.")
    
    # 요청 값 정리 및 로깅
    cleaned_process_id = clean_request_value(request.process_id)
    cleaned_eqp_id = clean_request_value(request.eqp_id)
    cleaned_operator = clean_request_value(request.operator)
    
    logger.info(f"[PM 이력] 요청 수신 - process_id: {cleaned_process_id}, eqp_id: {cleaned_eqp_id}, operator: {cleaned_operator}, start_date: {request.start_date}, end_date: {request.end_date}, limit: {request.limit}")
    
    # SQL 템플릿 파일 읽기
    sql = get_sql_template("pm_history.sql")
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, {
                "start_date": format_date_for_db(request.start_date),
                "end_date": format_date_for_db(request.end_date),
                "process_id": cleaned_process_id,
                "eqp_id": cleaned_eqp_id,
                "operator": cleaned_operator,
                "limit_val": request.limit or 10
            })
            
            rows = cursor.fetchall()
            cursor.close()
            
            result_list = [
                PMHistoryItem(
                    down_date=row[0],
                    down_type=row[1] or "SCHEDULED",
                    down_time_minutes=float(row[2]) if row[2] is not None else 0.0,
                    operator=row[3]
                )
                for row in rows
            ]
            
            logger.info(f"[PM 이력] 조회 결과: {len(result_list)}건")
            return PMHistoryResponse(list=result_list)
    
    except Exception as e:
        logger.error(f"[PM 이력] 조회 중 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"PM 이력 조회 중 오류가 발생했습니다: {str(e)}")


@app.post(
    "/api/v1/informnote/search",
    response_model=SearchResponse,
    tags=["조회"]
)
async def search_inform_notes(request: SearchRequest):
    """
    상세 조치 내역 검색 엔드포인트
    """
    if not db.test_connection():
        raise HTTPException(status_code=503, detail="데이터베이스에 연결할 수 없습니다.")
    
    # 요청 값 정리 및 로깅
    cleaned_process_id = clean_request_value(request.process_id)
    cleaned_eqp_id = clean_request_value(request.eqp_id)
    cleaned_operator = clean_request_value(request.operator)
    
    logger.info(f"[상세 검색] 요청 수신 - process_id: {cleaned_process_id}, eqp_id: {cleaned_eqp_id}, operator: {cleaned_operator}, start_date: {request.start_date}, end_date: {request.end_date}, limit: {request.limit}")
    
    # SQL 템플릿 파일 읽기
    sql = get_sql_template("search_inform_notes.sql")
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, {
                "start_date": format_date_for_db(request.start_date),
                "end_date": format_date_for_db(request.end_date),
                "process_id": cleaned_process_id,
                "eqp_id": cleaned_eqp_id,
                "operator": cleaned_operator,
                "status_id": request.status_id,
                "limit_val": request.limit or 20
            })
            
            rows = cursor.fetchall()
            cursor.close()
            
            result_list = [
                SearchItem(
                    informnote_id=row[0],
                    down_start_time=row[1],
                    process_name=row[2],
                    eqp_name=row[3],
                    error_code=row[4],
                    error_desc=row[5],
                    act_content=row[6],
                    operator=row[7],
                    status=row[9] or ("COMPLETED" if row[8] == 1 else "IN_PROGRESS" if row[8] == 0 else "UNKNOWN")
                )
                for row in rows
            ]
            
            logger.info(f"[상세 검색] 조회 결과: {len(result_list)}건")
            return SearchResponse(list=result_list)
    
    except Exception as e:
        logger.error(f"[상세 검색] 조회 중 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"상세 조회 중 오류가 발생했습니다: {str(e)}")


@app.post("/ask", response_model=AnswerResponse, tags=["질문-답변"])
async def ask_question(request: QuestionRequest):
    """
    질문을 받고 답변을 제공하는 엔드포인트
    """
    question = request.question.strip() if request.question else ""
    context = request.context.strip() if request.context else None
    
    if not question:
        raise HTTPException(status_code=400, detail="질문이 비어있습니다.")
    
    try:
        answer = await generate_answer(question, context)
        return AnswerResponse(
            question=question,
            answer=answer,
            success=True
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[질문-답변] 오류 발생: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")


async def generate_answer(question: str, context: Optional[str] = None) -> str:
    """질문에 대한 답변 생성"""
    # Dify API 호출 시도
    if is_dify_enabled():
        try:
            return await request_answer(question, context)
        except DifyClientError as e:
            logger.warning(f"[Dify API] 실패: {e}, Oracle DB 로직으로 대체")
        except Exception as e:
            logger.error(f"[Dify API] 오류: {e}", exc_info=True)
    
    # Oracle DB 기반 답변 생성 (간단한 폴백)
    if not db.test_connection():
        return "데이터베이스에 연결할 수 없습니다."
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT SYSDATE FROM DUAL")
        result = cursor.fetchone()
        cursor.close()
    
    if "시간" in question or "날짜" in question:
        return f"현재 데이터베이스 시간: {result[0] if result else '알 수 없음'}"
    elif "연결" in question or "상태" in question:
        return "데이터베이스 연결이 정상적으로 작동하고 있습니다."
    else:
        return f"질문 '{question}'에 대한 답변을 생성했습니다. (데이터베이스 연결 확인됨)"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )
