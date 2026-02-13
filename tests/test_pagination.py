"""pagination.py 단위 테스트"""

from datetime import date
from guitteum_mcp.pagination import _generate_windows


def test_generate_windows_exact():
    """3일 정확히 맞는 구간"""
    windows = list(_generate_windows(date(2024, 1, 1), date(2024, 1, 3)))
    assert len(windows) == 1
    assert windows[0] == (date(2024, 1, 1), date(2024, 1, 3))


def test_generate_windows_multiple():
    """7일 → 3일 + 3일 + 1일"""
    windows = list(_generate_windows(date(2024, 1, 1), date(2024, 1, 7)))
    assert len(windows) == 3
    assert windows[0] == (date(2024, 1, 1), date(2024, 1, 3))
    assert windows[1] == (date(2024, 1, 4), date(2024, 1, 6))
    assert windows[2] == (date(2024, 1, 7), date(2024, 1, 7))


def test_generate_windows_single_day():
    """1일 구간"""
    windows = list(_generate_windows(date(2024, 1, 1), date(2024, 1, 1)))
    assert len(windows) == 1
    assert windows[0] == (date(2024, 1, 1), date(2024, 1, 1))
