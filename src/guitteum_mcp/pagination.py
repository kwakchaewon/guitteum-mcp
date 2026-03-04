"""3일 윈도우 순회 + 파일 캐시 기반 가상 페이지네이션

일일 API 호출 한도(1,000회)를 고려하여 실행당 최대 500회만 호출한다.
최초 전체 수집은 여러 번 실행에 걸쳐 점진적으로 완료된다.
"""

import json
import logging
import os
from datetime import date, timedelta

from guitteum_mcp.api_client import fetch_speeches
from guitteum_mcp.config import get_cache_dir
from guitteum_mcp.mapper import map_item
from guitteum_mcp.models import SpeechData

logger = logging.getLogger(__name__)


def _get_collect_start() -> date:
    """수집 시작일. COLLECT_START_DATE 환경변수(YYYYMMDD)로 조정 가능."""
    raw = os.environ.get("COLLECT_START_DATE", "")
    if raw and len(raw) == 8 and raw.isdigit():
        return date(int(raw[:4]), int(raw[4:6]), int(raw[6:8]))
    return date(2008, 2, 25)  # 기본값: 이명박 정부 취임


# API 최대 조회 범위 (일)
WINDOW_DAYS = 3
CACHE_FILE = "speeches_cache.json"
MAX_API_CALLS = 500  # 실행당 최대 API 호출 수

# 인메모리 캐시
_cache: list[SpeechData] = []
_loaded = False


def _parse_yyyymmdd(s: str) -> date:
    """YYYYMMDD 문자열을 date로 변환한다."""
    return date(int(s[:4]), int(s[4:6]), int(s[6:8]))


def _cache_path():
    return get_cache_dir() / CACHE_FILE


def _save_cache(
    speeches: list[SpeechData], collect_end_date: str
) -> None:
    """캐시를 JSON 파일로 저장한다."""
    data = {
        "collect_end_date": collect_end_date,
        "speeches": [s.model_dump() for s in speeches],
    }
    _cache_path().write_text(
        json.dumps(data, ensure_ascii=False), encoding="utf-8"
    )
    logger.info(
        "캐시 저장: %d건, 수집 완료 구간: ~%s", len(speeches), collect_end_date
    )


def _load_cache_from_file() -> tuple[list[SpeechData], str | None]:
    """파일 캐시에서 로드한다. 없으면 ([], None) 반환."""
    path = _cache_path()
    if not path.exists():
        return [], None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        speeches = [SpeechData(**s) for s in data["speeches"]]
        return speeches, data.get("collect_end_date")
    except Exception:
        logger.exception("캐시 파일 파싱 실패, 처음부터 수집")
        return [], None


def _generate_windows(start: date, end: date):
    """start ~ end 구간을 WINDOW_DAYS 단위로 분할하여 (시작, 종료) 튜플을 생성한다."""
    cursor = start
    while cursor <= end:
        window_end = min(cursor + timedelta(days=WINDOW_DAYS - 1), end)
        yield cursor, window_end
        cursor = window_end + timedelta(days=1)


def _dedupe_and_sort(speeches: list[SpeechData]) -> list[SpeechData]:
    """id 기준 중복 제거 후 날짜 내림차순 정렬한다."""
    seen: set[str] = set()
    unique: list[SpeechData] = []
    for s in speeches:
        if s.id not in seen:
            seen.add(s.id)
            unique.append(s)
    unique.sort(key=lambda s: s.speech_date, reverse=True)
    return unique


async def _fetch_range(
    start: date, end: date, max_calls: int = MAX_API_CALLS
) -> tuple[list[SpeechData], date]:
    """지정 날짜 범위를 3일 윈도우로 순회하며 연설문을 수집한다.

    max_calls에 도달하면 조기 중단한다.

    Returns:
        (수집된 연설문 리스트, 마지막으로 수집 완료한 윈도우 종료일)
    """
    speeches: list[SpeechData] = []
    call_count = 0
    last_window_end = start

    for win_start, win_end in _generate_windows(start, end):
        if call_count >= max_calls:
            logger.info(
                "일일 호출 한도 도달 (%d회), 수집 중단: ~%s",
                max_calls,
                last_window_end.strftime("%Y%m%d"),
            )
            break

        start_str = win_start.strftime("%Y%m%d")
        end_str = win_end.strftime("%Y%m%d")

        try:
            items = await fetch_speeches(start_str, end_str)
        except Exception:
            logger.exception("API 호출 실패: %s~%s", start_str, end_str)
            call_count += 1
            last_window_end = win_end
            continue

        for item in items:
            speech = map_item(item)
            if speech:
                speeches.append(speech)

        call_count += 1
        last_window_end = win_end

        if call_count % 100 == 0:
            logger.info(
                "수집 진행: %d/%d 호출, %d건 수집",
                call_count,
                max_calls,
                len(speeches),
            )

    return speeches, last_window_end


async def _load_all() -> None:
    """파일 캐시를 로드하고, 미수집 구간을 최대 500회까지 추가 수집한다."""
    global _cache, _loaded

    if _loaded:
        return

    today = date.today()
    cached_speeches, collect_end_str = _load_cache_from_file()

    if cached_speeches and collect_end_str:
        collect_end = _parse_yyyymmdd(collect_end_str)
        next_start = collect_end + timedelta(days=1)

        if next_start > today:
            # 수집 완료 상태 → API 호출 없이 캐시 사용
            logger.info(
                "캐시 최신 상태: %d건 (수집 완료: ~%s)",
                len(cached_speeches),
                collect_end_str,
            )
            _cache = cached_speeches
            _loaded = True
            return

        # 미수집 구간 추가 수집
        logger.info(
            "캐시 로드: %d건, 추가 수집: %s ~ %s",
            len(cached_speeches),
            next_start.strftime("%Y%m%d"),
            today.strftime("%Y%m%d"),
        )
        new_speeches, last_end = await _fetch_range(next_start, today)
        all_speeches = cached_speeches + new_speeches
        save_end = last_end
    else:
        # 최초 수집
        start = _get_collect_start()
        logger.info(
            "캐시 없음: 최초 수집 시작 (%s ~ %s, 최대 %d회)",
            start.strftime("%Y%m%d"),
            today.strftime("%Y%m%d"),
            MAX_API_CALLS,
        )
        all_speeches, last_end = await _fetch_range(start, today)
        save_end = last_end

    _cache = _dedupe_and_sort(all_speeches)
    _loaded = True
    _save_cache(_cache, save_end.strftime("%Y%m%d"))

    # 수집 미완료 시 안내
    if save_end < today:
        remaining_days = (today - save_end).days
        remaining_calls = (remaining_days + WINDOW_DAYS - 1) // WINDOW_DAYS
        logger.info(
            "수집 미완료: %s 이후 미수집 (%d일, ~%d회 남음). 다음 실행 시 이어서 수집합니다.",
            save_end.strftime("%Y%m%d"),
            remaining_days,
            remaining_calls,
        )


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
