import os
import re
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

from gtts import gTTS   # Google Text-to-Speech

# =====================================================================
# 3. 특수기호 제거 함수
# =====================================================================
def clean_text(text: str) -> str:
    """
    TTS를 위해 텍스트에서 불필요한 특수기호를 제거하고
    자연스러운 문장만 남깁니다.
    """
    # 1. 마크다운/목록 기호 제거 (#, *, -, > 등)
    cleaned = re.sub(r"[#*>•\-]+", " ", text)

    # 2. 연속된 공백을 하나로 줄임
    cleaned = re.sub(r"\s+", " ", cleaned)

    # 3. 앞뒤 공백 제거
    cleaned = cleaned.strip()

    return cleaned


# =====================================================================
# 4. PDFQuizSystem 클래스
# =====================================================================
class PDFQuizSystem:
    def __init__(self):
        self.vectorstore = None
        self.summary = ""
        self.quiz = ""
        self.explainer = ""
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
아래 문서를 읽고 다음과 같은 항목을 포함한 구조화된 요약문을 작성하세요.

첫째, 한 줄 요약
둘째, 연구 배경과 문제 정의
셋째, 핵심 기술과 방법론
넷째, 주요 결과와 성능
다섯째, 기술적 시사점과 한계
여섯째, 핵심 키워드

문서 내용은 다음과 같습니다.
{document_content}

이제 한국어 요약을 작성해 주세요.
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
당신은 논문 기반 퀴즈 제작자입니다. 아래 문서를 참고하여 한국어 퀴즈를 만들어 주세요.

조건은 다음과 같습니다.
총 다섯 문항을 만들고, 객관식, 주관식, 서술형을 섞어서 구성합니다.
각 문항에 대해 정답과 해설을 함께 작성합니다.
제공할 문제의 경우에는, 논문의 저자 및 작성 시기 등과 같이 지엽적인 부분은 피하세요.
기술과 AI 및 논문의 핵심 내용을 기반으로 문제를 생성합니다. 
마지막에는 생각해볼 의견 세 가지와 실무 적용 방향 세 가지를 제시합니다.

문서 내용은 다음과 같습니다.
{document_content}

퀴즈를 작성해 주세요.
"""
        prompt_template = PromptTemplate.from_template(quiz_prompt)
        quiz_chain = prompt_template | self.llm_mini | StrOutputParser()
        quiz = quiz_chain.invoke({"document_content": document_content})
        print("✅ 퀴즈 생성 완료")
        return quiz

    # ------------------------
    # 3차 에이전트: 산업 적용 해설
    # ------------------------
    def generate_industry_explainer(self, vectorstore):
        chunks = vectorstore.similarity_search("detailed explanation with industry applications", k=15)
        document_content = "\n\n".join([c.page_content for c in chunks])

        explainer_prompt = """
당신은 전문 해설가입니다. 아래 논문을 바탕으로 해설 스크립트를 작성하세요.

스크립트는 세 부분으로 구성되어야 합니다.
첫째, 논문의 상세 설명
둘째, 일반인이 이해할 수 있도록 쉽게 풀어쓴 해설
셋째, 산업 현장에서 적용할 수 있는 두세 가지 시나리오 제시

문서 내용은 다음과 같습니다.
{document_content}

이제 한국어 해설 스크립트를 작성해 주세요.
"""
        prompt_template = PromptTemplate.from_template(explainer_prompt)
        explainer_chain = prompt_template | self.llm_full | StrOutputParser()
        script = explainer_chain.invoke({"document_content": document_content})
        print("✅ 산업 적용 해설 스크립트 생성 완료")
        return script

    # ------------------------
    # TTS (팟캐스트 생성)
    # ------------------------
    def export_podcast(self, script: str, filename="podcast.mp3"):
        if not script:
            print("❌ 변환할 스크립트가 없습니다.")
            return False

        # 👇 특수기호 제거 적용
        script_clean = clean_text(script)

        tts = gTTS(text=script_clean, lang="ko")
        tts.save(filename)
        print(f"🎧 팟캐스트 오디오 파일 생성 완료: {filename}")
        return True

    # ------------------------
    # 전체 실행
    # ------------------------
    def process_pdf(self, pdf_path_or_url: str):
        print(f"\n🎯 PDF 처리 시작: {pdf_path_or_url}")
        print("=" * 60)

        docs = self.load_pdf(pdf_path_or_url)
        self.vectorstore = self.build_vectorstore(docs)

        # 요약
        print("\n📖 1차 에이전트: 한국어 요약")
        print("-" * 50)
        self.summary = self.generate_summary(self.vectorstore)
        print(self.summary)

        # 퀴즈
        print("\n🎓 2차 에이전트: 퀴즈 생성")
        print("-" * 50)
        self.quiz = self.generate_quiz(self.vectorstore)
        print(self.quiz)

        # 산업 해설
        print("\n💡 3차 에이전트: 산업 적용 해설 생성")
        print("-" * 50)
        self.explainer = self.generate_industry_explainer(self.vectorstore)
        print(self.explainer)

        # 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f"summary_{timestamp}.txt", "w", encoding="utf-8") as f:
            f.write(self.summary)
        with open(f"quiz_{timestamp}.txt", "w", encoding="utf-8") as f:
            f.write(self.quiz)
        with open(f"explainer_{timestamp}.txt", "w", encoding="utf-8") as f:
            f.write(self.explainer)

        # 팟캐스트 파일로 변환
        self.export_podcast(self.explainer, f"industry_explainer_{timestamp}.mp3")

        print("\n🎉 모든 작업 완료!")
        print(f"📁 결과 저장: summary_{timestamp}.txt, quiz_{timestamp}.txt, explainer_{timestamp}.txt, industry_explainer_{timestamp}.mp3")
        return True


# =====================================================================
# 실행
# =====================================================================
if __name__ == "__main__":
    PDF_INPUT = "C:/Users/Administrator/Desktop/연습/2505.18397v3.pdf"
    system = PDFQuizSystem()
    system.process_pdf(PDF_INPUT)
