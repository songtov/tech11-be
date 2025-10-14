"""
Slide Agent - Creates PowerPoint presentations from research paper content
"""

import logging
from typing import Dict, List
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import AzureChatOpenAI

logger = logging.getLogger(__name__)


class SlideAgent:
    """Agent responsible for creating PowerPoint slides from research content"""

    def __init__(
        self, azure_endpoint: str, api_key: str, deployment_name: str = "gpt-4o-mini"
    ):
        self.llm = AzureChatOpenAI(
            azure_endpoint=azure_endpoint,
            api_key=api_key,
            azure_deployment=deployment_name,
            openai_api_version="2024-02-01",
            temperature=0.3,
        )

    def generate_slide_content(self, paper_data: Dict) -> List[Dict]:
        """Generate slide content structure from paper data"""
        system_prompt = """You are an expert presentation designer.
        Create a structured outline for a 3 slide presentation based on the research paper.
        Each slide should have:
        - A clear title
        - 3-5 key bullet points
        - Appropriate content for a 2-3 minute video

        Focus on making the content engaging and educational.
        Return a JSON list of exactly 3 slides with title and bullet_points fields."""

        sections = paper_data.get("sections", {})
        structure = paper_data.get("structure", {})

        content_summary = f"""
        Paper Analysis: {structure.get("analysis", "")}

        Abstract: {sections.get("abstract", "")[:500]}
        Introduction: {sections.get("introduction", "")[:500]}
        Methods: {sections.get("methods", "")[:500]}
        Results: {sections.get("results", "")[:500]}
        Conclusion: {sections.get("conclusion", "")[:500]}
        """

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=content_summary),
        ]

        try:
            response = self.llm.invoke(messages)
            logger.info("Successfully generated slide content structure")
            return self._parse_slide_content(response.content)
        except Exception as e:
            logger.error(f"Error generating slide content: {e}")
            return self._create_default_slides(paper_data)

    def _parse_slide_content(self, content: str) -> List[Dict]:
        """Parse LLM response into slide structure"""
        # Simple parsing - in production, you'd want more robust JSON parsing
        slides = []

        # Default slide structure if parsing fails
        default_slides = [
            {
                "title": "Research Overview",
                "bullet_points": [
                    "Introduction to the research topic",
                    "Key objectives and goals",
                    "Research methodology overview",
                    "Expected outcomes",
                ],
            },
            {
                "title": "Key Findings",
                "bullet_points": [
                    "Main research results",
                    "Statistical significance",
                    "Practical implications",
                    "Future research directions",
                ],
            },
        ]

        try:
            # Try to extract JSON from response
            import json
            import re

            # Look for JSON in the response
            json_match = re.search(r"\[.*\]", content, re.DOTALL)
            if json_match:
                slides = json.loads(json_match.group())
            else:
                slides = default_slides

        except Exception as e:
            logger.warning(f"Could not parse slide content, using defaults: {e}")
            slides = default_slides

        return slides[:3]  # Limit to 3 slides max for POC

    def _create_default_slides(self, paper_data: Dict) -> List[Dict]:
        """Create default slides when LLM fails"""
        sections = paper_data.get("sections", {})

        slides = [
            {
                "title": "Research Overview",
                "bullet_points": [
                    "Academic research presentation",
                    "Key findings and insights",
                    "Methodology and approach",
                    "Implications for the field",
                ],
            }
        ]

        if sections.get("abstract"):
            slides.append(
                {
                    "title": "Abstract",
                    "bullet_points": sections["abstract"][:200].split(".")[:4],
                }
            )

        if sections.get("results"):
            slides.append(
                {
                    "title": "Key Results",
                    "bullet_points": sections["results"][:200].split(".")[:4],
                }
            )

        if sections.get("conclusion"):
            slides.append(
                {
                    "title": "Conclusion",
                    "bullet_points": sections["conclusion"][:200].split(".")[:4],
                }
            )

        return slides

    def create_presentation(self, slides_data: List[Dict], output_path: str) -> str:
        """Create PowerPoint presentation from slide data"""
        try:
            # Create presentation
            prs = Presentation()

            # Set slide size to 16:9
            prs.slide_width = Inches(13.33)
            prs.slide_height = Inches(7.5)

            for slide_info in slides_data:
                # Add slide with title and content layout
                slide_layout = prs.slide_layouts[1]  # Title and content layout
                slide = prs.slides.add_slide(slide_layout)

                # Set title
                title = slide.shapes.title
                title.text = slide_info["title"]
                title.text_frame.paragraphs[0].font.size = Pt(32)
                title.text_frame.paragraphs[0].font.bold = True
                title.text_frame.paragraphs[0].font.color.rgb = RGBColor(0, 51, 102)

                # Set content
                content = slide.placeholders[1]
                text_frame = content.text_frame
                text_frame.clear()

                for bullet_point in slide_info["bullet_points"]:
                    p = (
                        text_frame.paragraphs[0]
                        if not text_frame.paragraphs
                        else text_frame.add_paragraph()
                    )
                    p.text = bullet_point
                    p.font.size = Pt(20)
                    p.font.color.rgb = RGBColor(51, 51, 51)
                    p.level = 0

                # Center align content
                for paragraph in text_frame.paragraphs:
                    paragraph.alignment = PP_ALIGN.CENTER

            # Save presentation
            prs.save(output_path)
            logger.info(
                f"Created presentation with {len(slides_data)} slides: {output_path}"
            )

            return output_path

        except Exception as e:
            logger.error(f"Error creating presentation: {e}")
            raise

    def process_paper_to_slides(
        self, paper_data: Dict, output_dir: str, research_id: int
    ) -> str:
        """Main method to convert paper data to PowerPoint slides"""
        logger.info(f"Creating slides for research ID: {research_id}")

        # Generate slide content
        slides_data = self.generate_slide_content(paper_data)

        # Create output path
        output_path = Path(output_dir) / f"slides_{research_id}.pptx"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Create presentation
        presentation_path = self.create_presentation(slides_data, str(output_path))

        return presentation_path
