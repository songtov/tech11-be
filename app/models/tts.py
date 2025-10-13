from sqlalchemy import Column, Float, Integer, String, Text
from sqlalchemy.sql import func
from sqlalchemy.types import JSON, DateTime

from app.core.database import Base


class TTS(Base):
    __tablename__ = "tts"

    id = Column(Integer, primary_key=True, index=True)
    research_id = Column(Integer, nullable=False)
    summary = Column(Text, nullable=False)
    explainer = Column(Text, nullable=False)
    object_key = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
