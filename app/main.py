# main.py
from fastapi import FastAPI

from app.routes.quiz import router as quiz_router
from app.routes.research import router as research_router
from app.routes.summary import router as summary_router
from app.routes.tts import router as tts_router

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI with uv!"}


app.include_router(research_router)
app.include_router(quiz_router)
app.include_router(tts_router)
app.include_router(summary_router)
