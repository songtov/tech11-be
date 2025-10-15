from typing import Optional, Literal

from pydantic import BaseModel, Field


class CreateVideoRequest(BaseModel):
    research_id: int = Field(
        ..., description="ID of the research entry to create a video for", gt=0
    )
    tts_mode: Literal["standard", "pro"] = Field(
        default="standard",
        description="TTS mode: 'standard' uses gTTS (free), 'pro' uses Typecast AI (paid)",
    )


class CreateVideoResponse(BaseModel):
    video_url: str = Field(
        ..., description="URL of the created video (streaming endpoint)"
    )
    research_id: int = Field(..., description="ID of the research paper")
    duration_seconds: Optional[float] = Field(
        None, description="Duration of the video in seconds"
    )
    slide_count: Optional[int] = Field(
        None, description="Number of slides in the presentation"
    )
    status: str = Field(default="completed", description="Status of video generation")
    s3_url: Optional[str] = Field(None, description="S3 URL of the video file")
    object_key: Optional[str] = Field(None, description="S3 object key for the video")
    presigned_url: Optional[str] = Field(
        None, description="Presigned URL for direct S3 access (expires in 1 hour)"
    )
    streaming_url: Optional[str] = Field(
        None, description="Backend streaming endpoint URL"
    )
