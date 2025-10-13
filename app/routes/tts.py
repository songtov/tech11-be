import mimetypes

import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.schemas.tts import TTSResearchRequest
from app.services.tts import TTSService

router = APIRouter(tags=["TTS"], prefix="/tts")


# =====================================================
# 1️⃣ Research ID 기반 TTS 생성 (RECOMMENDED)
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
                "research_id": request.research_id,
                "summary": result["summary"],
                "explainer": result.get("explainer", ""),
                "tts_id": result["tts_id"],
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
# 4️⃣ 음성 파일 다운로드
# =====================================================
@router.get("/stream/{filename}")
def stream_tts(filename: str):
    """
    🎧 생성된 음성 파일 스트리밍
    """
    try:
        # Initialize S3 client
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY,
            aws_secret_access_key=settings.AWS_SECRET_KEY,
        )

        # Construct S3 key for TTS files
        s3_key = f"output/tts/{filename}"

        # Get object from S3
        s3_obj = s3_client.get_object(Bucket=settings.S3_BUCKET, Key=s3_key)
        content = s3_obj["Body"].read()
        content_type = (
            s3_obj.get("ContentType")
            or mimetypes.guess_type(filename)[0]
            or "application/octet-stream"
        )

        return Response(
            content=content,
            media_type=content_type,
            headers={"Content-Disposition": f'inline; filename="{filename}"'},
        )

    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            raise HTTPException(
                status_code=404, detail="음성 파일이 존재하지 않습니다."
            )
        raise HTTPException(status_code=500, detail=f"S3 error: {e}")
