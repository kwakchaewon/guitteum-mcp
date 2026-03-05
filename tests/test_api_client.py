"""api_client.py 단위 테스트 (XML 파싱 로직 검증)"""

import xmltodict
from pathlib import Path


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_response.xml"


def test_parse_sample_xml():
    """sample_response.xml이 올바르게 파싱되는지 검증"""
    xml_text = FIXTURE_PATH.read_text(encoding="utf-8")
    parsed = xmltodict.parse(xml_text)

    body = parsed["response"]["body"]
    items = body["NewsItem"]
    assert isinstance(items, list)
    assert len(items) == 2
    assert items[0]["NewsItemId"] == "12345"
    assert items[0]["Title"] == "제78주년 광복절 경축사"


def test_single_item_normalization():
    """단건 응답(dict)을 리스트로 정규화하는 로직 검증"""
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <response>
      <header>
        <resultCode>0</resultCode>
        <resultMsg>성공</resultMsg>
      </header>
      <body>
        <NewsItem>
          <NewsItemId>99999</NewsItemId>
          <Title>단건 테스트</Title>
        </NewsItem>
      </body>
    </response>"""
    parsed = xmltodict.parse(xml)
    items = parsed["response"]["body"]["NewsItem"]
    # xmltodict은 단건이면 dict 반환
    if isinstance(items, dict):
        items = [items]
    assert isinstance(items, list)
    assert len(items) == 1
    assert items[0]["NewsItemId"] == "99999"
