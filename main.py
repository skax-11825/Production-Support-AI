"""
질문-답변 API 서버
FastAPI를 사용한 REST API 엔드포인트
"""
from fastapi import FastAPI, HTTPException, Depends, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import date
import logging
import json
from database import db
from config import settings
from dify_client import (
    is_dify_enabled,
    request_answer,
    DifyClientError,
)

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
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 요청/응답 모델
class QuestionRequest(BaseModel):
    """질문 요청 모델"""
    question: Optional[str] = ""
    context: Optional[str] = None  # 추가 컨텍스트 정보 (선택사항)


class AnswerResponse(BaseModel):
    """답변 응답 모델"""
    answer: str
    question: str
    success: bool


class HealthResponse(BaseModel):
    """헬스 체크 응답 모델"""
    status: str
    database_connected: bool
    dify_enabled: bool


class ErrorCodeStatsItem(BaseModel):
    """Error Code 통계 아이템 모델"""
    period: Optional[str] = None  # 기간 (월별/일별 집계 시 사용)
    process_id: Optional[str] = None
    process_name: Optional[str] = None
    eqp_id: Optional[str] = None
    eqp_name: Optional[str] = None
    model_id: Optional[str] = None
    model_name: Optional[str] = None
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
    group_by: Optional[str] = "error_code"  # 'error_code'(기본), 'month', 'day'


class PMHistoryItem(BaseModel):
    """PM(점검) 이력 아이템 모델"""
    down_date: str  # 다운(점검) 시작 날짜 (YYYY-MM-DD)
    down_type: str  # 다운 유형 이름 (SCHEDULED 등)
    down_time_minutes: float


class PMHistoryResponse(BaseModel):
    """PM 이력 응답 모델"""
    list: List[PMHistoryItem]


class PMHistoryRequest(BaseModel):
    """PM 이력 요청 모델"""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    process_id: Optional[str] = None
    eqp_id: Optional[str] = None
    limit: Optional[int] = 10  # 최근 N건 조회 (기본값 10)


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
    status: str  # "IN_PROGRESS" or "COMPLETED"


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
    status_id: Optional[int] = None  # 0: IN_PROGRESS, 1: COMPLETED
    limit: Optional[int] = 20


# 데이터베이스 연결 초기화
@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행"""
    try:
        db.create_pool()
        if db.test_connection():
            logger.info("데이터베이스 연결 성공")
        else:
            logger.warning("데이터베이스 연결 테스트 실패")
    except Exception as e:
        logger.error(f"시작 시 오류 발생: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행"""
    db.close_pool()
    logger.info("애플리케이션 종료")


# 엔드포인트
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


