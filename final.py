#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI Framework - AI Boot Camp Lab Final Version 1
논문 검색 → PDF 다운로드 → 멀티에이전트 기반 퀴즈/요약/해설 생성 및 TTS 팟캐스트 제작을 자동화하는 REST API
multitest.py의 고도화된 멀티에이전트 시스템과 axpress_scholar_agent_ver1.py를 결합
"""

import os
import re
import tempfile
import requests
import json
import sys
import subprocess
import time
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any, TypedDict
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

# FastAPI 및 관련 라이브러리
from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# 환경 변수 로드
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

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==========================
# 데이터 클래스 및 모델들
# ==========================
@dataclass
class Paper:
    """논문 정보를 담는 데이터 클래스"""
    id: str
    title: str
    authors: List[str]
    published_date: str
    updated_date: str
    abstract: str
    categories: List[str]
    pdf_url: str
    arxiv_url: str
    citation_count: int = 0
    relevance_score: float = 0.0

# Pydantic 모델들
class DomainRequest(BaseModel):
    domain: str = Field(..., description="검색할 도메인 (제조, 금융, CLOUD, 통신, 유통/물류, Gen AI)")
    additional_keywords: Optional[str] = Field(None, description="추가 검색 키워드")
    year_range: int = Field(1, ge=1, le=2, description="검색 기간 (1-2년)")

class PaperResponse(BaseModel):
    id: str
    title: str
    authors: List[str]
    published_date: str
    updated_date: str
    abstract: str
    categories: List[str]
    pdf_url: str
    arxiv_url: str
    citation_count: int = 0
    relevance_score: float = 0.0

class DownloadRequest(BaseModel):
    paper_index: int = Field(..., ge=0, description="다운로드할 논문 인덱스")

class QuizRequest(BaseModel):
    pdf_path: str = Field(..., description="분석할 PDF 파일 경로")

class WorkflowRequest(BaseModel):
    domain: str = Field(..., description="검색할 도메인")
    additional_keywords: Optional[str] = Field(None, description="추가 검색 키워드")
    year_range: int = Field(1, ge=1, le=2, description="검색 기간")
    paper_index: int = Field(0, ge=0, description="다운로드할 논문 인덱스")

class WorkflowResponse(BaseModel):
    success: bool
    message: str
    workflow_id: str
    papers: List[PaperResponse]
    downloaded_pdf: Optional[str] = None
    quiz_generated: bool = False
    summary_generated: bool = False
    explainer_generated: bool = False
    podcast_created: bool = False

class StatusResponse(BaseModel):
    workflow_id: str
    status: str
    progress: int
    current_step: str
    message: str
    results: Optional[Dict[str, Any]] = None

class MultiAgentResponse(BaseModel):
    success: bool
    message: str
    summary: Optional[str] = None
    quiz: Optional[str] = None
    explainer: Optional[str] = None
    figure_analysis: Optional[str] = None
    tts_file: Optional[str] = None

# ==========================
# LangGraph State 정의
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
# 유틸리티 함수들
# ==========================
def clean_text(text: str) -> str:
    """텍스트 정리(TTS용)"""
    cleaned = re.sub(r"[#*>•\-]+", " ", text)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()

def build_llm(use_mini: bool = True, temperature: float = 0.2):
    """LLM 팩토리"""
    return AzureChatOpenAI(
        openai_api_version="2024-02-01",
        azure_deployment=os.getenv("AOAI_DEPLOY_GPT4O_MINI") if use_mini else os.getenv("AOAI_DEPLOY_GPT4O"),
        api_key=os.getenv("AOAI_API_KEY"),
        azure_endpoint=os.getenv("AOAI_ENDPOINT"),
        temperature=temperature,
    )

def build_embeddings():
    """Embeddings 팩토리"""
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
    """PDF 로드 (로컬 파일 또는 URL)"""
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

def build_vectorstore(docs: List[Document], embeddings, chunk_size=1000, chunk_overlap=200):
    """벡터스토어 구축"""
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
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
    """요약 생성 체인"""
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
    """퀴즈 생성 체인"""
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
    """해설 생성 체인"""
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
    """그림 분석 체인"""
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
    """품질 판정 체인"""
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
# LangGraph 노드 함수들
# ==========================
def node_summarizer(state: AgentState) -> AgentState:
    """요약 생성 노드"""
    vs = state["vectorstore"]
    k = state.get("k", 12)
    chunks = vs.similarity_search(state.get("query_summary", "summary overview of this document"), k=k)
    content = "\n\n".join([c.page_content for c in chunks])
    summary_chain = make_summary_chain()
    summary = summary_chain.invoke({"document_content": content})
    return {"summary": summary}

def node_quiz(state: AgentState) -> AgentState:
    """퀴즈 생성 노드"""
    vs = state["vectorstore"]
    k = state.get("k", 10)
    chunks = vs.similarity_search(state.get("query_quiz", "Generate exam questions based on this document"), k=k)
    content = "\n\n".join([c.page_content for c in chunks])
    quiz_chain = make_quiz_chain()
    quiz = quiz_chain.invoke({"document_content": content})
    return {"quiz": quiz}

def node_explainer(state: AgentState) -> AgentState:
    """해설 생성 노드"""
    vs = state["vectorstore"]
    k = state.get("k", 15)
    chunks = vs.similarity_search(state.get("query_explainer", "detailed explanation with industry applications"), k=k)
    content = "\n\n".join([c.page_content for c in chunks])
    explainer_chain = make_explainer_chain()
    explainer = explainer_chain.invoke({"document_content": content})
    return {"explainer": explainer}

def node_judge_summary(state: AgentState) -> AgentState:
    """요약 품질 판정 노드"""
    judge = make_judge_chain()
    verdict = judge.invoke({"generated": state.get("summary", "")}).strip().upper()
    return {"judge_summary_ok": verdict.startswith("YES")}

def node_judge_quiz(state: AgentState) -> AgentState:
    """퀴즈 품질 판정 노드"""
    judge = make_judge_chain()
    verdict = judge.invoke({"generated": state.get("quiz", "")}).strip().upper()
    return {"judge_quiz_ok": verdict.startswith("YES")}

def node_judge_explainer(state: AgentState) -> AgentState:
    """해설 품질 판정 노드"""
    judge = make_judge_chain()
    verdict = judge.invoke({"generated": state.get("explainer", "")}).strip().upper()
    return {"judge_explainer_ok": verdict.startswith("YES")}

def cond_on_summary(state: AgentState) -> str:
    """요약 조건부 엣지 라우팅"""
    if state.get("judge_summary_ok", True):
        return "ok"
    # 미흡하면 k + 4 (상한선 40)
    new_k = min(40, state.get("k", 12) + 4)
    state["k"] = new_k
    return "retry"

def cond_on_quiz(state: AgentState) -> str:
    """퀴즈 조건부 엣지 라우팅"""
    if state.get("judge_quiz_ok", True):
        return "ok"
    new_k = min(40, state.get("k", 12) + 4)
    state["k"] = new_k
    return "retry"

def cond_on_explainer(state: AgentState) -> str:
    """해설 조건부 엣지 라우팅"""
    if state.get("judge_explainer_ok", True):
        return "ok"
    new_k = min(40, state.get("k", 12) + 4)
    state["k"] = new_k
    return "retry"

def node_figure_analysis(state: AgentState) -> AgentState:
    """그림 분석 노드"""
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
    """그림 분석 품질 판정 노드"""
    judge = make_judge_chain()
    verdict = judge.invoke({"generated": state.get("figure_analysis", "")}).strip().upper()
    return {"judge_figure_analysis_ok": verdict.startswith("YES")}


def cond_on_figure_analysis(state: AgentState) -> str:
    """그림 분석 조건부 엣지 라우팅"""
    if state.get("judge_figure_analysis_ok", True):
        return "ok"
    new_k = min(40, state.get("k", 12) + 4)
    state["k"] = new_k
    return "retry"


def node_tts(state: AgentState) -> AgentState:
    """TTS 생성 노드"""
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
    """멀티에이전트 워크플로우 구성"""
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
            "ok": "quiz"
        }
    )

    # quiz → judge → (retry: quiz, ok: explainer)
    graph.add_edge("quiz", "judge_quiz")
    graph.add_conditional_edges(
        "judge_quiz",
        cond_on_quiz,
        {
            "retry": "quiz",
            "ok": "explainer"
        }
    )

    # explainer → judge → (retry: explainer, ok: figure_analysis)
    graph.add_edge("explainer", "judge_explainer")
    graph.add_conditional_edges(
        "judge_explainer",
        cond_on_explainer,
        {
            "retry": "explainer",
            "ok": "figure_analysis"
        }
    )

    # figure_analysis → judge → (retry: figure_analysis, ok: tts)
    graph.add_edge("figure_analysis", "judge_figure_analysis")
    graph.add_conditional_edges(
        "judge_figure_analysis",
        cond_on_figure_analysis,
        {
            "retry": "figure_analysis",
            "ok": "tts"
        }
    )

    # 마지막 tts 후 종료
    graph.add_edge("tts", END)

    return graph.compile()

# ==========================
# 멀티에이전트 실행 함수
# ==========================
def run_multi_agent(pdf_path_or_url: str):
    """멀티에이전트 시스템 실행"""
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
    results = {}
    
    if final_state.get("summary"):
        with open(f"summary_{ts}.txt", "w", encoding="utf-8") as f:
            f.write(final_state["summary"])
        print(f"📝 요약 저장: summary_{ts}.txt")
        results["summary"] = final_state["summary"]

    if final_state.get("quiz"):
        with open(f"quiz_{ts}.txt", "w", encoding="utf-8") as f:
            f.write(final_state["quiz"])
        print(f"📝 퀴즈 저장: quiz_{ts}.txt")
        results["quiz"] = final_state["quiz"]

    if final_state.get("explainer"):
        with open(f"explainer_{ts}.txt", "w", encoding="utf-8") as f:
            f.write(final_state["explainer"])
        print(f"📝 해설 저장: explainer_{ts}.txt")
        results["explainer"] = final_state["explainer"]

    if final_state.get("figure_analysis"):
        with open(f"figure_analysis_{ts}.txt", "w", encoding="utf-8") as f:
            f.write(final_state["figure_analysis"])
        print(f"📊 그림 분석 저장: figure_analysis_{ts}.txt")
        results["figure_analysis"] = final_state["figure_analysis"]

    print("🎉 모든 작업 완료!")
    return results

# ==========================
# AXPressScholarAgent 클래스
# ==========================
class AXPressScholarAgent:
    """arXiv API를 활용한 논문 검색 및 추천 에이전트"""
    
    def __init__(self, download_dir: str = "downloaded_papers"):
        self.base_url = "http://export.arxiv.org/api/query"
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        
        # 도메인별 검색 키워드 매핑
        self.domain_keywords = {
            "제조": ["manufacturing", "production", "industrial", "factory", "automation", "robotics"],
            "금융": ["finance", "financial", "banking", "fintech", "investment", "trading", "economics"],
            "CLOUD": ["cloud computing", "distributed systems", "microservices", "kubernetes", "container"],
            "통신": ["telecommunications", "communication", "network", "5G", "6G", "wireless"],
            "유통/물류": ["logistics", "supply chain", "distribution", "retail", "e-commerce", "optimization"],
            "Gen AI": ["artificial intelligence", "machine learning", "deep learning", "LLM", "generative AI", "neural networks"]
        }
        
        # arXiv 카테고리 매핑 (더 정확한 검색을 위해)
        self.arxiv_categories = {
            "제조": ["cs.RO", "cs.SY", "eess.SY"],  # Robotics, Systems, Control Systems
            "금융": ["q-fin.GN", "q-fin.CP", "econ.GN"],  # General Finance, Computational Finance
            "CLOUD": ["cs.DC", "cs.DS", "cs.SE"],  # Distributed Computing, Data Structures, Software Engineering
            "통신": ["cs.NI", "eess.SP"],  # Networking, Signal Processing
            "유통/물류": ["cs.AI", "math.OC"],  # Artificial Intelligence, Optimization
            "Gen AI": ["cs.AI", "cs.LG", "cs.CL"]  # AI, Machine Learning, Computation and Language
        }
    
    def fetch_papers(self, domain: str) -> List[Paper]:
        """지정된 도메인에서 논문을 검색합니다."""
        logger.info(f"도메인 '{domain}'에서 논문 검색 시작")
        
        if domain not in self.domain_keywords:
            raise ValueError(f"지원하지 않는 도메인입니다: {domain}")
        
        papers = []
        
        try:
            # 최신 논문 4편 검색 (최근 1년)
            latest_papers = self._search_latest_papers(domain, max_results=10)
            
            # 인기 논문 1편 검색 (인용수 기준)
            popular_paper = self._search_popular_paper(domain)
            
            # 최신 논문 4편 선택 (중복 제거)
            selected_latest = []
            seen_ids = set()
            
            for paper in latest_papers:
                if paper.id not in seen_ids and len(selected_latest) < 4:
                    selected_latest.append(paper)
                    seen_ids.add(paper.id)
            
            # 인기 논문이 중복되지 않으면 추가
            if popular_paper and popular_paper.id not in seen_ids:
                papers.append(popular_paper)
            elif popular_paper:
                # 인기 논문이 중복이면 최신 논문 중 하나를 대체
                if selected_latest:
                    selected_latest[0] = popular_paper
            
            papers.extend(selected_latest)
            
            # 5편이 되도록 조정
            papers = papers[:5]
            
            logger.info(f"총 {len(papers)}편의 논문을 찾았습니다.")
            return papers
            
        except Exception as e:
            logger.error(f"논문 검색 중 오류 발생: {e}")
            raise
    
    def _search_latest_papers(self, domain: str, max_results: int = 10) -> List[Paper]:
        """최신 논문을 검색합니다."""
        keywords = self.domain_keywords[domain]
        categories = self.arxiv_categories.get(domain, [])
        
        # 검색 쿼리 구성
        search_query = " OR ".join([f'all:{keyword}' for keyword in keywords])
        if categories:
            category_query = " OR ".join([f'cat:{cat}' for cat in categories])
            search_query = f"({search_query}) OR ({category_query})"
        
        # 1년 전 날짜 계산
        one_year_ago = datetime.now() - timedelta(days=365)
        date_filter = one_year_ago.strftime("%Y%m%d")
        
        params = {
            'search_query': search_query,
            'start': 0,
            'max_results': max_results * 2,  # 더 많이 가져와서 필터링
            'sortBy': 'submittedDate',
            'sortOrder': 'descending'
        }
        
        return self._make_arxiv_request(params, max_results)
    
    def _search_popular_paper(self, domain: str) -> Optional[Paper]:
        """인기 논문을 검색합니다 (relevance 기준)."""
        keywords = self.domain_keywords[domain]
        categories = self.arxiv_categories.get(domain, [])
        
        # 검색 쿼리 구성
        search_query = " OR ".join([f'all:{keyword}' for keyword in keywords])
        if categories:
            category_query = " OR ".join([f'cat:{cat}' for cat in categories])
            search_query = f"({search_query}) OR ({category_query})"
        
        params = {
            'search_query': search_query,
            'start': 0,
            'max_results': 20,
            'sortBy': 'relevance',
            'sortOrder': 'descending'
        }
        
        papers = self._make_arxiv_request(params, 1)
        return papers[0] if papers else None
    
    def _make_arxiv_request(self, params: Dict, max_results: int) -> List[Paper]:
        """arXiv API에 요청을 보내고 결과를 파싱합니다."""
        try:
            logger.info(f"arXiv API 요청: {params}")
            
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            # XML 파싱
            from xml.etree import ElementTree as ET
            root = ET.fromstring(response.content)
            
            # 네임스페이스 정의
            ns = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }
            
            papers = []
            entries = root.findall('atom:entry', ns)
            
            for entry in entries[:max_results]:
                paper = self._parse_arxiv_entry(entry, ns)
                if paper:
                    papers.append(paper)
            
            return papers
            
        except requests.exceptions.RequestException as e:
            logger.error(f"arXiv API 요청 실패: {e}")
            raise
        except Exception as e:
            logger.error(f"논문 파싱 중 오류: {e}")
            raise
    
    def _parse_arxiv_entry(self, entry, ns: Dict) -> Optional[Paper]:
        """arXiv 엔트리를 파싱하여 Paper 객체로 변환합니다."""
        try:
            # ID 추출
            id_elem = entry.find('atom:id', ns)
            paper_id = id_elem.text.strip() if id_elem is not None else "unknown"
            
            # 제목 추출
            title_elem = entry.find('atom:title', ns)
            title = title_elem.text.strip() if title_elem is not None else "No Title"
            
            # 저자 추출
            authors = []
            for author in entry.findall('atom:author', ns):
                name_elem = author.find('atom:name', ns)
                if name_elem is not None:
                    authors.append(name_elem.text.strip())
            
            # 날짜 추출
            published_elem = entry.find('atom:published', ns)
            published_date = published_elem.text.strip() if published_elem is not None else ""
            
            updated_elem = entry.find('atom:updated', ns)
            updated_date = updated_elem.text.strip() if updated_elem is not None else ""
            
            # 요약 추출
            summary_elem = entry.find('atom:summary', ns)
            abstract = summary_elem.text.strip() if summary_elem is not None else ""
            
            # 카테고리 추출
            categories = []
            for category in entry.findall('atom:category', ns):
                term = category.get('term')
                if term:
                    categories.append(term)
            
            # PDF URL 생성
            pdf_url = f"https://arxiv.org/pdf/{paper_id.split('/')[-1]}.pdf"
            arxiv_url = paper_id
            
            return Paper(
                id=paper_id,
                title=title,
                authors=authors,
                published_date=published_date,
                updated_date=updated_date,
                abstract=abstract,
                categories=categories,
                pdf_url=pdf_url,
                arxiv_url=arxiv_url
            )
            
        except Exception as e:
            logger.error(f"논문 파싱 중 오류: {e}")
            return None
    
    def display_papers(self, papers: List[Paper]) -> None:
        """검색 결과를 표시합니다."""
        if not papers:
            print("검색된 논문이 없습니다.")
            return
        
        print("\n" + "="*80)
        print("📚 AXPress Scholar Agent - 논문 검색 결과")
        print("="*80)
        
        for i, paper in enumerate(papers, 1):
            print(f"\n{i}. {paper.title}")
            print(f"   저자: {', '.join(paper.authors[:3])}{' 외' if len(paper.authors) > 3 else ''}")
            
            # 날짜 포맷팅
            try:
                pub_date = datetime.fromisoformat(paper.published_date.replace('Z', '+00:00'))
                formatted_date = pub_date.strftime("%Y-%m-%d")
                print(f"   발표일: {formatted_date}")
            except:
                print(f"   발표일: {paper.published_date}")
            
            print(f"   카테고리: {', '.join(paper.categories[:3])}")
            print(f"   PDF: [PDF Available] - {paper.pdf_url}")
            
            # 요약 미리보기 (첫 100자)
            if paper.abstract:
                preview = paper.abstract[:100] + "..." if len(paper.abstract) > 100 else paper.abstract
                print(f"   요약: {preview}")
    
    def download_pdf(self, paper: Paper) -> Optional[str]:
        """논문의 PDF를 다운로드합니다."""
        try:
            # 파일명 생성
            safe_title = "".join(c for c in paper.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title[:100]  # 파일명 길이 제한
            filename = f"{safe_title}_{paper.id.split('/')[-1]}.pdf"
            filepath = self.download_dir / filename
            
            # 이미 다운로드된 파일이 있는지 확인
            if filepath.exists():
                logger.info(f"파일이 이미 존재합니다: {filepath}")
                return str(filepath)
            
            logger.info(f"PDF 다운로드 시작: {paper.pdf_url}")
            print(f"📥 다운로드 중: {paper.title[:50]}...")
            
            # PDF 다운로드
            response = requests.get(paper.pdf_url, timeout=30, stream=True)
            response.raise_for_status()
            
            # 파일 저장
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"PDF 다운로드 완료: {filepath}")
            print(f"✅ PDF 다운로드 완료: {filepath}")
            return str(filepath)
            
        except requests.exceptions.Timeout:
            logger.error("PDF 다운로드 시간 초과")
            print("❌ 다운로드 시간 초과")
            return None
        except requests.exceptions.ConnectionError:
            logger.error("PDF 다운로드 연결 오류")
            print("❌ 연결 오류")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"PDF 다운로드 HTTP 오류: {e}")
            print(f"❌ HTTP 오류: {e}")
            return None
        except Exception as e:
            logger.error(f"PDF 다운로드 실패: {e}")
            print(f"❌ 다운로드 실패: {e}")
            return None

# ==========================
# FastAPI 앱 초기화
# ==========================
# 실제 모델들 초기화
scholar_agent = AXPressScholarAgent()
downloaded_papers_dir = Path("downloaded_papers")
workflow_status = {}  # 워크플로우 상태 추적

# 지원 도메인
SUPPORTED_DOMAINS = ["제조", "금융", "CLOUD", "통신", "유통/물류", "Gen AI"]

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 생명주기 관리"""
    # 시작 시 실행
    downloaded_papers_dir.mkdir(exist_ok=True)
    logger.info("FastAPI 앱이 시작되었습니다.")
    
    yield
    
    # 종료 시 실행
    logger.info("FastAPI 앱이 종료되었습니다.")

