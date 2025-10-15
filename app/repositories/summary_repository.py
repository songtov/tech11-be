from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.summary import Summary


class SummaryRepository:
    """Repository for Summary database operations following DDD pattern"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, summary_id: int) -> Optional[Summary]:
        """Get a summary entry by ID"""
        return self.db.query(Summary).filter(Summary.id == summary_id).first()

    def get_by_research_id(self, research_id: int) -> List[Summary]:
        """Get all summaries for a specific research entry"""
        return (
            self.db.query(Summary)
            .filter(Summary.research_id == research_id)
            .order_by(Summary.created_at.desc())
            .all()
        )

    def get_by_title(self, title: str) -> List[Summary]:
        """Get summaries by title (partial match)"""
        return (
            self.db.query(Summary)
            .filter(Summary.title.contains(title))
            .order_by(Summary.created_at.desc())
            .all()
        )

    def create(self, summary_data: dict) -> Summary:
        """Create a new summary entry"""
        db_summary = Summary(**summary_data)
        self.db.add(db_summary)
        self.db.commit()
        self.db.refresh(db_summary)
        return db_summary

    def create_bulk(self, summary_data_list: List[dict]) -> List[Summary]:
        """Create multiple summary entries"""
        db_summary_list = [Summary(**data) for data in summary_data_list]
        self.db.add_all(db_summary_list)
        self.db.commit()
        for summary in db_summary_list:
            self.db.refresh(summary)
        return db_summary_list

    def update(self, summary: Summary, update_data: dict) -> Summary:
        """Update a summary entry"""
        for field, value in update_data.items():
            setattr(summary, field, value)
        self.db.commit()
        self.db.refresh(summary)
        return summary

    def update_pdf_link(self, summary_id: int, pdf_link: str) -> Optional[Summary]:
        """Update the PDF link for a summary entry"""
        summary = self.get_by_id(summary_id)
        if summary:
            summary.pdf_link = pdf_link
            self.db.commit()
            self.db.refresh(summary)
        return summary

    def delete(self, summary: Summary) -> bool:
        """Delete a summary entry"""
        self.db.delete(summary)
        self.db.commit()
        return True

    def delete_by_research_id(self, research_id: int) -> int:
        """Delete all summaries for a specific research entry"""
        deleted_count = (
            self.db.query(Summary).filter(Summary.research_id == research_id).delete()
        )
        self.db.commit()
        return deleted_count

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Summary]:
        """Get all summary entries with pagination"""
        return (
            self.db.query(Summary)
            .order_by(Summary.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_recent(self, limit: int = 10) -> List[Summary]:
        """Get recent summaries"""
        return (
            self.db.query(Summary)
            .order_by(Summary.created_at.desc())
            .limit(limit)
            .all()
        )
