from fastapi import APIRouter

router = APIRouter()


@router.get("/quiz")
def get_quiz():
    return {"message": "Quiz"}