# FastAPI 앱에 lifespan 추가
app = FastAPI(
    title="AI Boot Camp Lab - Final Version 1 API",
    description="논문 검색부터 멀티에이전트 기반 퀴즈/요약/해설 생성 및 TTS 팟캐스트 제작까지 자동화하는 REST API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================
# FastAPI 엔드포인트들
# ==========================
@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "AI Boot Camp Lab - Final Version 1 API",
        "version": "1.0.0",
        "docs": "/docs",
        "supported_domains": SUPPORTED_DOMAINS,
        "features": [
            "논문 검색 (arXiv API)",
            "PDF 다운로드",
            "멀티에이전트 기반 요약/퀴즈/해설 생성",
            "품질 검증 시스템",
            "TTS 팟캐스트 생성"
        ]
    }

@app.get("/domains")
async def get_supported_domains():
    """지원되는 도메인 목록 반환"""
    return {
        "domains": SUPPORTED_DOMAINS,
        "count": len(SUPPORTED_DOMAINS)
    }

@app.post("/search/papers", response_model=List[PaperResponse])
async def search_papers(request: DomainRequest):
    """도메인별 논문 검색"""
    try:
        if request.domain not in SUPPORTED_DOMAINS:
            raise HTTPException(
                status_code=400, 
                detail=f"지원하지 않는 도메인입니다. 지원 도메인: {SUPPORTED_DOMAINS}"
            )
        
        logger.info(f"논문 검색 시작: 도메인={request.domain}, 키워드={request.additional_keywords}")
        
        # 논문 검색 (실제 모델 사용)
        papers = scholar_agent.fetch_papers(request.domain)
        
        if not papers:
            raise HTTPException(status_code=404, detail="검색된 논문이 없습니다.")
        
        # Paper 객체를 PaperResponse로 변환
        paper_responses = []
        for paper in papers:
            paper_responses.append(PaperResponse(
                id=paper.id,
                title=paper.title,
                authors=paper.authors,
                published_date=paper.published_date,
                updated_date=paper.updated_date,
                abstract=paper.abstract,
                categories=paper.categories,
                pdf_url=paper.pdf_url,
                arxiv_url=paper.arxiv_url,
                citation_count=paper.citation_count,
                relevance_score=paper.relevance_score
            ))
        
        logger.info(f"논문 검색 완료: {len(paper_responses)}편 발견")
        return paper_responses
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"논문 검색 오류: {e}")
        raise HTTPException(status_code=500, detail=f"논문 검색 중 오류가 발생했습니다: {str(e)}")

