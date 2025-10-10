import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from xml.etree import ElementTree as ET

import requests
from sqlalchemy.orm import Session

from app.models.research import Research
from app.schemas.research import (
    DomainEnum,
    ResearchCreate,
    ResearchDownload,
    ResearchDownloadResponse,
    ResearchResponse,
    ResearchSearch,
    ResearchSearchResponse,
    ResearchUpdate,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Paper:
    """Paper information data class"""

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


class SimplifiedScholarAgent:
    """Simplified version of AXPressScholarAgent for research search"""

    def __init__(self):
        self.base_url = "http://export.arxiv.org/api/query"

        # Domain mapping from Korean enum to legacy Korean domain keys
        self.domain_mapping = {
            DomainEnum.FINANCE: "금융",
            DomainEnum.COMMUNICATION: "통신",
            DomainEnum.MANUFACTURE: "제조",
            DomainEnum.LOGISTICS: "유통/물류",
            DomainEnum.AI: "Gen AI",  # Map to legacy "Gen AI" key
            DomainEnum.CLOUD: "CLOUD",  # Map to legacy "CLOUD" key
        }

        # Domain keywords (from legacy)
        self.domain_keywords = {
            "제조": [
                "manufacturing",
                "production",
                "industrial",
                "factory",
                "automation",
                "robotics",
            ],
            "금융": [
                "finance",
                "financial",
                "banking",
                "fintech",
                "investment",
                "trading",
                "economics",
            ],
            "CLOUD": [
                "cloud computing",
                "distributed systems",
                "microservices",
                "kubernetes",
                "container",
            ],
            "통신": [
                "telecommunications",
                "communication",
                "network",
                "5G",
                "6G",
                "wireless",
            ],
            "유통/물류": [
                "logistics",
                "supply chain",
                "distribution",
                "retail",
                "e-commerce",
                "optimization",
            ],
            "Gen AI": [
                "artificial intelligence",
                "machine learning",
                "deep learning",
                "LLM",
                "generative AI",
                "neural networks",
            ],
        }

        # arXiv categories mapping
        self.arxiv_categories = {
            "제조": ["cs.RO", "cs.SY", "eess.SY"],
            "금융": ["q-fin.GN", "q-fin.CP", "econ.GN"],
            "CLOUD": ["cs.DC", "cs.DS", "cs.SE"],
            "통신": ["cs.NI", "eess.SP"],
            "유통/물류": ["cs.AI", "math.OC"],
            "Gen AI": ["cs.AI", "cs.LG", "cs.CL"],
        }

        # Domain journals for Semantic Scholar search
        self.domain_journals = {
            "금융": [
                "Journal of Finance",
                "Journal of Financial Economics",
                "Review of Financial Studies",
                "Science",
            ],
            "통신": [
                "IEEE Communications Magazine",
                "IEEE Transactions on Communications",
                "Science",
            ],
            "제조": ["Journal of Manufacturing Systems", "CIRP Annals", "Science"],
            "유통/물류": [
                "Transportation Research Part E",
                "International Journal of Physical Distribution & Logistics Management",
            ],
            "Gen AI": [
                "AI Journal",
                "Journal of Artificial Intelligence Research",
                "NeurIPS",
                "ICML",
                "ICLR",
                "Science",
            ],
            "CLOUD": [
                "IEEE Transactions on Cloud Computing",
                "Springer Journal of Cloud Computing",
                "Science",
            ],
        }

    def fetch_papers(self, domain: DomainEnum) -> List[Paper]:
        """Fetch papers for the specified domain (returns exactly 5 papers with arxiv_url)"""
        logger.info(f"Searching papers for domain: {domain}")

        # Map Korean domain enum to legacy domain key
        legacy_domain_key = self.domain_mapping.get(domain)
        if not legacy_domain_key:
            logger.error(f"Unsupported domain: {domain}")
            return []

        try:
            # Try Semantic Scholar + arXiv approach first
            papers = self._fetch_highly_cited_papers(legacy_domain_key)

            # Filter out papers without arxiv_url
            papers = [p for p in papers if p.arxiv_url and p.arxiv_url.strip()]
            logger.info(
                f"Found {len(papers)} papers with ArXiv URLs from Semantic Scholar"
            )

            # If not enough papers, fallback to arXiv only (which should always have arxiv_url)
            if len(papers) < 5:
                logger.info(
                    "Not enough papers with ArXiv URLs from Semantic Scholar, trying arXiv fallback"
                )
                arxiv_papers = self._search_arxiv_papers(
                    legacy_domain_key,
                    max_results=20,  # Increased to get more candidates
                )

                # Combine and deduplicate (arXiv papers should always have arxiv_url)
                existing_titles = {p.title.lower() for p in papers}
                for paper in arxiv_papers:
                    if (
                        paper.title.lower() not in existing_titles
                        and paper.arxiv_url
                        and paper.arxiv_url.strip()
                        and len(papers) < 5
                    ):
                        papers.append(paper)

            # If still not enough, try more arXiv papers
            if len(papers) < 5:
                logger.info("Still need more papers, trying additional arXiv search")
                additional_papers = self._search_arxiv_papers(
                    legacy_domain_key, max_results=30, start_offset=20
                )

                existing_titles = {p.title.lower() for p in papers}
                for paper in additional_papers:
                    if (
                        paper.title.lower() not in existing_titles
                        and paper.arxiv_url
                        and paper.arxiv_url.strip()
                        and len(papers) < 5
                    ):
                        papers.append(paper)

            # Ensure exactly 5 papers
            return papers[:5]

        except Exception as e:
            logger.error(f"Error fetching papers: {e}")
            return []

    def _fetch_highly_cited_papers(self, legacy_domain_key: str) -> List[Paper]:
        """Fetch highly cited papers using Semantic Scholar API"""
        try:
            journals = self.domain_journals.get(legacy_domain_key, [])
            if not journals:
                return []

            all_papers = []
            two_years_ago = datetime.now() - timedelta(days=730)

            for journal in journals[:2]:  # Limit to 2 journals for speed
                logger.info(f"Searching journal: {journal}")
                papers = self._search_semantic_scholar(journal, two_years_ago)
                all_papers.extend(papers)
                time.sleep(1.0)  # Rate limiting

                if len(all_papers) >= 10:  # Stop if we have enough
                    break

            # Filter recent papers and sort by citation count
            recent_papers = []
            for paper in all_papers:
                try:
                    if paper.published_date:
                        paper_year = int(paper.published_date.split("-")[0])
                        if paper_year >= two_years_ago.year:
                            recent_papers.append(paper)
                except (ValueError, IndexError, AttributeError):
                    continue

            recent_papers.sort(key=lambda x: x.citation_count, reverse=True)
            return recent_papers[:5]

        except Exception as e:
            logger.error(f"Error in highly cited papers search: {e}")
            return []

    def _search_semantic_scholar(self, journal: str, min_date: datetime) -> List[Paper]:
        """Search Semantic Scholar API for papers"""
        try:
            base_url = "https://api.semanticscholar.org/graph/v1/paper/search"

            params = {
                "query": journal,
                "limit": 20,
                "fields": "paperId,title,authors,year,venue,citationCount,abstract,isOpenAccess,openAccessPdf,externalIds",
            }

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            response = requests.get(
                base_url, params=params, headers=headers, timeout=30
            )

            if response.status_code != 200:
                logger.error(f"Semantic Scholar API error: {response.status_code}")
                return []

            data = response.json()
            papers = []

            for paper_data in data.get("data", []):
                try:
                    # Check if paper is from the target journal
                    paper_venue = paper_data.get("venue", "").lower()
                    journal_lower = journal.lower()

                    if journal_lower not in paper_venue and not any(
                        word in paper_venue for word in journal_lower.split()
                    ):
                        continue

                    # Extract paper information
                    paper_year = paper_data.get("year", 0)
                    external_ids = paper_data.get("externalIds", {})
                    arxiv_id = external_ids.get("ArXiv") if external_ids else None

                    authors = [
                        author.get("name", "")
                        for author in paper_data.get("authors", [])
                        if author.get("name")
                    ]

                    # Only include papers with ArXiv IDs
                    if not arxiv_id:
                        continue

                    # Generate URLs
                    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
                    arxiv_url = f"https://arxiv.org/abs/{arxiv_id}"

                    paper = Paper(
                        id=paper_data.get("paperId", ""),
                        title=paper_data.get("title", "No Title"),
                        authors=authors,
                        published_date=f"{paper_year}-01-01T00:00:00Z",
                        updated_date=f"{paper_year}-01-01T00:00:00Z",
                        abstract=paper_data.get("abstract", ""),
                        categories=[journal],
                        pdf_url=pdf_url,
                        arxiv_url=arxiv_url,
                        citation_count=paper_data.get("citationCount", 0),
                        relevance_score=0.0,
                    )

                    papers.append(paper)

                except Exception as e:
                    logger.warning(f"Error parsing paper: {e}")
                    continue

            return papers

        except Exception as e:
            logger.error(f"Semantic Scholar search error: {e}")
            return []

    def _search_arxiv_papers(
        self, legacy_domain_key: str, max_results: int = 5, start_offset: int = 0
    ) -> List[Paper]:
        """Search arXiv directly for papers"""
        try:
            keywords = self.domain_keywords.get(legacy_domain_key, [])
            categories = self.arxiv_categories.get(legacy_domain_key, [])

            # Build search query
            search_query = " OR ".join(
                [f"all:{keyword}" for keyword in keywords[:3]]
            )  # Limit keywords
            if categories:
                category_query = " OR ".join([f"cat:{cat}" for cat in categories])
                search_query = f"({search_query}) OR ({category_query})"

            params = {
                "search_query": search_query,
                "start": start_offset,
                "max_results": max_results * 2,
                "sortBy": "relevance",
                "sortOrder": "descending",
            }

            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()

            # Parse XML response
            root = ET.fromstring(response.content)
            ns = {
                "atom": "http://www.w3.org/2005/Atom",
                "arxiv": "http://arxiv.org/schemas/atom",
            }

            papers = []
            entries = root.findall("atom:entry", ns)

            for entry in entries[:max_results]:
                paper = self._parse_arxiv_entry(entry, ns)
                if paper:
                    papers.append(paper)

            return papers

        except Exception as e:
            logger.error(f"arXiv search error: {e}")
            return []

    def _parse_arxiv_entry(self, entry, ns: Dict) -> Optional[Paper]:
        """Parse arXiv entry to Paper object"""
        try:
            # Extract basic information
            id_elem = entry.find("atom:id", ns)
            paper_id = id_elem.text.strip() if id_elem is not None else "unknown"

            title_elem = entry.find("atom:title", ns)
            title = title_elem.text.strip() if title_elem is not None else "No Title"

            # Extract authors
            authors = []
            for author in entry.findall("atom:author", ns):
                name_elem = author.find("atom:name", ns)
                if name_elem is not None:
                    authors.append(name_elem.text.strip())

            # Extract dates
            published_elem = entry.find("atom:published", ns)
            published_date = (
                published_elem.text.strip() if published_elem is not None else ""
            )

            updated_elem = entry.find("atom:updated", ns)
            updated_date = updated_elem.text.strip() if updated_elem is not None else ""

            # Extract abstract
            summary_elem = entry.find("atom:summary", ns)
            abstract = summary_elem.text.strip() if summary_elem is not None else ""

            # Extract categories
            categories = []
            for category in entry.findall("atom:category", ns):
                term = category.get("term")
                if term:
                    categories.append(term)

            # Generate URLs
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
                arxiv_url=arxiv_url,
                citation_count=0,
                relevance_score=0.0,
            )

        except Exception as e:
            logger.error(f"Error parsing arXiv entry: {e}")
            return None


class ResearchService:
    def __init__(self, db: Session):
        self.db = db
        self.scholar_agent = SimplifiedScholarAgent()

    def create_research(self, research: ResearchCreate) -> Research:
        """Create a new research entry"""
        db_research = Research(title=research.title, abstract=research.abstract)
        self.db.add(db_research)
        self.db.commit()
        self.db.refresh(db_research)
        return db_research

    def search_research(self, research: ResearchSearch) -> ResearchSearchResponse:
        """Search for research papers using the legacy scholar agent"""
        logger.info(f"Starting research search for domain: {research.domain}")

        try:
            # Use the scholar agent to fetch papers
            papers = self.scholar_agent.fetch_papers(research.domain)

            if not papers:
                logger.warning(f"No papers found for domain: {research.domain}")
                # Return empty response with 5 dummy entries to satisfy schema
                dummy_responses = []
                for i in range(5):
                    dummy_responses.append(
                        ResearchResponse(
                            id=i + 1,
                            title=f"No papers found for domain {research.domain.value}",
                            abstract="No research papers were found for the specified domain. Please try a different domain or check back later.",
                            authors=[],
                            published_date=None,
                            updated_date=None,
                            categories=[],
                            pdf_url=None,
                            arxiv_url=None,
                            citation_count=0,
                            relevance_score=0.0,
                            created_at=datetime.now(),
                            updated_at=datetime.now(),
                        )
                    )
                return ResearchSearchResponse(data=dummy_responses)

            # Convert Paper objects to ResearchResponse objects
            research_responses = []
            for i, paper in enumerate(papers):
                # Parse the published date
                try:
                    if paper.published_date:
                        # Try to parse ISO format first
                        if "T" in paper.published_date:
                            created_at = datetime.fromisoformat(
                                paper.published_date.replace("Z", "+00:00")
                            )
                        else:
                            # Fallback to year-only format
                            year = int(paper.published_date.split("-")[0])
                            created_at = datetime(year, 1, 1)
                    else:
                        created_at = datetime.now()
                except (ValueError, IndexError, AttributeError):
                    created_at = datetime.now()

                research_response = ResearchResponse(
                    id=i + 1,  # Use index as ID since we don't store in DB
                    title=paper.title,
                    abstract=paper.abstract or "No abstract available",
                    authors=paper.authors,
                    published_date=paper.published_date,
                    updated_date=paper.updated_date,
                    categories=paper.categories,
                    pdf_url=paper.pdf_url,
                    arxiv_url=paper.arxiv_url,
                    citation_count=paper.citation_count,
                    relevance_score=paper.relevance_score,
                    created_at=created_at,
                    updated_at=created_at,
                )
                research_responses.append(research_response)

            # Ensure exactly 5 responses (pad with dummy if needed)
            while len(research_responses) < 5:
                research_responses.append(
                    ResearchResponse(
                        id=len(research_responses) + 1,
                        title="Additional research needed",
                        abstract="Additional research papers are being processed. Please check back later for more results.",
                        authors=[],
                        published_date=None,
                        updated_date=None,
                        categories=[],
                        pdf_url=None,
                        arxiv_url=None,
                        citation_count=0,
                        relevance_score=0.0,
                        created_at=datetime.now(),
                        updated_at=datetime.now(),
                    )
                )

            # Limit to exactly 5
            research_responses = research_responses[:5]

            logger.info(f"Successfully found {len(research_responses)} research papers")
            return ResearchSearchResponse(data=research_responses)

        except Exception as e:
            logger.error(f"Error in research search: {e}")
            # Return error response with 5 dummy entries
            error_responses = []
            for i in range(5):
                error_responses.append(
                    ResearchResponse(
                        id=i + 1,
                        title=f"Search Error for {research.domain.value}",
                        abstract=f"An error occurred while searching for research papers: {str(e)}. Please try again later.",
                        authors=[],
                        published_date=None,
                        updated_date=None,
                        categories=[],
                        pdf_url=None,
                        arxiv_url=None,
                        citation_count=0,
                        relevance_score=0.0,
                        created_at=datetime.now(),
                        updated_at=datetime.now(),
                    )
                )
            return ResearchSearchResponse(data=error_responses)

    def download_research(self, research: ResearchDownload) -> ResearchDownloadResponse:
        """Download a research paper PDF to output/research directory"""

        try:
            # Create output/research directory if it doesn't exist
            output_dir = Path("output/research")
            output_dir.mkdir(parents=True, exist_ok=True)

            # Generate safe filename based on title or arXiv ID
            safe_title = None

            # First try to use the research title if provided
            if research.title:
                # Clean the title for use as filename
                safe_title = "".join(
                    c for c in research.title if c.isalnum() or c in (" ", "-", "_")
                ).strip()
                safe_title = re.sub(
                    r"\s+", "_", safe_title
                )  # Replace spaces with underscores
                safe_title = safe_title[:100]  # Limit length to 100 characters

            # If no title, try to extract arXiv ID from URL
            if not safe_title and research.arxiv_url:
                match = re.search(r"arxiv\.org/abs/([^/]+)", research.arxiv_url)
                if match:
                    arxiv_id = match.group(1)
                    safe_title = arxiv_id.replace("/", "_").replace("\\", "_")

            # Final fallback: use timestamp
            if not safe_title:
                from datetime import datetime

                safe_title = (
                    f"research_paper_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )

            filename = f"{safe_title}.pdf"
            filepath = output_dir / filename

            # Check if file already exists
            if filepath.exists():
                download_url = f"/research/files/{filename}"
                return ResearchDownloadResponse(
                    output_path=str(filepath.absolute()),
                    download_url=download_url,
                    filename=filename,
                )

            # Download PDF from the provided URL
            pdf_url = research.pdf_url
            if not pdf_url:
                raise ValueError("PDF URL is required for download")

            print(f"📥 Downloading PDF from: {pdf_url}")
            print(f"💾 Saving to: {filepath}")

            # Download with proper headers and streaming
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }

            response = requests.get(pdf_url, headers=headers, timeout=30, stream=True)
            response.raise_for_status()

            # Check if response is actually a PDF
            content_type = response.headers.get("content-type", "").lower()
            if "pdf" not in content_type and not pdf_url.endswith(".pdf"):
                # Try to detect PDF by content
                first_chunk = next(response.iter_content(chunk_size=1024), b"")
                if not first_chunk.startswith(b"%PDF"):
                    raise ValueError("Downloaded content is not a valid PDF file")

                # Write the first chunk and continue with the rest
                with open(filepath, "wb") as f:
                    f.write(first_chunk)
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            else:
                # Standard PDF download
                with open(filepath, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

            # Verify file was created and has content
            if not filepath.exists() or filepath.stat().st_size == 0:
                raise ValueError("Failed to download PDF or file is empty")

            print(f"✅ PDF download completed: {filepath}")
            print(f"📊 File size: {filepath.stat().st_size} bytes")

            # Generate download URL for frontend
            download_url = f"/research/files/{filename}"

            return ResearchDownloadResponse(
                output_path=str(filepath.absolute()),
                download_url=download_url,
                filename=filename,
            )

        except requests.exceptions.Timeout:
            raise ValueError("PDF download timed out")
        except requests.exceptions.ConnectionError:
            raise ValueError("Connection error while downloading PDF")
        except requests.exceptions.HTTPError as e:
            raise ValueError(f"HTTP error while downloading PDF: {e}")
        except Exception as e:
            raise ValueError(f"Failed to download PDF: {str(e)}")

    def get_research(self, research_id: int) -> Optional[Research]:
        """Get a research entry by ID"""
        return self.db.query(Research).filter(Research.id == research_id).first()

    def get_all_research(self, skip: int = 0, limit: int = 100) -> List[Research]:
        """Get all research entries with pagination"""
        return self.db.query(Research).offset(skip).limit(limit).all()

    def update_research(
        self, research_id: int, research_update: ResearchUpdate
    ) -> Optional[Research]:
        """Update a research entry"""
        db_research = self.get_research(research_id)
        if not db_research:
            return None

        update_data = research_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_research, field, value)

        self.db.commit()
        self.db.refresh(db_research)
        return db_research

    def delete_research(self, research_id: int) -> bool:
        """Delete a research entry"""
        db_research = self.get_research(research_id)
        if not db_research:
            return False

        self.db.delete(db_research)
        self.db.commit()
        return True
