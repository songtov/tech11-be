import os
import re
import tempfile
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional, TypedDict

from dotenv import load_dotenv

load_dotenv()

# ========== LangChain / LangGraph ==========
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI

# LangGraph
from langgraph.graph import StateGraph, END

# TTS
from gtts import gTTS


# ==========================
# 유틸: 텍스트 정리(TTS용)
# ==========================
def clean_text(text: str) -> str:
    cleaned = re.sub(r"[#*>•\-]+", " ", text)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


# ==========================
# LLM / Embeddings 팩토리
# ==========================
def build_llm(use_mini: bool = True, temperature: float = 0.2):
    return AzureChatOpenAI(
        openai_api_version="2024-02-01",
        azure_deployment=(
            os.getenv("AOAI_DEPLOY_GPT4O_MINI")
            if use_mini
            else os.getenv("AOAI_DEPLOY_GPT4O")
        ),
        api_key=os.getenv("AOAI_API_KEY"),
        azure_endpoint=os.getenv("AOAI_ENDPOINT"),
        temperature=temperature,
    )


def build_embeddings():
    return AzureOpenAIEmbeddings(
        model=os.getenv("AOAI_DEPLOY_EMBED_3_LARGE"),
        openai_api_version="2024-02-01",
        api_key=os.getenv("AOAI_API_KEY"),
        azure_endpoint=os.getenv("AOAI_ENDPOINT"),
    )


# ==========================
# PDF 로드 & 벡터스토어 구축
# ==========================
def load_pdf(path_or_url: str) -> List[Document]:
    if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
        resp = requests.get(path_or_url, timeout=30)
        resp.raise_for_status()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(resp.content)
            tmp_path = tmp.name
        # 파일 핸들 닫힌 뒤 로더가 열도록
        loader = PyMuPDFLoader(tmp_path)
        docs = loader.load()
        os.unlink(tmp_path)
    else:
        loader = PyMuPDFLoader(path_or_url)
        docs = loader.load()
    return docs


