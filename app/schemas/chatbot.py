from pydantic import BaseModel, Field


class ChatbotRequest(BaseModel):
    question: str = Field(..., description="User's question about the research paper")


class ChatbotResponse(BaseModel):
    research_id: int = Field(..., description="Research ID used for context")
    research_title: str = Field(..., description="Title of the research paper")
    answer: str = Field(..., description="Chatbot's answer based on research context")
