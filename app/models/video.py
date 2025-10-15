from sqlalchemy import Column, Integer, String
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

from app.core.database import Base


class Video(Base):
    __tablename__ = "video"

    id = Column(Integer, primary_key=True, index=True)
    research_id = Column(Integer, nullable=False, index=True)
    object_key = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
