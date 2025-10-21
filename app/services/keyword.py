import json
import logging
import os
import tempfile
from typing import Dict

from fastapi import UploadFile
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy.orm import Session

from app.core.config import settings
from app.schemas.keyword import KeywordResponse

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KeywordService:
    def __init__(self, db: Session):
        self.db = db
        self.llm_mini = self._get_llm(temperature=0.2, use_mini=True)
        self.embeddings = self._get_embeddings()

    def _get_llm(self, temperature: float = 0.2, use_mini: bool = True):
        """Get Azure OpenAI LLM instance"""
        return AzureChatOpenAI(
            openai_api_version="2024-02-01",
            azure_deployment=(
                settings.AOAI_DEPLOY_GPT4O_MINI
                if use_mini
                else settings.AOAI_DEPLOY_GPT4O
            ),
            temperature=temperature,
            api_key=settings.AOAI_API_KEY,
            azure_endpoint=settings.AOAI_ENDPOINT,
        )

    def _get_embeddings(self):
        """Get Azure OpenAI embeddings instance"""
        return AzureOpenAIEmbeddings(
            model=settings.AOAI_DEPLOY_EMBED_3_LARGE,
            openai_api_version="2024-02-01",
            api_key=settings.AOAI_API_KEY,
            azure_endpoint=settings.AOAI_ENDPOINT,
        )

    async def _save_upload_file_temp(self, upload_file: UploadFile) -> str:
        """Save uploaded file to temporary location and return path"""
        try:
            # Create temporary file
            suffix = (
                os.path.splitext(upload_file.filename)[1]
                if upload_file.filename
                else ".pdf"
            )
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)

            # Read and write file content
            content = await upload_file.read()
            tmp.write(content)
            tmp.flush()
            tmp.close()

            logger.info(f"✅ File uploaded and saved to temporary location: {tmp.name}")
            return tmp.name

        except Exception as e:
            if tmp and os.path.exists(tmp.name):
                os.unlink(tmp.name)
            raise ValueError(f"Failed to save uploaded file: {str(e)}")

    def _build_vectorstore(self, docs, chunk_size=1000, chunk_overlap=200):
        """Build FAISS vectorstore from documents"""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        splits = splitter.split_documents(docs)

        # Add metadata prefix to each chunk
        for d in splits:
            page = d.metadata.get("page", None)
            src = d.metadata.get("source", "")
            prefix = f"[source: {os.path.basename(src)} | page: {page}] "
            d.page_content = prefix + d.page_content

        vs = FAISS.from_documents(splits, self.embeddings)
        return vs

    def _extract_keywords_from_content(self, content: str) -> Dict[str, str]:
        """Extract 5 keywords from content and translate to Korean"""
        keyword_prompt = """
당신은 학술 논문 및 기술 문서의 핵심 키워드를 추출하는 전문가입니다.

아래 제공된 내용을 분석하여 가장 중요한 영어 키워드 5개를 추출하고, 각각을 한국어로 번역해주세요.

조건:
- 정확히 5개의 키워드만 추출
- 키워드는 학술적/기술적으로 중요한 개념이어야 함
- 너무 일반적인 단어(예: "technology", "system")는 피하고 구체적인 용어 선택
- 각 키워드는 1-4 단어로 구성
- 응답은 반드시 JSON 형식으로만 제공

응답 형식 (JSON만 출력, 다른 설명 없이):
{{
    "한글번역1": "English Keyword 1",
    "한글번역2": "English Keyword 2",
    "한글번역3": "English Keyword 3",
    "한글번역4": "English Keyword 4",
    "한글번역5": "English Keyword 5"
}}

내용:
{content}

키워드를 JSON 형식으로 추출해주세요:
"""
        prompt_template = PromptTemplate.from_template(keyword_prompt)
        keyword_chain = prompt_template | self.llm_mini | StrOutputParser()
        result = keyword_chain.invoke({"content": content})

        # Parse JSON response
        try:
            # Clean up response - remove markdown code blocks if present
            result = result.strip()
            if result.startswith("```json"):
                result = result[7:]
            if result.startswith("```"):
                result = result[3:]
            if result.endswith("```"):
                result = result[:-3]
            result = result.strip()

            keywords_dict = json.loads(result)

            # Validate we have exactly 5 keywords
            if len(keywords_dict) != 5:
                logger.warning(
                    f"Expected 5 keywords but got {len(keywords_dict)}, regenerating..."
                )
                raise ValueError("Invalid number of keywords")

            return keywords_dict
        except Exception as e:
            logger.error(f"Failed to parse keyword response: {e}")
            # Return fallback keywords
            return {
                "키워드추출실패": "Keyword Extraction Failed",
                "재시도필요": "Retry Required",
                "시스템오류": "System Error",
                "분석실패": "Analysis Failed",
                "기본응답": "Default Response",
            }

    async def extract_keywords_from_pdf(self, file: UploadFile) -> KeywordResponse:
        """Extract keywords from uploaded PDF file using RAG"""
        temp_pdf_path = None

        try:
            # 1. Validate file type
            if not file.filename.lower().endswith(".pdf"):
                raise ValueError("Only PDF files are supported")

            logger.info(f"📥 Processing uploaded PDF: {file.filename}")

            # 2. Save uploaded file to temporary location
            temp_pdf_path = await self._save_upload_file_temp(file)

            # 3. Load PDF using RAG (from quiz.py)
            logger.info("📄 Loading PDF")
            loader = PyMuPDFLoader(temp_pdf_path)
            docs = loader.load()

            # 4. Build vectorstore
            logger.info("🔨 Building vectorstore")
            vectorstore = self._build_vectorstore(docs)

            # 5. Get relevant chunks for keyword extraction
            logger.info("🔍 Retrieving relevant content chunks")
            chunks = vectorstore.similarity_search(
                "Extract main keywords and concepts from this document", k=10
            )
            document_content = "\n\n".join([c.page_content for c in chunks])

            # 6. Extract keywords
            logger.info("🎯 Extracting keywords")
            keywords = self._extract_keywords_from_content(document_content)

            logger.info(f"✅ Keywords extracted successfully: {keywords}")
            return KeywordResponse(keywords=keywords)

        except ValueError as e:
            logger.error(f"❌ Validation error: {e}")
            raise e
        except Exception as e:
            logger.error(f"❌ Keyword extraction failed: {e}")
            raise ValueError(f"키워드 추출 중 오류가 발생했습니다: {str(e)}")
        finally:
            # Clean up temporary file
            if temp_pdf_path and os.path.exists(temp_pdf_path):
                os.unlink(temp_pdf_path)
                logger.info(f"🗑️ 임시 PDF 파일 삭제: {temp_pdf_path}")

    def extract_keywords_from_text(self, text: str) -> KeywordResponse:
        """Extract keywords from simple text input"""
        try:
            logger.info(f"🔍 Extracting keywords from text: {text[:100]}...")

            # Extract keywords directly from text
            keywords = self._extract_keywords_from_content(text)

            logger.info(f"✅ Keywords extracted successfully: {keywords}")
            return KeywordResponse(keywords=keywords)

        except Exception as e:
            logger.error(f"❌ Keyword extraction failed: {e}")
            raise ValueError(f"키워드 추출 중 오류가 발생했습니다: {str(e)}")
