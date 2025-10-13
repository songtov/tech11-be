from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.tts import TTS


class TTSRepository:
    """Repository for TTS database operations following DDD pattern"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, tts_id: int) -> Optional[TTS]:
        """Get a TTS entry by ID"""
        return self.db.query(TTS).filter(TTS.id == tts_id).first()

    def get_by_research_id(self, research_id: int) -> Optional[TTS]:
        """Get a TTS entry by research ID"""
        return self.db.query(TTS).filter(TTS.research_id == research_id).first()

    def create(self, tts_data: dict) -> TTS:
        """Create a new TTS entry"""
        db_tts = TTS(**tts_data)
        self.db.add(db_tts)
        self.db.commit()
        self.db.refresh(db_tts)
        return db_tts

    def get_all(self, skip: int = 0, limit: int = 100) -> List[TTS]:
        """Get all TTS entries with pagination"""
        return self.db.query(TTS).offset(skip).limit(limit).all()

    def update(self, tts: TTS, update_data: dict) -> TTS:
        """Update a TTS entry"""
        for field, value in update_data.items():
            setattr(tts, field, value)
        self.db.commit()
        self.db.refresh(tts)
        return tts

    def delete(self, tts: TTS) -> bool:
        """Delete a TTS entry"""
        self.db.delete(tts)
        self.db.commit()
        return True
