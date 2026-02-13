"""환경변수 로딩"""

import os


def get_api_key() -> str:
    """data.go.kr API 인증키를 환경변수에서 가져온다.

    백엔드 SpeechMcpClient가 ServerParameters.addEnvVar("API_KEY", apiKey)로 전달.
    """
    key = os.environ.get("API_KEY", "")
    if not key:
        raise RuntimeError(
            "API_KEY 환경변수가 설정되지 않았습니다. "
            "data.go.kr 인증키를 API_KEY 환경변수로 전달하세요."
        )
    return key
