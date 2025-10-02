from typing import List
from pydantic import BaseModel


class QuizCreate(BaseModel):
    path: str


class QuestionResponse(BaseModel):
    question: str
    answer: str
    explanation: str

class QuizResponse(BaseModel):
    data: List[QuestionResponse]
