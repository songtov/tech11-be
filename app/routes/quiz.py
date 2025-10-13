from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.quiz import QuizResearchRequest, QuizResponse
from app.services.quiz import QuizService

router = APIRouter(tags=["quiz"])


@router.post(
    "/quiz",
    response_model=QuizResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_quiz_from_research_id(
    request: QuizResearchRequest, db: Session = Depends(get_db)
):
    """
    Generate quiz from research ID (RECOMMENDED)

    Provide the research ID to fetch the associated PDF file from S3 bucket.
    The research must have an object_key field populated with the S3 path.
    """
    try:
        service = QuizService(db)
        return service.create_quiz_from_research_id(request.research_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )
