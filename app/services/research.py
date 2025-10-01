from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.research import Research
from app.schemas.research import ResearchCreate, ResearchUpdate


class ResearchService:
    def __init__(self, db: Session):
        self.db = db

    def create_research(self, research: ResearchCreate) -> Research:
        """Create a new research entry"""
        db_research = Research(
            title=research.title,
            abstract=research.abstract
        )
        self.db.add(db_research)
        self.db.commit()
        self.db.refresh(db_research)
        return db_research

    def get_research(self, research_id: int) -> Optional[Research]:
        """Get a research entry by ID"""
        return self.db.query(Research).filter(Research.id == research_id).first()

    def get_all_research(self, skip: int = 0, limit: int = 100) -> List[Research]:
        """Get all research entries with pagination"""
        return self.db.query(Research).offset(skip).limit(limit).all()

    def update_research(self, research_id: int, research_update: ResearchUpdate) -> Optional[Research]:
        """Update a research entry"""
        db_research = self.get_research(research_id)
        if not db_research:
            return None

        update_data = research_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_research, field, value)

        self.db.commit()
        self.db.refresh(db_research)
        return db_research

    def delete_research(self, research_id: int) -> bool:
        """Delete a research entry"""
        db_research = self.get_research(research_id)
        if not db_research:
            return False

        self.db.delete(db_research)
        self.db.commit()
        return True
