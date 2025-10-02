from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.research import (
    ResearchCreate,
    ResearchResponse,
    ResearchSearch,
    ResearchSearchResponse,
    ResearchDownload,
    ResearchDownloadResponse,
)
from app.services.research import ResearchService

router = APIRouter()


@router.post(
    "/research_search",
    response_model=ResearchSearchResponse,
    status_code=status.HTTP_201_CREATED,
)
def search_research(research: ResearchSearch, db: Session = Depends(get_db)):
    """Search for research entries"""
    service = ResearchService(db)
    return service.search_research(research)


@router.post(
    "/research_download",
    response_model=ResearchDownloadResponse,
    status_code=status.HTTP_200_OK,
)
def download_research(research: ResearchDownload, db: Session = Depends(get_db)):
    """
    Download a research paper PDF to output/research directory

    This endpoint downloads a research paper PDF from the provided URL and saves it to
    the output/research/<research_title>.pdf directory. The filename is generated based on:
    1. Research title (if provided) - cleaned and truncated to 100 characters
    2. arXiv ID (extracted from arxiv_url) - as fallback
    3. Timestamp - as final fallback

    Args:
        research: ResearchDownload object containing pdf_url, arxiv_url, and optional title

    Returns:
        ResearchDownloadResponse with the absolute path of the downloaded PDF

    Raises:
        ValueError: If PDF download fails or URL is invalid
    """
    service = ResearchService(db)
    return service.download_research(research)


@router.post(
    "/research", response_model=ResearchResponse, status_code=status.HTTP_201_CREATED
)
def create_research(research: ResearchCreate, db: Session = Depends(get_db)):
    """Create a new research entry"""
    service = ResearchService(db)
    return service.create_research(research)


@router.get("/research/{research_id}", response_model=ResearchResponse)
def get_research(research_id: int, db: Session = Depends(get_db)):
    """Get a research entry by ID"""
    service = ResearchService(db)
    research = service.get_research(research_id)
    if not research:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Research not found"
        )
    return research


@router.get("/research", response_model=List[ResearchResponse])
def get_all_research(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all research entries with pagination"""
    service = ResearchService(db)
    return service.get_all_research(skip=skip, limit=limit)


@router.delete("/research/{research_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_research(research_id: int, db: Session = Depends(get_db)):
    """Delete a research entry"""
    service = ResearchService(db)
    if not service.delete_research(research_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Research not found"
        )
