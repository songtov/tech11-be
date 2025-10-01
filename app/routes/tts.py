from fastapi import APIRouter

router = APIRouter()


@router.get("/tts")
def get_tts():
    return {"message": "tts"}
