from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.chatbot import ChatbotRequest, ChatbotResponse
from app.services.chatbot import ChatbotService

router = APIRouter(tags=["chatbot"])


@router.post(
    "/chatbot/{research_id}",
    response_model=ChatbotResponse,
    status_code=status.HTTP_200_OK,
)
def create_chatbot_from_research_id(research_id: int, db: Session = Depends(get_db)):
    """
    Validate chatbot can be created from research ID (RECOMMENDED)

    Provide the research ID to validate the associated PDF file exists in S3 bucket.
    The research must have an object_key field populated with the S3 path.

    This endpoint validates the research and returns a context summary.
    Use the /chatbot/chat/{research_id} endpoint to ask questions about the research.
    """
    try:
        service = ChatbotService(db)
        result = service.create_chatbot_from_research_id(research_id)
        return ChatbotResponse(
            research_id=research_id,
            research_title=result["title"],
            answer=result["answer"],
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.post(
    "/chatbot/chat/{research_id}",
    response_model=ChatbotResponse,
    status_code=status.HTTP_200_OK,
)
def chat_with_research(
    research_id: int, request: ChatbotRequest, db: Session = Depends(get_db)
):
    """
    Chat with a research paper using RAG (Retrieval Augmented Generation)

    Provide the research ID in the path and your question in the request body.
    The chatbot will:
    1. Load the research PDF from S3
    2. Create embeddings and vector store
    3. Retrieve relevant context
    4. Generate an answer using GPT-4o

    The research must have an object_key field (PDF must be downloaded first).
    """
    try:
        service = ChatbotService(db)
        answer = service.chat_with_research(research_id, request.question)
        return ChatbotResponse(
            research_id=research_id,
            research_title=answer.get("title", ""),
            answer=answer.get("answer", ""),
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )
