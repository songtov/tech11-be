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
import time
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
        
        # 도메인별 유명 저널 정보 (인용수 기반 검색용)
        self.domain_journals = {
            "금융": ["Journal of Finance", "Journal of Financial Economics", "Review of Financial Studies", "Science"],
            "통신": ["IEEE Communications Magazine", "IEEE Transactions on Communications", "Science"],
            "제조": ["Journal of Manufacturing Systems", "CIRP Annals", "Science"],
            "유통/물류": ["Transportation Research Part E", "International Journal of Physical Distribution & Logistics Management"],
            "Gen AI": ["AI Journal", "Journal of Artificial Intelligence Research", "NeurIPS", "ICML", "ICLR", "Science"],
            "CLOUD": ["IEEE Transactions on Cloud Computing", "Springer Journal of Cloud Computing", "Science"]
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
        """지정된 도메인에서 논문을 검색합니다. (2년 내 인용수 높은 5편)"""
        logger.info(f"도메인 '{domain}'에서 논문 검색 시작 (고인용 논문 모드)")
        
        # 새로운 고인용 논문 검색 기능 사용
        return self.fetch_highly_cited_papers(domain)
    
    
    def fetch_highly_cited_papers(self, domain: str) -> List[Paper]:
        """도메인별 유명 저널에서 2년 내 인용수가 가장 높은 5개 논문을 검색하고 arXiv에서 다운로드합니다."""
        logger.info(f"도메인 '{domain}'에서 고인용 논문 검색 시작 (Semantic Scholar + arXiv)")
        
        if domain not in self.domain_keywords:
            raise ValueError(f"지원하지 않는 도메인입니다: {domain}")
        
        try:
            # 2년 전 날짜 계산
            two_years_ago = datetime.now() - timedelta(days=730)
            
            # 도메인별 저널 정보 가져오기
            journals = self.domain_journals.get(domain, [])
            if not journals:
                logger.warning(f"도메인 '{domain}'에 대한 저널 정보가 없습니다. 기본 검색을 수행합니다.")
                return self.fetch_papers(domain)
            
            all_papers = []
            
            # 각 저널별로 Semantic Scholar API로 검색
            for journal in journals:
                logger.info(f"저널 '{journal}'에서 논문 검색 중...")
                
                # Semantic Scholar API로 검색 (모든 연도)
                journal_papers = self._search_semantic_scholar(journal, two_years_ago)
                all_papers.extend(journal_papers)
                
                # API 호출 제한을 위한 대기
                time.sleep(1.0)
            
            if not all_papers:
                logger.warning("Semantic Scholar에서 논문을 찾을 수 없습니다. 기본 검색을 수행합니다.")
                return self.fetch_papers(domain)
            
            # 2년 내 논문만 필터링
            recent_papers = []
            for paper in all_papers:
                try:
                    # published_date에서 연도 추출
                    if paper.published_date:
                        paper_year = int(paper.published_date.split('-')[0])
                        if paper_year >= two_years_ago.year:
                            recent_papers.append(paper)
                except:
                    continue
            
            if not recent_papers:
                logger.warning("2년 내 논문을 찾을 수 없습니다. 기본 검색을 수행합니다.")
                return self.fetch_papers(domain)
            
            # 인용수 기준으로 정렬 (2년 내 논문 중에서)
            recent_papers.sort(key=lambda x: x.citation_count, reverse=True)
            
            # 상위 5개 선택 (2년 내 인용수 가장 높은 논문들)
            selected_papers = recent_papers[:5]
            
            logger.info(f"2년 내 인용수 기준 상위 {len(selected_papers)}편의 논문을 찾았습니다.")
            
            # 이제 arXiv에서 해당 논문들을 검색하여 다운로드 가능한 버전을 찾습니다
            arxiv_papers = []
            for paper in selected_papers:
                logger.info(f"arXiv에서 '{paper.title}' 검색 중...")
                arxiv_paper = self._search_arxiv_by_title(paper.title)
                if arxiv_paper:
                    # Semantic Scholar에서 가져온 인용수 정보를 유지
                    arxiv_paper.citation_count = paper.citation_count
                    arxiv_papers.append(arxiv_paper)
                    logger.info(f"arXiv에서 발견: {arxiv_paper.title}")
                else:
                    logger.warning(f"arXiv에서 찾을 수 없음: {paper.title}")
                    # arXiv에서 찾을 수 없는 경우 원본 논문 정보를 그대로 사용
                    arxiv_papers.append(paper)
                
                # API 호출 제한을 위한 대기
                time.sleep(0.5)
            
            logger.info(f"최종 {len(arxiv_papers)}편의 논문을 반환합니다.")
            return arxiv_papers
            
        except Exception as e:
            logger.error(f"고인용 논문 검색 중 오류 발생: {e}")
            # 오류 발생 시 기본 검색으로 fallback
            return self.fetch_papers(domain)
    
    def _search_semantic_scholar(self, journal: str, min_date: datetime) -> List[Paper]:
        """Semantic Scholar API를 사용하여 특정 저널의 논문을 검색합니다."""
        try:
            # Semantic Scholar API 엔드포인트
            base_url = "https://api.semanticscholar.org/graph/v1/paper/search"
            
            # 검색 쿼리 구성 (더 간단한 형식으로 변경)
            query = journal  # venue: 제거하고 저널명만 사용
            
            params = {
                'query': query,
                'limit': 50,  # 제한을 줄여서 안정성 향상
                'fields': 'paperId,title,authors,year,venue,citationCount,abstract,isOpenAccess,openAccessPdf,externalIds'
            }
            
            logger.info(f"Semantic Scholar API 요청: {params}")
            
            # User-Agent 헤더 추가
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(base_url, params=params, headers=headers, timeout=30)
            logger.info(f"API 응답 상태: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"API 요청 실패: {response.status_code} - {response.text}")
                return []
            
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"API 응답 데이터: {len(data.get('data', []))}개 논문 발견")
            
            papers = []
            
            for paper_data in data.get('data', []):
                try:
                    # 논문이 해당 저널에서 나온 것인지 확인
                    paper_venue = paper_data.get('venue', '').lower()
                    journal_lower = journal.lower()
                    
                    # 저널명이 venue에 포함되어 있는지 확인
                    if journal_lower not in paper_venue and not any(word in paper_venue for word in journal_lower.split()):
                        continue
                    
                    # 모든 연도의 논문을 가져온 후 나중에 필터링
                    paper_year = paper_data.get('year', 0)
                    
                    # arXiv ID가 있는지 확인
                    arxiv_id = None
                    external_ids = paper_data.get('externalIds', {})
                    if external_ids:
                        arxiv_id = external_ids.get('ArXiv')
                    
                    # 저자 정보 추출
                    authors = []
                    for author in paper_data.get('authors', []):
                        if author.get('name'):
                            authors.append(author['name'])
                    
                    # PDF URL 생성 (arXiv 우선, 그 다음 openAccessPdf)
                    pdf_url = ""
                    if arxiv_id:
                        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
                    elif paper_data.get('openAccessPdf', {}).get('url'):
                        pdf_url = paper_data['openAccessPdf']['url']
                    
                    # arXiv URL 생성
                    arxiv_url = f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else ""
                    
                    # 발표일 처리 (year만 사용)
                    published_date = f"{paper_year}-01-01T00:00:00Z"
                    updated_date = f"{paper_year}-01-01T00:00:00Z"
                    
                    # Paper 객체 생성
                    paper = Paper(
                        id=paper_data.get('paperId', ''),
                        title=paper_data.get('title', 'No Title'),
                        authors=authors,
                        published_date=published_date,
                        updated_date=updated_date,
                        abstract=paper_data.get('abstract', ''),
                        categories=[journal],  # 저널명을 카테고리로 사용
                        pdf_url=pdf_url,
                        arxiv_url=arxiv_url,
                        citation_count=paper_data.get('citationCount', 0),
                        relevance_score=0.0
                    )
                    
                    papers.append(paper)
                    
                except Exception as e:
                    logger.warning(f"논문 파싱 중 오류: {e}")
                    continue
            
            logger.info(f"저널 '{journal}'에서 {len(papers)}편의 논문을 찾았습니다.")
            return papers
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Semantic Scholar API 요청 실패: {e}")
            return []
        except Exception as e:
            logger.error(f"Semantic Scholar 검색 중 오류: {e}")
            return []
    
    def _search_arxiv_by_title(self, title: str) -> Optional[Paper]:
        """제목으로 arXiv에서 논문을 검색합니다."""
        try:
            # arXiv API 검색 쿼리 구성
            search_query = f'ti:"{title}"'
            
            params = {
                'search_query': search_query,
                'start': 0,
                'max_results': 5,  # 최대 5개 결과
                'sortBy': 'relevance',
                'sortOrder': 'descending'
            }
            
            logger.info(f"arXiv 제목 검색: {search_query}")
            
            # arXiv API 요청
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
            
            entries = root.findall('atom:entry', ns)
            
            # 가장 관련성 높은 논문 반환
            if entries:
                paper = self._parse_arxiv_entry(entries[0], ns)
                if paper:
                    logger.info(f"arXiv에서 논문 발견: {paper.title}")
                    return paper
            
            return None
            
        except Exception as e:
            logger.error(f"arXiv 제목 검색 중 오류: {e}")
            return None
    
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
            
            # 인용수 표시 (Semantic Scholar에서 가져온 경우)
            if paper.citation_count > 0:
                print(f"   📊 인용수: {paper.citation_count}")
            
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
        
        # 새로운 기능: 고인용 논문 검색
        print("📊 고인용 논문 검색 모드 (2년 내 인용수 기준)")
        papers = agent.fetch_highly_cited_papers(selected_domain)
        
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

# final.py와 완전히 동일한 AXPressScholarAgent 클래스
# 이제 final.py를 수정하지 않고도 동일한 기능을 사용할 수 있습니다.

if __name__ == "__main__":
    main()
