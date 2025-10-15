"""
Reader Agent - Extracts and processes content from research papers
"""

import logging
from typing import Dict, List

import fitz  # PyMuPDF
from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import AzureChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


class ReaderAgent:
    """Agent responsible for reading and extracting content from PDF research papers"""

    def __init__(
        self, azure_endpoint: str, api_key: str, deployment_name: str = "gpt-4o-mini"
    ):
        self.llm = AzureChatOpenAI(
            azure_endpoint=azure_endpoint,
            api_key=api_key,
            azure_deployment=deployment_name,
            openai_api_version="2024-02-01",
            temperature=0.1,
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200,
            length_function=len,
        )

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text content from PDF file"""
        try:
            doc = fitz.open(pdf_path)
            text = ""

            for page_num in range(doc.page_count):
                page = doc[page_num]
                text += page.get_text()

            doc.close()
            logger.info(f"Extracted {len(text)} characters from PDF: {pdf_path}")
            return text

        except Exception as e:
            logger.error(f"Error extracting text from PDF {pdf_path}: {e}")
            raise

    def extract_figures_and_tables(self, pdf_path: str) -> List[Dict]:
        """Extract figures, tables, and images from PDF with enhanced metadata"""
        try:
            doc = fitz.open(pdf_path)
            visual_elements = []

            for page_num in range(doc.page_count):
                page = doc[page_num]

                # Extract images/figures with enhanced metadata
                image_list = page.get_images()
                for img_index, img in enumerate(image_list):
                    # Get image metadata
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)

                    # Extract image data
                    img_data = pix.tobytes("png")
                    img_size = (pix.width, pix.height)

                    # Determine if it's likely a figure, chart, or diagram
                    element_type = self._classify_visual_element(img_size, page_num)

                    visual_elements.append(
                        {
                            "page": page_num + 1,
                            "type": element_type,
                            "index": img_index,
                            "description": f"{element_type.title()} {img_index + 1} on page {page_num + 1}",
                            "size": img_size,
                            "data": img_data,
                            "xref": xref,
                            "is_large": img_size[0] > 200
                            and img_size[1] > 200,  # Likely important figure
                            "aspect_ratio": (
                                img_size[0] / img_size[1] if img_size[1] > 0 else 1
                            ),
                        }
                    )

                    pix = None  # Free memory

                # Extract tables using text analysis
                tables = self._extract_tables_from_page(page, page_num)
                visual_elements.extend(tables)

            doc.close()
            logger.info(
                f"Extracted {len(visual_elements)} visual elements from PDF: {pdf_path}"
            )
            return visual_elements

        except Exception as e:
            logger.error(f"Error extracting visual elements from PDF {pdf_path}: {e}")
            return []

    def _classify_visual_element(self, size: tuple, page_num: int) -> str:
        """Classify visual element based on size and context"""
        width, height = size

        # Large images are likely figures or charts
        if width > 300 and height > 200:
            return "figure"
        # Medium images might be diagrams
        elif width > 150 and height > 100:
            return "diagram"
        # Small images are likely icons or small charts
        else:
            return "chart"

    def _extract_tables_from_page(self, page, page_num: int) -> List[Dict]:
        """Extract table information from page text"""
        tables = []
        text = page.get_text()

        # Look for table-like structures in text
        lines = text.split("\n")
        table_candidates = []
        current_table = []

        for line in lines:
            line = line.strip()
            if not line:
                if current_table and len(current_table) >= 2:
                    table_candidates.append(current_table)
                current_table = []
            else:
                # Check if line looks like table data (multiple columns)
                if "\t" in line or len(line.split()) > 3:
                    current_table.append(line)

        # Process table candidates
        for i, table_data in enumerate(table_candidates):
            if len(table_data) >= 2:  # At least 2 rows
                tables.append(
                    {
                        "page": page_num + 1,
                        "type": "table",
                        "index": i,
                        "description": f"Table {i + 1} on page {page_num + 1}",
                        "data": table_data,
                        "rows": len(table_data),
                        "is_large": len(table_data) > 3,
                    }
                )

        return tables

    def summarize_paper_structure(self, text: str) -> Dict:
        """Analyze and summarize the paper structure with enhanced content extraction"""
        system_prompt = """You are an expert academic paper analyzer and presentation designer.
        Analyze the provided research paper text and extract comprehensive information for creating professional presentation slides:

        1. Title and main topic
        2. Abstract with key points (3-5 bullet points)
        3. Introduction with background and objectives
        4. Methodology/Approach with specific details
        5. Key Results/Findings with specific data and statistics
        6. Discussion/Implications with practical applications
        7. Conclusion with main takeaways
        8. Key figures/tables mentioned and their significance
        9. Important statistics, percentages, or numerical data
        10. Technical terms and their explanations
        11. Research questions and hypotheses
        12. Limitations and future work

        Focus on extracting:
        - Specific numbers, percentages, and statistics
        - Technical terms with explanations
        - Key findings that can be visualized
        - Important quotes or statements
        - Methodology details
        - Practical implications

        Return a comprehensive structured summary in JSON format that can be used to create information-rich presentation slides."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(
                content=f"Please analyze this research paper for presentation creation:\n\n{text[:10000]}"
            ),  # Increased text limit for better analysis
        ]

        try:
            response = self.llm.invoke(messages)
            logger.info("Successfully analyzed paper structure")
            return {
                "analysis": response.content,
                "text_length": len(text),
                "chunks": len(self.text_splitter.split_text(text)),
                "enhanced_extraction": True,
            }
        except Exception as e:
            logger.error(f"Error analyzing paper structure: {e}")
            return {
                "analysis": "Error in analysis",
                "text_length": len(text),
                "chunks": len(self.text_splitter.split_text(text)),
                "enhanced_extraction": False,
            }

    def extract_key_sections(self, text: str) -> Dict[str, str]:
        """Extract key sections for slide generation with enhanced detail"""
        sections = {
            "abstract": "",
            "introduction": "",
            "methods": "",
            "results": "",
            "conclusion": "",
            "statistics": "",
            "key_findings": "",
            "methodology": "",
            "implications": "",
        }

        # Enhanced text extraction with better section detection
        lines = text.split("\n")
        current_section = None
        section_content = []

        for line in lines:
            line_lower = line.lower().strip()
            line_original = line.strip()

            # More comprehensive section detection
            if any(
                keyword in line_lower for keyword in ["abstract", "summary", "overview"]
            ):
                if current_section and section_content:
                    sections[current_section] = "\n".join(section_content)
                current_section = "abstract"
                section_content = []
            elif any(
                keyword in line_lower
                for keyword in [
                    "introduction",
                    "background",
                    "motivation",
                    "problem statement",
                ]
            ):
                if current_section and section_content:
                    sections[current_section] = "\n".join(section_content)
                current_section = "introduction"
                section_content = []
            elif any(
                keyword in line_lower
                for keyword in [
                    "method",
                    "approach",
                    "experiment",
                    "methodology",
                    "procedure",
                ]
            ):
                if current_section and section_content:
                    sections[current_section] = "\n".join(section_content)
                current_section = "methods"
                section_content = []
            elif any(
                keyword in line_lower
                for keyword in ["result", "finding", "outcome", "analysis", "data"]
            ):
                if current_section and section_content:
                    sections[current_section] = "\n".join(section_content)
                current_section = "results"
                section_content = []
            elif any(
                keyword in line_lower
                for keyword in [
                    "conclusion",
                    "discussion",
                    "implication",
                    "future work",
                ]
            ):
                if current_section and section_content:
                    sections[current_section] = "\n".join(section_content)
                current_section = "conclusion"
                section_content = []
            elif any(
                keyword in line_lower
                for keyword in [
                    "statistical",
                    "percentage",
                    "%",
                    "significant",
                    "p-value",
                ]
            ):
                if current_section and section_content:
                    sections[current_section] = "\n".join(section_content)
                current_section = "statistics"
                section_content = []

            if current_section and line_original:
                section_content.append(line_original)

        # Save the last section
        if current_section and section_content:
            sections[current_section] = "\n".join(section_content)

        # Extract additional key information
        sections["key_findings"] = self._extract_key_findings(text)
        sections["methodology"] = self._extract_methodology_details(text)
        sections["implications"] = self._extract_implications(text)

        # Clean up and limit sections
        for key in sections:
            if sections[key]:
                sections[key] = sections[key].strip()[
                    :3000
                ]  # Increased limit for more content

        return sections

    def _extract_key_findings(self, text: str) -> str:
        """Extract key findings and statistics from text"""
        findings = []
        lines = text.split("\n")

        for line in lines:
            line = line.strip()
            # Look for lines with statistics or key findings
            if any(
                indicator in line.lower()
                for indicator in [
                    "significant",
                    "found that",
                    "showed",
                    "revealed",
                    "demonstrated",
                    "%",
                    "p <",
                    "p >",
                ]
            ):
                if len(line) > 20 and len(line) < 200:  # Reasonable length
                    findings.append(line)

        return "\n".join(findings[:5])  # Top 5 findings

    def _extract_methodology_details(self, text: str) -> str:
        """Extract methodology details"""
        methodology = []
        lines = text.split("\n")

        for line in lines:
            line = line.strip()
            # Look for methodology-related content
            if any(
                indicator in line.lower()
                for indicator in [
                    "participants",
                    "sample",
                    "procedure",
                    "data collection",
                    "analysis",
                    "software",
                    "tool",
                ]
            ):
                if len(line) > 20 and len(line) < 200:
                    methodology.append(line)

        return "\n".join(methodology[:5])

    def _extract_implications(self, text: str) -> str:
        """Extract implications and applications"""
        implications = []
        lines = text.split("\n")

        for line in lines:
            line = line.strip()
            # Look for implication-related content
            if any(
                indicator in line.lower()
                for indicator in [
                    "implication",
                    "application",
                    "practice",
                    "policy",
                    "future",
                    "recommendation",
                ]
            ):
                if len(line) > 20 and len(line) < 200:
                    implications.append(line)

        return "\n".join(implications[:5])

    def process_research_paper(self, pdf_path: str) -> Dict:
        """Main method to process a research paper"""
        logger.info(f"Processing research paper: {pdf_path}")

        # Extract text
        text = self.extract_text_from_pdf(pdf_path)

        # Extract figures
        figures = self.extract_figures_and_tables(pdf_path)

        # Analyze structure
        structure = self.summarize_paper_structure(text)

        # Extract key sections
        sections = self.extract_key_sections(text)

        return {
            "full_text": text,
            "sections": sections,
            "figures": figures,
            "structure": structure,
            "metadata": {
                "pdf_path": pdf_path,
                "text_length": len(text),
                "num_figures": len(figures),
            },
        }

    def process_research_paper_from_url(self, pdf_url: str) -> Dict:
        """Main method to process a research paper from URL"""
        logger.info(f"Processing research paper from URL: {pdf_url}")

        # Download PDF to temporary file
        import tempfile

        import requests

        try:
            # Download PDF
            response = requests.get(pdf_url, timeout=30)
            response.raise_for_status()

            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
                temp_file.write(response.content)
                temp_path = temp_file.name

            logger.info(f"Downloaded PDF to temporary file: {temp_path}")

            # Process the temporary file
            result = self.process_research_paper(temp_path)

            # Clean up temporary file
            import os

            os.unlink(temp_path)

            return result

        except Exception as e:
            logger.error(f"Error processing PDF from URL {pdf_url}: {e}")
            raise
