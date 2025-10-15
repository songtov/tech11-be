from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.chatbot import (
    ChatbotRequest,
    ChatbotResponse,
    CacheRefreshResponse,
)
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
    research_id: int,
    request: ChatbotRequest,
    db: Session = Depends(get_db)
):
    """
    Chat with a research paper using RAG (Retrieval Augmented Generation) with caching

    **NEW FEATURES:**
    - Vector store caching in S3 for faster responses
    - Conversation history maintained across requests
    - Context-aware responses based on previous questions

    The chatbot will:
    1. Try to load cached vector store from S3 (much faster!)
    2. If not cached, create embeddings and save to S3
    3. Retrieve relevant context based on your question
    4. Consider conversation history for coherent responses
    5. Generate an answer using GPT-4o

    **Request Body Example:**
    ```json
    {
        "question": "이 논문의 주요 내용은 무엇인가요?"
    }
    ```

    The research must have an object_key field (PDF must be downloaded first).
    """
    try:
        if not request.question or request.question.strip() == "":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question cannot be empty"
            )

        service = ChatbotService(db)
        answer = service.chat_with_research(research_id, request.question.strip())
        return ChatbotResponse(
            research_id=research_id,
            research_title=answer.get("title", ""),
            answer=answer.get("answer", ""),
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.post(
    "/chatbot/refresh-cache/{research_id}",
    response_model=CacheRefreshResponse,
    status_code=status.HTTP_200_OK,
)
def refresh_vector_store_cache(research_id: int, db: Session = Depends(get_db)):
    """
    ⚠️ DANGER ZONE: Refresh vector store cache and clear conversation history

    This will:
    1. DELETE the cached vector store from S3
    2. CLEAR the conversation history
    3. Force regeneration of vector store on next chat request

    **This operation is IRREVERSIBLE!**

    **COST WARNING:** Regenerating vector stores incurs embedding API costs!

    Only use this when:
    - The research PDF has been updated
    - The vector store is corrupted
    - Embedding model has changed
    - You want to free up S3 storage
    """
    try:
        service = ChatbotService(db)
        result = service.refresh_vector_store_cache(research_id)
        return CacheRefreshResponse(**result)
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )
