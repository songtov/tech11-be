"""
Script Agent - Generates narration scripts for video presentations
"""

import logging
from typing import Dict, List

from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import AzureChatOpenAI

logger = logging.getLogger(__name__)


class ScriptAgent:
    """Agent responsible for generating narration scripts from slide content"""

    def __init__(
        self, azure_endpoint: str, api_key: str, deployment_name: str = "gpt-4o-mini"
    ):
        self.llm = AzureChatOpenAI(
            azure_endpoint=azure_endpoint,
            api_key=api_key,
            azure_deployment=deployment_name,
            openai_api_version="2024-02-01",
            temperature=0.4,
        )

    def generate_narration_script(
        self, slides_data: List[Dict], paper_data: Dict
    ) -> List[Dict]:
        """Generate narration script for each slide"""
        system_prompt = """You are an expert educational narrator and presenter.
        Create engaging, conversational narration scripts for exactly 3 slides in Korean language.

        Requirements:
        - Each script should be 20-40 seconds when spoken (approximately 60-120 words)
        - Use conversational, educational tone in Korean
        - Include smooth transitions between slides
        - Make complex concepts accessible in Korean
        - Use "우리" and "여러분" to engage the audience
        - Include brief pauses indicated by [pause]
        - Ensure each script has substantial content (no empty scripts)
        - Write in natural, fluent Korean

        Return a JSON list with exactly 3 slides' narration scripts in Korean."""

        # Prepare context about the paper
        paper_context = f"""
        Paper Context:
        Abstract: {paper_data.get("sections", {}).get("abstract", "")[:300]}
        Key Findings: {paper_data.get("sections", {}).get("results", "")[:300]}
        """

        slides_context = "\n".join(
            [
                f"Slide {i + 1}: {slide['title']}\nPoints: {'; '.join(slide['bullet_points'])}"
                for i, slide in enumerate(slides_data)
            ]
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"{paper_context}\n\nSlides:\n{slides_context}"),
        ]

        try:
            response = self.llm.invoke(messages)
            logger.info("Successfully generated narration script")
            return self._parse_narration_script(response.content, slides_data)
        except Exception as e:
            logger.error(f"Error generating narration script: {e}")
            return self._create_default_scripts(slides_data)

    def _parse_narration_script(
        self, content: str, slides_data: List[Dict]
    ) -> List[Dict]:
        """Parse LLM response into narration script structure"""
        scripts = []

        try:
            import json
            import re

            # Look for JSON in the response
            json_match = re.search(r"\[.*\]", content, re.DOTALL)
            if json_match:
                parsed_scripts = json.loads(json_match.group())

                # Ensure we have scripts for all slides
                for i, slide in enumerate(slides_data):
                    if i < len(parsed_scripts):
                        scripts.append(
                            {
                                "slide_number": i + 1,
                                "slide_title": slide["title"],
                                "script": parsed_scripts[i].get(
                                    "narration", parsed_scripts[i].get("script", "")
                                ),
                                "duration_estimate": parsed_scripts[i].get(
                                    "duration", 20
                                ),
                            }
                        )
                    else:
                        scripts.append(self._create_slide_script(slide, i + 1))
            else:
                # Fallback to creating scripts manually
                scripts = self._create_default_scripts(slides_data)

        except Exception as e:
            logger.warning(f"Could not parse narration script, using defaults: {e}")
            scripts = self._create_default_scripts(slides_data)

        return scripts

    def _create_default_scripts(self, slides_data: List[Dict]) -> List[Dict]:
        """Create default narration scripts when LLM fails"""
        scripts = []

        for i, slide in enumerate(slides_data):
            scripts.append(self._create_slide_script(slide, i + 1))

        return scripts

    def _create_slide_script(self, slide: Dict, slide_number: int) -> Dict:
        """Create a basic script for a single slide"""
        title = slide["title"]
        bullet_points = slide["bullet_points"]

        # Create a simple script based on slide content
        if slide_number == 1:
            script = f"Welcome to this presentation on {title.lower()}. Today we'll explore the key findings and insights from this important research."
        elif "abstract" in title.lower():
            script = f"Let's start with the abstract. {bullet_points[0] if bullet_points else 'This research presents important findings in the field.'}"
        elif "result" in title.lower():
            script = f"Now let's look at the key results. {bullet_points[0] if bullet_points else 'The findings show significant insights.'}"
        elif "conclusion" in title.lower():
            script = f"In conclusion, {bullet_points[0].lower() if bullet_points else 'this research provides valuable insights.'} Thank you for watching."
        else:
            script = f"Moving on to {title.lower()}. {bullet_points[0] if bullet_points else 'This section covers important aspects of the research.'}"

        return {
            "slide_number": slide_number,
            "slide_title": title,
            "script": script,
            "duration_estimate": 20,
        }

    def optimize_script_for_tts(self, scripts: List[Dict]) -> List[Dict]:
        """Optimize scripts for text-to-speech conversion"""
        optimized_scripts = []

        for script_data in scripts:
            script = script_data["script"]

            # TTS optimizations
            optimized_script = script

            # Replace common academic abbreviations
            replacements = {
                "et al.": "et al",
                "i.e.": "that is",
                "e.g.": "for example",
                "vs.": "versus",
                "Fig.": "Figure",
                "Table": "Table",
                "p <": "p less than",
                "p >": "p greater than",
                "%": "percent",
                "&": "and",
            }

            for old, new in replacements.items():
                optimized_script = optimized_script.replace(old, new)

            # Add natural pauses
            optimized_script = optimized_script.replace(". ", ". [pause] ")
            optimized_script = optimized_script.replace(", ", ", [pause] ")

            optimized_scripts.append(
                {
                    **script_data,
                    "script": optimized_script,
                    "word_count": len(optimized_script.split()),
                }
            )

        return optimized_scripts

    def create_full_script(self, scripts: List[Dict]) -> str:
        """Create a complete narration script with transitions"""
        full_script = []

        for i, script_data in enumerate(scripts):
            script = script_data["script"]

            # Add slide transition
            if i > 0:
                full_script.append("[pause] Now let's move to the next slide. [pause]")

            full_script.append(script)

        # Add closing
        full_script.append("[pause] Thank you for watching this presentation. [pause]")

        return " ".join(full_script)

    def process_slides_to_script(
        self, slides_data: List[Dict], paper_data: Dict
    ) -> Dict:
        """Main method to convert slides to narration script"""
        logger.info(f"Generating narration script for {len(slides_data)} slides")

        # Generate scripts
        scripts = self.generate_narration_script(slides_data, paper_data)

        # Optimize for TTS
        optimized_scripts = self.optimize_script_for_tts(scripts)

        # Create full script
        full_script = self.create_full_script(optimized_scripts)

        return {
            "slide_scripts": optimized_scripts,
            "full_script": full_script,
            "total_duration_estimate": sum(
                s.get("duration_estimate", 20) for s in optimized_scripts
            ),
            "total_word_count": len(full_script.split()),
        }
