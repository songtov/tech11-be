from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ResearchBase(BaseModel):
    title: str
    abstract: str


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
