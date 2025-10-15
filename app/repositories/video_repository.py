from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.video import Video


class VideoRepository:
    """Repository for Video database operations following DDD pattern"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, video_id: int) -> Optional[Video]:
        """Get a video entry by ID"""
        return self.db.query(Video).filter(Video.id == video_id).first()

    def get_by_research_id(self, research_id: int) -> Optional[Video]:
        """Get a video entry by research ID"""
        return self.db.query(Video).filter(Video.research_id == research_id).first()

    def create(self, video_data: dict) -> Video:
        """Create a new video entry"""
        db_video = Video(**video_data)
        self.db.add(db_video)
        self.db.commit()
        self.db.refresh(db_video)
        return db_video

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Video]:
        """Get all video entries with pagination"""
        return self.db.query(Video).offset(skip).limit(limit).all()

    def update(self, video: Video, update_data: dict) -> Video:
        """Update a video entry"""
        for field, value in update_data.items():
            setattr(video, field, value)
        self.db.commit()
        self.db.refresh(video)
        return video

    def delete(self, video: Video) -> bool:
        """Delete a video entry"""
        self.db.delete(video)
        self.db.commit()
        return True
