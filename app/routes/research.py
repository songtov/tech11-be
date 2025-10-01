from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.research import ResearchCreate, ResearchResponse, ResearchUpdate
from app.services.research import ResearchService

router = APIRouter()


@router.post("/research", response_model=ResearchResponse, status_code=status.HTTP_201_CREATED)
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research not found"
        )
    return research


@router.get("/research", response_model=List[ResearchResponse])
def get_all_research(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all research entries with pagination"""
    service = ResearchService(db)
    return service.get_all_research(skip=skip, limit=limit)


@router.put("/research/{research_id}", response_model=ResearchResponse)
def update_research(research_id: int, research_update: ResearchUpdate, db: Session = Depends(get_db)):
    """Update a research entry"""
    service = ResearchService(db)
    research = service.update_research(research_id, research_update)
    if not research:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research not found"
        )
    return research


@router.delete("/research/{research_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_research(research_id: int, db: Session = Depends(get_db)):
    """Delete a research entry"""
    service = ResearchService(db)
    if not service.delete_research(research_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research not found"
        )
