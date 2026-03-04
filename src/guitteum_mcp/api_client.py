"""data.go.kr 정책브리핑 연설문 API 호출"""

import logging

import httpx
import xmltodict

from guitteum_mcp.config import get_api_key

logger = logging.getLogger(__name__)

BASE_URL = "https://apis.data.go.kr/1371000/speechService/speechList"


class QuotaExceededError(Exception):
    """API 호출 할당량 초과 시 발생하는 예외."""


async def fetch_speeches(start_date: str, end_date: str) -> list[dict]:
    """지정된 날짜 범위의 연설문을 조회한다.

    Args:
        start_date: 조회 시작일 (YYYYMMDD)
        end_date: 조회 종료일 (YYYYMMDD), start_date와 최대 3일 차이

    Returns:
        NewsItem 딕셔너리 리스트

    Raises:
        QuotaExceededError: API 할당량 초과 (429) 시
    """
    api_key = get_api_key()
    params = {
        "serviceKey": api_key,
        "startDate": start_date,
        "endDate": end_date,
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(BASE_URL, params=params)

    if resp.status_code == 429:
        raise QuotaExceededError(
            "API 할당량 초과 (429). data.go.kr에서 해당 API 활용 신청 여부와 일일 호출 한도를 확인하세요."
        )

    resp.raise_for_status()

    parsed = xmltodict.parse(resp.text)

    body = parsed.get("response", {}).get("body", {})
    if not body:
        return []

    total = int(body.get("totalCount", 0))
    if total == 0:
        return []

    items = body.get("items", {}).get("item", [])
    # 단건이면 dict로 옴 → 리스트로 정규화
    if isinstance(items, dict):
        items = [items]

    logger.info("API 응답: %s~%s, %d건", start_date, end_date, len(items))
    return items
