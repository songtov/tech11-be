"""
Figure Agent - Generates visual figures (charts, graphs, tables) based on slide content
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend
import matplotlib.pyplot as plt  # type: ignore
import numpy as np
from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import AzureChatOpenAI
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


class FigureAgent:
    """Agent responsible for generating visual figures based on slide content"""

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

        # Set matplotlib style for professional appearance
        try:
            plt.style.use("seaborn-v0_8-darkgrid")
        except OSError:
            # Fallback to default style if seaborn not available
            plt.style.use("default")

        # Figure dimensions
        self.figure_width = 600
        self.figure_height = 400

    def analyze_slide_for_visualization(self, slide_data: Dict) -> Dict:
        """Use LLM to determine what visualization would be most helpful for this slide"""
        system_prompt = """You are an expert data visualization specialist.
        Analyze the slide content and determine the most appropriate visualization.

        Consider:
        1. What type of data is mentioned (percentages, comparisons, trends, categories)
        2. What visualization would best represent this data
        3. What labels and title would be most informative

        Visualization types:
        - bar_chart: For comparing categories or groups
        - pie_chart: For showing proportions/percentages
        - line_chart: For showing trends over time
        - table: For detailed data presentation
        - process_flow: For methodology or process steps

        Return JSON with:
        {
            "visualization_type": "bar_chart|pie_chart|line_chart|table|process_flow",
            "title": "Chart/Table Title",
            "data": {
                "labels": ["Label1", "Label2", ...],
                "values": [value1, value2, ...],
                "description": "What this data represents"
            },
            "should_generate": true/false
        }

        Only suggest visualization if there's clear numerical data or categorical information."""

        slide_title = slide_data.get("title", "")
        bullet_points = slide_data.get("bullet_points", [])

        content = f"""
        Slide Title: {slide_title}

        Slide Content:
        {chr(10).join([f"• {point}" for point in bullet_points])}
        """

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=content),
        ]

        try:
            response = self.llm.invoke(messages)
            logger.info(f"Analyzed slide '{slide_title}' for visualization")

            # Parse JSON response
            import json
            import re

            json_match = re.search(r"\{.*\}", response.content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {"should_generate": False}

        except Exception as e:
            logger.error(f"Error analyzing slide for visualization: {e}")
            return {"should_generate": False}

    def generate_figure_for_slide(
        self, slide_data: Dict, output_dir: str, slide_number: int
    ) -> Optional[str]:
        """Main method to create figure for a single slide"""
        try:
            # Analyze slide content
            visualization_plan = self.analyze_slide_for_visualization(slide_data)

            if not visualization_plan.get("should_generate", False):
                logger.info(f"No visualization needed for slide {slide_number}")
                return None

            # Create output path
            output_path = Path(output_dir) / f"figure_{slide_number:02d}.png"
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Generate appropriate visualization
            viz_type = visualization_plan.get("visualization_type", "bar_chart")

            if viz_type in ["bar_chart", "pie_chart", "line_chart"]:
                self._create_chart(visualization_plan, str(output_path))
            elif viz_type == "table":
                self._create_table_visualization(visualization_plan, str(output_path))
            elif viz_type == "process_flow":
                self._create_process_flow(visualization_plan, str(output_path))
            else:
                logger.warning(f"Unknown visualization type: {viz_type}")
                return None

            logger.info(f"Generated {viz_type} for slide {slide_number}: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"Error generating figure for slide {slide_number}: {e}")
            return None

    def _create_chart(self, viz_plan: Dict, output_path: str):
        """Generate charts using matplotlib"""
        try:
            data = viz_plan.get("data", {})
            labels = data.get("labels", [])
            values = data.get("values", [])
            title = viz_plan.get("title", "Chart")

            # If no real data, create sample data based on slide content
            if not values or not labels:
                labels, values = self._generate_sample_data(viz_plan)

            # Create figure
            fig, ax = plt.subplots(
                figsize=(self.figure_width / 100, self.figure_height / 100)
            )

            viz_type = viz_plan.get("visualization_type", "bar_chart")

            if viz_type == "bar_chart":
                bars = ax.bar(labels, values, color="#003366", alpha=0.8)
                ax.set_ylabel("Values")

                # Add value labels on bars
                for bar, value in zip(bars, values):
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + 0.1,
                        f"{value}",
                        ha="center",
                        va="bottom",
                    )

            elif viz_type == "pie_chart":
                colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))
                wedges, texts, autotexts = ax.pie(
                    values,
                    labels=labels,
                    autopct="%1.1f%%",
                    colors=colors,
                    startangle=90,
                )

            elif viz_type == "line_chart":
                ax.plot(
                    labels,
                    values,
                    marker="o",
                    linewidth=2,
                    markersize=6,
                    color="#003366",
                )
                ax.set_ylabel("Values")
                ax.grid(True, alpha=0.3)

            ax.set_title(title, fontsize=14, fontweight="bold", pad=20)
            ax.tick_params(axis="x", rotation=45)

            plt.tight_layout()
            plt.savefig(
                output_path,
                dpi=100,
                bbox_inches="tight",
                facecolor="white",
                edgecolor="none",
            )
            plt.close()

        except Exception as e:
            logger.error(f"Error creating chart: {e}")
            # Create fallback image
            self._create_fallback_image(output_path, title)

    def _create_table_visualization(self, viz_plan: Dict, output_path: str):
        """Generate table visualization using PIL"""
        try:
            data = viz_plan.get("data", {})
            labels = data.get("labels", [])
            values = data.get("values", [])
            title = viz_plan.get("title", "Table")

            # Create image
            img = Image.new("RGB", (self.figure_width, self.figure_height), "white")
            draw = ImageDraw.Draw(img)

            # Load font
            try:
                title_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 20)
                header_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
                cell_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 14)
            except (OSError, IOError):
                title_font = ImageFont.load_default()
                header_font = ImageFont.load_default()
                cell_font = ImageFont.load_default()

            # Draw title
            title_bbox = draw.textbbox((0, 0), title, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_x = (self.figure_width - title_width) // 2
            draw.text((title_x, 20), title, fill=(0, 51, 102), font=title_font)

            # Draw table
            table_y = 60
            row_height = 30
            col_width = self.figure_width // 2

            # Draw headers
            draw.rectangle(
                [0, table_y, self.figure_width, table_y + row_height],
                outline=(0, 51, 102),
                width=2,
            )
            draw.text(
                (10, table_y + 5), "Category", fill=(0, 51, 102), font=header_font
            )
            draw.text(
                (col_width + 10, table_y + 5),
                "Value",
                fill=(0, 51, 102),
                font=header_font,
            )

            # Draw rows
            for i, (label, value) in enumerate(
                zip(labels[:6], values[:6])
            ):  # Limit to 6 rows
                if table_y + (i + 2) * row_height > self.figure_height - 20:
                    break

                row_y = table_y + (i + 1) * row_height

                # Draw row border
                draw.line(
                    [0, row_y, self.figure_width, row_y], fill=(200, 200, 200), width=1
                )
                draw.line(
                    [col_width, row_y, col_width, row_y + row_height],
                    fill=(200, 200, 200),
                    width=1,
                )

                # Draw cell content
                draw.text(
                    (10, row_y + 5), str(label)[:20], fill=(51, 51, 51), font=cell_font
                )
                draw.text(
                    (col_width + 10, row_y + 5),
                    str(value),
                    fill=(51, 51, 51),
                    font=cell_font,
                )

            img.save(output_path)

        except Exception as e:
            logger.error(f"Error creating table visualization: {e}")
            self._create_fallback_image(output_path, title)

    def _create_process_flow(self, viz_plan: Dict, output_path: str):
        """Generate process flow diagram"""
        try:
            data = viz_plan.get("data", {})
            labels = data.get("labels", [])
            title = viz_plan.get("title", "Process Flow")

            # Create image
            img = Image.new("RGB", (self.figure_width, self.figure_height), "white")
            draw = ImageDraw.Draw(img)

            # Load font
            try:
                title_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 20)
                box_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 14)
            except (OSError, IOError):
                title_font = ImageFont.load_default()
                box_font = ImageFont.load_default()

            # Draw title
            title_bbox = draw.textbbox((0, 0), title, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_x = (self.figure_width - title_width) // 2
            draw.text((title_x, 20), title, fill=(0, 51, 102), font=title_font)

            # Draw process boxes
            box_width = 150
            box_height = 60
            spacing = 50
            start_x = (
                self.figure_width
                - (len(labels) * box_width + (len(labels) - 1) * spacing)
            ) // 2

            for i, label in enumerate(labels[:4]):  # Limit to 4 boxes
                x = start_x + i * (box_width + spacing)
                y = 80

                # Draw box
                draw.rectangle(
                    [x, y, x + box_width, y + box_height],
                    outline=(0, 51, 102),
                    width=2,
                    fill=(240, 248, 255),
                )

                # Draw text
                text_bbox = draw.textbbox((0, 0), str(label)[:15], font=box_font)
                text_width = text_bbox[2] - text_bbox[0]
                text_x = x + (box_width - text_width) // 2
                text_y = y + (box_height - 20) // 2
                draw.text(
                    (text_x, text_y), str(label)[:15], fill=(0, 51, 102), font=box_font
                )

                # Draw arrow to next box
                if i < len(labels) - 1:
                    arrow_x = x + box_width + 10
                    arrow_y = y + box_height // 2
                    draw.polygon(
                        [
                            (arrow_x, arrow_y - 5),
                            (arrow_x + 20, arrow_y),
                            (arrow_x, arrow_y + 5),
                        ],
                        fill=(0, 51, 102),
                    )

            img.save(output_path)

        except Exception as e:
            logger.error(f"Error creating process flow: {e}")
            self._create_fallback_image(output_path, title)

    def _generate_sample_data(self, viz_plan: Dict) -> tuple:
        """Generate sample data when no real data is available"""
        viz_type = viz_plan.get("visualization_type", "bar_chart")

        if viz_type == "bar_chart":
            labels = ["Category A", "Category B", "Category C", "Category D"]
            values = [65, 45, 78, 52]
        elif viz_type == "pie_chart":
            labels = ["Group 1", "Group 2", "Group 3", "Group 4"]
            values = [35, 25, 20, 20]
        elif viz_type == "line_chart":
            labels = ["Q1", "Q2", "Q3", "Q4"]
            values = [45, 52, 48, 61]
        else:
            labels = ["Item 1", "Item 2", "Item 3", "Item 4"]
            values = [25, 40, 35, 30]

        return labels, values

    def _create_fallback_image(self, output_path: str, fallback_title: str):
        """Create a simple fallback image when chart generation fails"""
        try:
            img = Image.new("RGB", (self.figure_width, self.figure_height), "white")
            draw = ImageDraw.Draw(img)

            # Load font
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
            except (OSError, IOError):
                font = ImageFont.load_default()

            # Draw title
            title_bbox = draw.textbbox((0, 0), fallback_title, font=font)
            title_width = title_bbox[2] - title_bbox[0]
            title_x = (self.figure_width - title_width) // 2
            title_y = self.figure_height // 2 - 20

            draw.text((title_x, title_y), fallback_title, fill=(0, 51, 102), font=font)
            draw.text(
                (title_x, title_y + 40),
                "Data Visualization",
                fill=(128, 128, 128),
                font=font,
            )

            img.save(output_path)

        except Exception as e:
            logger.error(f"Error creating fallback image: {e}")

    def process_slides_to_figures(
        self, slides_data: List[Dict], output_dir: str
    ) -> List[Optional[str]]:
        """Process all slides and return figure paths"""
        logger.info(f"Generating figures for {len(slides_data)} slides")

        figure_paths = []

        for i, slide_data in enumerate(slides_data):
            figure_path = self.generate_figure_for_slide(slide_data, output_dir, i + 1)
            figure_paths.append(figure_path)

        generated_count = len([p for p in figure_paths if p is not None])
        logger.info(
            f"Generated {generated_count} figures out of {len(slides_data)} slides"
        )

        return figure_paths
