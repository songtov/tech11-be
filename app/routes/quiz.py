from fastapi import APIRouter, status
from app.schemas.quiz import QuizCreate, QuizResponse
from app.services.quiz import QuizService

router = APIRouter()


@router.post(
    "/quiz",
    response_model=QuizResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_quiz(quiz: QuizCreate):
    service = QuizService()
    return service.create_quiz(quiz)

