"""
Video Service - Main orchestration service for video generation pipeline
"""

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict

import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.agents.reader_agent import ReaderAgent
from app.agents.script_agent import ScriptAgent
from app.agents.slide_agent import SlideAgent
from app.agents.video_agent import VideoAgent
from app.agents.voice_agent import VoiceAgent
from app.core.config import settings
from app.repositories.research_repository import ResearchRepository
from app.repositories.video_repository import VideoRepository
from app.schemas.video import CreateVideoRequest, CreateVideoResponse

logger = logging.getLogger(__name__)


class VideoService:
    """Main service for orchestrating video generation pipeline"""

    def __init__(self, db: Session):
        self.db = db
        self.research_repo = ResearchRepository(db)
        self.video_repository = VideoRepository(db)

        # Initialize agents
        self._initialize_agents()

        # Set up output directory
        self.output_base_dir = Path("/Users/chihosong/sk/tech11-be/output/videos")
        self.output_base_dir.mkdir(parents=True, exist_ok=True)

        # Initialize S3 client
        self.s3_client = None
        if settings.AWS_ACCESS_KEY and settings.AWS_SECRET_KEY:
            self.s3_client = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY,
                aws_secret_access_key=settings.AWS_SECRET_KEY,
            )

    def _initialize_agents(self):
        """Initialize all agents with Azure OpenAI configuration"""
        try:
            # Validate Azure OpenAI configuration
            if not settings.AOAI_API_KEY or not settings.AOAI_ENDPOINT:
                raise ValueError(
                    "Azure OpenAI configuration not set. Please set AOAI_API_KEY and AOAI_ENDPOINT environment variables."
                )

            # Initialize agents with Azure OpenAI config
            self.reader_agent = ReaderAgent(
                azure_endpoint=settings.AOAI_ENDPOINT,
                api_key=settings.AOAI_API_KEY,
                deployment_name=settings.AOAI_DEPLOY_GPT4O_MINI,
            )
            self.slide_agent = SlideAgent(
                azure_endpoint=settings.AOAI_ENDPOINT,
                api_key=settings.AOAI_API_KEY,
                deployment_name=settings.AOAI_DEPLOY_GPT4O_MINI,
            )
            self.script_agent = ScriptAgent(
                azure_endpoint=settings.AOAI_ENDPOINT,
                api_key=settings.AOAI_API_KEY,
                deployment_name=settings.AOAI_DEPLOY_GPT4O_MINI,
            )
            self.voice_agent = VoiceAgent()
            self.video_agent = VideoAgent()

            logger.info("All agents initialized successfully with Azure OpenAI")

        except Exception as e:
            logger.error(f"Error initializing agents: {e}")
            raise

    # =====================================================
    # S3 Helper Methods
    # =====================================================
    def _upload_video_to_s3(self, local_file_path: str, filename: str) -> str:
        """Upload video file to S3 bucket and return object key"""
        if not settings.S3_BUCKET:
            raise ValueError("S3_BUCKET environment variable is not configured.")
        if not self.s3_client:
            raise ValueError("AWS credentials are not configured.")

        # Construct S3 key for video files
        s3_key = f"output/videos/{filename}"

        logger.info(f"📤 Uploading video to S3: s3://{settings.S3_BUCKET}/{s3_key}")

        try:
            # Upload file to S3
            self.s3_client.upload_file(
                local_file_path,
                settings.S3_BUCKET,
                s3_key,
                ExtraArgs={"ContentType": "video/mp4"},
            )

            logger.info(f"✅ Video uploaded successfully to S3: {s3_key}")
            return s3_key

        except Exception as e:
            raise ValueError(f"Failed to upload video to S3: {str(e)}")

    def _get_video_url_from_s3(self, object_key: str) -> str | None:
        """Generate presigned URL for video file in S3 using object_key"""
        if not settings.S3_BUCKET or not self.s3_client:
            return None

        try:
            # Check if file exists
            self.s3_client.head_object(Bucket=settings.S3_BUCKET, Key=object_key)

            # Generate presigned URL (valid for 1 hour)
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": settings.S3_BUCKET, "Key": object_key},
                ExpiresIn=3600,
            )
            return url
        except ClientError:
            return None

    def stream_video_from_s3(self, object_key: str) -> tuple[bytes, str, dict]:
        """
        Stream video file from S3 bucket using object_key
        Returns: (content_bytes, content_type, headers)
        """
        if not settings.S3_BUCKET:
            raise ValueError("S3_BUCKET environment variable is not configured.")
        if not self.s3_client:
            raise ValueError("AWS credentials are not configured.")

        logger.info(
            f"🎬 Streaming video from S3: s3://{settings.S3_BUCKET}/{object_key}"
        )

        try:
            # Get object from S3
            s3_obj = self.s3_client.get_object(
                Bucket=settings.S3_BUCKET, Key=object_key
            )
            content = s3_obj["Body"].read()

            # Determine content type
            import mimetypes

            # Extract filename from object_key for content type detection
            filename = object_key.split("/")[-1] if "/" in object_key else object_key
            content_type = (
                s3_obj.get("ContentType")
                or mimetypes.guess_type(filename)[0]
                or "application/octet-stream"
            )

            # Set headers
            headers = {"Content-Disposition": f'inline; filename="{filename}"'}

            logger.info(f"✅ Video streamed successfully from S3: {object_key}")
            return content, content_type, headers

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "NoSuchKey":
                raise FileNotFoundError(
                    f"비디오 파일 '{object_key}'이 S3에 존재하지 않습니다."
                )
            else:
                raise ValueError(f"S3 오류: {str(e)}")

    def stream_video_by_research_id(self, research_id: int) -> tuple[bytes, str, dict]:
        """
        Stream video file by research_id using database lookup
        Returns: (content_bytes, content_type, headers)
        """
        # Retrieve video record from database
        logger.info(f"🔍 Looking up video for research ID: {research_id}")
        video_record = self.video_repository.get_by_research_id(research_id)

        if not video_record:
            raise FileNotFoundError(
                f"Video not found for research ID {research_id}. "
                "Please generate video first using POST /video/ endpoint."
            )

        # Validate object_key exists
        if not video_record.object_key:
            raise ValueError(
                f"Video record for research ID {research_id} is missing object_key. "
                "Cannot stream video file."
            )

        # Stream video using object_key
        logger.info(f"🎬 Streaming video for research ID: {research_id}")
        return self.stream_video_from_s3(video_record.object_key)

    def _cleanup_video_files(self, research_id: int):
        """Clean up all local files after video generation and S3 upload"""
        try:
            video_dir = self.output_base_dir / str(research_id)

            if video_dir.exists():
                # Delete the entire directory
                shutil.rmtree(video_dir)
                logger.info(f"🗑️ Cleaned up video directory: {video_dir}")
            else:
                logger.info(f"📁 Video directory does not exist: {video_dir}")

        except Exception as e:
            logger.warning(f"⚠️ Error during cleanup: {e}")

    def get_video_by_research_id(self, research_id: int) -> CreateVideoResponse:
        """Get existing video for a research paper from database"""
        try:
            # Check database for existing video
            logger.info(f"🔍 Checking for video in database: research_id={research_id}")
            video_record = self.video_repository.get_by_research_id(research_id)

            if video_record:
                logger.info(f"✅ Found cached video for research ID: {research_id}")
                # Generate presigned URL for streaming
                presigned_url = self._get_video_url_from_s3(video_record.object_key)

                return CreateVideoResponse(
                    video_url=f"/video/stream/{research_id}",
                    research_id=research_id,
                    status="completed",
                    s3_url=f"s3://{settings.S3_BUCKET}/{video_record.object_key}",
                    object_key=video_record.object_key,
                    presigned_url=presigned_url,
                    streaming_url=f"/video/stream/{research_id}",
                )
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"Video not found for research ID: {research_id}. Please generate video first.",
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting video for research ID {research_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    def create_video_from_research_id(
        self, video_request: CreateVideoRequest, force_regenerate: bool = False
    ) -> CreateVideoResponse:
        """Create a video from a research paper using multi-agent pipeline with caching"""
        research_id = video_request.research_id

        try:
            # Step 1: Check cache first (if not force_regenerate)
            if not force_regenerate:
                logger.info(f"🔍 Checking video cache for research ID: {research_id}")
                existing_video = self.video_repository.get_by_research_id(research_id)

                if existing_video:
                    logger.info(f"✅ Found cached video for research ID: {research_id}")
                    # Generate presigned URL for the cached video file
                    presigned_url = self._get_video_url_from_s3(
                        existing_video.object_key
                    )

                    return CreateVideoResponse(
                        video_url=f"/video/stream/{research_id}",
                        research_id=research_id,
                        status="completed",
                        s3_url=f"s3://{settings.S3_BUCKET}/{existing_video.object_key}",
                        object_key=existing_video.object_key,
                        presigned_url=presigned_url,
                        streaming_url=f"/video/stream/{research_id}",
                    )

            # Step 2: No cache found or force_regenerate - generate new video
            logger.info(f"🚀 Starting video generation for research ID: {research_id}")

            # Step 3: Get research paper data
            research_data = self._get_research_data(research_id)
            pdf_url = research_data["pdf_url"]

            # Step 4: Process paper with reader agent
            logger.info("Step 1: Processing research paper...")
            paper_data = self.reader_agent.process_research_paper_from_url(pdf_url)

            # Step 5: Create slides with slide agent
            logger.info("Step 2: Creating presentation slides...")
            slides_path = self.slide_agent.process_paper_to_slides(
                paper_data, str(self.output_base_dir / str(research_id)), research_id
            )

            # Step 6: Generate narration script
            logger.info("Step 3: Generating narration script...")
            script_data = self.script_agent.process_slides_to_script(
                self.slide_agent.generate_slide_content(paper_data), paper_data
            )

            # Step 7: Convert script to audio
            logger.info("Step 4: Converting script to audio...")
            audio_data = self.voice_agent.process_scripts_to_audio(
                script_data, str(self.output_base_dir / str(research_id)), research_id
            )

            # Step 8: Assemble final video
            logger.info("Step 5: Assembling final video...")
            self.video_agent.process_slides_and_audio_to_video(
                slides_path,
                audio_data,
                str(self.output_base_dir / str(research_id)),
                research_id,
            )

            # Step 9: Upload video to S3
            logger.info("Step 6: Uploading video to S3...")
            video_path = (
                self.output_base_dir / str(research_id) / f"video_{research_id}.mp4"
            )

            if not video_path.exists():
                raise ValueError(f"Video file not found at: {video_path}")

            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            video_filename = f"video_{research_id}_{timestamp}.mp4"

            # Upload to S3
            object_key = self._upload_video_to_s3(str(video_path), video_filename)

            # Step 10: Save to database
            logger.info("Step 7: Saving video metadata to database...")
            video_data = {
                "research_id": research_id,
                "object_key": object_key,
            }

            # Update existing record or create new one
            if force_regenerate:
                existing_video = self.video_repository.get_by_research_id(research_id)
                if existing_video:
                    saved_video = self.video_repository.update(
                        existing_video, video_data
                    )
                    logger.info(
                        f"✅ Video record updated in database with ID: {saved_video.id}"
                    )
                else:
                    saved_video = self.video_repository.create(video_data)
                    logger.info(f"✅ Video saved to database with ID: {saved_video.id}")
            else:
                saved_video = self.video_repository.create(video_data)
                logger.info(f"✅ Video saved to database with ID: {saved_video.id}")

            # Step 11: Clean up all local files
            logger.info("Step 8: Cleaning up local files...")
            self._cleanup_video_files(research_id)

            # Step 12: Generate presigned URL and return response
            presigned_url = self._get_video_url_from_s3(object_key)

            # Get metadata
            slide_count = len(script_data.get("slide_scripts", []))
            duration_seconds = audio_data.get("duration_seconds", 0)

            logger.info(
                f"✅ Video generation completed successfully for research ID: {research_id}"
            )

            return CreateVideoResponse(
                video_url=f"/video/stream/{research_id}",
                research_id=research_id,
                duration_seconds=duration_seconds,
                slide_count=slide_count,
                status="completed",
                s3_url=f"s3://{settings.S3_BUCKET}/{object_key}",
                object_key=object_key,
                presigned_url=presigned_url,
                streaming_url=f"/video/stream/{research_id}",
            )

        except Exception as e:
            logger.error(f"❌ Error creating video for research ID {research_id}: {e}")
            # Clean up on error
            try:
                self._cleanup_video_files(research_id)
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup video files: {cleanup_error}")
            raise HTTPException(status_code=500, detail=str(e))

    def _get_research_data(self, research_id: int) -> Dict:
        """Get research paper data from database"""
        try:
            research = self.research_repo.get_by_id(research_id)
            if not research:
                raise ValueError(f"Research paper not found for ID: {research_id}")

            # Check if research has a downloaded PDF file
            if not research.object_key:
                raise ValueError(
                    f"Research paper with ID {research_id} has not been downloaded yet. Please download the PDF first."
                )

            # Extract filename from object_key (format: "output/research/filename.pdf")
            filename = (
                research.object_key.split("/")[-1]
                if "/" in research.object_key
                else research.object_key
            )

            # For now, we'll use the PDF URL directly since files are stored in S3
            # In a production system, you might want to download from S3 to local storage first
            pdf_url = research.pdf_url
            if not pdf_url:
                raise ValueError(
                    f"Research paper with ID {research_id} does not have a PDF URL"
                )

            return {
                "research_id": research_id,
                "title": research.title,
                "pdf_url": pdf_url,
                "object_key": research.object_key,
                "filename": filename,
            }

        except Exception as e:
            logger.error(f"Error getting research data for ID {research_id}: {e}")
            raise

    def cleanup_temp_files(self, research_id: int):
        """Clean up temporary files after video generation"""
        try:
            video_dir = self.output_base_dir / str(research_id)

            # Keep only the final video file
            for file_path in video_dir.glob("*"):
                if not file_path.name.startswith(f"video_{research_id}.mp4"):
                    try:
                        file_path.unlink()
                        logger.info(f"Cleaned up temporary file: {file_path}")
                    except Exception as e:
                        logger.warning(f"Could not delete {file_path}: {e}")

        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")

    def get_video_generation_status(self, research_id: int) -> Dict:
        """Get the status of video generation process"""
        video_dir = self.output_base_dir / str(research_id)

        status = {
            "research_id": research_id,
            "video_exists": False,
            "slides_exist": False,
            "audio_exists": False,
            "files": [],
        }

        if video_dir.exists():
            for file_path in video_dir.iterdir():
                status["files"].append(file_path.name)

                if file_path.name == f"video_{research_id}.mp4":
                    status["video_exists"] = True
                elif file_path.name == f"slides_{research_id}.pptx":
                    status["slides_exist"] = True
                elif file_path.name == f"narration_{research_id}.mp3":
                    status["audio_exists"] = True

        return status
