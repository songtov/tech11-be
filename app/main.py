# main.py
from fastapi import FastAPI
from app.routes.research import router as research_router

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI with uv!"}

app.include_router(research_router)
