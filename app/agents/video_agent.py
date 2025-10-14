"""
Video Agent - Assembles final video from slides and audio using MoviePy
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

try:
    from moviepy.editor import (
        AudioFileClip,
        ImageClip,
        concatenate_videoclips,
    )
except ImportError:
    # Fallback for moviepy 2.x
    from moviepy import AudioFileClip, concatenate_videoclips, ImageClip

import os
import tempfile

from pptx import Presentation

logger = logging.getLogger(__name__)


class VideoAgent:
    """Agent responsible for creating final video from slides and audio"""

    def __init__(self, fps: int = 1, resolution: tuple = (1920, 1080)):
        self.fps = fps
        self.resolution = resolution

    def convert_pptx_to_images(self, pptx_path: str, output_dir: str) -> List[str]:
        """Convert PowerPoint slides to images"""
        try:
            # This is a simplified approach - in production you'd use python-pptx with PIL
            # or a more robust solution like LibreOffice headless

            # For now, we'll create placeholder images
            # In a real implementation, you'd extract slides as images
            image_paths = []

            prs = Presentation(pptx_path)

            for i, slide in enumerate(prs.slides):
                # Create a placeholder image path
                image_path = Path(output_dir) / f"slide_{i + 1:02d}.png"
                image_path.parent.mkdir(parents=True, exist_ok=True)

                # Extract slide content and create image
                slide_content = self._extract_slide_content(slide)
                self._create_slide_image(str(image_path), slide_content)
                image_paths.append(str(image_path))

            logger.info(f"Converted {len(image_paths)} slides to images")
            return image_paths

        except Exception as e:
            logger.error(f"Error converting PPTX to images: {e}")
            raise

    def _extract_slide_content(self, slide):
        """Extract content from a PowerPoint slide"""
        content = {"title": "", "bullet_points": []}

        try:
            # Extract all text from slide shapes
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text:
                    text = shape.text.strip()
                    if not content["title"]:  # First text is usually title
                        content["title"] = text
                    else:
                        # Extract bullet points from content shape
                        lines = text.split("\n")
                        for line in lines:
                            line = line.strip()
                            if line and not line.startswith(
                                "•"
                            ):  # Skip empty lines and bullet markers
                                content["bullet_points"].append(line)
                        break  # Found content, stop looking
        except Exception as e:
            logger.warning(f"Error extracting slide content: {e}")

        return content

    def _create_slide_image(self, image_path: str, slide_content: Dict):
        """Create a slide image with actual content"""
        try:
            from PIL import Image, ImageDraw, ImageFont

            # Create image
            img = Image.new("RGB", self.resolution, color="white")
            draw = ImageDraw.Draw(img)

            # Load fonts
            try:
                title_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 72)
                bullet_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 48)
            except:
                title_font = ImageFont.load_default()
                bullet_font = ImageFont.load_default()

            # Draw title
            title = slide_content.get("title", "Untitled Slide")
            title_bbox = draw.textbbox((0, 0), title, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_x = (self.resolution[0] - title_width) // 2
            title_y = 100

            draw.text((title_x, title_y), title, fill=(0, 51, 102), font=title_font)

            # Draw bullet points
            bullet_points = slide_content.get("bullet_points", [])
            bullet_y = title_y + 150

            for i, point in enumerate(bullet_points[:5]):  # Limit to 5 bullet points
                if bullet_y > self.resolution[1] - 100:  # Don't go off screen
                    break

                # Draw bullet point
                bullet_text = f"• {point}"
                bullet_bbox = draw.textbbox((0, 0), bullet_text, font=bullet_font)
                bullet_width = bullet_bbox[2] - bullet_bbox[0]
                bullet_x = (self.resolution[0] - bullet_width) // 2

                draw.text(
                    (bullet_x, bullet_y),
                    bullet_text,
                    fill=(51, 51, 51),
                    font=bullet_font,
                )
                bullet_y += 80

            # Save image
            img.save(image_path)
            logger.info(f"Created slide image: {image_path}")

        except ImportError:
            # Fallback: create a simple text file as placeholder
            with open(image_path.replace(".png", ".txt"), "w") as f:
                f.write(f"Slide: {slide_content.get('title', 'Untitled')}")
        except Exception as e:
            logger.warning(f"Could not create slide image: {e}")

    def create_slide_video_clips(
        self, image_paths: List[str], audio_path: str, slide_durations: List[float]
    ) -> List[ImageClip]:
        """Create video clips for each slide"""
        clips = []

        try:
            # Load audio to get total duration
            audio_clip = AudioFileClip(audio_path)
            total_duration = audio_clip.duration

            # Calculate duration per slide
            if slide_durations:
                durations = slide_durations
            else:
                # Equal duration for all slides
                duration_per_slide = total_duration / len(image_paths)
                durations = [duration_per_slide] * len(image_paths)

            for i, image_path in enumerate(image_paths):
                if os.path.exists(image_path):
                    # Create image clip
                    clip = ImageClip(image_path, duration=durations[i])
                    clip = clip.resized(self.resolution)
                    clips.append(clip)
                else:
                    logger.warning(f"Image not found: {image_path}")

            audio_clip.close()

        except Exception as e:
            logger.error(f"Error creating slide video clips: {e}")
            raise

        return clips

    def assemble_video(
        self, video_clips: List[ImageClip], audio_path: str, output_path: str
    ) -> str:
        """Assemble final video from clips and audio"""
        try:
            # Concatenate video clips
            final_video = concatenate_videoclips(video_clips, method="compose")

            # Add audio
            audio_clip = AudioFileClip(audio_path)
            final_video = final_video.with_audio(audio_clip)

            # Write video file
            final_video.write_videofile(
                output_path,
                fps=self.fps,
                codec="libx264",
                audio_codec="aac",
                temp_audiofile="temp-audio.m4a",
                remove_temp=True,
            )

            # Clean up
            final_video.close()
            audio_clip.close()

            logger.info(f"Created final video: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error assembling video: {e}")
            raise

    def create_video_from_slides_and_audio(
        self,
        pptx_path: str,
        audio_path: str,
        output_path: str,
        slide_durations: Optional[List[float]] = None,
    ) -> str:
        """Main method to create video from slides and audio"""
        logger.info(f"Creating video from slides: {pptx_path}")

        # Create temporary directory for images
        with tempfile.TemporaryDirectory() as temp_dir:
            # Convert slides to images
            image_paths = self.convert_pptx_to_images(pptx_path, temp_dir)

            # Create video clips
            video_clips = self.create_slide_video_clips(
                image_paths, audio_path, slide_durations
            )

            # Assemble final video
            final_video_path = self.assemble_video(video_clips, audio_path, output_path)

            return final_video_path

    def process_slides_and_audio_to_video(
        self, slides_path: str, audio_data: Dict, output_dir: str, research_id: int
    ) -> str:
        """Main method to process slides and audio into final video"""
        logger.info(f"Creating final video for research ID: {research_id}")

        # Create output path
        output_path = Path(output_dir) / f"video_{research_id}.mp4"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Get audio path
        audio_path = audio_data["full_audio_path"]

        # Calculate slide durations based on audio segments
        slide_durations = []
        if "slide_audio_files" in audio_data:
            for audio_file in audio_data["slide_audio_files"]:
                try:
                    audio_clip = AudioFileClip(audio_file)
                    duration = audio_clip.duration
                    audio_clip.close()
                    slide_durations.append(duration)
                except Exception as e:
                    logger.warning(f"Could not get duration for {audio_file}: {e}")
                    slide_durations.append(5.0)  # Default duration

        # Create video
        video_path = self.create_video_from_slides_and_audio(
            slides_path, audio_path, str(output_path), slide_durations
        )

        return video_path
