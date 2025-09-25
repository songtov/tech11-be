#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Boot Camp Lab - Main Agent Controller
논문 검색 → PDF 다운로드 → 퀴즈 생성 및 TTS 팟캐스트 제작을 자동화
"""

import os
import sys
import subprocess
import time
import re
import tempfile
import requests
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, TypedDict

from dotenv import load_dotenv
load_dotenv()

# 기존 에이전트들 임포트
from axpress_scholar_agent_ver1 import AXPressScholarAgent, Paper

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


def make_figure_analysis_chain():
    prompt = PromptTemplate.from_template(
        """당신은 논문의 그림, 차트, 그래프를 분석하는 전문가입니다.
아래 문서를 읽고 다음 항목을 포함해 상세한 그림 분석을 작성하세요.

1) 주요 그림/차트/그래프 식별
2) 각 그림의 핵심 메시지와 의미
3) 데이터 해석 및 인사이트
4) 그림 간의 연관성과 흐름
5) 실무 적용 시 시각화 방향

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
    query_figure_analysis: str
    k: int  # RAG 검색 개수

    # 산출물
    summary: str
    quiz: str
    explainer: str
    figure_analysis: str

    # 내부 신호
    judge_summary_ok: bool
    judge_quiz_ok: bool
    judge_explainer_ok: bool
    judge_figure_analysis_ok: bool


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
        state.get(
            "query_explainer", "detailed explanation with industry applications"
        ),
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


def node_figure_analysis(state: AgentState) -> AgentState:
    vs = state["vectorstore"]
    k = state.get("k", 12)
    chunks = vs.similarity_search(
        state.get("query_figure_analysis", "figure analysis and visualization interpretation"), k=k
    )
    content = "\n\n".join([c.page_content for c in chunks])
    figure_analysis_chain = make_figure_analysis_chain()
    figure_analysis = figure_analysis_chain.invoke({"document_content": content})
    return {"figure_analysis": figure_analysis}


def node_judge_figure_analysis(state: AgentState) -> AgentState:
    judge = make_judge_chain()
    verdict = judge.invoke({"generated": state.get("figure_analysis", "")}).strip().upper()
    return {"judge_figure_analysis_ok": verdict.startswith("YES")}


