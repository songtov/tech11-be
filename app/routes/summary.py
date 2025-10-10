from fastapi import APIRouter, HTTPException, status

from app.schemas.summary import SummaryCreate, SummaryResponse
from app.services.summary import SummaryService

router = APIRouter()


@router.post(
    "/summary",
    response_model=SummaryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_summary(summary: SummaryCreate):
    """Generate a summarized report from PDF file"""
    try:
        service = SummaryService()
        return service.create_summary(summary)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )
