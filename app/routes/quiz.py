from fastapi import APIRouter, HTTPException, status

from app.schemas.quiz import QuizCreate, QuizFilenameRequest, QuizResponse
from app.services.quiz import QuizService

router = APIRouter(tags=["quiz"])


@router.post(
    "/quiz/from-s3",
    response_model=QuizResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_quiz_from_s3(request: QuizFilenameRequest):
    """
    Generate quiz from PDF file in S3 bucket (RECOMMENDED)

    Provide the filename of the PDF stored in S3 bucket at s3://bucket/output/research/
    """
    try:
        service = QuizService()
        return service.create_quiz_from_s3(request.filename)
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.post(
    "/quiz",
    response_model=QuizResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_quiz(quiz: QuizCreate):
    """
    Generate quiz from PDF file (LEGACY - for backward compatibility)

    Use /quiz/from-s3 for new implementations
    """
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
