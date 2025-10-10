import os

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse, RedirectResponse

from app.schemas.tts import TTSFilenameRequest, TTSPdfPathRequest
from app.services.tts import TTSService

router = APIRouter(tags=["TTS"], prefix="/tts")


# =====================================================
# 1️⃣ S3 기반 PDF 파일 처리 (NEW - RECOMMENDED)
# =====================================================
@router.post("/from-s3")
async def create_tts_from_s3(request: TTSFilenameRequest):
    """
    S3 PDF 파일명 입력 → S3에서 다운로드 → Multi-Agent 요약 → TTS 음성 생성 → S3 업로드
    """
    try:
        service = TTSService()
        result = await service.process_pdf_from_s3_to_tts(request.filename)

        return JSONResponse(
            {
                "message": "✅ S3 PDF 처리 및 TTS 생성 완료",
                "pdf_filename": request.filename,
                "summary": result["summary"],
                "explainer": result.get("explainer", ""),
                "tts_id": result["tts_id"],
                "audio_filename": result["audio_filename"],
                "s3_url": result.get("s3_url"),
                "presigned_url": result.get("presigned_url"),
                "download_url": f"/tts/{result['audio_filename']}/download",
                "stream_url": f"/tts/{result['audio_filename']}/stream",
            }
        )

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"S3 PDF to TTS processing failed: {str(e)}",
        )


# =====================================================
# 2️⃣ PDF 파일 경로 입력 방식 (LEGACY - for backward compatibility)
# =====================================================
@router.post("/from-pdf-path")
async def create_tts_from_pdf_path(request: TTSPdfPathRequest):
    """
    PDF 경로 입력 → Multi-Agent 요약 → TTS 음성 생성 → 결과 반환
    (Legacy endpoint for backward compatibility - use /from-s3 for new implementations)
    """
    try:
        service = TTSService()

        if not os.path.exists(request.pdf_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"PDF 파일을 찾을 수 없습니다: {request.pdf_path}",
            )

        result = await service.process_pdf_to_tts(request.pdf_path)

        return JSONResponse(
            {
                "message": "✅ PDF 처리 및 TTS 생성 완료",
                "pdf_path": request.pdf_path,
                "summary": result["summary"],
                "explainer": result.get("explainer", ""),
                "tts_id": result["tts_id"],
                "audio_file": result["audio_filename"],
                "download_url": f"/tts/{result['audio_filename']}/download",
                "stream_url": f"/tts/{result['audio_filename']}/stream",
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF to TTS processing failed: {str(e)}",
        )


# =====================================================
# 3️⃣ 음성 파일 다운로드
# =====================================================
@router.get("/{filename}/download")
def download_tts(filename: str):
    """
    🎧 생성된 음성 파일 다운로드
    """
    service = TTSService()

    # S3에서 확인
    presigned_url = service._get_audio_url_from_s3(filename)
    if presigned_url:
        return RedirectResponse(url=presigned_url)

    # 둘 다 없으면 404
    raise HTTPException(status_code=404, detail="음성 파일이 존재하지 않습니다.")


# =====================================================
# 4️⃣ 음성 파일 즉시 재생
# =====================================================
@router.get("/{filename}/stream")
def stream_tts(filename: str):
    """
    🎵 음성 파일 브라우저 즉시 재생용
    """
    service = TTSService()

    # S3에서 확인
    presigned_url = service._get_audio_url_from_s3(filename)
    if presigned_url:
        return RedirectResponse(url=presigned_url)

    # 둘 다 없으면 404
    raise HTTPException(status_code=404, detail="음성 파일이 존재하지 않습니다.")
