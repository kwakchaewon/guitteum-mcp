"""FastMCP 서버 + 도구 등록

stdout은 JSON-RPC 통신 전용이므로 모든 로깅은 stderr로 출력한다.
"""

import logging
import sys

from mcp.server.fastmcp import FastMCP

from guitteum_mcp.pagination import get_page, search_by_president

# stderr 로깅 (stdout 오염 방지)
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)

mcp = FastMCP("guitteum-mcp")


@mcp.tool()
async def list_speeches(page: int = 1, per_page: int = 100) -> str:
    """전체 대통령 연설문을 페이지 단위로 반환한다.

    Args:
        page: 페이지 번호 (1부터 시작)
        per_page: 페이지당 항목 수

    Returns:
        SpeechData JSON 배열 문자열
    """
    speeches = await get_page(page, per_page)
    return _to_json(speeches)


@mcp.tool()
async def search_speeches(
    president: str, page: int = 1, per_page: int = 100
) -> str:
    """대통령명으로 필터링된 연설문을 반환한다.

    Args:
        president: 대통령 이름 (예: "윤석열", "문재인")
        page: 페이지 번호 (1부터 시작)
        per_page: 페이지당 항목 수

    Returns:
        SpeechData JSON 배열 문자열
    """
    speeches = await search_by_president(president, page, per_page)
    return _to_json(speeches)


def _to_json(speeches: list) -> str:
    """SpeechData 리스트를 JSON 배열 문자열로 변환한다."""
    import json

    return json.dumps(
        [s.model_dump() for s in speeches],
        ensure_ascii=False,
    )
