"""
질문-답변 API 서버
FastAPI를 사용한 REST API 엔드포인트
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import logging
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
    question: str
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
async def ask_question(request: QuestionRequest):
    """
    질문을 받고 답변을 제공하는 엔드포인트
    
    - **question**: 사용자의 질문
    - **context**: 추가 컨텍스트 정보 (선택사항)
    """
    try:
        question = request.question.strip()
        
        if not question:
            raise HTTPException(status_code=400, detail="질문이 비어있습니다.")
        
        logger.info(f"질문 수신: {question}")
        
        # 데이터베이스에서 관련 정보 조회 (예시)
        # 실제 구현에서는 데이터베이스에서 관련 정보를 검색하거나
        # AI 모델을 사용하여 답변을 생성할 수 있습니다.
        
        # 간단한 예시: 데이터베이스에서 질문과 관련된 정보를 조회
        answer = await generate_answer(question, request.context)
        
        return AnswerResponse(
            question=question,
            answer=answer,
            success=True
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"질문 처리 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")


async def generate_answer(question: str, context: Optional[str] = None) -> str:
    """
    질문에 대한 답변 생성
    
    현재는 간단한 예시 구현입니다.
    실제로는 데이터베이스에서 정보를 검색하거나 AI 모델을 사용할 수 있습니다.
    """
    # 1) Dify 연동이 구성된 경우 우선 호출
    if is_dify_enabled():
        try:
            return await request_answer(question, context)
        except DifyClientError as exc:
            logger.error("Dify 호출 실패, DB 로직으로 대체합니다: %s", exc)

    # 2) Oracle DB 기반 기본 답변 로직
    try:
        # 데이터베이스에서 관련 정보 조회 예시
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 예시: 질문을 로그에 저장하거나 관련 데이터 조회
            # 실제 구현에 맞게 수정 필요
            cursor.execute("SELECT SYSDATE FROM DUAL")
            result = cursor.fetchone()
            cursor.close()
            
            # 간단한 답변 생성 (실제로는 더 복잡한 로직 필요)
            if "시간" in question or "날짜" in question:
                return f"현재 데이터베이스 시간: {result[0] if result else '알 수 없음'}"
            elif "연결" in question or "상태" in question:
                return "데이터베이스 연결이 정상적으로 작동하고 있습니다."
            else:
                return f"질문 '{question}'에 대한 답변을 생성했습니다. (데이터베이스 연결 확인됨)"
    
    except Exception as e:
        logger.error(f"답변 생성 중 오류: {e}")
        return f"질문을 처리하는 중 오류가 발생했습니다: {str(e)}"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )

