"""
질문-답변 API 서버
FastAPI를 사용한 REST API 엔드포인트
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import date
import logging
import json
from database import db
from config import settings
from dify_client import is_dify_enabled, request_answer, DifyClientError

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


class IdLookupRequest(BaseModel):
    """ID 조회 요청 모델"""
    process_name: Optional[str] = None
    model_name: Optional[str] = None
    eqp_name: Optional[str] = None
    proc_keyword: Optional[str] = None
    model_keyword: Optional[str] = None
    eqp_keyword: Optional[str] = None
    text: Optional[str] = None
    structured_output: Optional[dict] = None


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


def extract_keyword_from_dify(request: IdLookupRequest) -> Dict[str, Optional[str]]:
    """Dify 구조화 출력에서 키워드 추출"""
    extracted = {}
    
    # structured_output에서 추출
    if request.structured_output:
        if isinstance(request.structured_output, dict):
            extracted.update(request.structured_output)
        else:
            logger.warning(f"[키워드 추출] structured_output이 dict가 아님: {type(request.structured_output)}")
    
    # text 필드가 JSON 문자열인 경우 파싱
    if request.text:
        try:
            text_content = request.text.strip()
            # null 문자열 제거
            if text_content.lower() == 'null' or not text_content:
                logger.debug("[키워드 추출] text 필드가 null이거나 비어있음")
            else:
                parsed = json.loads(text_content)
                if isinstance(parsed, dict):
                    extracted.update(parsed)
                else:
                    logger.warning(f"[키워드 추출] text 필드 파싱 결과가 dict가 아님: {type(parsed)}")
        except json.JSONDecodeError as e:
            logger.warning(f"[키워드 추출] text 필드 JSON 파싱 실패: {e}, 원본: {request.text[:100]}")
        except Exception as e:
            logger.warning(f"[키워드 추출] text 필드 처리 중 오류: {e}")
    
    # 최종 매핑: keyword > name > extracted
    result = {}
    
    def clean_value(value):
        """값 정리: None, 빈 문자열, 'null' 문자열, 변수 참조 패턴 처리"""
        if value is None:
            return None
        str_val = str(value).strip()
        if not str_val or str_val.lower() == 'null':
            return None
        
        # OR 연산자(||)로 분리되어 있는 경우 처리
        if '||' in str_val:
            parts = [part.strip() for part in str_val.split('||')]
            # 변수 참조가 아닌 실제 값만 추출
            for part in parts:
                if part and not is_variable_reference(part):
                    logger.info(f"[키워드 추출] OR 연산자에서 실제 값 추출: '{part}' (전체: '{str_val}')")
                    return part
            # 모두 변수 참조인 경우
            logger.warning(f"[키워드 추출] OR 연산자로 분리된 값이 모두 변수 참조: {str_val}")
            return None
        
        # 변수 참조 패턴 확인
        if is_variable_reference(str_val):
            logger.warning(f"[키워드 추출] 변수 참조 패턴 감지, 무시: {str_val}")
            return None
        
        return str_val
    
    def is_variable_reference(value: str) -> bool:
        """변수 참조 패턴인지 확인"""
        if not value or not isinstance(value, str):
            return False
        value_lower = value.lower().strip()
        # 변수 참조 패턴: 숫자.structured_output.keyword 또는 .keyword, .output 등
        if '.' in value_lower:
            # 점(.)으로 시작하거나, 숫자.xxx.xxx 패턴
            if value_lower.startswith('.') or (
                any(char.isdigit() for char in value_lower[:10]) and 
                any(kw in value_lower for kw in ['structured_output', 'keyword', 'output', 'variable'])
            ):
                return True
        return False
    
    # process_name 매핑
    process_value = (
        clean_value(extracted.get('proc_keyword')) or
        clean_value(getattr(request, 'proc_keyword', None)) or
        clean_value(extracted.get('process_name')) or
        clean_value(getattr(request, 'process_name', None))
    )
    result['process_name'] = process_value
    
    # model_name 매핑
    model_value = (
        clean_value(extracted.get('model_keyword')) or
        clean_value(getattr(request, 'model_keyword', None)) or
        clean_value(extracted.get('model_name')) or
        clean_value(getattr(request, 'model_name', None))
    )
    result['model_name'] = model_value
    
    # eqp_name 매핑
    eqp_value = (
        clean_value(extracted.get('eqp_keyword')) or
        clean_value(getattr(request, 'eqp_keyword', None)) or
        clean_value(extracted.get('eqp_name')) or
        clean_value(getattr(request, 'eqp_name', None))
    )
    result['eqp_name'] = eqp_value
    
    logger.info(f"[키워드 추출] 최종 결과: {result}")
    return result


def lookup_id_by_name(table: str, id_col: str, name_col: str, search_value: str) -> Optional[str]:
    """테이블에서 이름으로 ID 조회"""
    if not search_value:
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
            cursor.execute(query, [search_value, search_value])
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
    
    process_name, model_name, eqp_name 또는 proc_keyword, model_keyword, eqp_keyword 중
    하나 이상을 입력받아 해당하는 ID 값을 반환합니다.
    """
    # 디버깅: 요청 본문 전체 로깅
    request_dict = request.model_dump(exclude_none=True)
    logger.info(f"[ID 조회] 요청 수신 - 전체 요청: {json.dumps(request_dict, ensure_ascii=False)}")
    
    keywords = extract_keyword_from_dify(request)
    logger.info(f"[ID 조회] 추출된 keywords: {keywords}")
    
    # 키워드가 모두 None인 경우 경고
    if not any(keywords.values()):
        logger.warning(f"[ID 조회] 모든 키워드가 None입니다. 원본 요청: {request_dict}")
    
    result = IdLookupResponse(
        process_id=lookup_id_by_name("PROCESS", "PROCESS_ID", "PROCESS_NAME", keywords.get("process_name")),
        model_id=lookup_id_by_name("MODEL", "MODEL_ID", "MODEL_NAME", keywords.get("model_name")),
        eqp_id=lookup_id_by_name("EQUIPMENT", "EQP_ID", "EQP_NAME", keywords.get("eqp_name"))
    )
    
    logger.info(f"[ID 조회] 최종 결과: {result.model_dump()}")
    return result


