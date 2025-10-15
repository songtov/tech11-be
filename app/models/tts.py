from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

from app.core.database import Base


class TTS(Base):
    __tablename__ = "tts"

    id = Column(Integer, primary_key=True, index=True)
    research_id = Column(Integer, ForeignKey("research.id"), nullable=False, index=True)
    summary = Column(Text, nullable=False)
    explainer = Column(Text, nullable=False)
    object_key = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # 한 research당 1개만 허용하려면 아래 Unique 제약을 활성화하세요
    # __table_args__ = (UniqueConstraint("research_id", name="uq_tts_research_id"),)