def cond_on_figure_analysis(state: AgentState) -> str:
    if state.get("judge_figure_analysis_ok", True):
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
    graph.add_node("figure_analysis", node_figure_analysis)
    graph.add_node("judge_figure_analysis", node_judge_figure_analysis)
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

    # explainer → judge → (retry: explainer, ok: figure_analysis)
    graph.add_edge("explainer", "judge_explainer")
    graph.add_conditional_edges(
        "judge_explainer",
        cond_on_explainer,
        {
            "retry": "explainer",
            "ok": "figure_analysis",
        },
    )

    # figure_analysis → judge → (retry: figure_analysis, ok: tts)
    graph.add_edge("figure_analysis", "judge_figure_analysis")
    graph.add_conditional_edges(
        "judge_figure_analysis",
        cond_on_figure_analysis,
        {
            "retry": "figure_analysis",
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
        "query_figure_analysis": "figure analysis and visualization interpretation",
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

    if final_state.get("figure_analysis"):
        with open(f"figure_analysis_{ts}.txt", "w", encoding="utf-8") as f:
            f.write(final_state["figure_analysis"])
        print(f"📊 그림 분석 저장: figure_analysis_{ts}.txt")

    print("🎉 모든 작업 완료!")
    return final_state


class MainAgentController:
    """논문 검색부터 퀴즈 생성까지 통합 관리하는 메인 컨트롤러"""
    
    def __init__(self):
        self.scholar_agent = AXPressScholarAgent()
        self.downloaded_papers_dir = Path("downloaded_papers")
        
    def find_downloaded_papers(self) -> List[str]:
        """downloaded_papers 폴더에서 PDF 파일들을 찾습니다."""
        if not self.downloaded_papers_dir.exists():
            return []
        
        pdf_files = list(self.downloaded_papers_dir.glob("*.pdf"))
        return [str(f) for f in pdf_files]
    
    def get_latest_pdf(self) -> Optional[str]:
        """가장 최근에 다운로드된 PDF 파일을 반환합니다."""
        pdf_files = self.find_downloaded_papers()
        if not pdf_files:
            return None
        
        # 파일 수정 시간 기준으로 정렬하여 가장 최근 파일 반환
        latest_file = max(pdf_files, key=lambda f: os.path.getmtime(f))
        return latest_file
    
    def run_scholar_agent(self) -> bool:
        """AXPress Scholar Agent를 실행하여 논문을 다운로드합니다."""
        print("\n🔬 1단계: AXPress Scholar Agent 실행")
        print("=" * 60)
        
        try:
            # 지원 도메인 표시
            domains = ["제조", "금융", "CLOUD", "통신", "유통/물류", "Gen AI"]
            print("\n📋 지원 도메인:")
            for i, domain in enumerate(domains, 1):
                print(f"   {i}. {domain}")
            
            # 도메인 선택
            while True:
                try:
                    choice = input(f"\n도메인을 선택하세요 (1-{len(domains)}): ").strip()
                    domain_index = int(choice) - 1
                    
                    if 0 <= domain_index < len(domains):
                        selected_domain = domains[domain_index]
                        break
                    else:
                        print("❌ 잘못된 번호입니다. 다시 입력해주세요.")
                except ValueError:
                    print("❌ 숫자를 입력해주세요.")
            
            print(f"\n🔍 '{selected_domain}' 도메인에서 논문을 검색합니다...")
            
            # 논문 검색
            papers = self.scholar_agent.fetch_papers(selected_domain)
            
            if not papers:
                print("❌ 검색된 논문이 없습니다.")
                return False
            
            # 결과 표시
            self.scholar_agent.display_papers(papers)
            
            # PDF 다운로드 선택
            print(f"\n📄 총 {len(papers)}편의 논문 중에서 PDF를 다운로드할 논문을 선택하세요.")
            print("번호를 입력하세요 (0: 종료): ", end="")
            
            try:
                choice = int(input().strip())
                if choice == 0:
                    print("프로그램을 종료합니다.")
                    return False
                elif 1 <= choice <= len(papers):
                    selected_paper = papers[choice - 1]
                    print(f"\n선택된 논문: {selected_paper.title}")
                    
                    filepath = self.scholar_agent.download_pdf(selected_paper)
                    
                    if filepath:
                        print(f"\n✅ PDF 다운로드가 완료되었습니다!")
                        print(f"저장 위치: {filepath}")
                        return True
                    else:
                        print("\n❌ PDF 다운로드에 실패했습니다.")
                        return False
                else:
                    print("❌ 잘못된 번호입니다.")
                    return False
            except ValueError:
                print("❌ 숫자를 입력해주세요.")
                return False
                
        except KeyboardInterrupt:
            print("\n프로그램을 종료합니다.")
            return False
        except Exception as e:
            print(f"❌ 오류가 발생했습니다: {e}")
            return False
    
    def run_quiz_agent(self, pdf_path: str) -> bool:
        """Multi Agent 시스템을 실행하여 PDF를 분석하고 퀴즈를 생성합니다."""
        print(f"\n🎓 2단계: Multi Agent 시스템 실행")
        print("=" * 60)
        print(f"📄 분석할 PDF: {os.path.basename(pdf_path)}")
        
        try:
            # Multi Agent 시스템으로 PDF 처리
            final_state = run_multi_agent(pdf_path)
            
            if final_state:
                print("\n✅ Multi Agent 시스템 실행 완료!")
                return True
            else:
                print("\n❌ Multi Agent 시스템 실행 실패!")
                return False
                
        except Exception as e:
            print(f"❌ Multi Agent 시스템 실행 중 오류: {e}")
            return False
    
    def run_automatic_workflow(self) -> bool:
        """논문 검색부터 퀴즈 생성까지 자동으로 실행합니다."""
        print("\n🚀 자동 워크플로우 시작")
        print("=" * 60)
        
        # 1단계: 논문 검색 및 다운로드
        if not self.run_scholar_agent():
            return False
        
        # 잠시 대기
        print("\n⏳ 잠시 대기 중...")
        time.sleep(2)
        
        # 2단계: 가장 최근 다운로드된 PDF로 퀴즈 생성
        latest_pdf = self.get_latest_pdf()
        if not latest_pdf:
            print("❌ 다운로드된 PDF 파일을 찾을 수 없습니다.")
            return False
        
        print(f"\n📄 최근 다운로드된 PDF를 자동 선택: {os.path.basename(latest_pdf)}")
        
        if not self.run_quiz_agent(latest_pdf):
            return False
        
        print("\n🎉 전체 워크플로우 완료!")
        return True
    
    def run_manual_workflow(self) -> bool:
        """수동으로 각 단계를 선택하여 실행합니다."""
        while True:
            print("\n" + "="*80)
            print("🤖 AI Boot Camp Lab - Main Agent Controller")
            print("="*80)
            print("\n사용 가능한 작업:")
            print("1. 논문 검색 및 PDF 다운로드 (AXPress Scholar Agent)")
            print("2. PDF 분석 및 퀴즈 생성 (Multi Agent 시스템)")
            print("3. 자동 워크플로우 (1번 + 2번 연속 실행)")
            print("4. 종료")
            print("="*80)
            
            try:
                choice = input("\n작업을 선택하세요 (1-4): ").strip()
                
                if choice == "1":
                    self.run_scholar_agent()
                elif choice == "2":
                    # 다운로드된 PDF 파일 목록 표시
                    pdf_files = self.find_downloaded_papers()
                    if not pdf_files:
                        print("❌ downloaded_papers 폴더에 PDF 파일이 없습니다.")
                        print("   먼저 1번 작업으로 논문을 다운로드해주세요.")
                        continue
                    
                    print(f"\n📁 다운로드된 PDF 파일 ({len(pdf_files)}개):")
                    for i, pdf_file in enumerate(pdf_files, 1):
                        filename = os.path.basename(pdf_file)
                        print(f"   {i}. {filename}")
                    
                    if len(pdf_files) == 1:
                        selected_pdf = pdf_files[0]
                        print(f"\n📄 자동 선택: {os.path.basename(selected_pdf)}")
                    else:
                        while True:
                            try:
                                pdf_choice = input(f"\n분석할 PDF 파일을 선택하세요 (1-{len(pdf_files)}): ").strip()
                                pdf_choice_idx = int(pdf_choice) - 1
                                
                                if 0 <= pdf_choice_idx < len(pdf_files):
                                    selected_pdf = pdf_files[pdf_choice_idx]
                                    break
                                else:
                                    print("❌ 잘못된 번호입니다. 다시 입력해주세요.")
                            except ValueError:
                                print("❌ 숫자를 입력해주세요.")
                    
                    self.run_quiz_agent(selected_pdf)
                    
                elif choice == "3":
                    self.run_automatic_workflow()
                elif choice == "4":
                    print("\n👋 프로그램을 종료합니다.")
                    break
                else:
                    print("❌ 잘못된 선택입니다. 1-4 중에서 선택해주세요.")
                    
            except KeyboardInterrupt:
                print("\n\n👋 프로그램을 종료합니다.")
                break
            except Exception as e:
                print(f"\n❌ 오류가 발생했습니다: {e}")
                input("계속하려면 Enter를 누르세요...")

def main():
    """메인 함수"""
    print("🤖 AI Boot Camp Lab - Main Agent Controller")
    print("논문 검색 → PDF 다운로드 → 퀴즈 생성 및 TTS 팟캐스트 제작")
    print("=" * 80)
    
    try:
        controller = MainAgentController()
        
        # 실행 모드 선택
        print("\n실행 모드를 선택하세요:")
        print("1. 자동 워크플로우 (논문 검색 → PDF 다운로드 → 퀴즈 생성)")
        print("2. 수동 모드 (각 단계별 선택)")
        
        while True:
            try:
                mode_choice = input("\n모드를 선택하세요 (1-2): ").strip()
                
                if mode_choice == "1":
                    controller.run_automatic_workflow()
                    break
                elif mode_choice == "2":
                    controller.run_manual_workflow()
                    break
                else:
                    print("❌ 1 또는 2를 입력해주세요.")
                    
            except KeyboardInterrupt:
                print("\n\n👋 프로그램을 종료합니다.")
                break
            except Exception as e:
                print(f"\n❌ 오류가 발생했습니다: {e}")
                
    except KeyboardInterrupt:
        print("\n\n👋 프로그램을 종료합니다.")
    except Exception as e:
        print(f"\n❌ 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    main()
