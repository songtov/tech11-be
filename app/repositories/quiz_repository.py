from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.quiz import Quiz


class QuizRepository:
    """Repository for Quiz database operations following DDD pattern"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, quiz_id: int) -> Optional[Quiz]:
        """Get a quiz entry by ID"""
        return self.db.query(Quiz).filter(Quiz.id == quiz_id).first()

    def get_by_research_id(self, research_id: int) -> Optional[Quiz]:
        """Get a quiz entry by research ID (for caching)"""
        return self.db.query(Quiz).filter(Quiz.research_id == research_id).first()

    def create(self, quiz_data: dict) -> Quiz:
        """Create a new quiz entry"""
        db_quiz = Quiz(**quiz_data)
        self.db.add(db_quiz)
        self.db.commit()
        self.db.refresh(db_quiz)
        return db_quiz

    def delete(self, quiz: Quiz) -> bool:
        """Delete a quiz entry"""
        self.db.delete(quiz)
        self.db.commit()
        return True

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Quiz]:
        """Get all quiz entries with pagination"""
        return self.db.query(Quiz).offset(skip).limit(limit).all()
