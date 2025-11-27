"""
Dify OpenAPI 연동 모듈
"""
from typing import Optional

import httpx
import logging

from config import settings

logger = logging.getLogger(__name__)


class DifyClientError(Exception):
    """Dify API 호출 중 발생한 오류"""


def is_dify_enabled() -> bool:
    """Dify 연동 사용 여부"""
    return bool(settings.DIFY_API_BASE and settings.DIFY_API_KEY)


async def request_answer(question: str, context: Optional[str] = None) -> str:
    """
    Dify API를 호출하여 답변을 획득
    
    이 함수는 로컬 서버에서 Dify API를 직접 호출합니다.
    Dify 워크플로우와는 별개로, Dify의 Chat API를 사용합니다.
    """
    if not is_dify_enabled():
        raise DifyClientError("Dify 설정이 구성되지 않았습니다.")

    # 프롬프트 구성
    prompt = question.strip()
    if context:
        prompt = f"{context.strip()}\n\n질문: {prompt}"
    
    logger.info(f"[Dify API] 프롬프트 구성 완료 (길이: {len(prompt)} 문자)")

    # Dify API 요청 페이로드 구성
    payload = {
        "inputs": {},
        "query": prompt,
        "response_mode": "blocking",
        "conversation_id": None,
        "user": settings.DIFY_USER_ID,
    }

    headers = {
        "Authorization": f"Bearer {settings.DIFY_API_KEY}",
        "Content-Type": "application/json",
    }

    base_url = settings.DIFY_API_BASE.rstrip("/")
    url = f"{base_url}/chat-messages"
    
    logger.info(f"[Dify API] 요청 URL: {url}")
    logger.info(f"[Dify API] 요청 페이로드: query='{prompt[:100]}...'")

    try:
        # 일부 배포 환경에서는 HTTP -> HTTPS 308 리다이렉트가 발생하므로
        # follow_redirects=True 로 설정해 안정적으로 응답을 받는다.
        logger.info("[Dify API] HTTP 요청 전송 중...")
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            follow_redirects=True,
        ) as client:
            response = await client.post(url, json=payload, headers=headers)
            logger.info(f"[Dify API] 응답 수신 - Status Code: {response.status_code}")
            response.raise_for_status()
            data = response.json()
            logger.info(f"[Dify API] 응답 파싱 완료 - 키: {list(data.keys())}")
            
    except httpx.HTTPStatusError as exc:
        logger.error(
            "[Dify API] HTTP 상태 오류 (status=%s, body=%s)",
            exc.response.status_code,
            exc.response.text,
        )
        raise DifyClientError(
            f"Dify API 호출 실패: {exc.response.status_code}"
        ) from exc
    except httpx.HTTPError as exc:
        logger.error(f"[Dify API] 네트워크 오류: {exc}")
        raise DifyClientError("Dify API 네트워크 오류") from exc

    # 응답에서 답변 추출
    answer = (
        data.get("answer")
        or data.get("output_text")
        or _extract_answer_from_outputs(data)
    )

    if not answer:
        logger.warning(f"[Dify API] 응답에서 answer를 찾을 수 없음. 전체 응답: {data}")
        raise DifyClientError("Dify 응답에서 answer를 찾을 수 없습니다.")

    logger.info(f"[Dify API] 답변 추출 성공 (길이: {len(answer)} 문자)")
    return answer


def _extract_answer_from_outputs(payload: dict) -> Optional[str]:
    outputs = payload.get("outputs")
    if isinstance(outputs, list) and outputs:
        first = outputs[0]
        if isinstance(first, dict):
            return first.get("text") or first.get("answer")
    return None

