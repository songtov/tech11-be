from fastapi import APIRouter, HTTPException, status

from app.schemas.quiz import QuizCreate, QuizResponse
from app.services.quiz import QuizService

router = APIRouter()


@router.post(
    "/quiz",
    response_model=QuizResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_quiz(quiz: QuizCreate):
    """Generate quiz from PDF file"""
    try:
        service = QuizService()
        return service.create_quiz(quiz)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )
