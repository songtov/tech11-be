from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.summary import SummaryResearchRequest, SummaryResponse
from app.services.summary import SummaryService

router = APIRouter(tags=["summary"])


@router.post(
    "/summary",
    response_model=SummaryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_summary_from_research_id(
    request: SummaryResearchRequest, db: Session = Depends(get_db)
):
    """
    Generate summary from research ID (RECOMMENDED)

    Provide the research ID to fetch the associated PDF file from S3 bucket.
    The research must have an object_key field populated with the S3 path.
    """
    try:
        service = SummaryService(db)
        return service.create_summary_from_research_id(request.research_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )
