"""
데이터 조회 API 서버
FastAPI를 사용한 REST API 엔드포인트
Dify에서 받은 입력값으로 DB를 조회하고 결과를 반환합니다.
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Tuple, Any, Dict
from datetime import date
import logging
import json
import httpx
from database import db
from config import settings
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
    description="데이터 조회 API 서버 - Dify에서 받은 입력값으로 DB를 조회하고 결과를 반환합니다."
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


class IdLookupResponse(BaseModel):
    """ID 조회 응답 모델"""
    process_id: Optional[str] = None
    model_id: Optional[str] = None
    eqp_id: Optional[str] = None


class HealthResponse(BaseModel):
    """헬스 체크 응답 모델"""
    status: str
    database_connected: bool


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


def clean_request_value(value: Optional[str]) -> Optional[str]:
    """요청 값 정리: None, 빈 문자열, 'null' 문자열 처리"""
    if value is None:
        return None
    str_val = str(value).strip()
    if not str_val or str_val.lower() == 'null':
        return None
    return str_val


def get_sql_template(filename: str) -> str:
    """SQL 템플릿 파일 읽기"""
    template_path = Path(__file__).parent / "sql_templates" / filename
    sql_content = read_sql_file(template_path)
    if not sql_content:
        logger.error(f"SQL 템플릿 파일을 읽을 수 없습니다: {template_path}")
        raise HTTPException(status_code=500, detail=f"SQL 템플릿 파일을 읽을 수 없습니다: {filename}")
    return sql_content.strip()




def lookup_id_by_id_or_name(table: str, id_col: str, name_col: str, id_value: Optional[str] = None, name_value: Optional[str] = None) -> Optional[str]:
    """테이블에서 ID 또는 NAME으로 실제 ID 조회 (OR 조건)"""
    id_val = clean_request_value(id_value)
    name_val = clean_request_value(name_value)
    
    # 둘 다 없으면 None 반환
    if not id_val and not name_val:
        return None
    
    # SQL Injection 방지: 테이블/컬럼명 화이트리스트 검증
    ALLOWED_TABLES = {'PROCESS', 'MODEL', 'EQUIPMENT'}
    ALLOWED_COLUMNS = {
        'PROCESS': {'PROCESS_ID', 'PROCESS_NAME'},
        'MODEL': {'MODEL_ID', 'MODEL_NAME'},
        'EQUIPMENT': {'EQP_ID', 'EQP_NAME'}
    }
    
    table_upper = table.upper()
    id_col_upper = id_col.upper()
    name_col_upper = name_col.upper()
    
    if table_upper not in ALLOWED_TABLES:
        logger.error(f"허용되지 않은 테이블: {table}")
        return None
    
    if id_col_upper not in ALLOWED_COLUMNS[table_upper]:
        logger.error(f"허용되지 않은 컬럼: {id_col} (테이블: {table})")
        return None
    
    if name_col_upper not in ALLOWED_COLUMNS[table_upper]:
        logger.error(f"허용되지 않은 컬럼: {name_col} (테이블: {table})")
        return None
    
    try:
        # SQL 템플릿 파일 읽기
        sql_template = get_sql_template("lookup_id.sql")
        
        # WHERE 조건 구성
        conditions = []
        params = []
        param_index = 1
        
        if id_val:
            conditions.append(f"UPPER(TRIM({id_col_upper})) = UPPER(:{param_index})")
            params.append(id_val.strip())
            param_index += 1
        
        if name_val:
            conditions.append(f"UPPER(TRIM({name_col_upper})) = UPPER(:{param_index})")
            params.append(name_val.strip())
        
        # SQL 템플릿에 동적 값 주입 (화이트리스트 검증 완료)
        query = sql_template.format(
            id_col=id_col_upper,
            name_col=name_col_upper,
            table=table_upper,
            where_conditions=' OR '.join(conditions)
        )
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            cursor.close()
            return row[0] if row else None
    except Exception as e:
        logger.error(f"ID/NAME 조회 오류 ({table}): {e}")
        return None


def extract_id_from_request(request: IdLookupRequest, entity_type: str, info_obj: Optional[BaseModel] = None) -> Tuple[Optional[str], Optional[str]]:
    """요청에서 ID와 NAME 추출 (Dify 형식 및 단순 형식 지원)"""
    id_val = None
    name_val = None
    
    # Dify 형식: 객체에서 추출
    if info_obj:
        id_val = clean_request_value(getattr(info_obj, 'id', None))
        name_val = clean_request_value(getattr(info_obj, 'name', None))
    
    # 단순 형식: 직접 필드에서 추출
    if not id_val:
        id_val = clean_request_value(getattr(request, f'{entity_type}_id', None))
    if not name_val:
        name_val = clean_request_value(getattr(request, f'{entity_type}_name', None))
    
    return id_val, name_val


def resolve_entity_id(table: str, id_col: str, name_col: str, entity_type: str, id_val: Optional[str], name_val: Optional[str]) -> Optional[str]:
    """엔티티 ID 해결 및 로깅"""
    if not id_val and not name_val:
        return None
    
    final_id = lookup_id_by_id_or_name(table, id_col, name_col, id_val, name_val)
    if final_id:
        logger.info(f"[ID 조회] {entity_type} (id={id_val}, name={name_val}) -> ID '{final_id}'")
    else:
        logger.warning(f"[ID 조회] {entity_type} (id={id_val}, name={name_val})에 해당하는 ID를 찾을 수 없음")
    
    return final_id


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
        "message": "데이터 조회 API 서버에 오신 것을 환영합니다.",
        "version": settings.APP_VERSION
    }


@app.get("/health", response_model=HealthResponse, tags=["기본"])
async def health_check():
    """헬스 체크 엔드포인트"""
    db_connected = db.test_connection()
    return HealthResponse(
        status="healthy" if db_connected else "unhealthy",
        database_connected=db_connected,
    )


@app.post("/lookup/ids", response_model=IdLookupResponse, tags=["조회"])
async def lookup_ids(request: IdLookupRequest):
    """
    ID 조회 API
    
    process_id/process_name, model_id/model_name, eqp_id/eqp_name 또는
    Dify 형식(process/model/equipment 객체)으로 ID 조회.
    
    - ID 또는 NAME을 받으면 DB에서 WHERE OR 조건으로 조회하여 실제 ID 반환
    - 조회가 안 되면 null 반환
    """
    request_dict = request.model_dump(exclude_none=True)
    logger.info(f"[ID 조회] 요청 수신 - 전체 요청: {json.dumps(request_dict, ensure_ascii=False)}")
    
    # Process ID 처리
    process_id, process_name = extract_id_from_request(request, 'process', request.process)
    final_process_id = resolve_entity_id("PROCESS", "PROCESS_ID", "PROCESS_NAME", "process", process_id, process_name)
    
    # Model ID 처리
    model_id, model_name = extract_id_from_request(request, 'model', request.model)
    final_model_id = resolve_entity_id("MODEL", "MODEL_ID", "MODEL_NAME", "model", model_id, model_name)
    
    # Equipment ID 처리
    eqp_id, eqp_name = extract_id_from_request(request, 'eqp', request.equipment)
    final_eqp_id = resolve_entity_id("EQUIPMENT", "EQP_ID", "EQP_NAME", "equipment", eqp_id, eqp_name)
    
    result = IdLookupResponse(
        process_id=final_process_id,
        model_id=final_model_id,
        eqp_id=final_eqp_id
    )
    
    logger.info(f"[ID 조회] 최종 결과: {result.model_dump()}")
    return result


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
    
    # 요청 값 정리
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
    
    # 요청 값 정리
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
    
    # 요청 값 정리
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


# ============================================================================
# Dify 프록시 엔드포인트 (Vercel 미국 서버 → 로컬 한국 IP → Dify 한국 서버)
# ============================================================================

class DifyProxyRequest(BaseModel):
    """Dify 프록시 요청 모델"""
    url: str = Field(..., description="Dify API URL")
    apiKey: str = Field(..., description="Dify API Key")
    appType: Optional[str] = Field("chatbot", description="앱 타입: chatbot, workflow, completion")
    authHeaderType: Optional[str] = Field("bearer", description="인증 헤더 타입: bearer, api-key, x-api-key")
    payload: Dict[str, Any] = Field(..., description="Dify API 요청 payload")


@app.post("/proxy/dify")
async def proxy_dify(request: DifyProxyRequest):
    """
    Dify API 프록시 엔드포인트
    
    Vercel(미국)에서 직접 Dify(한국)에 접근할 수 없을 때,
    로컬 서버(한국 IP)를 통해 프록시하여 접근합니다.
    """
    logger.info(f"[Dify Proxy] 요청 수신 - URL: {request.url}, 앱 타입: {request.appType}")
    
    # API Key 정리
    clean_api_key = request.apiKey.strip().replace(" ", "")
    
    if not clean_api_key:
        raise HTTPException(status_code=400, detail="API Key가 비어있습니다.")
    
    # URL 정리
    clean_url = request.url.strip().rstrip("/,; ")
    
    # 엔드포인트가 없으면 추가
    if not any(ep in clean_url for ep in ["/chat-messages", "/workflows/run", "/completion-messages"]):
        # /v1 추가
        if not clean_url.endswith("/v1"):
            if ":" in clean_url.split("/")[-1]:  # 포트 번호가 있는 경우
                clean_url = f"{clean_url}/v1"
            elif "/" not in clean_url[8:]:  # 프로토콜 이후 경로가 없는 경우
                clean_url = f"{clean_url}/v1"
        
        # 엔드포인트 추가
        app_type = request.appType or "chatbot"
        if app_type == "workflow":
            clean_url = f"{clean_url}/workflows/run"
        elif app_type == "completion":
            clean_url = f"{clean_url}/completion-messages"
        else:
            clean_url = f"{clean_url}/chat-messages"
    
    # 인증 헤더 생성
    auth_header_type = request.authHeaderType or "bearer"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Dify-Proxy/1.0",
    }
    
    if auth_header_type == "api-key":
        headers["Authorization"] = f"Api-Key {clean_api_key}"
    elif auth_header_type == "x-api-key":
        headers["X-Api-Key"] = clean_api_key
    else:  # bearer (기본)
        headers["Authorization"] = f"Bearer {clean_api_key}"
    
    logger.info(f"[Dify Proxy] 최종 URL: {clean_url}")
    logger.info(f"[Dify Proxy] 인증 헤더 타입: {auth_header_type}")
    logger.info(f"[Dify Proxy] Payload: {json.dumps(request.payload, ensure_ascii=False)[:200]}...")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                clean_url,
                headers=headers,
                json=request.payload
            )
            
            logger.info(f"[Dify Proxy] 응답 상태: {response.status_code}")
            
            # 응답 텍스트 가져오기
            response_text = response.text
            
            # HTML 응답 체크
            if response_text.strip().startswith(("<!DOCTYPE", "<html", "<!doctype")):
                logger.error(f"[Dify Proxy] HTML 응답 감지")
                return JSONResponse(
                    status_code=response.status_code or 500,
                    content={"error": "Dify 서버에서 HTML 페이지를 반환했습니다. URL을 확인하세요."}
                )
            
            # JSON 파싱 시도
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response_text[:500]}
            
            if not response.is_success:
                logger.error(f"[Dify Proxy] 오류 응답: {response_text[:500]}")
                return JSONResponse(
                    status_code=response.status_code,
                    content={"error": response_data.get("message") or response_data.get("error") or response_text[:200]}
                )
            
            logger.info(f"[Dify Proxy] 성공 응답")
            return JSONResponse(content=response_data)
            
    except httpx.TimeoutException:
        logger.error("[Dify Proxy] 타임아웃")
        raise HTTPException(status_code=504, detail="Dify 서버 응답 타임아웃 (60초 초과)")
    except httpx.ConnectError as e:
        logger.error(f"[Dify Proxy] 연결 오류: {e}")
        raise HTTPException(status_code=502, detail=f"Dify 서버에 연결할 수 없습니다: {str(e)}")
    except Exception as e:
        logger.error(f"[Dify Proxy] 예외: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"프록시 오류: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )
