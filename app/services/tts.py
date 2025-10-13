from __future__ import annotations

import logging
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError
from gtts import gTTS
from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories.research_repository import ResearchRepository

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===========================================================
# ✅ S3 기반 TTS 서비스
# ===========================================================


def clean_text(text: str) -> str:
    """TTS용 텍스트 정제"""
    cleaned = re.sub(r"[#*>•\-]+", " ", text)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


class TTSService:
    def __init__(self, db: Session = None):
        self.db = db
        self.output_dir = Path("output/tts")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.legacy_papers_dir = Path("legacy/downloaded_papers")

        # Initialize database repository if db session provided
        self.research_repository = ResearchRepository(db) if db else None

        # Initialize S3 client
        self.s3_client = None
        if settings.AWS_ACCESS_KEY and settings.AWS_SECRET_KEY:
            self.s3_client = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY,
                aws_secret_access_key=settings.AWS_SECRET_KEY,
            )

    # =====================================================
    # 0️⃣ S3 Helper Methods
    # =====================================================
    def _download_pdf_from_s3(self, filename: str) -> str:
        """Download PDF file from S3 bucket and return temporary file path"""
        # Validate S3 configuration
        if not settings.S3_BUCKET:
            raise ValueError(
                "S3_BUCKET environment variable is not configured. "
                "Please set S3_BUCKET in your environment variables."
            )
        if not self.s3_client:
            raise ValueError(
                "AWS credentials are not configured. "
                "Please set AWS_ACCESS_KEY and AWS_SECRET_KEY in your environment variables."
            )

        # Construct S3 key
        s3_key = f"output/research/{filename}"

        logger.info(f"📥 Downloading PDF from S3: s3://{settings.S3_BUCKET}/{s3_key}")

        try:
            # Check if file exists in S3
            self.s3_client.head_object(Bucket=settings.S3_BUCKET, Key=s3_key)
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "404":
                raise FileNotFoundError(
                    f"PDF file '{filename}' not found in S3 bucket. "
                    f"Expected location: s3://{settings.S3_BUCKET}/{s3_key}"
                )
            else:
                raise ValueError(f"Error accessing S3 file: {str(e)}")

        # Download PDF from S3 to temporary file
        try:
            # Create temporary file
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")

            # Download from S3
            self.s3_client.download_fileobj(settings.S3_BUCKET, s3_key, tmp)
            tmp.flush()
            tmp.close()

            logger.info("✅ PDF downloaded successfully from S3")
            return tmp.name

        except Exception as e:
            # Clean up temporary file if it exists
            if tmp and os.path.exists(tmp.name):
                os.unlink(tmp.name)
            raise ValueError(f"Failed to download PDF from S3: {str(e)}")

    def _upload_audio_to_s3(self, local_file_path: str, filename: str) -> str:
        """Upload audio file to S3 bucket and return S3 URL"""
        if not settings.S3_BUCKET:
            raise ValueError("S3_BUCKET environment variable is not configured.")
        if not self.s3_client:
            raise ValueError("AWS credentials are not configured.")

        # Construct S3 key for TTS audio files
        s3_key = f"output/tts/{filename}"

        logger.info(f"📤 Uploading audio to S3: s3://{settings.S3_BUCKET}/{s3_key}")

        try:
            # Upload file to S3
            self.s3_client.upload_file(
                local_file_path,
                settings.S3_BUCKET,
                s3_key,
                ExtraArgs={"ContentType": "audio/mpeg"},
            )

            # Generate S3 URL
            s3_url = f"s3://{settings.S3_BUCKET}/{s3_key}"
            logger.info(f"✅ Audio uploaded successfully to S3: {s3_url}")

            return s3_url

        except Exception as e:
            raise ValueError(f"Failed to upload audio to S3: {str(e)}")

    def _get_audio_url_from_s3(self, filename: str) -> str | None:
        """Generate presigned URL for audio file in S3"""
        if not settings.S3_BUCKET or not self.s3_client:
            return None

        s3_key = f"output/tts/{filename}"

        try:
            # Check if file exists
            self.s3_client.head_object(Bucket=settings.S3_BUCKET, Key=s3_key)

            # Generate presigned URL (valid for 1 hour)
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": settings.S3_BUCKET, "Key": s3_key},
                ExpiresIn=3600,
            )
            return url
        except ClientError:
            return None

    # =====================================================
    # 1️⃣ 멀티에이전트 실행 (임시 더미 구현 or 실제 호출)
    # =====================================================
    async def _run_legacy_multi_agent(self, pdf_path: str) -> Dict[str, Any]:
        """
        Legacy multitest.py의 run_multi_agent 함수를 직접 호출
        PDF → 벡터스토어 → summary/quiz/explainer 생성
        """
        try:
            import sys

            # Set environment variables for legacy code to access
            os.environ["AOAI_ENDPOINT"] = settings.AOAI_ENDPOINT
            os.environ["AOAI_API_KEY"] = settings.AOAI_API_KEY
            os.environ["AOAI_DEPLOY_GPT4O_MINI"] = settings.AOAI_DEPLOY_GPT4O_MINI
            os.environ["AOAI_DEPLOY_GPT4O"] = settings.AOAI_DEPLOY_GPT4O
            os.environ["AOAI_DEPLOY_EMBED_3_LARGE"] = settings.AOAI_DEPLOY_EMBED_3_LARGE

            legacy_path = Path(__file__).parent.parent.parent / "legacy"
            sys.path.insert(0, str(legacy_path))

            from multitest import run_multi_agent  # type: ignore

            logger.info(f"🎯 Legacy 멀티에이전트 실행 시작: {pdf_path}")
            final_state = run_multi_agent(pdf_path)
            logger.info("✅ Legacy 멀티에이전트 실행 완료")

            return {
                "summary": final_state.get("summary", ""),
                "explainer": final_state.get("explainer", ""),
                "quiz": final_state.get("quiz", ""),
            }
        except Exception as e:
            logger.error(f"❌ Legacy 멀티에이전트 실행 실패: {e}")
            raise e

    # =====================================================
    # 2️⃣ PDF → 멀티에이전트 → TTS 변환 전체 흐름
    # =====================================================
    async def process_pdf_to_tts(self, pdf_path: str) -> Dict[str, Any]:
        """
        Legacy multitest.py의 node_tts 로직을 정확히 따름
        PDF → 멀티에이전트 → explainer만 TTS 변환
        (Local file path version for backward compatibility)
        """
        try:
            # 1. 멀티에이전트 실행 (legacy run_multi_agent 호출)
            logger.info(f"📘 Processing PDF: {pdf_path}")
            agent_result = await self._run_legacy_multi_agent(pdf_path)

            # 2. Legacy node_tts와 동일: explainer만 사용
            script = agent_result.get("explainer", "")
            if not script:
                # Legacy와 동일: explainer가 없으면 빈 결과 반환
                return {
                    "summary": agent_result.get("summary", ""),
                    "explainer": "",
                    "tts_id": None,
                    "audio_filename": None,
                    "audio_file_path": None,
                }

            # 3. Legacy node_tts와 동일: clean_text 적용
            script_clean = clean_text(script)

            # 4. Legacy node_tts와 동일: 파일명 생성
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_filename = f"industry_explainer_{ts}.mp3"
            file_path = self.output_dir / audio_filename

            # 5. Legacy node_tts와 동일: gTTS 생성 및 저장
            tts = gTTS(text=script_clean, lang="ko")
            tts.save(str(file_path))
            logger.info(f"🎧 TTS 저장 완료: {audio_filename}")

            return {
                "summary": agent_result.get("summary", ""),
                "explainer": script,
                "tts_id": ts,
                "audio_filename": audio_filename,
                "audio_file_path": str(file_path),
            }

        except Exception as e:
            logger.error(f"❌ PDF → TTS 처리 실패: {e}")
            raise e

    async def process_pdf_from_s3_to_tts(self, filename: str) -> Dict[str, Any]:
        """
        S3 기반 PDF → 멀티에이전트 → TTS 변환 → S3 업로드
        PDF를 S3에서 다운로드, 처리 후 TTS를 S3에 업로드
        """
        temp_pdf_path = None
        temp_audio_path = None

        try:
            # 1. S3에서 PDF 다운로드
            logger.info(f"📥 Downloading PDF from S3: {filename}")
            temp_pdf_path = self._download_pdf_from_s3(filename)

            # 2. 멀티에이전트 실행
            logger.info("🤖 Running multi-agent on PDF")
            agent_result = await self._run_legacy_multi_agent(temp_pdf_path)

            # 3. Explainer 텍스트 추출
            script = agent_result.get("explainer", "")
            if not script:
                logger.warning("⚠️ No explainer text generated")
                return {
                    "summary": agent_result.get("summary", ""),
                    "explainer": "",
                    "tts_id": None,
                    "audio_filename": None,
                    "s3_url": None,
                    "presigned_url": None,
                }

            # 4. 텍스트 정제
            script_clean = clean_text(script)

            # 5. TTS 파일명 생성
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_filename = f"industry_explainer_{ts}.mp3"

            # 6. 임시 파일로 TTS 생성
            temp_audio_path = tempfile.NamedTemporaryFile(
                delete=False, suffix=".mp3"
            ).name
            tts = gTTS(text=script_clean, lang="ko")
            tts.save(temp_audio_path)
            logger.info(f"🎧 TTS 생성 완료: {audio_filename}")

            # 7. S3에 TTS 파일 업로드
            s3_url = self._upload_audio_to_s3(temp_audio_path, audio_filename)

            # 8. Presigned URL 생성 (다운로드용)
            presigned_url = self._get_audio_url_from_s3(audio_filename)

            # 9. 로컬 임시 파일에도 저장 (선택사항)
            local_file_path = self.output_dir / audio_filename
            os.rename(temp_audio_path, str(local_file_path))
            temp_audio_path = None  # 이동했으므로 삭제 방지

            return {
                "summary": agent_result.get("summary", ""),
                "explainer": script,
                "tts_id": ts,
                "audio_filename": audio_filename,
                "s3_url": s3_url,
                "presigned_url": presigned_url,
                "local_path": str(local_file_path),
            }

        except Exception as e:
            logger.error(f"❌ S3 PDF → TTS 처리 실패: {e}")
            raise e
        finally:
            # 임시 파일 정리
            if temp_pdf_path and os.path.exists(temp_pdf_path):
                os.unlink(temp_pdf_path)
                logger.info(f"🗑️ 임시 PDF 파일 삭제: {temp_pdf_path}")
            if temp_audio_path and os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)
                logger.info(f"🗑️ 임시 TTS 파일 삭제: {temp_audio_path}")

    # =====================================================
    # 3️⃣ 파일 기반 헬퍼 함수들
    # =====================================================
    def get_audio_file_by_filename(self, filename: str) -> str | None:
        """생성된 오디오 파일 경로 반환"""
        file_path = self.output_dir / filename
        return str(file_path) if file_path.exists() else None

    def get_first_legacy_pdf(self) -> str | None:
        """legacy/downloaded_papers 폴더의 첫 번째 PDF 반환"""
        pdf_files = list(self.legacy_papers_dir.glob("*.pdf"))
        return str(pdf_files[0]) if pdf_files else None

    # =====================================================
    # 4️⃣ TTS 파일 스트리밍
    # =====================================================
    def stream_audio_from_s3(self, filename: str) -> tuple[bytes, str, dict]:
        """
        Stream audio file from S3 bucket
        Returns: (content_bytes, content_type, headers)
        """
        if not settings.S3_BUCKET:
            raise ValueError("S3_BUCKET environment variable is not configured.")
        if not self.s3_client:
            raise ValueError("AWS credentials are not configured.")

        # Construct S3 key for TTS files
        s3_key = f"output/tts/{filename}"

        logger.info(f"🎧 Streaming audio from S3: s3://{settings.S3_BUCKET}/{s3_key}")

        try:
            # Get object from S3
            s3_obj = self.s3_client.get_object(Bucket=settings.S3_BUCKET, Key=s3_key)
            content = s3_obj["Body"].read()

            # Determine content type
            import mimetypes

            content_type = (
                s3_obj.get("ContentType")
                or mimetypes.guess_type(filename)[0]
                or "application/octet-stream"
            )

            # Set headers
            headers = {"Content-Disposition": f'inline; filename="{filename}"'}

            logger.info(f"✅ Audio streamed successfully from S3: {filename}")
            return content, content_type, headers

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "NoSuchKey":
                raise FileNotFoundError(
                    f"음성 파일 '{filename}'이 S3에 존재하지 않습니다."
                )
            else:
                raise ValueError(f"S3 오류: {str(e)}")

    # =====================================================
    # 5️⃣ Research ID 기반 TTS 생성
    # =====================================================
    async def create_tts_from_research_id(self, research_id: int) -> Dict[str, Any]:
        """Create TTS from research ID by fetching research from database"""
        try:
            # Validate database session and repository
            if not self.db or not self.research_repository:
                raise ValueError(
                    "Database session is required for research_id operations. "
                    "Initialize TTSService with db parameter."
                )

            # 1. Fetch research from database
            logger.info(f"🔍 Fetching research with ID: {research_id}")
            research = self.research_repository.get_by_id(research_id)

            if not research:
                raise ValueError(f"Research with ID {research_id} not found")

            # 2. Validate research has object_key (S3 filename)
            if not research.object_key:
                raise ValueError(
                    f"Research with ID {research_id} does not have an associated PDF file (missing object_key)"
                )

            # 3. Extract filename from object_key
            # object_key format: "output/research/filename.pdf"
            object_key = research.object_key
            filename = object_key.split("/")[-1] if "/" in object_key else object_key

            logger.info(f"📄 Using filename from research object_key: {filename}")

            # 4. Generate TTS using existing S3 method
            return await self.process_pdf_from_s3_to_tts(filename)

        except ValueError as e:
            logger.error(f"❌ Research validation failed: {e}")
            raise e
        except Exception as e:
            logger.error(f"❌ TTS generation from research ID failed: {e}")
            raise ValueError(f"TTS 생성 중 오류가 발생했습니다: {str(e)}")
