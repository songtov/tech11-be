from pydantic import BaseModel, Field

# ============================================================================
# Request Schemas
# ============================================================================


class ChatbotRequest(BaseModel):
    """Request schema for asking questions to the chatbot"""

    question: str = Field(..., description="User's question about the research paper")


# ============================================================================
# Response Schemas
# ============================================================================


class ChatbotResponse(BaseModel):
    """Response schema for chatbot interactions"""

    research_id: int = Field(..., description="Research ID used for context")
    research_title: str = Field(..., description="Title of the research paper")
    answer: str = Field(
        ...,
        description="Chatbot's answer (could be initial greeting or answer to question)",
    )


class CacheRefreshResponse(BaseModel):
    """Response for cache refresh operation"""

    status: str = Field(..., description="Operation status")
    message: str = Field(..., description="Status message in Korean")
    cache_deleted: bool = Field(..., description="Whether cache was deleted from S3")
    history_cleared: bool = Field(
        ..., description="Whether conversation history was cleared"
    )
