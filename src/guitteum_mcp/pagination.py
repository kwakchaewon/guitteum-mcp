"""3일 윈도우 순회 + 인메모리 캐시 기반 가상 페이지네이션"""

import logging
from datetime import date, timedelta

from guitteum_mcp.api_client import fetch_speeches
from guitteum_mcp.mapper import map_item
from guitteum_mcp.models import SpeechData

logger = logging.getLogger(__name__)

# 수집 시작일 (이명박 정부 취임)
COLLECT_START = date(2008, 2, 25)

# API 최대 조회 범위 (일)
WINDOW_DAYS = 3

# 인메모리 캐시
_cache: list[SpeechData] = []
_loaded = False


def _generate_windows(start: date, end: date):
    """start ~ end 구간을 WINDOW_DAYS 단위로 분할하여 (시작, 종료) 튜플을 생성한다."""
    cursor = start
    while cursor <= end:
        window_end = min(cursor + timedelta(days=WINDOW_DAYS - 1), end)
        yield cursor, window_end
        cursor = window_end + timedelta(days=1)


async def _load_all() -> None:
    """전체 날짜 범위를 3일 윈도우로 순회하며 캐시에 적재한다."""
    global _cache, _loaded

    if _loaded:
        return

    today = date.today()
    speeches: list[SpeechData] = []
    window_count = 0

    for win_start, win_end in _generate_windows(COLLECT_START, today):
        start_str = win_start.strftime("%Y%m%d")
        end_str = win_end.strftime("%Y%m%d")

        try:
            items = await fetch_speeches(start_str, end_str)
        except Exception:
            logger.exception("API 호출 실패: %s~%s", start_str, end_str)
            continue

        for item in items:
            speech = map_item(item)
            if speech:
                speeches.append(speech)

        window_count += 1
        if window_count % 100 == 0:
            logger.info("수집 진행: %d 윈도우 완료, %d건 수집", window_count, len(speeches))

    # id 기준 중복 제거
    seen: set[str] = set()
    unique: list[SpeechData] = []
    for s in speeches:
        if s.id not in seen:
            seen.add(s.id)
            unique.append(s)

    # 날짜 내림차순 정렬
    unique.sort(key=lambda s: s.speech_date, reverse=True)

    _cache = unique
    _loaded = True
    logger.info("전체 수집 완료: %d건", len(_cache))


async def get_page(page: int = 1, per_page: int = 100) -> list[SpeechData]:
    """캐시에서 page/per_page 기반 슬라이싱으로 반환한다."""
    await _load_all()
    start = (page - 1) * per_page
    end = start + per_page
    return _cache[start:end]


async def search_by_president(
    president: str, page: int = 1, per_page: int = 100
) -> list[SpeechData]:
    """대통령명으로 필터링 후 페이지네이션하여 반환한다."""
    await _load_all()
    filtered = [s for s in _cache if s.president == president]
    start = (page - 1) * per_page
    end = start + per_page
    return filtered[start:end]
