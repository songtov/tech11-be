from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.keyword import KeywordExtractFromTextRequest, KeywordResponse
from app.services.keyword import KeywordService

router = APIRouter(tags=["keyword"])


@router.post(
    "/keyword/extract/pdf",
    response_model=KeywordResponse,
    status_code=status.HTTP_200_OK,
)
async def extract_keywords_from_pdf(
    file: UploadFile = File(..., description="PDF 파일을 업로드하세요"),
    db: Session = Depends(get_db),
):
    """
    업로드된 PDF 파일로부터 키워드 추출

    프론트엔드에서 PDF 파일을 업로드하면 백엔드가 파일을 분석하여 핵심 키워드 5개를 추출합니다.
    RAG(Retrieval-Augmented Generation)를 사용하여 PDF 내용을 분석하고,
    영어 키워드와 한글 번역을 함께 제공합니다.

    Args:
        file: UploadFile - 업로드된 PDF 파일

    Returns:
        KeywordResponse: 한글-영어 키워드 매핑 (5개)

    Example:
        POST /keyword/extract/pdf
        Content-Type: multipart/form-data
        file: [PDF 파일]

        Response:
        {
            "keywords": {
                "인공지능": "Artificial Intelligence",
                "기계학습": "Machine Learning",
                "딥러닝": "Deep Learning",
                "신경망": "Neural Network",
                "자연어처리": "Natural Language Processing"
            }
        }
    """
    try:
        service = KeywordService(db)
        return await service.extract_keywords_from_pdf(file)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.post(
    "/keyword/extract/text",
    response_model=KeywordResponse,
    status_code=status.HTTP_200_OK,
)
def extract_keywords_from_text(
    request: KeywordExtractFromTextRequest, db: Session = Depends(get_db)
):
    """
    텍스트로부터 키워드 추출

    제공된 텍스트 또는 검색어를 분석하여 핵심 키워드 5개를 추출합니다.
    영어 키워드와 한글 번역을 함께 제공합니다.

    Args:
        request: KeywordExtractFromTextRequest (text 포함)

    Returns:
        KeywordResponse: 한글-영어 키워드 매핑 (5개)

    Example:
        POST /keyword/extract/text
        {
            "text": "인공지능과 머신러닝을 활용한 자연어 처리 기술의 발전"
        }

        Response:
        {
            "keywords": {
                "인공지능": "Artificial Intelligence",
                "기계학습": "Machine Learning",
                "자연어처리": "Natural Language Processing",
                "딥러닝": "Deep Learning",
                "언어모델": "Language Model"
            }
        }
    """
    try:
        service = KeywordService(db)
        return service.extract_keywords_from_text(request.text)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )
