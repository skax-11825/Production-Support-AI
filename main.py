"""
질문-답변 API 서버
FastAPI를 사용한 REST API 엔드포인트
"""
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
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
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )

