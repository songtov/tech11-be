import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.schemas.research import (
    ResearchDownload,
    ResearchDownloadByIdRequest,
    ResearchDownloadResponse,
    ResearchSearch,
    ResearchSearchResponse,
)
from app.services.research import ResearchService

router = APIRouter(tags=["research"])


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
    "/research/download/{research_id}",
    response_model=ResearchDownloadResponse,
    status_code=status.HTTP_200_OK,
)
def download_research_by_id(
    research_id: int, db: Session = Depends(get_db)
):
    """
    Download a research paper PDF by research ID and upload to S3 bucket (RECOMMENDED)

    This endpoint fetches a research entry by ID from the database and downloads its PDF
    to the S3 bucket at path: <bucket_name>/output/research/<filename>.pdf

    The research must have a pdf_url field populated with the PDF download URL.

    Args:
        request: ResearchDownloadByIdRequest containing the research ID

    Returns:
        ResearchDownloadResponse with:
        - output_path: S3 URI (s3://<bucket>/output/research/<filename>.pdf)
        - download_url: API endpoint to download the file (/research/files/<filename>)
        - filename: The generated PDF filename

    Raises:
        HTTPException: 404 if research not found, 400 if missing pdf_url, 500 for other errors
    """
    try:
        service = ResearchService(db)
        return service.download_research_by_id(research_id)
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.get("/research/files/{research_id}")
def download_research_file_by_id(research_id: int, db: Session = Depends(get_db)):
    """
    Serve a downloaded research PDF file from S3 bucket by research ID (RECOMMENDED)

    This endpoint fetches a research entry by ID from the database and serves its PDF
    file from S3 bucket. The research must have an object_key field populated with the S3 path.

    Args:
        research_id: The ID of the research entry to download PDF for

    Returns:
        StreamingResponse: The PDF file for download from S3

    Raises:
        HTTPException: 404 if research not found or file not found, 400 if missing object_key, 500 for other errors
    """
    try:
        service = ResearchService(db)
        file_stream, filename = service.get_research_file_stream(research_id)

        # Return as streaming response
        return StreamingResponse(
            file_stream,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving research file: {str(e)}",
        )
