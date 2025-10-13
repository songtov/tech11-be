from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.tts import TTSResearchRequest
from app.services.tts import TTSService

router = APIRouter(tags=["TTS"], prefix="/tts")


# =====================================================
# 1️⃣ Research ID 기반 TTS 생성
# =====================================================
@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
)
async def create_tts_from_research_id(
    request: TTSResearchRequest, db: Session = Depends(get_db)
):
    """
    Generate TTS from research ID (RECOMMENDED)

    Provide the research ID to fetch the associated PDF file from S3 bucket.
    The research must have an object_key field populated with the S3 path.
    """
    try:
        service = TTSService(db)
        result = await service.create_tts_from_research_id(request.research_id)

        return JSONResponse(
            {
                "message": "✅ TTS 생성 완료",
                "id": result.get("id"),
                "research_id": request.research_id,
                "summary": result["summary"],
                "explainer": result.get("explainer", ""),
                "audio_filename": result["audio_filename"],
                "s3_url": result.get("s3_url"),
                "presigned_url": result.get("presigned_url"),
            }
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


# =====================================================
# 2️⃣ 음성 파일 스트리밍
# =====================================================
@router.get("/stream/{filename}")
def stream_tts(filename: str, db: Session = Depends(get_db)):
    """
    🎧 생성된 음성 파일 스트리밍
    """
    try:
        service = TTSService(db)
        content, content_type, headers = service.stream_audio_from_s3(filename)

        return Response(
            content=content,
            media_type=content_type,
            headers=headers,
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
