"""
Voice Agent - Converts narration scripts to audio using Text-to-Speech
"""

import logging
from typing import Dict, List
from pathlib import Path

from gtts import gTTS

logger = logging.getLogger(__name__)


class VoiceAgent:
    """Agent responsible for converting text to speech"""

    def __init__(self, language: str = "en", slow: bool = False):
        self.language = language
        self.slow = slow

    def text_to_speech(self, text: str, output_path: str) -> str:
        """Convert text to speech and save as MP3"""
        try:
            # Clean text for TTS
            cleaned_text = self._clean_text_for_tts(text)

            # Check if text is empty after cleaning
            if not cleaned_text or cleaned_text.strip() == "":
                logger.warning(f"Empty text for TTS, using default text")
                cleaned_text = (
                    "This slide contains important information from the research paper."
                )

            # Create TTS object
            tts = gTTS(text=cleaned_text, lang=self.language, slow=self.slow)

            # Save to file
            tts.save(output_path)
            logger.info(f"Generated TTS audio: {output_path}")

            return output_path

        except Exception as e:
            logger.error(f"Error generating TTS audio: {e}")
            raise

    def _clean_text_for_tts(self, text: str) -> str:
        """Clean text for better TTS output"""
        # Remove pause markers
        cleaned = text.replace("[pause]", "")

        # Remove extra whitespace
        cleaned = " ".join(cleaned.split())

        # Handle common TTS issues
        replacements = {
            "et al": "et al",
            "i.e.": "that is",
            "e.g.": "for example",
            "vs.": "versus",
            "Fig.": "Figure",
            "p <": "p less than",
            "p >": "p greater than",
            "%": "percent",
            "&": "and",
            "Dr.": "Doctor",
            "Prof.": "Professor",
            "Mr.": "Mister",
            "Ms.": "Miss",
            "Mrs.": "Misses",
        }

        for old, new in replacements.items():
            cleaned = cleaned.replace(old, new)

        return cleaned

    def create_slide_audio(
        self, script_data: Dict, output_dir: str, slide_number: int
    ) -> str:
        """Create audio for a single slide"""
        script = script_data["script"]

        # Create output path
        output_path = Path(output_dir) / f"slide_{slide_number:02d}_audio.mp3"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate audio
        audio_path = self.text_to_speech(script, str(output_path))

        return audio_path

    def create_full_audio(
        self, full_script: str, output_dir: str, research_id: int
    ) -> str:
        """Create complete audio narration"""
        output_path = Path(output_dir) / f"narration_{research_id}.mp3"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate audio
        audio_path = self.text_to_speech(full_script, str(output_path))

        return audio_path

    def create_slide_audio_segments(
        self, scripts: List[Dict], output_dir: str
    ) -> List[str]:
        """Create individual audio files for each slide"""
        audio_files = []

        for script_data in scripts:
            slide_number = script_data["slide_number"]
            audio_path = self.create_slide_audio(script_data, output_dir, slide_number)
            audio_files.append(audio_path)

        return audio_files

    def get_audio_duration(self, audio_path: str) -> float:
        """Get duration of audio file in seconds"""
        try:
            import librosa

            duration = librosa.get_duration(filename=audio_path)
            return duration
        except ImportError:
            logger.warning("librosa not available, cannot get audio duration")
            return 0.0
        except Exception as e:
            logger.error(f"Error getting audio duration: {e}")
            return 0.0

    def process_scripts_to_audio(
        self, script_data: Dict, output_dir: str, research_id: int
    ) -> Dict:
        """Main method to convert scripts to audio"""
        logger.info(f"Converting scripts to audio for research ID: {research_id}")

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Create full narration audio
        full_script = script_data["full_script"]
        full_audio_path = self.create_full_audio(
            full_script, str(output_path), research_id
        )

        # Create individual slide audio segments
        slide_scripts = script_data["slide_scripts"]
        slide_audio_files = self.create_slide_audio_segments(
            slide_scripts, str(output_path)
        )

        # Get audio duration
        duration = self.get_audio_duration(full_audio_path)

        return {
            "full_audio_path": full_audio_path,
            "slide_audio_files": slide_audio_files,
            "duration_seconds": duration,
            "estimated_duration": script_data["total_duration_estimate"],
            "word_count": script_data["total_word_count"],
        }
