from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.research import (
    ResearchCreate,
    ResearchDownload,
    ResearchDownloadResponse,
    ResearchResponse,
    ResearchSearch,
    ResearchSearchResponse,
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


@router.get("/research/files/{filename}")
def download_research_file(filename: str):
    """
    Serve a downloaded research PDF file

    This endpoint serves PDF files that were downloaded via the /research_download endpoint.
    Files are stored in the output/research directory.

    Args:
        filename: The name of the PDF file to download

    Returns:
        FileResponse: The PDF file for download

    Raises:
        HTTPException: If the file is not found or is not a PDF
    """
    # Construct the file path
    file_path = Path("output/research") / filename

    # Security: Check if file exists and is within the output/research directory
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
        )

    # Security: Ensure the resolved path is still within output/research
    try:
        file_path = file_path.resolve()
        output_dir = Path("output/research").resolve()
        if not str(file_path).startswith(str(output_dir)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid file path"
        )

    # Security: Only serve PDF files
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are allowed"
        )

    # Return the file as a downloadable attachment
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
