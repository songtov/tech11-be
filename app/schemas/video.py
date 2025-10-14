from typing import Optional

from pydantic import BaseModel, Field


class CreateVideoRequest(BaseModel):
    research_id: int = Field(
        ..., description="ID of the research entry to create a video for", gt=0
    )


class CreateVideoResponse(BaseModel):
    video_url: str = Field(..., description="URL of the created video")
    research_id: int = Field(..., description="ID of the research paper")
    duration_seconds: Optional[float] = Field(
        None, description="Duration of the video in seconds"
    )
    slide_count: Optional[int] = Field(
        None, description="Number of slides in the presentation"
    )
    status: str = Field(default="completed", description="Status of video generation")
