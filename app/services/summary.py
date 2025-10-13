import logging
import os
import tempfile

import boto3
from botocore.exceptions import ClientError
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.prompts import PromptTemplate
from langchain_openai import AzureChatOpenAI
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories.research_repository import ResearchRepository
from app.schemas.summary import SummaryCreate, SummaryResponse

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SummaryService:
    def __init__(self, db: Session):
        self.db = db
        self.research_repository = ResearchRepository(db)
        self.llm = AzureChatOpenAI(
            openai_api_version="2024-02-01",
            azure_deployment=settings.AOAI_DEPLOY_GPT4O,
            temperature=0.3,
            api_key=settings.AOAI_API_KEY,
            azure_endpoint=settings.AOAI_ENDPOINT,
        )

    def _load_pdf_from_s3(self, filename: str):
        """Load PDF file from S3 bucket"""
        # Validate S3 configuration
        if not settings.S3_BUCKET:
            raise ValueError(
                "S3_BUCKET environment variable is not configured. "
                "Please set S3_BUCKET in your environment variables."
            )
        if not settings.AWS_ACCESS_KEY or not settings.AWS_SECRET_KEY:
            raise ValueError(
                "AWS credentials are not configured. "
                "Please set AWS_ACCESS_KEY and AWS_SECRET_KEY in your environment variables."
            )

        # Construct S3 key (assuming files are in output/research/ directory)
        s3_key = f"output/research/{filename}"

        logger.info(f"📥 Downloading PDF from S3: s3://{settings.S3_BUCKET}/{s3_key}")

        # Initialize S3 client
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY,
            aws_secret_access_key=settings.AWS_SECRET_KEY,
        )

        try:
            # Check if file exists in S3
            s3_client.head_object(Bucket=settings.S3_BUCKET, Key=s3_key)
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "404":
                raise FileNotFoundError(
                    f"PDF file '{filename}' not found in S3 bucket. "
                    f"Expected location: s3://{settings.S3_BUCKET}/{s3_key}"
                )
            else:
                raise ValueError(f"Error accessing S3 file: {str(e)}")

        # Download PDF from S3 to temporary file
        try:
            # Create temporary file
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")

            # Download from S3
            s3_client.download_fileobj(settings.S3_BUCKET, s3_key, tmp)
            tmp.flush()
            tmp.close()

            logger.info("✅ PDF downloaded successfully from S3")

            # Load PDF using PyMuPDFLoader
            loader = PyMuPDFLoader(tmp.name)
            docs = loader.load()

            # Clean up temporary file
            os.unlink(tmp.name)

            return docs

        except Exception as e:
            # Clean up temporary file if it exists
            if tmp and os.path.exists(tmp.name):
                os.unlink(tmp.name)
            raise ValueError(f"Failed to download or load PDF from S3: {str(e)}")

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

        # Register Korean font (try multiple locations for cross-platform support)
        font_registered = False
        korean_fonts = [
            # Linux/Docker paths (Noto Sans KR - install via apt-get install fonts-noto-cjk)
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
            # macOS paths
            "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
            "/Library/Fonts/AppleGothic.ttf",
            "/System/Library/Fonts/AppleSDGothicNeo.ttc",
            # Windows paths
            r"C:\Windows\Fonts\malgun.ttf",
            r"C:\Windows\Fonts\gulim.ttc",
            r"C:\Windows\Fonts\batang.ttc",
        ]

        for font_path in korean_fonts:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont("Korean", font_path))
                    font_registered = True
                    logger.info(f"✅ Korean font registered: {font_path}")
                    break
                except Exception as e:
                    logger.warning(f"Failed to register font {font_path}: {e}")
                    continue

        if not font_registered:
            logger.warning(
                "⚠️ No Korean font found. PDF may not display Korean text correctly."
            )

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
        """Main summary creation pipeline - fetch PDF from S3 and generate summary"""
        logger.info(f"Creating summary for PDF: {summary.filename}")

        # Load PDF from S3
        docs = self._load_pdf_from_s3(summary.filename)

        # Generate summary
        summarized_text = self._summarize(docs)

        # Create summary PDF
        pdf_path = self._make_pdf(summarized_text)

        return SummaryResponse(
            title="논문 요약 보고서",
            summary=summarized_text,
            pdf_link=pdf_path,
        )

    def create_summary_from_research_id(self, research_id: int) -> SummaryResponse:
        """Create summary from research ID by fetching research from database"""
        try:
            # 1. Fetch research from database
            logger.info(f"🔍 Fetching research with ID: {research_id}")
            research = self.research_repository.get_by_id(research_id)

            if not research:
                raise ValueError(f"Research with ID {research_id} not found")

            # 2. Validate research has object_key (S3 filename)
            if not research.object_key:
                raise ValueError(
                    f"Research with ID {research_id} does not have an associated PDF file (missing object_key)"
                )

            # 3. Extract filename from object_key
            # object_key format: "output/research/filename.pdf"
            object_key = research.object_key
            filename = object_key.split("/")[-1] if "/" in object_key else object_key

            logger.info(f"📄 Using filename from research object_key: {filename}")

            # 4. Generate summary using existing method
            return self.create_summary(SummaryCreate(filename=filename))

        except ValueError as e:
            logger.error(f"❌ Research validation failed: {e}")
            raise e
        except Exception as e:
            logger.error(f"❌ Summary generation from research ID failed: {e}")
            raise ValueError(f"요약 생성 중 오류가 발생했습니다: {str(e)}")
