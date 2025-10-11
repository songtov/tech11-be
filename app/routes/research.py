import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.schemas.research import (
    ResearchDownload,
    ResearchDownloadResponse,
    ResearchSearch,
    ResearchSearchResponse,
)
from app.services.research import ResearchService

router = APIRouter()


@router.post(
    "/research_search",
    response_model=ResearchSearchResponse,
    status_code=status.HTTP_200_OK,
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
    Download a research paper PDF and upload to S3 bucket

    This endpoint downloads a research paper PDF from the provided URL and uploads it to
    the S3 bucket at path: <bucket_name>/output/research/<filename>.pdf

    The filename is generated based on:
    1. Research title (if provided) - cleaned and truncated to 100 characters
    2. arXiv ID (extracted from arxiv_url) - as fallback
    3. Timestamp - as final fallback

    Args:
        research: ResearchDownload object containing pdf_url, arxiv_url, and optional title

    Returns:
        ResearchDownloadResponse with:
        - output_path: S3 URI (s3://<bucket>/output/research/<filename>.pdf)
        - download_url: API endpoint to download the file (/research/files/<filename>)
        - filename: The generated PDF filename

    Raises:
        ValueError: If PDF download fails, URL is invalid, or S3 upload fails
    """
    service = ResearchService(db)
    return service.download_research(research)


# @router.post(
#     "/research", response_model=ResearchResponse, status_code=status.HTTP_201_CREATED
# )
# def create_research(research: ResearchCreate, db: Session = Depends(get_db)):
#     """Create a new research entry"""
#     service = ResearchService(db)
#     return service.create_research(research)


@router.get("/research/files/{filename}")
def download_research_file(filename: str):
    """
    Serve a downloaded research PDF file from S3 bucket

    This endpoint serves PDF files that were uploaded to S3 via the /research_download endpoint.
    Files are stored in the S3 bucket at path: output/research/<filename>

    Args:
        filename: The name of the PDF file to download

    Returns:
        StreamingResponse: The PDF file for download from S3

    Raises:
        HTTPException: If the file is not found or is not a PDF
    """
    # Security: Only serve PDF files
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are allowed"
        )

    # Security: Prevent path traversal attacks
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid filename"
        )

    try:
        # Initialize S3 client
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY,
            aws_secret_access_key=settings.AWS_SECRET_KEY,
        )

        # Construct S3 key path
        s3_key = f"output/research/{filename}"

        # Try to get the file from S3
        try:
            response = s3_client.get_object(Bucket=settings.S3_BUCKET, Key=s3_key)
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "NoSuchKey":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="File not found in S3 bucket",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error accessing S3: {str(e)}",
                )

        # Stream the file content from S3
        file_stream = response["Body"]

        # Return as streaming response
        return StreamingResponse(
            file_stream,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error downloading file from S3: {str(e)}",
        )
