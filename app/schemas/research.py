from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class DomainEnum(str, Enum):
    FINANCE = "금융"
    COMMUNICATION = "통신"
    MANUFACTURE = "제조"
    LOGISTICS = "유통/물류"
    AI = "AI"
    CLOUD = "클라우드"


class ResearchBase(BaseModel):
    title: str
    abstract: str


class ResearchSearch(BaseModel):
    domain: DomainEnum

class ResearchCreate(ResearchBase):
    pass


class ResearchUpdate(BaseModel):
    title: Optional[str] = None
    abstract: Optional[str] = None


class ResearchResponse(ResearchBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ResearchSearchResponse(BaseModel):
    data: List[ResearchResponse] = Field(..., min_length=5, max_length=5, description="Exactly 5 research responses")
