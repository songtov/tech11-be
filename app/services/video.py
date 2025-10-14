"""
Video Service - Main orchestration service for video generation pipeline
"""

import logging
from pathlib import Path
from typing import Dict

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.agents.reader_agent import ReaderAgent
from app.agents.script_agent import ScriptAgent
from app.agents.slide_agent import SlideAgent
from app.agents.video_agent import VideoAgent
from app.agents.voice_agent import VoiceAgent
from app.core.config import settings
from app.repositories.research_repository import ResearchRepository
from app.schemas.video import CreateVideoRequest, CreateVideoResponse

logger = logging.getLogger(__name__)


class VideoService:
    """Main service for orchestrating video generation pipeline"""

    def __init__(self, db: Session):
        self.db = db
        self.research_repo = ResearchRepository(db)

        # Initialize agents
        self._initialize_agents()

        # Set up output directory
        self.output_base_dir = Path("/Users/chihosong/sk/tech11-be/output/videos")
        self.output_base_dir.mkdir(parents=True, exist_ok=True)

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

    def get_video_by_research_id(self, research_id: int) -> CreateVideoResponse:
        """Get existing video for a research paper"""
        try:
            # Check if video already exists
            video_dir = self.output_base_dir / str(research_id)
            video_path = video_dir / f"video_{research_id}.mp4"

            if video_path.exists():
                video_url = f"/output/videos/{research_id}/video_{research_id}.mp4"
                return CreateVideoResponse(
                    video_url=video_url, research_id=research_id, status="completed"
                )
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"Video not found for research ID: {research_id}",
                )

        except Exception as e:
            logger.error(f"Error getting video for research ID {research_id}: {e}")
            raise

    def create_video_from_research_id(
        self, video_request: CreateVideoRequest
    ) -> CreateVideoResponse:
        """Create a video from a research paper using multi-agent pipeline"""
        research_id = video_request.research_id

        try:
            logger.info(f"Starting video generation for research ID: {research_id}")

            # Step 1: Get research paper data
            research_data = self._get_research_data(research_id)
            pdf_url = research_data["pdf_url"]

            # Step 2: Process paper with reader agent
            logger.info("Step 1: Processing research paper...")
            paper_data = self.reader_agent.process_research_paper_from_url(pdf_url)

            # Step 3: Create slides with slide agent
            logger.info("Step 2: Creating presentation slides...")
            slides_path = self.slide_agent.process_paper_to_slides(
                paper_data, str(self.output_base_dir / str(research_id)), research_id
            )

            # Step 4: Generate narration script
            logger.info("Step 3: Generating narration script...")
            script_data = self.script_agent.process_slides_to_script(
                self.slide_agent.generate_slide_content(paper_data), paper_data
            )

            # Step 5: Convert script to audio
            logger.info("Step 4: Converting script to audio...")
            audio_data = self.voice_agent.process_scripts_to_audio(
                script_data, str(self.output_base_dir / str(research_id)), research_id
            )

            # Step 6: Assemble final video
            logger.info("Step 5: Assembling final video...")
            self.video_agent.process_slides_and_audio_to_video(
                slides_path,
                audio_data,
                str(self.output_base_dir / str(research_id)),
                research_id,
            )

            # Step 7: Return video URL with metadata
            video_url = f"/output/videos/{research_id}/video_{research_id}.mp4"

            # Get slide count from script data
            slide_count = len(script_data.get("slide_scripts", []))

            # Get duration from audio data
            duration_seconds = audio_data.get("duration_seconds", 0)

            logger.info(f"Video generation completed successfully: {video_url}")

            return CreateVideoResponse(
                video_url=video_url,
                research_id=research_id,
                duration_seconds=duration_seconds,
                slide_count=slide_count,
                status="completed",
            )

        except Exception as e:
            logger.error(f"Error creating video for research ID {research_id}: {e}")
            raise

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