def build_vectorstore(
    docs: List[Document],
    embeddings,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    splits = splitter.split_documents(docs)
    for d in splits:
        page = d.metadata.get("page", None)
        src = d.metadata.get("source", "")
        prefix = f"[source: {os.path.basename(src)} | page: {page}] "
        d.page_content = prefix + d.page_content
    vs = FAISS.from_documents(splits, embeddings)
    return vs


# ==========================
# 체인: 요약 / 퀴즈 / 해설 / 판정
# ==========================
def make_summary_chain():
    prompt = PromptTemplate.from_template(
        """당신은 논문을 한국어로 요약하는 전문가입니다.
아래 문서를 읽고 다음 항목을 포함해 간결하고 구조화된 요약을 작성하세요.

1) 한 줄 요약
2) 연구 배경과 문제 정의
3) 핵심 기술과 방법론
4) 주요 결과와 성능
5) 기술적 시사점과 한계
6) 핵심 키워드

문서 내용:
{document_content}
"""
    )
    return prompt | build_llm(use_mini=True) | StrOutputParser()


def make_quiz_chain():
    prompt = PromptTemplate.from_template(
        """당신은 논문 기반 퀴즈 제작자입니다. 다음 조건을 만족하는 한국어 퀴즈를 작성하세요.

- 총 5문항: 객관식/주관식/서술형 혼합
- 각 문항마다 정답과 해설 포함
- 저자/연도 같은 지엽적 사실은 피하고, 핵심 개념 중심
- 마지막에 '생각해볼 의견 3가지'와 '실무 적용 방향 3가지' 추가

문서 내용:
{document_content}
"""
    )
    return prompt | build_llm(use_mini=True) | StrOutputParser()


def make_explainer_chain():
    prompt = PromptTemplate.from_template(
        """당신은 전문 해설가입니다. 아래 문서를 바탕으로 한국어 해설 스크립트를 작성하세요.

구성:
1) 논문의 상세 설명
2) 일반인도 이해할 수 있는 쉬운 설명
3) 산업 현장에서의 적용 시나리오 2~3가지

문서 내용:
{document_content}
"""
    )
    return prompt | build_llm(use_mini=False) | StrOutputParser()


def make_judge_chain():
    prompt = PromptTemplate.from_template(
        """다음 생성물의 품질을 평가하세요.
기준: (A) 문서 핵심 주제를 빠짐없이 다루었는가, (B) 논리적 일관성, (C) 과도한 환각(문서에 없는 주장) 여부.

결과는 반드시 아래 중 하나만 출력:
- YES: 충분히 양호
- NO: 불충분 (재검색/재생성 필요)

평가할 텍스트:
{generated}
"""
    )
    # 판단은 보수적으로 → gpt-4o로 판단
    return prompt | build_llm(use_mini=False, temperature=0.0) | StrOutputParser()


# ==========================
# 상태 정의 (LangGraph State)
# ==========================
class AgentState(TypedDict, total=False):
    # 입력/공유
    vectorstore: Any
    query_summary: str
    query_quiz: str
    query_explainer: str
    k: int  # RAG 검색 개수

    # 산출물
    summary: str
    quiz: str
    explainer: str

    # 내부 신호
    judge_summary_ok: bool
    judge_quiz_ok: bool
    judge_explainer_ok: bool


# ==========================
# 그래프 노드 함수들
# ==========================
def node_summarizer(state: AgentState) -> AgentState:
    vs = state["vectorstore"]
    k = state.get("k", 12)
    chunks = vs.similarity_search(
        state.get("query_summary", "summary overview of this document"), k=k
    )
    content = "\n\n".join([c.page_content for c in chunks])
    summary_chain = make_summary_chain()
    summary = summary_chain.invoke({"document_content": content})
    return {"summary": summary}


def node_quiz(state: AgentState) -> AgentState:
    vs = state["vectorstore"]
    k = state.get("k", 10)
    chunks = vs.similarity_search(
        state.get("query_quiz", "Generate exam questions based on this document"), k=k
    )
    content = "\n\n".join([c.page_content for c in chunks])
    quiz_chain = make_quiz_chain()
    quiz = quiz_chain.invoke({"document_content": content})
    return {"quiz": quiz}


def node_explainer(state: AgentState) -> AgentState:
    vs = state["vectorstore"]
    k = state.get("k", 15)
    chunks = vs.similarity_search(
        state.get("query_explainer", "detailed explanation with industry applications"),
        k=k,
    )
    content = "\n\n".join([c.page_content for c in chunks])
    explainer_chain = make_explainer_chain()
    explainer = explainer_chain.invoke({"document_content": content})
    return {"explainer": explainer}


def node_judge_summary(state: AgentState) -> AgentState:
    judge = make_judge_chain()
    verdict = judge.invoke({"generated": state.get("summary", "")}).strip().upper()
    return {"judge_summary_ok": verdict.startswith("YES")}


def node_judge_quiz(state: AgentState) -> AgentState:
    judge = make_judge_chain()
    verdict = judge.invoke({"generated": state.get("quiz", "")}).strip().upper()
    return {"judge_quiz_ok": verdict.startswith("YES")}


def node_judge_explainer(state: AgentState) -> AgentState:
    judge = make_judge_chain()
    verdict = judge.invoke({"generated": state.get("explainer", "")}).strip().upper()
    return {"judge_explainer_ok": verdict.startswith("YES")}


def cond_on_summary(state: AgentState) -> str:
    """
    조건부 엣지 라우팅:
    - 요약 미흡 → k를 증가시키고 summarizer 재시도
    - 충분 → quiz로 진행
    """
    if state.get("judge_summary_ok", True):
        return "ok"
    # 미흡하면 k + 4 (상한선 40)
    new_k = min(40, state.get("k", 12) + 4)
    state["k"] = new_k
    return "retry"


def cond_on_quiz(state: AgentState) -> str:
    if state.get("judge_quiz_ok", True):
        return "ok"
    new_k = min(40, state.get("k", 12) + 4)
    state["k"] = new_k
    return "retry"


def cond_on_explainer(state: AgentState) -> str:
    if state.get("judge_explainer_ok", True):
        return "ok"
    new_k = min(40, state.get("k", 12) + 4)
    state["k"] = new_k
    return "retry"


def node_tts(state: AgentState) -> AgentState:
    script = state.get("explainer", "")
    if not script:
        return {}
    script_clean = clean_text(script)
    tts = gTTS(text=script_clean, lang="ko")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_mp3 = f"industry_explainer_{ts}.mp3"
    tts.save(out_mp3)
    print(f"🎧 TTS 저장 완료: {out_mp3}")
    return {}


# ==========================
# 워크플로우 구성 (LangGraph)
# ==========================
def build_workflow():
    graph = StateGraph(AgentState)

    # 노드 등록
    graph.add_node("summarizer", node_summarizer)
    graph.add_node("judge_summary", node_judge_summary)
    graph.add_node("quiz", node_quiz)
    graph.add_node("judge_quiz", node_judge_quiz)
    graph.add_node("explainer", node_explainer)
    graph.add_node("judge_explainer", node_judge_explainer)
    graph.add_node("tts", node_tts)

    # 진입점
    graph.set_entry_point("summarizer")

    # summarizer → judge → (retry: summarizer, ok: quiz)
    graph.add_edge("summarizer", "judge_summary")
    graph.add_conditional_edges(
        "judge_summary",
        cond_on_summary,
        {
            "retry": "summarizer",
            "ok": "quiz",
        },
    )

    # quiz → judge → (retry: quiz, ok: explainer)
    graph.add_edge("quiz", "judge_quiz")
    graph.add_conditional_edges(
        "judge_quiz",
        cond_on_quiz,
        {
            "retry": "quiz",
            "ok": "explainer",
        },
    )

    # explainer → judge → (retry: explainer, ok: tts)
    graph.add_edge("explainer", "judge_explainer")
    graph.add_conditional_edges(
        "judge_explainer",
        cond_on_explainer,
        {
            "retry": "explainer",
            "ok": "tts",
        },
    )

    # 마지막 tts 후 종료
    graph.add_edge("tts", END)

    return graph.compile()


# ==========================
# 실행 함수
# ==========================
def run_multi_agent(pdf_path_or_url: str):
    print(f"\n🎯 PDF 처리 시작: {pdf_path_or_url}")
    docs = load_pdf(pdf_path_or_url)
    print(f"✅ PDF 로드 완료: {len(docs)}개 문서")

    embeddings = build_embeddings()
    vs = build_vectorstore(docs, embeddings)
    print(f"✅ 벡터스토어 구축 완료")

    workflow = build_workflow()
    init_state: AgentState = {
        "vectorstore": vs,
        "k": 12,
        "query_summary": "summary overview of this document",
        "query_quiz": "Generate exam questions based on this document",
        "query_explainer": "detailed explanation with industry applications",
    }

    # 실행
    final_state = workflow.invoke(init_state)

    # 산출물 저장
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    if final_state.get("summary"):
        with open(f"summary_{ts}.txt", "w", encoding="utf-8") as f:
            f.write(final_state["summary"])
        print(f"📝 요약 저장: summary_{ts}.txt")

    if final_state.get("quiz"):
        with open(f"quiz_{ts}.txt", "w", encoding="utf-8") as f:
            f.write(final_state["quiz"])
        print(f"📝 퀴즈 저장: quiz_{ts}.txt")

    if final_state.get("explainer"):
        with open(f"explainer_{ts}.txt", "w", encoding="utf-8") as f:
            f.write(final_state["explainer"])
        print(f"📝 해설 저장: explainer_{ts}.txt")

    print("🎉 모든 작업 완료!")
    return final_state


# ==========================
# main
# ==========================
if __name__ == "__main__":
    # Windows 경로 주의: 백슬래시는 r"..." 혹은 슬래시 사용
    PDF_INPUT = r"C:/Users/Administrator/Desktop/연습/2505.18397v3.pdf"
    run_multi_agent(PDF_INPUT)
