import os
import tempfile
import requests
from datetime import datetime
from typing import List, Dict, Any

# =====================================================================
# 1. 환경변수 로드 (.env 사용)
# =====================================================================
from dotenv import load_dotenv
load_dotenv()  # .env 파일 읽기

# =====================================================================
# 2. 필요한 라이브러리 임포트
# =====================================================================
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI

# =====================================================================
# 3. PDFQuizSystem 클래스
# =====================================================================
class PDFQuizSystem:
    def __init__(self):
        self.vectorstore = None
        self.summary = ""
        self.quiz = ""
        self.llm_mini = self.get_llm(temperature=0.2, use_mini=True)
        self.llm_full = self.get_llm(temperature=0.2, use_mini=False)
        self.embeddings = self.get_embeddings()

    # ------------------------
    # LLM & 임베딩
    # ------------------------
    def get_llm(self, temperature: float = 0.2, use_mini: bool = True):
        return AzureChatOpenAI(
            openai_api_version="2024-02-01",
            azure_deployment=os.getenv("AOAI_DEPLOY_GPT4O_MINI") if use_mini else os.getenv("AOAI_DEPLOY_GPT4O"),
            temperature=temperature,
            api_key=os.getenv("AOAI_API_KEY"),
            azure_endpoint=os.getenv("AOAI_ENDPOINT"),
        )

    def get_embeddings(self):
        return AzureOpenAIEmbeddings(
            model=os.getenv("AOAI_DEPLOY_EMBED_3_LARGE"),
            openai_api_version="2024-02-01",
            api_key=os.getenv("AOAI_API_KEY"),
            azure_endpoint=os.getenv("AOAI_ENDPOINT"),
        )

    # ------------------------
    # PDF 로드
    # ------------------------
    def load_pdf(self, path_or_url: str):
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
            loader = PyMuPDFLoader(path_or_url)
            docs = loader.load()
        print(f"✅ PDF 로드 완료: {len(docs)}개 문서")
        return docs

    # ------------------------
    # 벡터스토어 구축
    # ------------------------
    def build_vectorstore(self, docs, chunk_size=1000, chunk_overlap=200):
        splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        splits = splitter.split_documents(docs)

        for d in splits:
            page = d.metadata.get("page", None)
            src = d.metadata.get("source", "")
            prefix = f"[source: {os.path.basename(src)} | page: {page}] "
            d.page_content = prefix + d.page_content

        vs = FAISS.from_documents(splits, self.embeddings)
        print(f"✅ 벡터스토어 구축 완료: {len(splits)}개 청크")
        return vs

    # ------------------------
    # 1차 에이전트: 요약
    # ------------------------
    def generate_summary(self, vectorstore):
        chunks = vectorstore.similarity_search("summary overview of this document", k=12)
        document_content = "\n\n".join([c.page_content for c in chunks])

        summary_prompt = """
당신은 논문을 한국어로 요약하는 전문가입니다.
아래 문서 내용을 바탕으로 구조화된 한국어 요약을 작성하세요.

요구 형식:
# 한 줄 요약(TL;DR)
# 배경/문제정의
# 핵심 기술 및 방법론
# 주요 결과 및 성능
# 기술적 시사점/한계
# 핵심 키워드

[문서 내용]
{document_content}

[한국어 요약]
"""
        prompt_template = PromptTemplate.from_template(summary_prompt)
        summary_chain = prompt_template | self.llm_mini | StrOutputParser()
        summary = summary_chain.invoke({"document_content": document_content})
        print("✅ 한국어 요약 완료")
        return summary

    # ------------------------
    # 2차 에이전트: 퀴즈
    # ------------------------
    def generate_quiz(self, vectorstore):
        chunks = vectorstore.similarity_search("Generate exam questions based on this document", k=10)
        document_content = "\n\n".join([c.page_content for c in chunks])

        quiz_prompt = """
당신은 논문 기반의 퀴즈 메이커입니다. 아래 문서 내용을 근거로 한국어 퀴즈를 만드세요.

요구 사항:
- 총 5문항
- 객관식, 주관식, 서술형을 섞어서
- 각 문항에 대해 정답과 해설 제공
- 마지막에 '생각해볼 의견(3개)'과 '실무 적용 방향(3개)' 제시

[문서 내용]
{document_content}

[퀴즈 형식]
Q1. ...
정답: ...
해설: ...
"""
        prompt_template = PromptTemplate.from_template(quiz_prompt)
        quiz_chain = prompt_template | self.llm_mini | StrOutputParser()
        quiz = quiz_chain.invoke({"document_content": document_content})
        print("✅ 퀴즈 생성 완료")
        return quiz

    # ------------------------
    # 전체 실행
    # ------------------------
    def process_pdf(self, pdf_path_or_url: str):
        print(f"\n🎯 PDF 처리 시작: {pdf_path_or_url}")
        print("=" * 60)

        docs = self.load_pdf(pdf_path_or_url)
        self.vectorstore = self.build_vectorstore(docs)

        print("\n📖 1차 에이전트: 한국어 요약")
        print("-" * 50)
        self.summary = self.generate_summary(self.vectorstore)
        print(self.summary)

        print("\n🎓 2차 에이전트: 퀴즈 생성")
        print("-" * 50)
        self.quiz = self.generate_quiz(self.vectorstore)
        print(self.quiz)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f"summary_{timestamp}.txt", "w", encoding="utf-8") as f:
            f.write(self.summary)
        with open(f"quiz_{timestamp}.txt", "w", encoding="utf-8") as f:
            f.write(self.quiz)

        print("\n🎉 모든 작업 완료!")
        print(f"📁 결과 저장: summary_{timestamp}.txt, quiz_{timestamp}.txt")
        return True

# =====================================================================
# 실행
# =====================================================================
if __name__ == "__main__":
    PDF_INPUT = "C:/Users/Administrator/Desktop/연습/2505.18397v3.pdf"   # 파일 경로
    system = PDFQuizSystem()
    system.process_pdf(PDF_INPUT)
