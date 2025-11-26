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
    """
    if not is_dify_enabled():
        raise DifyClientError("Dify 설정이 구성되지 않았습니다.")

    prompt = question.strip()
    if context:
        prompt = f"{context.strip()}\n\n질문: {prompt}"

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

    try:
        # 일부 배포 환경에서는 HTTP -> HTTPS 308 리다이렉트가 발생하므로
        # follow_redirects=True 로 설정해 안정적으로 응답을 받는다.
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            follow_redirects=True,
        ) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as exc:
        logger.error(
            "Dify API 호출 실패 (status=%s, body=%s)",
            exc.response.status_code,
            exc.response.text,
        )
        raise DifyClientError(
            f"Dify API 호출 실패: {exc.response.status_code}"
        ) from exc
    except httpx.HTTPError as exc:
        logger.error("Dify API 호출 중 네트워크 오류: %s", exc)
        raise DifyClientError("Dify API 네트워크 오류") from exc

    answer = (
        data.get("answer")
        or data.get("output_text")
        or _extract_answer_from_outputs(data)
    )

    if not answer:
        logger.warning("Dify 응답: %s", data)
        raise DifyClientError("Dify 응답에서 answer를 찾을 수 없습니다.")

    return answer


def _extract_answer_from_outputs(payload: dict) -> Optional[str]:
    outputs = payload.get("outputs")
    if isinstance(outputs, list) and outputs:
        first = outputs[0]
        if isinstance(first, dict):
            return first.get("text") or first.get("answer")
    return None

