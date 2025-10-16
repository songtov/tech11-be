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


class ResearchSearchByKeyword(BaseModel):
    keyword: str = Field(..., description="검색할 키워드", min_length=1, max_length=200)


class ResearchCreate(ResearchBase):
    pass


class ResearchUpdate(BaseModel):
    title: Optional[str] = None
    abstract: Optional[str] = None


class ResearchResponse(ResearchBase):
    id: int
    authors: List[str] = []
    published_date: Optional[str] = None
    updated_date: Optional[str] = None
    categories: List[str] = []
    pdf_url: Optional[str] = None
    arxiv_url: Optional[str] = None
    citation_count: int = 0
    relevance_score: float = 0.0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ResearchSearchResponse(BaseModel):
    data: List[ResearchResponse] = Field(
        ..., min_length=5, max_length=5, description="Exactly 5 research responses"
    )


class ResearchDownload(BaseModel):
    pdf_url: str
    arxiv_url: str
    title: Optional[str] = None


class ResearchDownloadByIdRequest(BaseModel):
    research_id: int = Field(
        ..., description="ID of the research entry to download PDF for", gt=0
    )


class ResearchDownloadResponse(BaseModel):
    output_path: str = Field(
        ..., description="Absolute path to the downloaded PDF file"
    )
    download_url: str = Field(
        ..., description="URL to download the PDF file from the server"
    )
    filename: str = Field(..., description="Name of the downloaded PDF file")
