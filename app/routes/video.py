from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.video import CreateVideoRequest, CreateVideoResponse
from app.services.video import VideoService

router = APIRouter(tags=["video"])


@router.get(
    "/video/{research_id}",
    status_code=status.HTTP_200_OK,
    response_model=CreateVideoResponse,
)
def get_video_by_research_id(research_id: int, db: Session = Depends(get_db)):
    """Get a video from a research paper"""
    service = VideoService(db)
    return service.get_video_by_research_id(research_id)

@router.post(
    "/video",
    status_code=status.HTTP_201_CREATED,
    response_model=CreateVideoResponse,
)
def create_video_from_research_id(video_request: CreateVideoRequest, db: Session = Depends(get_db)):
    """Create a video from a research paper"""
    service = VideoService(db)
    return service.create_video_from_research_id(video_request)

