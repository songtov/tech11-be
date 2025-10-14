from datetime import datetime
from typing import Optional
from enum import Enum

from pydantic import BaseModel, Field


class TTSLanguage(str, Enum):
    KOREAN = "ko"


class TTSStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TTSBase(BaseModel):
    path: str = Field(..., description="Path to the pdf file")


class TTSCreate(TTSBase):
    pass


class TTSUpdate(BaseModel):
    text: Optional[str] = Field(None, description="Updated text to convert to speech")
    language: Optional[TTSLanguage] = Field(None, description="Updated language for TTS")
    filename: Optional[str] = Field(None, description="Updated custom filename")


class TTSResponse(BaseModel):
    path: str = Field(..., description="Path to the output mp3 file")

class TTSRequest(BaseModel):
    path: str = Field(..., description="Path to the pdf file")


class TTSFileResponse(BaseModel):
    id: int
    filename: str
    file_path: str
    file_size: int
    created_at: datetime
    download_url: str


class TTSExplainerRequest(BaseModel):
    explainer_text: str = Field(..., description="Explainer text to convert to speech (from multi-agent workflow)")
    # language 필드 제거: 한국어 고정이므로 불필요


class TTSPdfPathRequest(BaseModel):
    pdf_path: str = Field(..., description="Path to the PDF file to process for TTS generation")


class TTSResearchRequest(BaseModel):
    """Research ID 기반 TTS 생성 요청"""
    research_id: int = Field(..., description="Research ID to generate TTS from", gt=0)