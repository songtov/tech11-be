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
        """Extract figures and tables metadata from PDF"""
        try:
            doc = fitz.open(pdf_path)
            figures = []

            for page_num in range(doc.page_count):
                page = doc[page_num]
                # Extract images/figures
                image_list = page.get_images()
                for img_index, img in enumerate(image_list):
                    figures.append(
                        {
                            "page": page_num + 1,
                            "type": "figure",
                            "index": img_index,
                            "description": f"Figure {img_index + 1} on page {page_num + 1}",
                        }
                    )

            doc.close()
            logger.info(f"Extracted {len(figures)} figures from PDF: {pdf_path}")
            return figures

        except Exception as e:
            logger.error(f"Error extracting figures from PDF {pdf_path}: {e}")
            return []

    def summarize_paper_structure(self, text: str) -> Dict:
        """Analyze and summarize the paper structure"""
        system_prompt = """You are an expert academic paper analyzer.
        Analyze the provided research paper text and extract:
        1. Title
        2. Abstract
        3. Key sections (Introduction, Methods, Results, Discussion, Conclusion)
        4. Main findings/key points
        5. Methodology
        6. Key figures/tables mentioned

        Return a structured summary in JSON format."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(
                content=f"Please analyze this research paper:\n\n{text[:8000]}"
            ),  # Limit text for API
        ]

        try:
            response = self.llm.invoke(messages)
            logger.info("Successfully analyzed paper structure")
            return {
                "analysis": response.content,
                "text_length": len(text),
                "chunks": len(self.text_splitter.split_text(text)),
            }
        except Exception as e:
            logger.error(f"Error analyzing paper structure: {e}")
            return {
                "analysis": "Error in analysis",
                "text_length": len(text),
                "chunks": len(self.text_splitter.split_text(text)),
            }

    def extract_key_sections(self, text: str) -> Dict[str, str]:
        """Extract key sections for slide generation"""
        sections = {
            "abstract": "",
            "introduction": "",
            "methods": "",
            "results": "",
            "conclusion": "",
        }

        # Simple text extraction based on common section headers
        lines = text.split("\n")
        current_section = None

        for line in lines:
            line_lower = line.lower().strip()

            if any(keyword in line_lower for keyword in ["abstract", "summary"]):
                current_section = "abstract"
            elif any(
                keyword in line_lower for keyword in ["introduction", "background"]
            ):
                current_section = "introduction"
            elif any(
                keyword in line_lower
                for keyword in ["method", "approach", "experiment"]
            ):
                current_section = "methods"
            elif any(
                keyword in line_lower for keyword in ["result", "finding", "outcome"]
            ):
                current_section = "results"
            elif any(
                keyword in line_lower
                for keyword in ["conclusion", "discussion", "summary"]
            ):
                current_section = "conclusion"

            if current_section and line.strip():
                sections[current_section] += line + "\n"

        # Clean up sections
        for key in sections:
            sections[key] = sections[key].strip()[:2000]  # Limit length

        return sections

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
