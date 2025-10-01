from fastapi import APIRouter

router = APIRouter()


@router.get("/summary")
def get_summary():
    return {"message": "Summary"}
