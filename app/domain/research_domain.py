from dataclasses import dataclass
from datetime import datetime
from typing import List

from app.models.research import Research
from app.schemas.research import DomainEnum, ResearchResponse


@dataclass
class PaperData:
    """Domain entity for paper data"""

    title: str
    abstract: str
    domain: str
    authors: List[str]
    published_date: str
    updated_date: str
    categories: List[str]
    pdf_url: str
    arxiv_url: str
    citation_count: int = 0
    relevance_score: float = 0.0


class ResearchDomain:
    """Domain logic for Research entities"""

    @staticmethod
    def to_response(research: Research) -> ResearchResponse:
        """
        Convert Research model to ResearchResponse schema
        """
        # Parse created_at for response
        try:
            if research.created_at:
                created_at = research.created_at
            else:
                created_at = datetime.now()
        except (ValueError, AttributeError):
            created_at = datetime.now()

        # Parse updated_at for response
        try:
            if research.updated_at:
                updated_at = research.updated_at
            else:
                updated_at = datetime.now()
        except (ValueError, AttributeError):
            updated_at = datetime.now()

        return ResearchResponse(
            id=research.id,
            title=research.title,
            abstract=research.abstract,
            authors=research.authors or [],
            published_date=research.published_date,
            updated_date=research.updated_date,
            categories=research.categories or [],
            pdf_url=research.pdf_url,
            arxiv_url=research.arxiv_url,
            citation_count=research.citation_count,
            relevance_score=research.relevance_score,
            created_at=created_at,
            updated_at=updated_at,
        )

    @staticmethod
    def to_response_list(research_list: List[Research]) -> List[ResearchResponse]:
        """Convert list of Research models to list of ResearchResponse schemas"""
        return [ResearchDomain.to_response(research) for research in research_list]

    @staticmethod
    def paper_to_dict(paper_data: PaperData) -> dict:
        """Convert PaperData domain entity to dictionary for repository"""
        return {
            "title": paper_data.title,
            "abstract": paper_data.abstract or "No abstract available",
            "domain": paper_data.domain,
            "authors": paper_data.authors,
            "published_date": paper_data.published_date,
            "updated_date": paper_data.updated_date,
            "categories": paper_data.categories,
            "pdf_url": paper_data.pdf_url,
            "arxiv_url": paper_data.arxiv_url,
            "citation_count": paper_data.citation_count,
            "relevance_score": paper_data.relevance_score,
        }

    @staticmethod
    def validate_paper_count(papers: List[Research], required_count: int = 5) -> bool:
        """Check if we have enough papers"""
        return len(papers) >= required_count

    @staticmethod
    def create_dummy_response(
        domain: DomainEnum, message: str, count: int = 5
    ) -> List[ResearchResponse]:
        """Create dummy response entries for error/empty cases"""
        dummy_responses = []
        for i in range(count):
            dummy_responses.append(
                ResearchResponse(
                    id=i + 1,
                    title=f"{message} - {domain.value}",
                    abstract=message,
                    authors=[],
                    published_date=None,
                    updated_date=None,
                    categories=[],
                    pdf_url=None,
                    arxiv_url=None,
                    citation_count=0,
                    relevance_score=0.0,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
            )
        return dummy_responses
