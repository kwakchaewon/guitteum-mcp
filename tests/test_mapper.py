"""mapper.py 단위 테스트"""

from guitteum_mcp.mapper import _parse_date, _resolve_president, _strip_html, map_item
from datetime import date


def test_strip_html_removes_tags():
    assert _strip_html("<p>안녕하세요</p>") == "안녕하세요"


def test_strip_html_normalizes_whitespace():
    assert _strip_html("<p>여러   공백</p>  <p>정규화</p>") == "여러 공백 정규화"


def test_parse_date_yyyymmdd():
    assert _parse_date("20230815") == date(2023, 8, 15)


def test_parse_date_with_dash():
    assert _parse_date("2023-08-15") == date(2023, 8, 15)


def test_parse_date_invalid():
    assert _parse_date("invalid") is None


def test_resolve_president_yoon():
    assert _resolve_president(date(2023, 8, 15)) == "윤석열"


def test_resolve_president_moon():
    assert _resolve_president(date(2020, 1, 1)) == "문재인"


def test_resolve_president_park():
    assert _resolve_president(date(2015, 6, 1)) == "박근혜"


def test_resolve_president_lee():
    assert _resolve_president(date(2010, 3, 1)) == "이명박"


def test_resolve_president_unknown():
    assert _resolve_president(date(2000, 1, 1)) == ""


def test_map_item_full():
    item = {
        "NewsItemId": "12345",
        "Title": "광복절 경축사",
        "DataContents": "<p>존경하는 국민 여러분</p>",
        "ApproveDate": "20230815",
        "SubTitle1": "서울",
        "OriginalUrl": "https://www.korea.kr/12345",
    }
    result = map_item(item)
    assert result is not None
    assert result.id == "12345"
    assert result.president == "윤석열"
    assert result.title == "광복절 경축사"
    assert result.content == "존경하는 국민 여러분"
    assert result.speech_date == "2023-08-15"
    assert result.speech_year == 2023
    assert result.location == "서울"


def test_map_item_no_id_returns_none():
    assert map_item({}) is None
