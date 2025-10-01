from fastapi import APIRouter

router = APIRouter()


@router.get("/research")
def get_research():
    return {"message": "Research"}
