from io import BytesIO

from fastapi import APIRouter, Depends, status
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
    """Get video metadata for a research paper"""
    service = VideoService(db)
    return service.get_video_by_research_id(research_id)


@router.get(
    "/video/stream/{research_id}",
    status_code=status.HTTP_200_OK,
)
def stream_video_by_research_id(research_id: int, db: Session = Depends(get_db)):
    """Stream video file from S3 by research_id"""
    service = VideoService(db)
    content, content_type, headers = service.stream_video_by_research_id(research_id)

    # Create a streaming response with proper headers for video playback
    video_stream = BytesIO(content)

    return StreamingResponse(video_stream, media_type=content_type, headers=headers)


@router.post(
    "/video",
    status_code=status.HTTP_201_CREATED,
    response_model=CreateVideoResponse,
)
def create_video_from_research_id(
    video_request: CreateVideoRequest,
    force_regenerate: bool = False,
    db: Session = Depends(get_db),
):
    """Create a video from a research paper. Set force_regenerate=true to regenerate existing videos.
    Use tts_mode='pro' for high-quality Typecast AI TTS (paid) or 'standard' for gTTS (free).
    """
    service = VideoService(db)
    return service.create_video_from_research_id(video_request, force_regenerate)
