from __future__ import annotations

import logging
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, TypedDict

import boto3
from botocore.exceptions import ClientError
from gtts import gTTS
from langchain.retrievers import EnsembleRetriever
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories.research_repository import ResearchRepository
from app.repositories.tts_repository import TTSRepository

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===========================================================
# ✅ S3 기반 TTS 서비스 (Legacy 독립형)
# ===========================================================


# Agent State Type
class AgentState(TypedDict, total=False):
    vectorstore: Any
    k: int
    summary: str
    explainer: str


def clean_text(text: str) -> str:
    """TTS용 텍스트 정제"""
    cleaned = re.sub(r"[#*>•\-]+", " ", text)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


class TTSService:
    def __init__(self, db: Session = None):
        self.db = db

        self.temp_dir = Path(settings.TEMP_DIR)
        self.output_dir = self.temp_dir / "tech11_tts"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.legacy_papers_dir = Path("legacy/downloaded_papers")

        # Initialize database repositories if db session provided
        self.research_repository = ResearchRepository(db) if db else None
        self.tts_repository = TTSRepository(db) if db else None

        # Initialize S3 client
        self.s3_client = None
        if settings.AWS_ACCESS_KEY and settings.AWS_SECRET_KEY:
            self.s3_client = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY,
                aws_secret_access_key=settings.AWS_SECRET_KEY,
            )

    # =====================================================
    # 0️⃣ S3 Helper Methods
    # =====================================================
    def _download_pdf_from_s3(self, filename: str) -> str:
        """Download PDF file from S3 bucket and return temporary file path"""
        # Validate S3 configuration
        if not settings.S3_BUCKET:
            raise ValueError(
                "S3_BUCKET environment variable is not configured. "
                "Please set S3_BUCKET in your environment variables."
            )
        if not self.s3_client:
            raise ValueError(
                "AWS credentials are not configured. "
                "Please set AWS_ACCESS_KEY and AWS_SECRET_KEY in your environment variables."
            )

        # Construct S3 key
        s3_key = f"output/research/{filename}"

        logger.info(f"📥 Downloading PDF from S3: s3://{settings.S3_BUCKET}/{s3_key}")

        try:
            # Check if file exists in S3
            self.s3_client.head_object(Bucket=settings.S3_BUCKET, Key=s3_key)
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
            self.s3_client.download_fileobj(settings.S3_BUCKET, s3_key, tmp)
            tmp.flush()
            tmp.close()

            logger.info("✅ PDF downloaded successfully from S3")
            return tmp.name

        except Exception as e:
            # Clean up temporary file if it exists
            if tmp and os.path.exists(tmp.name):
                os.unlink(tmp.name)
            raise ValueError(f"Failed to download PDF from S3: {str(e)}")

    def _upload_audio_to_s3(self, local_file_path: str, filename: str) -> str:
        """Upload audio file to S3 bucket and return S3 URL"""
        if not settings.S3_BUCKET:
            raise ValueError("S3_BUCKET environment variable is not configured.")
        if not self.s3_client:
            raise ValueError("AWS credentials are not configured.")

        # Construct S3 key for TTS audio files
        s3_key = f"output/tts/{filename}"

        logger.info(f"📤 Uploading audio to S3: s3://{settings.S3_BUCKET}/{s3_key}")

        try:
            # Upload file to S3
            self.s3_client.upload_file(
                local_file_path,
                settings.S3_BUCKET,
                s3_key,
                ExtraArgs={"ContentType": "audio/mpeg"},
            )

            # Generate S3 URL
            s3_url = f"s3://{settings.S3_BUCKET}/{s3_key}"
            logger.info(f"✅ Audio uploaded successfully to S3: {s3_url}")

            return s3_url

        except Exception as e:
            raise ValueError(f"Failed to upload audio to S3: {str(e)}")

    def _get_audio_url_from_s3(self, object_key: str) -> str | None:
        """Generate presigned URL for audio file in S3 using object_key"""
        if not settings.S3_BUCKET or not self.s3_client:
            return None

        try:
            # Check if file exists
            self.s3_client.head_object(Bucket=settings.S3_BUCKET, Key=object_key)

            # Generate presigned URL (valid for 1 hour)
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": settings.S3_BUCKET, "Key": object_key},
                ExpiresIn=3600,
            )
            return url
        except ClientError:
            return None

    # =====================================================
    # 1️⃣ LLM/Embeddings 팩토리 (Legacy 통합)
    # =====================================================
    def _build_llm(self, use_mini: bool = True, temperature: float = 0.2):
        """Azure OpenAI LLM 생성"""
        return AzureChatOpenAI(
            openai_api_version="2024-02-01",
            azure_deployment=(
                settings.AOAI_DEPLOY_GPT4O_MINI
                if use_mini
                else settings.AOAI_DEPLOY_GPT4O
            ),
            api_key=settings.AOAI_API_KEY,
            azure_endpoint=settings.AOAI_ENDPOINT,
            temperature=temperature,
        )

    def _build_embeddings(self):
        """Azure OpenAI Embeddings 생성"""
        return AzureOpenAIEmbeddings(
            model=settings.AOAI_DEPLOY_EMBED_3_LARGE,
            openai_api_version="2024-02-01",
            api_key=settings.AOAI_API_KEY,
            azure_endpoint=settings.AOAI_ENDPOINT,
        )

    # =====================================================
    # 2️⃣ PDF 처리 (Legacy 통합)
    # =====================================================
    def _load_pdf(self, path: str) -> List[Document]:
        """PDF 로딩"""
        loader = PyMuPDFLoader(path)
        return loader.load()

    def _build_vectorstore(
        self, docs: List[Document], chunk_size: int = 1500, chunk_overlap: int = 300
    ):
        """하이브리드 검색을 위한 벡터스토어 및 리트리버 구축 (FAISS + BM25)"""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        splits = splitter.split_documents(docs)

        # 메타데이터 추가
        for d in splits:
            page = d.metadata.get("page", None)
            src = d.metadata.get("source", "")
            prefix = f"[source: {os.path.basename(src)} | page: {page}] "
            d.page_content = prefix + d.page_content

        # 1. FAISS 벡터 검색 (Dense Retrieval)
        embeddings = self._build_embeddings()
        faiss_vectorstore = FAISS.from_documents(splits, embeddings)
        faiss_retriever = faiss_vectorstore.as_retriever(search_kwargs={"k": 12})

        # 2. BM25 키워드 검색 (Sparse Retrieval)
        bm25_retriever = BM25Retriever.from_documents(splits)
        bm25_retriever.k = 12

        # 3. 하이브리드 앙상블 리트리버 (가중치: FAISS 0.6, BM25 0.4)
        hybrid_retriever = EnsembleRetriever(
            retrievers=[faiss_retriever, bm25_retriever],
            weights=[0.6, 0.4],  # 벡터 검색에 더 높은 가중치
        )

        # 기존 코드와의 호환성을 위해 vectorstore 객체에 hybrid_retriever 추가
        faiss_vectorstore.hybrid_retriever = hybrid_retriever

        return faiss_vectorstore

    # =====================================================
    # 3️⃣ 프롬프트 체인들 (Legacy 통합)
    # =====================================================
    def _make_summary_chain(self):
        """요약 생성 체인"""
        prompt = PromptTemplate.from_template(
            """당신은 논문을 한국어로 요약하는 전문가입니다.
아래 문서를 읽고 다음 항목을 포함해 간결하고 구조화된 요약을 작성하세요.

1) 한 줄 요약
2) 연구 배경과 문제 정의
3) 핵심 기술과 방법론
4) 주요 결과와 성능
5) 기술적 시사점과 해당 도메인을 넘어 AI 및 DT 시장에 적용할 수 있는 방향 제시
6) 핵심 키워드 다시 한 번 설명. 해당 문서의 핵심 용어 및 새로운 개념에 대해 짚어주기.

문서 내용:
{document_content}
"""
        )
        return prompt | self._build_llm(use_mini=True) | StrOutputParser()

    def _make_explainer_chain(self):
        """해설 생성 체인 - 열정적인 교육 팟캐스트 스타일"""
        prompt = PromptTemplate.from_template(
            """당신은 열정적인 교수이자 팟캐스트 진행자입니다. 청취자들이 흥미를 가지고 쉽게 이해할 수 있도록 친근하고 구어체로 설명하세요.

**중요한 규칙:**
- 제목, 헤더, 번호 매기기를 절대 사용하지 마세요 (예: ###, ####, 1), 2) 등)
- 마크다운 형식(###, **, ---, #### 등)을 사용하지 마세요
- 괄호 ()를 스크립트로 만들지 말고, 서술을 통해 말해줘. 예를 들어 기존의 'LSTM(LongShortTermMemory)' 을 'LongShortTermMemory로 불리우는 LSTM은' 으로 수정
- "한국어 해설 스크립트", "논문의 상세 설명", "일반인도 이해할 수 있는 쉬운 설명" 같은 메타 정보를 쓰지 마세요
- 구어체를 사용하세요 (~해요, ~이에요, ~거든요, ~네요, ~잖아요 등)
- 팟캐스트와 같은 컨셉으로, 청취자에게 직접 말하듯이 작성하세요 ("여러분", "우리", "~해볼까요?", "~보세요" 등)
- 열정적이고 친근한 톤으로 작성하세요
- 복잡한 용어는 일상적인 비유나 예시로 풀어서 설명하세요
- 항상 첫 시작 문장은 '가장 앞선 세상을 배우다, 오늘의 에이엑스프레스 시작합니다!'로 시작하고, 팟캐스트 dj처럼 진행하는 것으로 해줘.

**내용 구성:**
자연스러운 이야기 흐름으로 다음을 포함하세요:
1. 연구 주제를 흥미롭게 소개하며 시작. 다만, 첫 소개에서는 전문적인 용어를 그대로 사용하여 명확하게 내용을 전달.
2. 핵심 개념을 쉬운 비유와 예시로 설명
3. 수식 및 실험 결과 설명에 대해서는 명확하게 전문 용어를 그대로 사용할 것.
4. 실제 산업 현장에서의 활용 사례 2-3가지를 구체적으로 소개(가능하다면, AI 및 IT 서비스와 연결지으면 좋을 것.)
5. 이 연구의 의의와 함께 왜 이 연구가 중요한지 마무리로 설명.

문서 내용:
{document_content}

이제 청취자들이 집중하며 들을 수 있도록, 친근하고 열정적으로 설명을 시작하세요:"""
        )
        return (
            prompt
            | self._build_llm(use_mini=False, temperature=0.5)
            | StrOutputParser()
        )

    # =====================================================
    # 4️⃣ LangGraph 노드들 (Legacy 통합)
    # =====================================================
    def _node_summarizer(self, state: AgentState) -> AgentState:
        """요약 생성 노드 - 하이브리드 검색 사용"""
        vs = state["vectorstore"]
        query = "summary overview of this document"

        # 하이브리드 검색 사용 (FAISS + BM25)
        chunks = vs.hybrid_retriever.get_relevant_documents(query)
        content = "\n\n".join([c.page_content for c in chunks])

        logger.info("📝 요약 생성 중... (하이브리드 검색)")
        summary_chain = self._make_summary_chain()
        summary = summary_chain.invoke({"document_content": content})
        return {"summary": summary}

    def _node_explainer(self, state: AgentState) -> AgentState:
        """해설 생성 노드 - 하이브리드 검색 사용"""
        vs = state["vectorstore"]
        query = "detailed explanation with industry applications"

        # 하이브리드 검색 사용 (FAISS + BM25)
        chunks = vs.hybrid_retriever.get_relevant_documents(query)
        content = "\n\n".join([c.page_content for c in chunks])

        logger.info("📖 해설 생성 중... (하이브리드 검색)")
        explainer_chain = self._make_explainer_chain()
        explainer = explainer_chain.invoke({"document_content": content})
        return {"explainer": explainer}

    # =====================================================
    # 5️⃣ 멀티에이전트 실행 (Legacy 독립형)
    # =====================================================
    async def _run_legacy_multi_agent(self, pdf_path: str) -> Dict[str, Any]:
        """
        Legacy 독립형 멀티에이전트 실행
        PDF → 벡터스토어 → summary/explainer 생성 (Legacy 폴더 불필요)
        """
        try:
            logger.info(f"🎯 PDF 처리 시작: {pdf_path}")

            # 1. PDF 로드
            docs = self._load_pdf(pdf_path)
            logger.info(f"✅ PDF 로드 완료: {len(docs)}개 문서")

            # 2. 벡터스토어 구축
            vs = self._build_vectorstore(docs)
            logger.info("✅ 벡터스토어 구축 완료")

            # 3. 상태 초기화
            state: AgentState = {"vectorstore": vs, "k": 20}

            # 4. 요약 생성
            summary_result = self._node_summarizer(state)
            state.update(summary_result)

            # 5. 해설 생성
            explainer_result = self._node_explainer(state)
            state.update(explainer_result)

            logger.info("✅ 멀티에이전트 처리 완료")

            # 6. 결과 파일 저장 (output/tts)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            if state.get("summary"):
                summary_path = self.output_dir / f"summary_{ts}.txt"
                with open(summary_path, "w", encoding="utf-8") as f:
                    f.write(state["summary"])
                logger.info(f"📝 요약 저장: {summary_path}")

            if state.get("explainer"):
                explainer_path = self.output_dir / f"explainer_{ts}.txt"
                with open(explainer_path, "w", encoding="utf-8") as f:
                    f.write(state["explainer"])
                logger.info(f"📝 해설 저장: {explainer_path}")

            return {
                "summary": state.get("summary", ""),
                "explainer": state.get("explainer", ""),
                "quiz": "",  # TTS에서는 사용하지 않음
            }
        except Exception as e:
            logger.error(f"❌ 멀티에이전트 실행 실패: {e}")
            raise e

    # =====================================================
    # 2️⃣ PDF → 멀티에이전트 → TTS 변환 전체 흐름
    # =====================================================
    async def process_pdf_to_tts(self, pdf_path: str) -> Dict[str, Any]:
        """
        Legacy multitest.py의 node_tts 로직을 정확히 따름
        PDF → 멀티에이전트 → explainer만 TTS 변환
        (Local file path version for backward compatibility)
        """
        try:
            # 1. 멀티에이전트 실행 (legacy run_multi_agent 호출)
            logger.info(f"📘 Processing PDF: {pdf_path}")
            agent_result = await self._run_legacy_multi_agent(pdf_path)

            # 2. Legacy node_tts와 동일: explainer만 사용
            script = agent_result.get("explainer", "")
            if not script:
                # Legacy와 동일: explainer가 없으면 빈 결과 반환
                return {
                    "summary": agent_result.get("summary", ""),
                    "explainer": "",
                    "tts_id": None,
                    "audio_filename": None,
                    "audio_file_path": None,
                }

            # 3. Legacy node_tts와 동일: clean_text 적용
            script_clean = clean_text(script)

            # 4. Legacy node_tts와 동일: 파일명 생성
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_filename = f"industry_explainer_{ts}.mp3"
            file_path = self.output_dir / audio_filename

            # 5. Legacy node_tts와 동일: gTTS 생성 및 저장
            tts = gTTS(text=script_clean, lang="ko")
            tts.save(str(file_path))
            logger.info(f"🎧 TTS 저장 완료: {audio_filename}")

            return {
                "summary": agent_result.get("summary", ""),
                "explainer": script,
                "tts_id": ts,
                "audio_filename": audio_filename,
                "audio_file_path": str(file_path),
            }

        except Exception as e:
            logger.error(f"❌ PDF → TTS 처리 실패: {e}")
            raise e

    async def process_pdf_from_s3_to_tts(self, filename: str) -> Dict[str, Any]:
        """
        S3 기반 PDF → 멀티에이전트 → TTS 변환 → S3 업로드
        PDF를 S3에서 다운로드, 처리 후 TTS를 S3에 업로드
        """
        temp_pdf_path = None
        temp_audio_path = None

        try:
            # 1. S3에서 PDF 다운로드
            logger.info(f"📥 Downloading PDF from S3: {filename}")
            temp_pdf_path = self._download_pdf_from_s3(filename)

            # 2. 멀티에이전트 실행
            logger.info("🤖 Running multi-agent on PDF")
            agent_result = await self._run_legacy_multi_agent(temp_pdf_path)

            # 3. Explainer 텍스트 추출
            script = agent_result.get("explainer", "")
            if not script:
                logger.warning("⚠️ No explainer text generated")
                return {
                    "summary": agent_result.get("summary", ""),
                    "explainer": "",
                    "tts_id": None,
                    "audio_filename": None,
                    "s3_url": None,
                    "presigned_url": None,
                }

            # 4. 텍스트 정제
            script_clean = clean_text(script)

            # 5. TTS 파일명 생성
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_filename = f"industry_explainer_{ts}.mp3"

            # 6. 임시 파일로 TTS 생성
            temp_audio_path = tempfile.NamedTemporaryFile(
                delete=False, suffix=".mp3"
            ).name
            tts = gTTS(text=script_clean, lang="ko")
            tts.save(temp_audio_path)
            logger.info(f"🎧 TTS 생성 완료: {audio_filename}")

            # 7. S3에 TTS 파일 업로드
            s3_url = self._upload_audio_to_s3(temp_audio_path, audio_filename)

            # 8. Presigned URL 생성 (다운로드용)
            # Extract object_key from s3_url for presigned URL generation
            audio_object_key = s3_url.replace(f"s3://{settings.S3_BUCKET}/", "")
            presigned_url = self._get_audio_url_from_s3(audio_object_key)

            # 9. 로컬 임시 파일에도 저장 (선택사항)
            local_file_path = self.output_dir / audio_filename
            os.rename(temp_audio_path, str(local_file_path))
            temp_audio_path = None  # 이동했으므로 삭제 방지

            return {
                "summary": agent_result.get("summary", ""),
                "explainer": script,
                "tts_id": ts,
                "audio_filename": audio_filename,
                "s3_url": s3_url,
                "presigned_url": presigned_url,
                "local_path": str(local_file_path),
            }

        except Exception as e:
            logger.error(f"❌ S3 PDF → TTS 처리 실패: {e}")
            raise e
        finally:
            # 임시 파일 정리
            if temp_pdf_path and os.path.exists(temp_pdf_path):
                os.unlink(temp_pdf_path)
                logger.info(f"🗑️ 임시 PDF 파일 삭제: {temp_pdf_path}")
            if temp_audio_path and os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)
                logger.info(f"🗑️ 임시 TTS 파일 삭제: {temp_audio_path}")

    # =====================================================
    # 3️⃣ 파일 기반 헬퍼 함수들
    # =====================================================
    def get_audio_file_by_filename(self, filename: str) -> str | None:
        """생성된 오디오 파일 경로 반환"""
        file_path = self.output_dir / filename
        return str(file_path) if file_path.exists() else None

    def get_first_legacy_pdf(self) -> str | None:
        """legacy/downloaded_papers 폴더의 첫 번째 PDF 반환"""
        pdf_files = list(self.legacy_papers_dir.glob("*.pdf"))
        return str(pdf_files[0]) if pdf_files else None

    # =====================================================
    # 4️⃣ TTS 파일 스트리밍
    # =====================================================
    def stream_audio_from_s3(self, object_key: str) -> tuple[bytes, str, dict]:
        """
        Stream audio file from S3 bucket using object_key
        Returns: (content_bytes, content_type, headers)
        """
        if not settings.S3_BUCKET:
            raise ValueError("S3_BUCKET environment variable is not configured.")
        if not self.s3_client:
            raise ValueError("AWS credentials are not configured.")

        logger.info(
            f"🎧 Streaming audio from S3: s3://{settings.S3_BUCKET}/{object_key}"
        )

        try:
            # Get object from S3
            s3_obj = self.s3_client.get_object(
                Bucket=settings.S3_BUCKET, Key=object_key
            )
            content = s3_obj["Body"].read()

            # Determine content type
            import mimetypes

            # Extract filename from object_key for content type detection
            filename = object_key.split("/")[-1] if "/" in object_key else object_key
            content_type = (
                s3_obj.get("ContentType")
                or mimetypes.guess_type(filename)[0]
                or "application/octet-stream"
            )

            # Set headers
            headers = {"Content-Disposition": f'inline; filename="{filename}"'}

            logger.info(f"✅ Audio streamed successfully from S3: {object_key}")
            return content, content_type, headers

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "NoSuchKey":
                raise FileNotFoundError(
                    f"음성 파일 '{object_key}'이 S3에 존재하지 않습니다."
                )
            else:
                raise ValueError(f"S3 오류: {str(e)}")

    def stream_audio_by_research_id(self, research_id: int) -> tuple[bytes, str, dict]:
        """
        Stream audio file by research_id using database lookup
        Returns: (content_bytes, content_type, headers)
        """
        # Validate database session and repositories
        if not self.db or not self.tts_repository:
            raise ValueError(
                "Database session is required for research_id operations. "
                "Initialize TTSService with db parameter."
            )

        # 1. Retrieve TTS record from database
        logger.info(f"🔍 Looking up TTS for research ID: {research_id}")
        tts_record = self.tts_repository.get_by_research_id(research_id)

        if not tts_record:
            raise FileNotFoundError(
                f"TTS audio not found for research ID {research_id}. "
                "Please generate TTS first using POST /tts/ endpoint."
            )

        # 2. Validate object_key exists
        if not tts_record.object_key:
            raise ValueError(
                f"TTS record for research ID {research_id} is missing object_key. "
                "Cannot stream audio file."
            )

        # 3. Stream audio using object_key
        logger.info(f"🎧 Streaming TTS audio for research ID: {research_id}")
        return self.stream_audio_from_s3(tts_record.object_key)

    # =====================================================
    # 5️⃣ Research ID 기반 TTS 생성
    # =====================================================
    async def create_tts_from_research_id(self, research_id: int) -> Dict[str, Any]:
        """Create TTS from research ID with caching logic"""
        try:
            # Validate database session and repositories
            if not self.db or not self.research_repository or not self.tts_repository:
                raise ValueError(
                    "Database session is required for research_id operations. "
                    "Initialize TTSService with db parameter."
                )

            # 1. Check cache first - look for existing TTS by research_id
            logger.info(f"🔍 Checking TTS cache for research ID: {research_id}")
            existing_tts = self.tts_repository.get_by_research_id(research_id)

            if existing_tts:
                logger.info(f"✅ Found cached TTS for research ID: {research_id}")
                # Extract filename from object_key for presigned URL generation
                object_key = existing_tts.object_key
                filename = (
                    object_key.split("/")[-1] if "/" in object_key else object_key
                )

                # Generate presigned URL for the cached audio file
                presigned_url = self._get_audio_url_from_s3(object_key)

                return {
                    "id": existing_tts.id,
                    "research_id": existing_tts.research_id,
                    "summary": existing_tts.summary,
                    "explainer": existing_tts.explainer,
                    "audio_filename": filename,
                    "s3_url": f"s3://{settings.S3_BUCKET}/{object_key}",
                    "presigned_url": presigned_url,
                }

            # 2. No cache found - fetch research from database
            logger.info(f"🔍 No cache found. Fetching research with ID: {research_id}")
            research = self.research_repository.get_by_id(research_id)

            if not research:
                raise ValueError(f"Research with ID {research_id} not found")

            # 3. Validate research has object_key (S3 filename)
            if not research.object_key:
                raise ValueError(
                    f"Research with ID {research_id} does not have an associated PDF file (missing object_key)"
                )

            # 4. Extract filename from object_key
            # object_key format: "output/research/filename.pdf"
            research_object_key = research.object_key
            filename = (
                research_object_key.split("/")[-1]
                if "/" in research_object_key
                else research_object_key
            )

            logger.info(f"📄 Using filename from research object_key: {filename}")

            # 5. Generate TTS using existing S3 method
            logger.info(f"🎧 Generating new TTS for research ID: {research_id}")
            tts_result = await self.process_pdf_from_s3_to_tts(filename)

            # 6. Save TTS to database
            if tts_result.get("audio_filename") and tts_result.get("s3_url"):
                # Extract object_key from s3_url
                s3_url = tts_result["s3_url"]
                audio_object_key = s3_url.replace(f"s3://{settings.S3_BUCKET}/", "")

                tts_data = {
                    "research_id": research_id,
                    "summary": tts_result.get("summary", ""),
                    "explainer": tts_result.get("explainer", ""),
                    "object_key": audio_object_key,
                }

                saved_tts = self.tts_repository.create(tts_data)
                logger.info(f"✅ TTS saved to database with ID: {saved_tts.id}")

                # Add tts_id to result
                tts_result["tts_id"] = saved_tts.id

            return tts_result

        except ValueError as e:
            logger.error(f"❌ Research validation failed: {e}")
            raise e
        except Exception as e:
            logger.error(f"❌ TTS generation from research ID failed: {e}")
            raise ValueError(f"TTS 생성 중 오류가 발생했습니다: {str(e)}")
