"""XML NewsItem → SpeechData 변환"""

import re
from datetime import date

from guitteum_mcp.models import SpeechData

# HTML 태그 제거 패턴
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")

# 임기 기간별 대통령 매핑 (취임일 기준)
_PRESIDENT_TERMS: list[tuple[date, date, str]] = [
    (date(2008, 2, 25), date(2013, 2, 24), "이명박"),
    (date(2013, 2, 25), date(2017, 3, 10), "박근혜"),
    (date(2017, 5, 10), date(2022, 5, 9), "문재인"),
    (date(2022, 5, 10), date(2027, 5, 9), "윤석열"),
]


def _strip_html(text: str) -> str:
    """HTML 태그를 제거하고 공백을 정규화한다."""
    text = _HTML_TAG_RE.sub(" ", text)
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text


def _resolve_president(d: date) -> str:
    """날짜로 재임 대통령을 판별한다."""
    for start, end, name in _PRESIDENT_TERMS:
        if start <= d <= end:
            return name
    return ""


def _parse_date(raw: str) -> date | None:
    """ApproveDate 문자열(YYYYMMDD 또는 YYYY-MM-DD)을 date로 파싱한다."""
    cleaned = raw.strip().replace("-", "")
    if len(cleaned) >= 8 and cleaned[:8].isdigit():
        return date(int(cleaned[:4]), int(cleaned[4:6]), int(cleaned[6:8]))
    return None


def map_item(item: dict) -> SpeechData | None:
    """API 응답의 NewsItem 딕셔너리를 SpeechData로 변환한다."""
    news_id = item.get("NewsItemId", "")
    if not news_id:
        return None

    raw_date = item.get("ApproveDate", "")
    parsed = _parse_date(raw_date)

    president = ""
    speech_date = ""
    speech_year: int | None = None
    if parsed:
        president = _resolve_president(parsed)
        speech_date = parsed.isoformat()
        speech_year = parsed.year

    raw_content = item.get("DataContents", "")
    content = _strip_html(raw_content) if raw_content else ""

    return SpeechData(
        id=str(news_id),
        president=president,
        title=item.get("Title", ""),
        content=content,
        date=speech_date,
        speech_date=speech_date,
        speech_year=speech_year,
        location=item.get("SubTitle1", ""),
        source_url=item.get("OriginalUrl", ""),
    )
