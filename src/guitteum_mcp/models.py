"""응답 스키마 - 백엔드 SpeechData.java와 일치"""

from pydantic import BaseModel


class SpeechData(BaseModel):
    id: str
    president: str = ""
    title: str = ""
    content: str = ""
    date: str = ""
    speech_date: str = ""
    speech_year: int | None = None
    location: str = ""
    source_url: str = ""
