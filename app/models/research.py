from sqlalchemy import Column, Float, Integer, String, Text
from sqlalchemy.sql import func
from sqlalchemy.types import JSON, DateTime

from app.core.database import Base


class Research(Base):
    __tablename__ = "research"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    abstract = Column(Text, nullable=False)
    domain = Column(String(50), nullable=False, index=True)
    authors = Column(JSON, nullable=True)
    published_date = Column(String(50), nullable=True)
    updated_date = Column(String(50), nullable=True)
    categories = Column(JSON, nullable=True)
    pdf_url = Column(String(500), nullable=True)
    arxiv_url = Column(String(500), nullable=True, index=True)
    citation_count = Column(Integer, default=0, nullable=False)
    relevance_score = Column(Float, default=0.0, nullable=False)
    object_key = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
