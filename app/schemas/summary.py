from pydantic import BaseModel, Field, validator

class SummaryCreate(BaseModel):
    path: str = Field(..., description="Path to the PDF file (local path or URL)", min_length=1)

    @validator("path")
    def validate_path(cls, v):
        if not v or not v.strip():
            raise ValueError("Path cannot be empty")
        return v.strip()

class SummaryResponse(BaseModel):
    title: str = Field(..., description="Summary title")
    summary: str = Field(..., description="Summarized content")
    pdf_link: str | None = Field(None, description="Link or path to generated PDF (optional)")