@app.post(
    "/api/v1/informnote/stats/error-code",
    response_model=ErrorCodeStatsResponse,
    tags=["통계"]
)
async def get_error_code_stats(request: ErrorCodeStatsRequest):
    """
    공정/장비 Error Code별 건수·Down Time 집계 엔드포인트
    
    - **start_date**: 조회 시작일 (선택)
    - **end_date**: 조회 종료일 (선택)
    - **process_id**: 공정 ID (선택)
    - **model_id**: 장비 모델 ID (선택)
    - **eqp_id**: 장비 ID (선택)
    - **error_code**: 에러 코드 (선택)
    - **group_by**: 집계 기준 ('error_code', 'month', 'day'). 기본값은 'error_code'
    """
    # 요청 파라미터 JSON 로깅
    request_params = request.model_dump()
    # date 객체는 JSON 직렬화가 안되므로 문자열로 변환
    if request_params.get("start_date"):
        request_params["start_date"] = str(request_params["start_date"])
    if request_params.get("end_date"):
        request_params["end_date"] = str(request_params["end_date"])
        
    logger.info(f"[Error Code 통계] 요청 파라미터:\n{json.dumps(request_params, indent=2, ensure_ascii=False)}")
    
    try:
        # 데이터베이스 연결 확인
        if not db.test_connection():
            logger.error("[Error Code 통계] 데이터베이스 연결 실패")
            raise HTTPException(status_code=503, detail="데이터베이스에 연결할 수 없습니다.")
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. 기본 컬럼 정의 (항상 조회 및 그룹핑 대상이 될 수 있는 후보들)
            # (컬럼명, 셀렉트절 표현식, 그룹바이절 표현식, 필수여부)
            columns_map = {
                'process': ('process_id', 'n.process_id', 'p.process_name', 'n.process_id, p.process_name'),
                'model': ('model_id', 'n.model_id', 'm.model_name', 'n.model_id, m.model_name'),
                'eqp': ('eqp_id', 'n.eqp_id', 'e.eqp_name', 'n.eqp_id, e.eqp_name'),
                'error': ('error_code', 'n.error_code', 'ec.error_desc', 'n.error_code, ec.error_desc'),
            }
            
            # 2. 동적 쿼리 구성을 위한 리스트
            select_items = []
            group_by_items = []
            order_by_items = []
            
            # 3. 기간(Period) 처리
            if request.group_by == 'month':
                select_items.append("TO_CHAR(n.down_start_time, 'YYYY-MM') AS period")
                group_by_items.append("TO_CHAR(n.down_start_time, 'YYYY-MM')")
                order_by_items.append("period ASC")
            elif request.group_by == 'day':
                select_items.append("TO_CHAR(n.down_start_time, 'YYYY-MM-DD') AS period")
                group_by_items.append("TO_CHAR(n.down_start_time, 'YYYY-MM-DD')")
                order_by_items.append("period ASC")
            else:
                select_items.append("NULL AS period")
            
            # 4. 차원(Dimension) 처리 - 요청에 값이 있거나 group_by에 포함된 경우만 선택
            # Process는 필수라고 가정 (항상 포함)
            select_items.extend(["n.process_id", "p.process_name"])
            group_by_items.append(columns_map['process'][3])
            order_by_items.append("n.process_id")

            # Model (request에 있거나, group_by가 'eqp' 이상 상세 레벨일 때 포함)
            # group_by가 'process'일 때는 제외
            if request.model_id or request.group_by in ['eqp', 'error_code', 'model'] or (request.group_by not in ['process', 'month', 'day']):
                select_items.extend(["n.model_id", "m.model_name"])
                group_by_items.append(columns_map['model'][3])
                order_by_items.append("n.model_id")
            else:
                select_items.extend(["NULL AS model_id", "NULL AS model_name"])

            # Equipment (request에 있거나, group_by가 'eqp' 이상 상세 레벨일 때 포함)
            if request.eqp_id or request.group_by in ['eqp', 'error_code'] or (request.group_by not in ['process', 'month', 'day', 'model']):
                select_items.extend(["n.eqp_id", "e.eqp_name"])
                group_by_items.append(columns_map['eqp'][3])
                order_by_items.append("n.eqp_id")
            else:
                select_items.extend(["NULL AS eqp_id", "NULL AS eqp_name"])
                
            # Error Code (request에 있거나, group_by가 'error_code'인 경우)
            # group_by가 'process', 'eqp', 'model' 일 때는 제외
            if request.error_code or request.group_by == 'error_code' or (request.group_by not in ['process', 'eqp', 'model', 'month', 'day']):
                select_items.extend(["n.error_code", "ec.error_desc AS error_des"])
                group_by_items.append(columns_map['error'][3])
                order_by_items.append("n.error_code")
            else:
                select_items.extend(["NULL AS error_code", "NULL AS error_des"])

            # 5. SQL 조합
            select_clause = ",\n                    ".join(select_items)
            group_by_clause = ",\n                    ".join(group_by_items)
            order_by_clause = ", ".join(order_by_items)
            
            sql = f"""
                SELECT
                    {select_clause},
                    COUNT(*) AS event_cnt,
                    SUM(n.down_time_minutes) AS total_down_time_minutes
                FROM INFORM_NOTE n
                LEFT JOIN PROCESS p ON n.process_id = p.process_id
                LEFT JOIN EQUIPMENT e ON n.eqp_id = e.eqp_id
                LEFT JOIN MODEL m ON n.model_id = m.model_id
                LEFT JOIN ERROR_CODE ec ON n.error_code = ec.error_code
                WHERE (:start_date IS NULL OR n.down_start_time >= TO_DATE(:start_date, 'YYYY-MM-DD'))
                  AND (:end_date IS NULL OR n.down_start_time < TO_DATE(:end_date, 'YYYY-MM-DD') + 1)
                  AND (:process_id IS NULL OR n.process_id = :process_id)
                  AND (:model_id IS NULL OR n.model_id = :model_id)
                  AND (:eqp_id IS NULL OR n.eqp_id = :eqp_id)
                  AND (:error_code IS NULL OR n.error_code = :error_code)
                  AND n.down_type_id = 1
                GROUP BY
                    {group_by_clause}
                ORDER BY
                    {order_by_clause}
            """
            
            final_sql = sql # 이미 f-string으로 완성됨
            start_date_str = request.start_date.strftime('%Y-%m-%d') if request.start_date else None
            end_date_str = request.end_date.strftime('%Y-%m-%d') if request.end_date else None
            
            # 쿼리 실행
            cursor.execute(final_sql, {
                "start_date": start_date_str,
                "end_date": end_date_str,
                "process_id": request.process_id,
                "model_id": request.model_id,
                "eqp_id": request.eqp_id,
                "error_code": request.error_code
            })
            
            # 결과 조회
            rows = cursor.fetchall()
            cursor.close()
            
            # 결과를 응답 모델로 변환
            result_list = []
            for row in rows:
                result_list.append(ErrorCodeStatsItem(
                    period=row[0],
                    process_id=row[1],
                    process_name=row[2],
                    model_id=row[3],    # 순서 주의: SELECT 순서 변경됨 (Process -> Model -> Eqp -> Error)
                    model_name=row[4],
                    eqp_id=row[5],
                    eqp_name=row[6],
                    error_code=row[7],
                    error_des=row[8],
                    event_cnt=row[9],
                    total_down_time_minutes=float(row[10]) if row[10] is not None else None
                ))
            
            # 응답 데이터 JSON 로깅
            response_content = [item.model_dump() for item in result_list]
            logger.info(f"[Error Code 통계] 응답 데이터 ({len(result_list)}건):\n{json.dumps(response_content, indent=2, ensure_ascii=False)}")
            
            return ErrorCodeStatsResponse(list=result_list)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Error Code 통계] 조회 중 오류 발생: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"통계 조회 중 오류가 발생했습니다: {str(e)}")


