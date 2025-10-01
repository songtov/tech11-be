from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

from app.core.database import Base


class Research(Base):
    __tablename__ = "research"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    abstract = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
