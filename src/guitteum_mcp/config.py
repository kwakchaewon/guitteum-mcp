"""환경변수 로딩"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


def get_api_key() -> str:
    """data.go.kr API 인증키를 환경변수에서 가져온다."""
    key = os.environ.get("DATA_GO_API_KEY", "")
    if not key:
        raise RuntimeError(
            "DATA_GO_API_KEY 환경변수가 설정되지 않았습니다. "
            "data.go.kr 인증키를 DATA_GO_API_KEY 환경변수로 전달하세요."
        )
    return key
