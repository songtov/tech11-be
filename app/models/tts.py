from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Enum
from sqlalchemy.sql import func

from app.core.database import Base
from app.schemas.tts import TTSLanguage, TTSStatus


class TTS(Base):
    __tablename__ = "tts"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    language = Column(Enum(TTSLanguage), nullable=False, default=TTSLanguage.KOREAN)
    filename = Column(String(255), nullable=True)
    status = Column(Enum(TTSStatus), nullable=False, default=TTSStatus.PENDING)
    audio_file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    duration = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
