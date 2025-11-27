"""
질문-답변 API 서버
FastAPI를 사용한 REST API 엔드포인트

전체 흐름:
1. Dify 워크플로우 → HTTP Request 노드 → 백엔드 서버 (/ask)
2. 백엔드에서 질문 분석 및 공정정보 추출
3. Oracle DB 쿼리 실행 (공정정보 특정 가능한 경우)
4. 결과를 Dify에 반환 (answer 필드)
5. Dify가 최종 답변 생성
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Tuple
import logging
import json
from database import db
from config import settings
from dify_client import (
    is_dify_enabled,
    request_answer,
    DifyClientError,
)
from question_analyzer import question_analyzer, ProcessInfo
from process_query_builder import query_builder

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
    """질문 요청 모델 (Dify에서 전달)"""
    question: str = Field(..., description="사용자 질문 (Dify input 변수)")
    context: Optional[str] = Field(None, description="추가 컨텍스트 정보 (선택사항)")


class AnswerResponse(BaseModel):
    """답변 응답 모델 (Dify로 반환)"""
    answer: str = Field(..., description="생성된 답변 (Dify output 변수로 사용)")
    question: str = Field(..., description="원본 질문")
    success: bool = Field(True, description="처리 성공 여부")
    process_specific: Optional[bool] = Field(None, description="공정정보 특정 가능 여부")
    data_count: Optional[int] = Field(None, description="조회된 데이터 건수 (공정정보 특정 가능한 경우)")


class HealthResponse(BaseModel):
    """헬스 체크 응답 모델"""
    status: str
    database_connected: bool
    dify_enabled: bool


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


@app.post("/ask", response_model=AnswerResponse, tags=["질문-답변"])
async def ask_question(request: QuestionRequest, http_request: Request):
    """
    질문을 받고 답변을 제공하는 엔드포인트
    
    Dify 워크플로우에서 HTTP Request 노드를 통해 호출됩니다.
    
    전체 흐름:
    1. Dify → HTTP Request → 백엔드 서버 (/ask)
    2. 백엔드에서 질문 분석 및 공정정보 추출
    3. Oracle DB 쿼리 실행 (공정정보 특정 가능한 경우)
    4. 결과를 Dify에 반환 (answer 필드)
    5. Dify가 최종 답변 생성
    
    Request Body:
    - question: 사용자의 질문 (Dify input 변수, 필수)
    - context: 추가 컨텍스트 정보 (선택사항)
    
    Response:
    - answer: 생성된 답변 (Dify output 변수로 사용)
    - question: 원본 질문
    - success: 처리 성공 여부
    - process_specific: 공정정보 특정 가능 여부
    - data_count: 조회된 데이터 건수
    """
    try:
        # 1단계: 요청 정보 로깅
        logger.info("=" * 80)
        logger.info("[Dify 워크플로우 요청 수신]")
        logger.info(f"요청 URL: {http_request.url}")
        logger.info(f"요청 Method: {http_request.method}")
        
        # 파싱된 요청 정보
        question = request.question.strip() if request.question else ""
        context = request.context.strip() if request.context else None
        
        logger.info(f"질문: {question}")
        if context:
            logger.info(f"컨텍스트: {context[:100]}...")
        
        # 2단계: 입력 검증
        if not question:
            logger.error("[오류] 질문이 비어있습니다.")
            raise HTTPException(
                status_code=400, 
                detail="질문이 비어있습니다. 'question' 필드는 필수입니다."
            )
        
        # 3단계: 질문 분석 및 답변 생성
        logger.info(f"[답변 생성 시작] 질문: '{question[:100]}...'")
        
        # 질문 분석: 공정정보 추출 및 특정 가능 여부 판단
        process_info, is_specific = question_analyzer.analyze(question)
        
        data_count = None
        if is_specific:
            logger.info("[공정정보 특정 가능] Oracle DB 쿼리 기반 답변 생성")
            answer, data_count = await generate_answer_with_process_info(
                question, process_info, context
            )
        else:
            logger.info("[공정정보 특정 불가] 일반 답변 생성 (Dify 또는 기본 답변)")
            answer = await generate_answer(question, context)
        
        # 4단계: 응답 반환 (Dify로 전달)
        logger.info(f"[답변 생성 완료] 답변 길이: {len(answer)} 문자")
        if data_count is not None:
            logger.info(f"[답변 생성 완료] 조회된 데이터: {data_count}건")
        logger.info("=" * 80)
        
        return AnswerResponse(
            question=question,
            answer=answer,
            success=True,
            process_specific=is_specific,
            data_count=data_count
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
        logger.error("=" * 80, exc_info=True)
        
        # Dify에 전달할 수 있는 형식으로 에러 메시지 반환
        error_answer = (
            f"질문을 처리하는 중 오류가 발생했습니다: {str(e)}\n"
            "시스템 관리자에게 문의하세요."
        )
        
        return AnswerResponse(
            question=request.question if hasattr(request, 'question') else "",
            answer=error_answer,
            success=False,
            process_specific=None,
            data_count=None
        )


async def generate_answer_with_process_info(
    question: str, 
    process_info: ProcessInfo, 
    context: Optional[str] = None
) -> Tuple[str, int]:
    """
    공정정보가 특정 가능한 경우의 답변 생성
    
    처리 순서:
    1. Oracle DB에서 공정정보 기반 데이터 조회
    2. 조회 결과를 기반으로 답변 생성
    3. Dify API 호출 (선택사항, 컨텍스트로 사용)
    """
    logger.info(f"[공정정보 기반 답변] 시작 - 질문: '{question[:50]}...'")
    logger.info(f"[공정정보 기반 답변] 추출된 정보: {process_info.to_dict()}")
    
    try:
        # 데이터베이스 연결 확인
        if not db.test_connection():
            logger.error("[공정정보 기반 답변] 데이터베이스 연결 실패")
            return "데이터베이스에 연결할 수 없습니다. 시스템 관리자에게 문의하세요."
        
        logger.info("[공정정보 기반 답변] 데이터베이스 연결 성공")
        
        # 쿼리 생성 및 실행
        query, bind_params = query_builder.build_query(process_info)
        results = query_builder.execute_query(query, bind_params, limit=50)
        
        logger.info(f"[공정정보 기반 답변] 쿼리 결과: {len(results)}건")
        
        if not results:
            # 결과가 없는 경우
            answer = f"조건에 맞는 다운타임 정보를 찾을 수 없습니다.\n\n"
            answer += f"검색 조건:\n"
            if process_info.site_id:
                answer += f"- 사이트: {process_info.site_id}\n"
            if process_info.factory_id:
                answer += f"- 공장: {process_info.factory_id}\n"
            if process_info.process_id:
                answer += f"- 공정: {process_info.process_id}\n"
            if process_info.model_id:
                answer += f"- 모델: {process_info.model_id}\n"
            if process_info.down_type:
                answer += f"- 다운타임 유형: {process_info.down_type}\n"
            if process_info.down_time_minutes:
                answer += f"- 다운타임 시간: {process_info.down_time_minutes}분\n"
            
            return answer, 0
        
        # 통계 정보 조회
        stats = query_builder.get_statistics(process_info)
        
        # 답변 생성
        answer = _format_process_answer(results, stats, process_info, question)
        data_count = len(results)
        
        # Dify API 호출 비활성화 (공정정보 기반 답변은 DB 결과를 직접 사용)
        # Dify 워크플로우에서 이미 처리하므로 여기서는 DB 결과만 반환
        if False and is_dify_enabled() and len(results) > 20:
            try:
                logger.info("[공정정보 기반 답변] Dify API로 요약 요청")
                dify_context = f"다음은 조회된 다운타임 데이터입니다:\n\n{answer[:3000]}..."
                dify_answer = await request_answer(
                    f"위 데이터를 바탕으로 '{question}'에 대한 요약 답변을 자연스럽게 제공해주세요.",
                    dify_context
                )
                if dify_answer and len(dify_answer) > 50:
                    answer = f"{dify_answer}\n\n[상세 데이터]\n{answer}"
                    logger.info("[공정정보 기반 답변] Dify 요약 완료")
            except Exception as e:
                logger.warning(f"[공정정보 기반 답변] Dify 요약 실패 (기본 답변 사용): {e}")
        
        logger.info(f"[공정정보 기반 답변] 완료 - 답변 길이: {len(answer)} 문자, 데이터: {data_count}건")
        return answer, data_count
        
    except Exception as e:
        logger.error(f"[공정정보 기반 답변] 오류 발생: {e}", exc_info=True)
        error_msg = (
            f"공정정보 기반 답변 생성 중 오류가 발생했습니다: {str(e)}\n"
            "시스템 관리자에게 문의하세요."
        )
        return error_msg, 0


def _format_process_answer(
    results: list, 
    stats: dict, 
    process_info: ProcessInfo, 
    question: str
) -> str:
    """공정정보 기반 답변 포맷팅"""
    answer_parts = []
    
    # 통계 정보
    answer_parts.append("=" * 60)
    answer_parts.append("다운타임 정보 조회 결과")
    answer_parts.append("=" * 60)
    
    if stats.get('total_count', 0) > 0:
        answer_parts.append(f"\n[통계 정보]")
        answer_parts.append(f"- 총 건수: {int(stats.get('total_count', 0))}건")
        answer_parts.append(f"- 총 다운타임: {stats.get('total_minutes', 0):.1f}분 ({stats.get('total_minutes', 0)/60:.2f}시간)")
        answer_parts.append(f"- 평균 다운타임: {stats.get('avg_minutes', 0):.1f}분")
        answer_parts.append(f"- 최소 다운타임: {stats.get('min_minutes', 0):.1f}분")
        answer_parts.append(f"- 최대 다운타임: {stats.get('max_minutes', 0):.1f}분")
        answer_parts.append(f"- 계획 다운타임: {int(stats.get('scheduled_count', 0))}건")
        answer_parts.append(f"- 비계획 다운타임: {int(stats.get('unscheduled_count', 0))}건")
        answer_parts.append(f"- 완료: {int(stats.get('completed_count', 0))}건")
        answer_parts.append(f"- 진행중: {int(stats.get('in_progress_count', 0))}건")
    
    # 상세 정보 (최대 10건)
    if results:
        answer_parts.append(f"\n[상세 정보] (최근 {min(len(results), 10)}건)")
        answer_parts.append("-" * 60)
        
        for i, result in enumerate(results[:10], 1):
            # Oracle DB는 컬럼명을 대문자로 반환하므로 대소문자 모두 확인
            informnote_id = result.get('informnote_id') or result.get('INFORMNOTE_ID') or 'N/A'
            answer_parts.append(f"\n{i}. 다운타임 ID: {informnote_id}")
            
            site_id = result.get('site_id') or result.get('SITE_ID')
            if site_id:
                answer_parts.append(f"   사이트: {site_id}")
            
            factory_id = result.get('factory_id') or result.get('FACTORY_ID')
            if factory_id:
                answer_parts.append(f"   공장: {factory_id}")
            
            process_id = result.get('process_id') or result.get('PROCESS_ID')
            if process_id:
                answer_parts.append(f"   공정: {process_id}")
            
            eqp_id = result.get('eqp_id') or result.get('EQP_ID')
            if eqp_id:
                answer_parts.append(f"   장비: {eqp_id}")
            
            down_start_time = result.get('down_start_time') or result.get('DOWN_START_TIME')
            if down_start_time:
                answer_parts.append(f"   다운 시작: {down_start_time}")
            
            down_end_time = result.get('down_end_time') or result.get('DOWN_END_TIME')
            if down_end_time:
                answer_parts.append(f"   다운 종료: {down_end_time}")
            
            down_time_minutes = result.get('down_time_minutes') or result.get('DOWN_TIME_MINUTES')
            if down_time_minutes is not None:
                answer_parts.append(f"   지속 시간: {down_time_minutes}분")
            
            down_type = result.get('down_type') or result.get('DOWN_TYPE')
            if down_type:
                answer_parts.append(f"   유형: {down_type}")
            
            error_code = result.get('error_code') or result.get('ERROR_CODE')
            if error_code:
                answer_parts.append(f"   에러 코드: {error_code}")
            
            status_id = result.get('status_id') or result.get('STATUS_ID')
            if status_id:
                answer_parts.append(f"   상태: {status_id}")
        
        if len(results) > 10:
            answer_parts.append(f"\n... 외 {len(results) - 10}건 더 있습니다.")
    
    return "\n".join(answer_parts)


async def generate_answer(question: str, context: Optional[str] = None) -> str:
    """
    공정정보를 특정할 수 없는 경우의 답변 생성
    
    처리 순서:
    1. Dify API 호출 시도 (설정된 경우) - Dify 워크플로우에서 최종 답변 생성
    2. Dify 실패 시 기본 답변 반환
    
    Note: 공정정보를 특정할 수 없는 일반 질문은 Dify 워크플로우에서 처리하는 것이 좋습니다.
    """
    logger.info(f"[일반 답변 생성] 시작 - 질문: '{question[:100]}...'")
    
    # 1단계: Dify API 호출 시도 (Dify 워크플로우에서 최종 처리)
    if is_dify_enabled():
        logger.info("[일반 답변] Dify API 호출 시도")
        logger.info(f"[일반 답변] Dify API Base: {settings.DIFY_API_BASE}")
        try:
            logger.info("[일반 답변] Dify API로 답변 요청 중...")
            answer = await request_answer(question, context)
            logger.info(f"[일반 답변] Dify API 성공! 답변 길이: {len(answer)} 문자")
            return answer
        except DifyClientError as exc:
            logger.warning(f"[일반 답변] Dify API 호출 실패: {exc}")
            logger.info("[일반 답변] 기본 답변으로 대체합니다.")
        except Exception as exc:
            logger.error(f"[일반 답변] Dify API 예상치 못한 오류: {exc}", exc_info=True)
            logger.info("[일반 답변] 기본 답변으로 대체합니다.")
    else:
        logger.info("[일반 답변] Dify 연동이 비활성화되어 있습니다.")

    # 2단계: 기본 답변 생성 (Dify 실패 시 또는 Dify 미설정 시)
    logger.info("[일반 답변] 기본 답변 생성")
    
    # 데이터베이스 연결 확인
    db_connected = db.test_connection()
    
    if db_connected:
        answer = (
            f"질문을 받았습니다: '{question}'\n\n"
            "공정정보를 특정할 수 없는 일반 질문입니다. "
            "더 구체적인 정보(사이트, 공장, 공정, 장비 등)를 포함해 주시면 "
            "정확한 다운타임 정보를 조회할 수 있습니다.\n\n"
            "예시:\n"
            "- 'ICH 사이트의 FAB1에서 PHOTO 공정 다운타임 알려줘'\n"
            "- '비계획 다운타임 2시간 이상인 경우 조회'\n"
            "- 'MODEL-A 장비의 SCHEDULED 다운타임 통계'"
        )
    else:
        answer = (
            f"질문을 받았습니다: '{question}'\n\n"
            "현재 데이터베이스에 연결할 수 없습니다. "
            "시스템 관리자에게 문의하세요."
        )
    
    logger.info(f"[일반 답변] 완료 - 답변 길이: {len(answer)} 문자")
    return answer


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )

