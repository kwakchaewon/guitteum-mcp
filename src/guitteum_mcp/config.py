"""환경변수 로딩"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


def get_cache_dir() -> Path:
    """캐시 디렉토리 경로. CACHE_DIR 환경변수로 변경 가능."""
    raw = os.environ.get("CACHE_DIR", "")
    if raw:
        p = Path(raw)
    else:
        p = Path(__file__).resolve().parents[2] / ".cache"
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_api_key() -> str:
    """data.go.kr API 인증키를 환경변수에서 가져온다."""
    key = os.environ.get("DATA_GO_API_KEY", "")
    if not key:
        raise RuntimeError(
            "DATA_GO_API_KEY 환경변수가 설정되지 않았습니다. "
            "data.go.kr 인증키를 DATA_GO_API_KEY 환경변수로 전달하세요."
        )
    return key
