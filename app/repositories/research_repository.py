from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.research import Research
from app.schemas.research import DomainEnum


class ResearchRepository:
    """Repository for Research database operations following DDD pattern"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, research_id: int) -> Optional[Research]:
        """Get a research entry by ID"""
        return self.db.query(Research).filter(Research.id == research_id).first()

    def get_by_arxiv_url(self, arxiv_url: str) -> Optional[Research]:
        """Get a research entry by ArXiv URL"""
        return self.db.query(Research).filter(Research.arxiv_url == arxiv_url).first()

    def get_by_domain_and_date(
        self, domain: DomainEnum, target_date: date
    ) -> List[Research]:
        """
        Get research entries by domain for a specific date.
        Uses created_at date comparison.
        """
        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = datetime.combine(target_date, datetime.max.time())

        return (
            self.db.query(Research)
            .filter(
                and_(
                    Research.domain == domain.value,
                    Research.created_at >= start_of_day,
                    Research.created_at <= end_of_day,
                )
            )
            .order_by(Research.relevance_score.desc(), Research.citation_count.desc())
            .all()
        )

    def create(self, research_data: dict) -> Research:
        """Create a new research entry"""
        db_research = Research(**research_data)
        self.db.add(db_research)
        self.db.commit()
        self.db.refresh(db_research)
        return db_research

    def create_bulk(self, research_data_list: List[dict]) -> List[Research]:
        """Create multiple research entries"""
        db_research_list = [Research(**data) for data in research_data_list]
        self.db.add_all(db_research_list)
        self.db.commit()
        for research in db_research_list:
            self.db.refresh(research)
        return db_research_list

    def update(self, research: Research, update_data: dict) -> Research:
        """Update a research entry"""
        for field, value in update_data.items():
            setattr(research, field, value)
        self.db.commit()
        self.db.refresh(research)
        return research

    def update_object_key(self, arxiv_url: str, object_key: str) -> Optional[Research]:
        """Update the S3 object_key for a research entry by arxiv_url"""
        research = self.get_by_arxiv_url(arxiv_url)
        if research:
            research.object_key = object_key
            self.db.commit()
            self.db.refresh(research)
        return research

    def delete(self, research: Research) -> bool:
        """Delete a research entry"""
        self.db.delete(research)
        self.db.commit()
        return True

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Research]:
        """Get all research entries with pagination"""
        return self.db.query(Research).offset(skip).limit(limit).all()
