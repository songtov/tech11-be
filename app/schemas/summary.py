from pydantic import BaseModel, Field, validator


class SummaryCreate(BaseModel):
    filename: str = Field(
        ...,
        description="Filename of the PDF in S3 bucket (e.g., 'research_paper.pdf')",
        min_length=1,
    )

    @validator("filename")
    def validate_filename(cls, v):
        if not v or not v.strip():
            raise ValueError("Filename cannot be empty")

        # Validate it's a PDF file
        if not v.strip().lower().endswith(".pdf"):
            raise ValueError("Filename must end with .pdf")

        return v.strip()


class SummaryResponse(BaseModel):
    title: str = Field(..., description="Summary title")
    summary: str = Field(..., description="Summarized content")
    pdf_link: str | None = Field(
        None, description="Link or path to generated PDF (optional)"
    )