@app.post(
    "/api/v1/informnote/history/pm",
    response_model=PMHistoryResponse,
    tags=["통계"]
)
async def get_pm_history(request: PMHistoryRequest):
    """
    PM(장비 점검) 이력 조회 엔드포인트 (down_type_id=0)
    
    - **start_date**: 조회 시작일 (선택)
    - **end_date**: 조회 종료일 (선택)
    - **process_id**: 공정 ID (선택)
    - **eqp_id**: 장비 ID (선택)
    - **limit**: 조회할 최대 건수 (기본값 10, 최근 순)
    """
    # 요청 파라미터 JSON 로깅
    request_params = request.model_dump()
    if request_params.get("start_date"):
        request_params["start_date"] = str(request_params["start_date"])
    if request_params.get("end_date"):
        request_params["end_date"] = str(request_params["end_date"])
        
    logger.info(f"[PM 이력] 요청 파라미터:\n{json.dumps(request_params, indent=2, ensure_ascii=False)}")
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            sql = """
                SELECT
                    TO_CHAR(n.down_start_time, 'YYYY-MM-DD') as down_date,
                    dt.down_type_name,
                    n.down_time_minutes
                FROM INFORM_NOTE n
                LEFT JOIN DOWN_TYPE dt ON n.down_type_id = dt.down_type_id
                WHERE (:start_date IS NULL OR n.down_start_time >= TO_DATE(:start_date, 'YYYY-MM-DD'))
                  AND (:end_date IS NULL OR n.down_start_time < TO_DATE(:end_date, 'YYYY-MM-DD') + 1)
                  AND (:process_id IS NULL OR n.process_id = :process_id)
                  AND (:eqp_id IS NULL OR n.eqp_id = :eqp_id)
                  AND n.down_type_id = 0  -- PM(SCHEDULED)만 조회
                ORDER BY n.down_start_time DESC
                FETCH FIRST :limit_val ROWS ONLY
            """
            
            start_date_str = request.start_date.strftime('%Y-%m-%d') if request.start_date else None
            end_date_str = request.end_date.strftime('%Y-%m-%d') if request.end_date else None
            
            # limit 값이 없으면 기본값 사용 (물론 모델에서 기본값이 있지만 안전장치)
            limit_val = request.limit if request.limit else 10
            
            cursor.execute(sql, {
                "start_date": start_date_str,
                "end_date": end_date_str,
                "process_id": request.process_id,
                "eqp_id": request.eqp_id,
                "limit_val": limit_val
            })
            
            rows = cursor.fetchall()
            cursor.close()
            
            result_list = []
            for row in rows:
                result_list.append(PMHistoryItem(
                    down_date=row[0],
                    down_type=row[1] if row[1] else "SCHEDULED",
                    down_time_minutes=float(row[2]) if row[2] is not None else 0.0
                ))
            
            logger.info(f"[PM 이력] 조회 결과: {len(result_list)}건")
            return PMHistoryResponse(list=result_list)

    except Exception as e:
        logger.error(f"[PM 이력] 조회 중 오류 발생: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"PM 이력 조회 중 오류가 발생했습니다: {str(e)}")


@app.post(
    "/api/v1/informnote/search",
    response_model=SearchResponse,
    tags=["조회"]
)
async def search_inform_notes(request: SearchRequest):
    """
    상세 조치 내역 검색 엔드포인트
    
    - **operator**: 작업자 이름 (선택)
    - **status_id**: 상태 (0: 진행중, 1: 완료) (선택)
    - **process_id**: 공정 ID (선택)
    - **eqp_id**: 장비 ID (선택)
    """
    request_params = request.model_dump()
    if request_params.get("start_date"):
        request_params["start_date"] = str(request_params["start_date"])
    if request_params.get("end_date"):
        request_params["end_date"] = str(request_params["end_date"])
        
    logger.info(f"[상세 검색] 요청 파라미터:\n{json.dumps(request_params, indent=2, ensure_ascii=False)}")
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            sql = """
                SELECT
                    n.informnote_id,
                    TO_CHAR(n.down_start_time, 'YYYY-MM-DD HH24:MI:SS') as down_start_time,
                    p.process_name,
                    e.eqp_name,
                    n.error_code,
                    ec.error_desc,
                    n.act_content,
                    n.operator,
                    n.status_id,
                    s.status_name
                FROM INFORM_NOTE n
                LEFT JOIN PROCESS p ON n.process_id = p.process_id
                LEFT JOIN EQUIPMENT e ON n.eqp_id = e.eqp_id
                LEFT JOIN ERROR_CODE ec ON n.error_code = ec.error_code
                LEFT JOIN STATUS s ON n.status_id = s.status_id
                WHERE (:start_date IS NULL OR n.down_start_time >= TO_DATE(:start_date, 'YYYY-MM-DD'))
                  AND (:end_date IS NULL OR n.down_start_time < TO_DATE(:end_date, 'YYYY-MM-DD') + 1)
                  AND (:process_id IS NULL OR n.process_id = :process_id)
                  AND (:eqp_id IS NULL OR n.eqp_id = :eqp_id)
                  AND (:operator IS NULL OR n.operator = :operator)
                  AND (:status_id IS NULL OR n.status_id = :status_id)
                ORDER BY n.down_start_time DESC
                FETCH FIRST :limit_val ROWS ONLY
            """
            
            start_date_str = request.start_date.strftime('%Y-%m-%d') if request.start_date else None
            end_date_str = request.end_date.strftime('%Y-%m-%d') if request.end_date else None
            limit_val = request.limit if request.limit else 20
            
            cursor.execute(sql, {
                "start_date": start_date_str,
                "end_date": end_date_str,
                "process_id": request.process_id,
                "eqp_id": request.eqp_id,
                "operator": request.operator,
                "status_id": request.status_id,
                "limit_val": limit_val
            })
            
            rows = cursor.fetchall()
            cursor.close()
            
            result_list = []
            for row in rows:
                # status_name이 있으면 쓰고, 없으면 status_id로 추론 (0: IN_PROGRESS, 1: COMPLETED)
                status_str = row[9]
                if not status_str:
                    status_str = "COMPLETED" if row[8] == 1 else "IN_PROGRESS" if row[8] == 0 else "UNKNOWN"
                
                result_list.append(SearchItem(
                    informnote_id=row[0],
                    down_start_time=row[1],
                    process_name=row[2],
                    eqp_name=row[3],
                    error_code=row[4],
                    error_desc=row[5],
                    act_content=row[6],
                    operator=row[7],
                    status=status_str
                ))
            
            logger.info(f"[상세 검색] 조회 결과: {len(result_list)}건")
            return SearchResponse(list=result_list)

    except Exception as e:
        logger.error(f"[상세 검색] 조회 중 오류 발생: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"상세 조회 중 오류가 발생했습니다: {str(e)}")


@app.post("/ask", response_model=AnswerResponse, tags=["질문-답변"])
async def ask_question(request: QuestionRequest, http_request: Request):
    """
    질문을 받고 답변을 제공하는 엔드포인트
    
    Dify 워크플로우에서 HTTP Request 노드를 통해 호출됩니다.
    
    - **question**: 사용자의 질문 (Dify에서 전달된 input 변수)
    - **context**: 추가 컨텍스트 정보 (선택사항)
    """
    try:
        # 1단계: 요청 정보 로깅
        logger.info("=" * 80)
        logger.info("[Dify 워크플로우 요청 수신]")
        logger.info(f"요청 URL: {http_request.url}")
        logger.info(f"요청 Method: {http_request.method}")
        
        # 원본 요청 본문 로깅
        try:
            body = await http_request.body()
            body_str = body.decode('utf-8') if body else 'empty'
            logger.info(f"원본 요청 Body: {body_str}")
        except Exception as e:
            logger.warning(f"요청 Body 읽기 실패: {e}")
        
        # 파싱된 요청 정보
        question = request.question.strip() if request.question else ""
        context = request.context.strip() if request.context else None
        
        logger.info(f"파싱된 질문: {question}")
        logger.info(f"파싱된 컨텍스트: {context}")
        
        # 2단계: 입력 검증
        if not question:
            logger.error("[오류] 질문이 비어있습니다.")
            logger.error(f"요청 전체 내용: {request.model_dump()}")
            raise HTTPException(status_code=400, detail="질문이 비어있습니다.")
        
        # 3단계: 답변 생성 시작
        logger.info(f"[답변 생성 시작] 질문: '{question}'")
        answer = await generate_answer(question, context)
        
        # 4단계: 응답 반환
        logger.info(f"[답변 생성 완료] 답변 길이: {len(answer)} 문자")
        logger.info("=" * 80)
        
        return AnswerResponse(
            question=question,
            answer=answer,
            success=True
        )
    
    except HTTPException:
        # HTTP 예외는 그대로 전달
        raise
    except Exception as e:
        # 예상치 못한 오류 처리
        logger.error("=" * 80)
        logger.error(f"[치명적 오류] 질문 처리 중 예외 발생")
        logger.error(f"오류 메시지: {str(e)}")
        logger.error(f"오류 타입: {type(e).__name__}")
        logger.error(f"요청 정보: {request.model_dump() if hasattr(request, 'model_dump') else str(request)}")
        logger.error("=" * 80, exc_info=True)
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")


async def generate_answer(question: str, context: Optional[str] = None) -> str:
    """
    질문에 대한 답변 생성
    
    처리 순서:
    1. Dify API 호출 (설정된 경우)
    2. Oracle DB 기반 답변 생성 (Dify 실패 시 또는 Dify 미설정 시)
    """
    logger.info(f"[답변 생성] 시작 - 질문: '{question[:50]}...' (전체 길이: {len(question)})")
    
    # 1단계: Dify API 호출 시도
    if is_dify_enabled():
        logger.info("[Dify API 호출] Dify 연동이 활성화되어 있습니다.")
        logger.info(f"[Dify API 호출] Dify API Base: {settings.DIFY_API_BASE}")
        try:
            logger.info("[Dify API 호출] Dify API로 답변 요청 중...")
            answer = await request_answer(question, context)
            logger.info(f"[Dify API 호출] 성공! 답변 길이: {len(answer)} 문자")
            logger.info(f"[Dify API 호출] 답변 미리보기: {answer[:100]}...")
            return answer
        except DifyClientError as exc:
            logger.warning(f"[Dify API 호출] 실패: {exc}")
            logger.info("[Dify API 호출] Oracle DB 로직으로 대체합니다.")
        except Exception as exc:
            logger.error(f"[Dify API 호출] 예상치 못한 오류: {exc}", exc_info=True)
            logger.info("[Dify API 호출] Oracle DB 로직으로 대체합니다.")
    else:
        logger.info("[Dify API 호출] Dify 연동이 비활성화되어 있습니다.")
        logger.info("[Dify API 호출] Oracle DB 로직을 사용합니다.")

    # 2단계: Oracle DB 기반 답변 생성 (Dify 실패 시 또는 Dify 미설정 시)
    logger.info("[Oracle DB] 데이터베이스 기반 답변 생성 시작")
    try:
        # 데이터베이스 연결 확인
        if not db.test_connection():
            logger.error("[Oracle DB] 데이터베이스 연결 실패")
            return "데이터베이스에 연결할 수 없습니다. 시스템 관리자에게 문의하세요."
        
        logger.info("[Oracle DB] 데이터베이스 연결 성공")
        
        # 데이터베이스에서 관련 정보 조회
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 예시: 질문을 로그에 저장하거나 관련 데이터 조회
            # 실제 구현에 맞게 수정 필요
            cursor.execute("SELECT SYSDATE FROM DUAL")
            result = cursor.fetchone()
            cursor.close()
            
            logger.info(f"[Oracle DB] 데이터 조회 완료: {result}")
            
            # 간단한 답변 생성 (실제로는 더 복잡한 로직 필요)
            if "시간" in question or "날짜" in question:
                answer = f"현재 데이터베이스 시간: {result[0] if result else '알 수 없음'}"
            elif "연결" in question or "상태" in question:
                answer = "데이터베이스 연결이 정상적으로 작동하고 있습니다."
            else:
                answer = f"질문 '{question}'에 대한 답변을 생성했습니다. (데이터베이스 연결 확인됨)"
            
            logger.info(f"[Oracle DB] 답변 생성 완료: {answer[:100]}...")
            return answer
    
    except Exception as e:
        logger.error(f"[Oracle DB] 답변 생성 중 오류: {e}", exc_info=True)
        error_msg = f"질문을 처리하는 중 오류가 발생했습니다: {str(e)}"
        logger.error(f"[Oracle DB] 오류 메시지 반환: {error_msg}")
        return error_msg


if __name__ == "__main__":
    import uvicorn
    
    # ngrok 설정을 위한 환경변수 또는 플래그 확인이 좋겠지만, 
    # 사용자 요청에 따라 직접 통합합니다.
    try:
        from pyngrok import ngrok
        
        # ngrok 터널 생성 (포트 8000)
        # 주의: 최초 실행 시 ngrok 바이너리가 설치됩니다.
        # ngrok auth token이 설정되어 있지 않으면 세션 만료 시간이 있을 수 있습니다.
        public_url = ngrok.connect(8000).public_url
        logger.info(f"ngrok tunnel opened: {public_url} -> http://localhost:8000")
        print(f"\n[ngrok] Public URL: {public_url}\n")
        
    except Exception as e:
        logger.warning(f"ngrok 실행 실패: {e}")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False  # ngrok 안정성을 위해 리로드 비활성화
    )
