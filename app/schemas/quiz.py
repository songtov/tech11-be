from typing import List

from pydantic import BaseModel, Field, validator


class QuizCreate(BaseModel):
    path: str = Field(
        ..., description="Path to the PDF file (local path or URL)", min_length=1
    )

    @validator("path")
    def validate_path(cls, v):
        if not v or not v.strip():
            raise ValueError("Path cannot be empty")
        return v.strip()


class QuestionResponse(BaseModel):
    question: str = Field(..., description="The quiz question")
    answer: str = Field(..., description="The correct answer")
    explanation: str = Field(..., description="Explanation of the answer")


class QuizResponse(BaseModel):
    data: List[QuestionResponse] = Field(
        ..., description="List of quiz questions and answers"
    )
