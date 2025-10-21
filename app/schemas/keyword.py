from typing import Dict

from pydantic import BaseModel, Field


class KeywordExtractFromTextRequest(BaseModel):
    """텍스트로부터 키워드 추출 요청"""

    text: str = Field(
        ..., description="키워드를 추출할 텍스트 또는 검색어", min_length=1, max_length=1000
    )


class KeywordResponse(BaseModel):
    """키워드 추출 응답 - 한글:영어 매핑"""

    keywords: Dict[str, str] = Field(
        ...,
        description="키워드 매핑 (한글: 영어). 정확히 5개의 키워드 포함",
        min_length=5,
        max_length=5,
    )

    class Config:
        json_schema_extra = {
            "example": {
                "keywords": {
                    "인공지능": "Artificial Intelligence",
                    "기계학습": "Machine Learning",
                    "딥러닝": "Deep Learning",
                    "신경망": "Neural Network",
                    "자연어처리": "Natural Language Processing",
                }
            }
        }
