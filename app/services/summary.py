import os
import tempfile

import requests
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.prompts import PromptTemplate
from langchain_openai import AzureChatOpenAI
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from app.core.config import settings
from app.schemas.summary import SummaryCreate, SummaryResponse


class SummaryService:
    def __init__(self):
        self.llm = AzureChatOpenAI(
            openai_api_version="2024-02-01",
            azure_deployment=settings.AOAI_DEPLOY_GPT4O,
            temperature=0.3,
            api_key=settings.AOAI_API_KEY,
            azure_endpoint=settings.AOAI_ENDPOINT,
        )

    def _load_pdf(self, path_or_url: str):
        """Load PDF file from local path or URL"""
        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            resp = requests.get(path_or_url, timeout=30)
            resp.raise_for_status()
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            tmp.write(resp.content)
            tmp.flush()
            loader = PyMuPDFLoader(tmp.name)
            docs = loader.load()
            os.unlink(tmp.name)
        else:
            if not os.path.exists(path_or_url):
                raise FileNotFoundError(f"PDF not found: {path_or_url}")
            loader = PyMuPDFLoader(path_or_url)
            docs = loader.load()
        return docs

    def _summarize(self, docs):
        """Use LLM to summarize document"""
        full_text = "\n".join([d.page_content for d in docs])

        prompt = """
당신은 전문 논문 요약가입니다. 아래 논문의 주요 내용을 5단락으로 한국어로 요약하세요.
- 주요 주제, 연구 목적, 방법, 결과, 결론 순서로 요약합니다.
- 필요시 핵심 용어를 영어로 병기하세요.
- 문체는 논문 요약 형식(격식체)으로 작성하세요.

본문:
{content}

요약:
"""
        tmpl = PromptTemplate.from_template(prompt)
        chain = tmpl | self.llm
        result = chain.invoke({"content": full_text})
        return result.content.strip()

    def _make_pdf(self, text: str, title="논문 요약 보고서"):
        """Generate PDF file from summarized text"""
        temp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name

        # Register Korean font (try multiple locations)
        font_registered = False
        korean_fonts = [
            r"C:\Windows\Fonts\malgun.ttf",
            r"C:\Windows\Fonts\gulim.ttc",
            r"C:\Windows\Fonts\batang.ttc",
        ]

        for font_path in korean_fonts:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont("Korean", font_path))
                    font_registered = True
                    break
                except Exception:
                    continue

        # Create PDF document
        doc = SimpleDocTemplate(temp_path, pagesize=A4)
        story = []

        # Get styles
        styles = getSampleStyleSheet()

        # Create custom styles with Korean font
        if font_registered:
            title_style = ParagraphStyle(
                "CustomTitle",
                parent=styles["Heading1"],
                fontName="Korean",
                fontSize=18,
                alignment=TA_CENTER,
                spaceAfter=30,
            )
            body_style = ParagraphStyle(
                "CustomBody",
                parent=styles["Normal"],
                fontName="Korean",
                fontSize=11,
                alignment=TA_LEFT,
                leading=16,
            )
        else:
            # Fallback to default fonts (won't show Korean properly)
            title_style = ParagraphStyle(
                "CustomTitle",
                parent=styles["Heading1"],
                fontSize=18,
                alignment=TA_CENTER,
                spaceAfter=30,
            )
            body_style = ParagraphStyle(
                "CustomBody",
                parent=styles["Normal"],
                fontSize=11,
                alignment=TA_LEFT,
                leading=16,
            )

        # Add title
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 20))

        # Add content (split by paragraphs)
        paragraphs = text.split("\n")
        for para in paragraphs:
            if para.strip():
                story.append(Paragraph(para, body_style))
                story.append(Spacer(1, 12))

        # Build PDF
        doc.build(story)
        return temp_path

    def create_summary(self, summary: SummaryCreate) -> SummaryResponse:
        """Main summary creation pipeline"""
        docs = self._load_pdf(summary.path)
        summarized_text = self._summarize(docs)
        pdf_path = self._make_pdf(summarized_text)
        return SummaryResponse(
            title="논문 요약 보고서",
            summary=summarized_text,
            pdf_link=pdf_path,
        )