@app.post("/download/pdf")
async def download_pdf(request: DownloadRequest, papers_data: List[PaperResponse]):
    """논문 PDF 다운로드"""
    try:
        if request.paper_index >= len(papers_data):
            raise HTTPException(
                status_code=400, 
                detail=f"잘못된 논문 인덱스입니다. 0-{len(papers_data)-1} 범위에서 선택해주세요."
            )
        
        selected_paper_data = papers_data[request.paper_index]
        
        # Paper 객체 생성 (실제 모델 구조에 맞게)
        paper = Paper(
            id=selected_paper_data.id,
            title=selected_paper_data.title,
            authors=selected_paper_data.authors,
            published_date=selected_paper_data.published_date,
            updated_date=selected_paper_data.updated_date,
            abstract=selected_paper_data.abstract,
            categories=selected_paper_data.categories,
            pdf_url=selected_paper_data.pdf_url,
            arxiv_url=selected_paper_data.arxiv_url,
            citation_count=selected_paper_data.citation_count,
            relevance_score=selected_paper_data.relevance_score
        )
        
        logger.info(f"PDF 다운로드 시작: {paper.title}")
        
        # PDF 다운로드 (실제 모델 사용)
        filepath = scholar_agent.download_pdf(paper)
        
        if not filepath:
            raise HTTPException(status_code=500, detail="PDF 다운로드에 실패했습니다.")
        
        logger.info(f"PDF 다운로드 완료: {filepath}")
        
        return {
            "success": True,
            "message": "PDF 다운로드가 완료되었습니다.",
            "filepath": filepath,
            "filename": os.path.basename(filepath)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF 다운로드 오류: {e}")
        raise HTTPException(status_code=500, detail=f"PDF 다운로드 중 오류가 발생했습니다: {str(e)}")

@app.post("/multiagent/process", response_model=MultiAgentResponse)
async def process_with_multiagent(request: QuizRequest):
    """멀티에이전트 시스템으로 PDF 처리 (요약/퀴즈/해설/TTS)"""
    try:
        if not os.path.exists(request.pdf_path):
            raise HTTPException(status_code=404, detail="지정된 PDF 파일을 찾을 수 없습니다.")
        
        logger.info(f"멀티에이전트 처리 시작: {request.pdf_path}")
        
        # 멀티에이전트 시스템 실행
        results = run_multi_agent(request.pdf_path)
        
        logger.info("멀티에이전트 처리 완료")
        
        return MultiAgentResponse(
            success=True,
            message="멀티에이전트 처리가 완료되었습니다.",
            summary=results.get("summary"),
            quiz=results.get("quiz"),
            explainer=results.get("explainer"),
            tts_file=f"industry_explainer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"멀티에이전트 처리 오류: {e}")
        raise HTTPException(status_code=500, detail=f"멀티에이전트 처리 중 오류가 발생했습니다: {str(e)}")

@app.post("/workflow/start", response_model=WorkflowResponse)
async def start_workflow(request: WorkflowRequest, background_tasks: BackgroundTasks):
    """전체 워크플로우 시작 (논문 검색 → PDF 다운로드 → 멀티에이전트 처리)"""
    try:
        workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 워크플로우 상태 초기화
        workflow_status[workflow_id] = {
            "status": "started",
            "progress": 0,
            "current_step": "논문 검색",
            "message": "워크플로우가 시작되었습니다.",
            "results": {}
        }
        
        # 백그라운드에서 워크플로우 실행
        background_tasks.add_task(
            execute_workflow, 
            workflow_id, 
            request.domain, 
            request.additional_keywords,
            request.year_range,
            request.paper_index
        )
        
        return WorkflowResponse(
            success=True,
            message="워크플로우가 시작되었습니다.",
            workflow_id=workflow_id,
            papers=[],
            downloaded_pdf=None,
            quiz_generated=False,
            summary_generated=False,
            explainer_generated=False,
            podcast_created=False
        )
        
    except Exception as e:
        logger.error(f"워크플로우 시작 오류: {e}")
        raise HTTPException(status_code=500, detail=f"워크플로우 시작 중 오류가 발생했습니다: {str(e)}")

async def execute_workflow(workflow_id: str, domain: str, additional_keywords: Optional[str], 
                         year_range: int, paper_index: int):
    """백그라운드에서 워크플로우 실행 (실제 모델 사용)"""
    try:
        # 1단계: 논문 검색 (실제 모델 사용)
        workflow_status[workflow_id].update({
            "status": "running",
            "progress": 20,
            "current_step": "논문 검색",
            "message": f"'{domain}' 도메인에서 논문을 검색하고 있습니다..."
        })
        
        papers = scholar_agent.fetch_papers(domain)
        
        if not papers:
            workflow_status[workflow_id].update({
                "status": "failed",
                "progress": 0,
                "current_step": "논문 검색",
                "message": "검색된 논문이 없습니다."
            })
            return
        
        # 2단계: PDF 다운로드 (실제 모델 사용)
        workflow_status[workflow_id].update({
            "progress": 40,
            "current_step": "PDF 다운로드",
            "message": f"논문 '{papers[paper_index].title}' PDF를 다운로드하고 있습니다..."
        })
        
        filepath = scholar_agent.download_pdf(papers[paper_index])
        
        if not filepath:
            workflow_status[workflow_id].update({
                "status": "failed",
                "progress": 40,
                "current_step": "PDF 다운로드",
                "message": "PDF 다운로드에 실패했습니다."
            })
            return
        
        # 3단계: 멀티에이전트 처리 (실제 모델 사용)
        workflow_status[workflow_id].update({
            "progress": 60,
            "current_step": "멀티에이전트 처리",
            "message": "PDF를 분석하고 요약/퀴즈/해설을 생성하고 있습니다..."
        })
        
        multiagent_results = run_multi_agent(filepath)
        
        # 완료
        workflow_status[workflow_id].update({
            "status": "completed",
            "progress": 100,
            "current_step": "완료",
            "message": "전체 워크플로우가 완료되었습니다.",
            "results": {
                "papers_found": len(papers),
                "downloaded_pdf": filepath,
                "summary_generated": bool(multiagent_results.get("summary")),
                "quiz_generated": bool(multiagent_results.get("quiz")),
                "explainer_generated": bool(multiagent_results.get("explainer")),
                "podcast_created": bool(multiagent_results.get("explainer"))
            }
        })
        
        logger.info(f"워크플로우 {workflow_id} 완료")
        
    except Exception as e:
        workflow_status[workflow_id].update({
            "status": "failed",
            "current_step": "오류",
            "message": f"워크플로우 실행 중 오류가 발생했습니다: {str(e)}"
        })
        logger.error(f"워크플로우 {workflow_id} 실행 오류: {e}")

@app.get("/workflow/status/{workflow_id}", response_model=StatusResponse)
async def get_workflow_status(workflow_id: str):
    """워크플로우 상태 조회"""
    if workflow_id not in workflow_status:
        raise HTTPException(status_code=404, detail="워크플로우를 찾을 수 없습니다.")
    
    status_data = workflow_status[workflow_id]
    return StatusResponse(
        workflow_id=workflow_id,
        status=status_data["status"],
        progress=status_data["progress"],
        current_step=status_data["current_step"],
        message=status_data["message"],
        results=status_data.get("results")
    )

@app.get("/workflow/list")
async def list_workflows():
    """실행 중인 워크플로우 목록"""
    return {
        "workflows": list(workflow_status.keys()),
        "count": len(workflow_status)
    }

@app.get("/papers/downloaded")
async def get_downloaded_papers():
    """다운로드된 PDF 파일 목록 반환"""
    try:
        if not downloaded_papers_dir.exists():
            return {"papers": [], "count": 0}
        
        pdf_files = list(downloaded_papers_dir.glob("*.pdf"))
        papers_info = []
        
        for pdf_file in pdf_files:
            stat = pdf_file.stat()
            papers_info.append({
                "filename": pdf_file.name,
                "filepath": str(pdf_file),
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        
        # 수정 시간 기준으로 정렬 (최신순)
        papers_info.sort(key=lambda x: x["modified"], reverse=True)
        
        return {
            "papers": papers_info,
            "count": len(papers_info)
        }
        
    except Exception as e:
        logger.error(f"다운로드된 논문 목록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=f"논문 목록 조회 중 오류가 발생했습니다: {str(e)}")

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "features": "멀티에이전트 기반 논문 분석 시스템"
    }

# 에러 핸들러
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "요청한 리소스를 찾을 수 없습니다."}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "내부 서버 오류가 발생했습니다."}
    )

if __name__ == "__main__":
    # 개발 서버 실행
    uvicorn.run(
        "final:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
