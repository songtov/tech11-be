import os
import tempfile
from fastapi import (
    APIRouter,
    HTTPException,
    status,
    UploadFile,
    File
)
from fastapi.responses import FileResponse, JSONResponse

from app.schemas.tts import TTSPdfPathRequest
from app.services.tts import TTSService

router = APIRouter(tags=["TTS"], prefix="/tts")


# =====================================================
# 1️⃣ PDF 파일 업로드 방식 (직접 업로드)
# =====================================================
@router.post("/process_pdf/")
async def process_pdf(file: UploadFile = File(...)):
    """
    PDF 파일 업로드 → Multi-Agent 실행 → 요약 + 음성 파일 생성
    """
    try:
        # 임시 파일 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp_path = tmp.name
            content = await file.read()
            tmp.write(content)

        service = TTSService()
        result = await service.process_pdf_to_tts(tmp_path)

        os.unlink(tmp_path)  # 임시 파일 삭제

        return JSONResponse({
            "message": "✅ PDF 업로드 및 TTS 생성 완료",
            "summary": result["summary"],
            "explainer": result.get("explainer", ""),
            "tts_id": result["tts_id"],
            "audio_file": result["audio_filename"],
            "download_url": f"/tts/{result['audio_filename']}/download",
            "stream_url": f"/tts/{result['audio_filename']}/stream"
        })

    except Exception as e:
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF 처리 실패: {str(e)}"
        )


# =====================================================
# 2️⃣ PDF 파일 경로 입력 방식
# =====================================================
@router.post("/from-pdf-path")
async def create_tts_from_pdf_path(request: TTSPdfPathRequest):
    """
    PDF 경로 입력 → Multi-Agent 요약 → TTS 음성 생성 → 결과 반환
    """
    try:
        service = TTSService()

        if not os.path.exists(request.pdf_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"PDF 파일을 찾을 수 없습니다: {request.pdf_path}"
            )

        result = await service.process_pdf_to_tts(request.pdf_path)

        return JSONResponse({
            "message": "✅ PDF 처리 및 TTS 생성 완료",
            "pdf_path": request.pdf_path,
            "summary": result["summary"],
            "explainer": result.get("explainer", ""),
            "tts_id": result["tts_id"],
            "audio_file": result["audio_filename"],
            "download_url": f"/tts/{result['audio_filename']}/download",
            "stream_url": f"/tts/{result['audio_filename']}/stream"
        })

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF to TTS processing failed: {str(e)}"
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
    file_path = service.get_audio_file_by_filename(filename)

    if not file_path:
        raise HTTPException(status_code=404, detail="음성 파일이 존재하지 않습니다.")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="audio/mpeg"
    )


# =====================================================
# 4️⃣ 음성 파일 즉시 재생
# =====================================================
@router.get("/{filename}/stream")
def stream_tts(filename: str):
    """
    🎵 음성 파일 브라우저 즉시 재생용
    """
    service = TTSService()
    file_path = service.get_audio_file_by_filename(filename)

    if not file_path:
        raise HTTPException(status_code=404, detail="음성 파일이 존재하지 않습니다.")

    return FileResponse(
        path=file_path,
        media_type="audio/mpeg",
        filename=filename,
        headers={"Content-Disposition": "inline"}  # ✅ 바로 재생
    )


# =====================================================
# 5️⃣ TTS 시스템 테스트
# =====================================================
@router.get("/test")
async def test_tts_system():
    """
    🔧 TTS 시스템 테스트용
    """
    service = TTSService()
    test_pdf_path = "sample.pdf"  # 예시 (존재하지 않아도 테스트 가능)

    result = await service.process_pdf_to_tts(test_pdf_path)

    return {
        "message": "✅ TTS 테스트 완료",
        "tts_id": result["tts_id"],
        "filename": result["audio_filename"],
        "download_url": f"/tts/{result['audio_filename']}/download",
        "stream_url": f"/tts/{result['audio_filename']}/stream"
    }