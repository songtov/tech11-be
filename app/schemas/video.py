from pydantic import BaseModel, Field


class CreateVideoRequest(BaseModel):
    research_id: int = Field(
        ..., description="ID of the research entry to create a video for", gt=0
    )

class CreateVideoResponse(BaseModel):
    video_url: str = Field(
        ..., description="URL of the created video"
    )
