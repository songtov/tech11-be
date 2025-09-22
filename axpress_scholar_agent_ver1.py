#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AXPress Scholar Agent - arXiv API 기반 논문 검색 및 추천 시스템
특정 도메인의 최신 논문과 인기 논문을 추천하고 PDF 다운로드를 제공합니다.
"""

import requests
import json
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

def main():
    """메인 함수"""
    print("🔬 AXPress Scholar Agent - arXiv 논문 검색 시스템")
    print("="*60)
    
    # 지원 도메인 표시
    domains = ["제조", "금융", "CLOUD", "통신", "유통/물류", "Gen AI"]
    print("\n📋 지원 도메인:")
    for i, domain in enumerate(domains, 1):
        print(f"   {i}. {domain}")
    
    try:
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
        
        # 에이전트 생성 및 논문 검색
        agent = AXPressScholarAgent()
        print(f"\n🔍 '{selected_domain}' 도메인에서 논문을 검색합니다...")
        
        papers = agent.fetch_papers(selected_domain)
        
        if not papers:
            print("검색된 논문이 없습니다.")
            return
        
        # 결과 표시
        agent.display_papers(papers)
        
        # PDF 다운로드 선택
        print(f"\n📄 총 {len(papers)}편의 논문 중에서 PDF를 다운로드할 논문을 선택하세요.")
        print("번호를 입력하세요 (0: 종료): ", end="")
        
        try:
            choice = int(input().strip())
            if choice == 0:
                print("프로그램을 종료합니다.")
                return
            elif 1 <= choice <= len(papers):
                selected_paper = papers[choice - 1]
                print(f"\n선택된 논문: {selected_paper.title}")
                
                filepath = agent.download_pdf(selected_paper)
                
                if filepath:
                    print(f"\n✅ PDF 다운로드가 완료되었습니다!")
                    print(f"저장 위치: {filepath}")
                else:
                    print("\n❌ PDF 다운로드에 실패했습니다.")
            else:
                print("❌ 잘못된 번호입니다.")
        except ValueError:
            print("❌ 숫자를 입력해주세요.")
        except KeyboardInterrupt:
            print("\n프로그램을 종료합니다.")
    
    except KeyboardInterrupt:
        print("\n프로그램을 종료합니다.")
    except Exception as e:
        logger.error(f"프로그램 실행 중 오류: {e}")
        print(f"❌ 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    main()