def clean_request_value(value: Optional[str], field_name: str = "") -> Optional[str]:
    """요청 값 정리: 변수 참조 패턴, null 문자열 처리"""
    if value is None:
        return None
    str_val = str(value).strip()
    if not str_val or str_val.lower() == 'null':
        return None
    # Dify 변수 참조 패턴 감지 ({{ ... }} 또는 http7.response.xxx)
    if '{{' in str_val or '}}' in str_val or 'http' in str_val.lower() or '.response.' in str_val.lower():
        logger.warning(f"[요청 값 정리] {field_name} 필드에 변수 참조 패턴 감지, 무시: {str_val}")
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
    cleaned_process_id = clean_request_value(request.process_id, "process_id")
    cleaned_model_id = clean_request_value(request.model_id, "model_id")
    cleaned_eqp_id = clean_request_value(request.eqp_id, "eqp_id")
    cleaned_error_code = clean_request_value(request.error_code, "error_code")
    
    logger.info(f"[Error Code 통계] 요청 수신 - process_id: {cleaned_process_id}, model_id: {cleaned_model_id}, eqp_id: {cleaned_eqp_id}, error_code: {cleaned_error_code}, group_by: {request.group_by}")
    
    # error_code 필드에 장비명이나 공정명이 들어온 경우 감지
    if cleaned_error_code:
        # 장비명 패턴 (ASML_PH_#001, M14-PH-001 등)
        if 'ASML' in cleaned_error_code.upper() or 'M14-' in cleaned_error_code or '#' in cleaned_error_code:
            logger.warning(f"[Error Code 통계] error_code 필드에 장비명이 들어옴: {cleaned_error_code}, None으로 처리")
            cleaned_error_code = None
        # 공정명 패턴 (Cleaning, CMP 등)
        elif cleaned_error_code.upper() in ['CLEANING', 'CMP', 'DIFFUSION', 'ETCH', 'PHOTOLITHOGRAPHY']:
            logger.warning(f"[Error Code 통계] error_code 필드에 공정명이 들어옴: {cleaned_error_code}, None으로 처리")
            cleaned_error_code = None
    
    # 모든 필터가 None인 경우 경고 (전체 데이터 조회됨)
    if not any([cleaned_process_id, cleaned_model_id, cleaned_eqp_id, cleaned_error_code, request.start_date, request.end_date]):
        logger.warning(f"[Error Code 통계] 모든 필터가 None입니다. 전체 데이터 조회됩니다. (원본 요청: process_id={request.process_id}, error_code={request.error_code})")
    
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
        
        sql = f"""
            SELECT
                {period_select},
                n.process_id,
                p.process_name,
                n.model_id,
                m.model_name,
                n.eqp_id,
                e.eqp_name,
                n.error_code,
                ec.error_desc AS error_des,
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
            GROUP BY {', '.join(group_cols)}
            ORDER BY {', '.join(order_cols)}
        """
        
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
    cleaned_process_id = clean_request_value(request.process_id, "process_id")
    cleaned_eqp_id = clean_request_value(request.eqp_id, "eqp_id")
    cleaned_operator = clean_request_value(request.operator, "operator")
    
    logger.info(f"[PM 이력] 요청 수신 - process_id: {cleaned_process_id}, eqp_id: {cleaned_eqp_id}, operator: {cleaned_operator}, start_date: {request.start_date}, end_date: {request.end_date}, limit: {request.limit}")
    
    # 모든 필터가 None인 경우 경고
    if not any([cleaned_process_id, cleaned_eqp_id, cleaned_operator, request.start_date, request.end_date]):
        logger.warning(f"[PM 이력] 모든 필터가 None입니다. 전체 데이터 조회됩니다. (원본 요청: process_id={request.process_id}, eqp_id={request.eqp_id}, operator={request.operator})")
    
    sql = """
        SELECT
            TO_CHAR(n.down_start_time, 'YYYY-MM-DD') as down_date,
            dt.down_type_name,
            n.down_time_minutes,
            n.operator
        FROM INFORM_NOTE n
        LEFT JOIN DOWN_TYPE dt ON n.down_type_id = dt.down_type_id
        WHERE (:start_date IS NULL OR n.down_start_time >= TO_DATE(:start_date, 'YYYY-MM-DD'))
          AND (:end_date IS NULL OR n.down_start_time < TO_DATE(:end_date, 'YYYY-MM-DD') + 1)
          AND (:process_id IS NULL OR n.process_id = :process_id)
          AND (:eqp_id IS NULL OR n.eqp_id = :eqp_id)
          AND (:operator IS NULL OR n.operator LIKE '%' || :operator || '%')
          AND n.down_type_id = 0
        ORDER BY n.down_start_time DESC
        FETCH FIRST :limit_val ROWS ONLY
    """
    
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
    cleaned_process_id = clean_request_value(request.process_id, "process_id")
    cleaned_eqp_id = clean_request_value(request.eqp_id, "eqp_id")
    cleaned_operator = clean_request_value(request.operator, "operator")
    
    logger.info(f"[상세 검색] 요청 수신 - process_id: {cleaned_process_id}, eqp_id: {cleaned_eqp_id}, operator: {cleaned_operator}, start_date: {request.start_date}, end_date: {request.end_date}, limit: {request.limit}")
    
    # 모든 필터가 None인 경우 경고
    if not any([cleaned_process_id, cleaned_eqp_id, cleaned_operator, request.start_date, request.end_date]):
        logger.warning(f"[상세 검색] 모든 필터가 None입니다. 전체 데이터 조회됩니다. (원본 요청: process_id={request.process_id}, eqp_id={request.eqp_id})")
    
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
          AND (:operator IS NULL OR n.operator LIKE '%' || :operator || '%')
          AND (:status_id IS NULL OR n.status_id = :status_id)
        ORDER BY n.down_start_time DESC
        FETCH FIRST :limit_val ROWS ONLY
    """
    
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
