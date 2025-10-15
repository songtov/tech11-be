from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

from app.core.database import Base


class Summary(Base):
    __tablename__ = "summary"

    id = Column(Integer, primary_key=True, index=True)
    research_id = Column(Integer, ForeignKey("research.id"), nullable=False, index=True)
    title = Column(String(500), nullable=False, index=True)
    summary = Column(Text, nullable=False)
    pdf_link = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
