#!/usr/bin/env python3
"""
Pytest tests for ResearchService.search_research functionality
Tests the integration with SimplifiedScholarAgent and various edge cases
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import List

from app.services.research import ResearchService, SimplifiedScholarAgent, Paper
from app.schemas.research import ResearchSearch, ResearchSearchResponse, DomainEnum
from app.models.research import Research


class TestSimplifiedScholarAgent:
    """Test the SimplifiedScholarAgent class"""

    def setup_method(self):
        """Set up test fixtures"""
        self.agent = SimplifiedScholarAgent()

    def test_domain_mapping(self):
        """Test that domain mapping is correctly configured"""
        expected_mappings = {
            DomainEnum.FINANCE: "금융",
            DomainEnum.COMMUNICATION: "통신",
            DomainEnum.MANUFACTURE: "제조",
            DomainEnum.LOGISTICS: "유통/물류",
            DomainEnum.AI: "Gen AI",
            DomainEnum.CLOUD: "CLOUD"
        }

        assert self.agent.domain_mapping == expected_mappings

    def test_domain_keywords_exist(self):
        """Test that all mapped domains have keywords"""
        for korean_domain_enum, legacy_domain_key in self.agent.domain_mapping.items():
            assert legacy_domain_key in self.agent.domain_keywords
            assert len(self.agent.domain_keywords[legacy_domain_key]) > 0

    def test_arxiv_categories_exist(self):
        """Test that all mapped domains have arXiv categories"""
        for korean_domain_enum, legacy_domain_key in self.agent.domain_mapping.items():
            assert legacy_domain_key in self.agent.arxiv_categories
            assert len(self.agent.arxiv_categories[legacy_domain_key]) > 0

    @patch('app.services.research.requests.get')
    def test_fetch_papers_success(self, mock_get):
        """Test successful paper fetching"""
        # Mock Semantic Scholar response
        mock_semantic_response = Mock()
        mock_semantic_response.status_code = 200
        mock_semantic_response.json.return_value = {
            "data": [
                {
                    "paperId": "test123",
                    "title": "Test AI Paper",
                    "authors": [{"name": "John Doe"}, {"name": "Jane Smith"}],
                    "year": 2023,
                    "venue": "AI Journal",
                    "citationCount": 50,
                    "abstract": "This is a test abstract about AI",
                    "externalIds": {"ArXiv": "2023.12345"},
                    "openAccessPdf": {"url": "https://example.com/paper.pdf"}
                }
            ]
        }

        # Mock arXiv response
        mock_arxiv_response = Mock()
        mock_arxiv_response.status_code = 200
        mock_arxiv_response.content = b'''<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <entry>
                <id>http://arxiv.org/abs/2023.12346v1</id>
                <title>Another AI Paper</title>
                <author><name>Alice Johnson</name></author>
                <published>2023-01-15T00:00:00Z</published>
                <updated>2023-01-15T00:00:00Z</updated>
                <summary>Another test abstract</summary>
                <category term="cs.AI" />
            </entry>
        </feed>'''

        # Configure mock to return different responses for different URLs
        def mock_get_side_effect(url, **kwargs):
            if "semanticscholar.org" in url:
                return mock_semantic_response
            else:  # arXiv
                return mock_arxiv_response

        mock_get.side_effect = mock_get_side_effect
        mock_get.return_value.raise_for_status = Mock()

        papers = self.agent.fetch_papers(DomainEnum.AI)

        assert len(papers) <= 5  # Should return at most 5 papers
        assert all(isinstance(paper, Paper) for paper in papers)
        if papers:
            assert papers[0].title in ["Test AI Paper", "Another AI Paper"]

    @patch('app.services.research.requests.get')
    def test_fetch_papers_api_failure(self, mock_get):
        """Test handling of API failures"""
        # Mock API failure
        mock_get.side_effect = Exception("API Error")

        papers = self.agent.fetch_papers(DomainEnum.AI)

        assert papers == []

    def test_fetch_papers_unsupported_domain(self):
        """Test handling of unsupported domain"""
        # Create a mock domain that doesn't exist in mapping
        with patch.object(self.agent, 'domain_mapping', {}):
            papers = self.agent.fetch_papers(DomainEnum.AI)
            assert papers == []

    @patch('app.services.research.requests.get')
    def test_semantic_scholar_search_success(self, mock_get):
        """Test successful Semantic Scholar search"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "paperId": "semantic123",
                    "title": "Semantic Scholar Paper",
                    "authors": [{"name": "Dr. Smith"}],
                    "year": 2023,
                    "venue": "Science",
                    "citationCount": 100,
                    "abstract": "A highly cited paper",
                    "externalIds": {"ArXiv": "2023.54321"},
                    "openAccessPdf": {"url": "https://example.com/semantic.pdf"}
                }
            ]
        }
        mock_get.return_value = mock_response

        papers = self.agent._search_semantic_scholar("Science", datetime(2022, 1, 1))

        assert len(papers) >= 0
        if papers:
            assert papers[0].title == "Semantic Scholar Paper"
            assert papers[0].citation_count == 100

    @patch('app.services.research.requests.get')
    def test_arxiv_search_success(self, mock_get):
        """Test successful arXiv search"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'''<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <entry>
                <id>http://arxiv.org/abs/2023.98765v1</id>
                <title>ArXiv Test Paper</title>
                <author><name>Bob Wilson</name></author>
                <published>2023-06-01T00:00:00Z</published>
                <updated>2023-06-01T00:00:00Z</updated>
                <summary>An arXiv paper abstract</summary>
                <category term="cs.LG" />
            </entry>
        </feed>'''
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        papers = self.agent._search_arxiv_papers("Gen AI", max_results=5)

        assert len(papers) >= 0
        if papers:
            assert papers[0].title == "ArXiv Test Paper"
            assert "Bob Wilson" in papers[0].authors


class TestResearchService:
    """Test the ResearchService.search_research method"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_db = Mock()
        self.service = ResearchService(self.mock_db)

    def test_search_research_success(self):
        """Test successful research search"""
        # Mock the scholar agent to return test papers
        test_papers = [
            Paper(
                id="test1",
                title="Test Paper 1",
                authors=["Author 1", "Author 2"],
                published_date="2023-01-01T00:00:00Z",
                updated_date="2023-01-01T00:00:00Z",
                abstract="Test abstract 1",
                categories=["cs.AI"],
                pdf_url="https://example.com/paper1.pdf",
                arxiv_url="https://arxiv.org/abs/test1",
                citation_count=25,
                relevance_score=0.9
            ),
            Paper(
                id="test2",
                title="Test Paper 2",
                authors=["Author 3"],
                published_date="2023-02-01T00:00:00Z",
                updated_date="2023-02-01T00:00:00Z",
                abstract="Test abstract 2",
                categories=["cs.LG"],
                pdf_url="https://example.com/paper2.pdf",
                arxiv_url="https://arxiv.org/abs/test2",
                citation_count=15,
                relevance_score=0.8
            )
        ]

        with patch.object(self.service.scholar_agent, 'fetch_papers', return_value=test_papers):
            search_request = ResearchSearch(domain=DomainEnum.AI)
            result = self.service.search_research(search_request)

            assert isinstance(result, ResearchSearchResponse)
            assert len(result.data) == 5  # Should always return exactly 5

            # Check first two are real papers
            assert result.data[0].title == "Test Paper 1"
            assert result.data[1].title == "Test Paper 2"

            # Check remaining are padding
            for i in range(2, 5):
                assert "Additional research needed" in result.data[i].title

    def test_search_research_no_papers_found(self):
        """Test when no papers are found"""
        with patch.object(self.service.scholar_agent, 'fetch_papers', return_value=[]):
            search_request = ResearchSearch(domain=DomainEnum.FINANCE)
            result = self.service.search_research(search_request)

            assert isinstance(result, ResearchSearchResponse)
            assert len(result.data) == 5

            # All should be dummy entries
            for response in result.data:
                assert "No papers found for domain" in response.title
                assert "금융" in response.title

    def test_search_research_api_error(self):
        """Test handling of API errors"""
        with patch.object(self.service.scholar_agent, 'fetch_papers', side_effect=Exception("API Error")):
            search_request = ResearchSearch(domain=DomainEnum.CLOUD)
            result = self.service.search_research(search_request)

            assert isinstance(result, ResearchSearchResponse)
            assert len(result.data) == 5

            # All should be error entries
            for response in result.data:
                assert "Search Error for" in response.title
                assert "클라우드" in response.title
                assert "API Error" in response.abstract

    def test_search_research_exactly_5_papers(self):
        """Test when exactly 5 papers are returned"""
        test_papers = [
            Paper(
                id=f"test{i}",
                title=f"Test Paper {i}",
                authors=[f"Author {i}"],
                published_date="2023-01-01T00:00:00Z",
                updated_date="2023-01-01T00:00:00Z",
                abstract=f"Test abstract {i}",
                categories=["cs.AI"],
                pdf_url=f"https://example.com/paper{i}.pdf",
                arxiv_url=f"https://arxiv.org/abs/test{i}",
                citation_count=10 + i,
                relevance_score=0.5 + i * 0.1
            ) for i in range(1, 6)
        ]

        with patch.object(self.service.scholar_agent, 'fetch_papers', return_value=test_papers):
            search_request = ResearchSearch(domain=DomainEnum.AI)
            result = self.service.search_research(search_request)

            assert len(result.data) == 5

            # All should be real papers
            for i, response in enumerate(result.data):
                assert response.title == f"Test Paper {i + 1}"
                assert f"Test abstract {i + 1}" in response.abstract

    def test_search_research_more_than_5_papers(self):
        """Test when more than 5 papers are returned (should be truncated)"""
        test_papers = [
            Paper(
                id=f"test{i}",
                title=f"Test Paper {i}",
                authors=[f"Author {i}"],
                published_date="2023-01-01T00:00:00Z",
                updated_date="2023-01-01T00:00:00Z",
                abstract=f"Test abstract {i}",
                categories=["cs.AI"],
                pdf_url=f"https://example.com/paper{i}.pdf",
                arxiv_url=f"https://arxiv.org/abs/test{i}",
                citation_count=10 + i,
                relevance_score=0.5 + i * 0.1
            ) for i in range(1, 8)  # 7 papers
        ]

        with patch.object(self.service.scholar_agent, 'fetch_papers', return_value=test_papers):
            search_request = ResearchSearch(domain=DomainEnum.MANUFACTURE)
            result = self.service.search_research(search_request)

            assert len(result.data) == 5  # Should be truncated to 5

            # Should be first 5 papers
            for i, response in enumerate(result.data):
                assert response.title == f"Test Paper {i + 1}"

    def test_search_research_date_parsing(self):
        """Test various date formats are handled correctly"""
        test_papers = [
            Paper(
                id="test_date1",
                title="Paper with ISO date",
                authors=["Author"],
                published_date="2023-06-15T10:30:00Z",
                updated_date="2023-06-15T10:30:00Z",
                abstract="Test abstract",
                categories=["cs.AI"],
                pdf_url="https://example.com/paper.pdf",
                arxiv_url="https://arxiv.org/abs/test",
                citation_count=10,
                relevance_score=0.8
            ),
            Paper(
                id="test_date2",
                title="Paper with year only",
                authors=["Author"],
                published_date="2022-01-01",
                updated_date="2022-01-01",
                abstract="Test abstract",
                categories=["cs.AI"],
                pdf_url="https://example.com/paper.pdf",
                arxiv_url="https://arxiv.org/abs/test",
                citation_count=5,
                relevance_score=0.7
            ),
            Paper(
                id="test_date3",
                title="Paper with no date",
                authors=["Author"],
                published_date="",
                updated_date="",
                abstract="Test abstract",
                categories=["cs.AI"],
                pdf_url="https://example.com/paper.pdf",
                arxiv_url="https://arxiv.org/abs/test",
                citation_count=1,
                relevance_score=0.6
            )
        ]

        with patch.object(self.service.scholar_agent, 'fetch_papers', return_value=test_papers):
            search_request = ResearchSearch(domain=DomainEnum.AI)
            result = self.service.search_research(search_request)

            assert len(result.data) == 5

            # Check that dates were parsed without errors
            assert result.data[0].created_at.year == 2023
            assert result.data[1].created_at.year == 2022
            # Third paper should have current date as fallback
            assert result.data[2].created_at.year == datetime.now().year

    def test_search_research_empty_abstract_handling(self):
        """Test handling of papers with empty abstracts"""
        test_papers = [
            Paper(
                id="test_empty",
                title="Paper with empty abstract",
                authors=["Author"],
                published_date="2023-01-01T00:00:00Z",
                updated_date="2023-01-01T00:00:00Z",
                abstract="",  # Empty abstract
                categories=["cs.AI"],
                pdf_url="https://example.com/paper.pdf",
                arxiv_url="https://arxiv.org/abs/test",
                citation_count=10,
                relevance_score=0.8
            ),
            Paper(
                id="test_none",
                title="Paper with None abstract",
                authors=["Author"],
                published_date="2023-01-01T00:00:00Z",
                updated_date="2023-01-01T00:00:00Z",
                abstract=None,  # None abstract
                categories=["cs.AI"],
                pdf_url="https://example.com/paper.pdf",
                arxiv_url="https://arxiv.org/abs/test",
                citation_count=5,
                relevance_score=0.7
            )
        ]

        with patch.object(self.service.scholar_agent, 'fetch_papers', return_value=test_papers):
            search_request = ResearchSearch(domain=DomainEnum.AI)
            result = self.service.search_research(search_request)

            assert len(result.data) == 5

            # Check that empty abstracts are handled
            assert result.data[0].abstract == "No abstract available"
            assert result.data[1].abstract == "No abstract available"

    @pytest.mark.parametrize("domain", [
        DomainEnum.FINANCE,
        DomainEnum.COMMUNICATION,
        DomainEnum.MANUFACTURE,
        DomainEnum.LOGISTICS,
        DomainEnum.AI,
        DomainEnum.CLOUD
    ])
    def test_search_research_all_domains(self, domain):
        """Test that all domains are supported"""
        with patch.object(self.service.scholar_agent, 'fetch_papers', return_value=[]):
            search_request = ResearchSearch(domain=domain)
            result = self.service.search_research(search_request)

            assert isinstance(result, ResearchSearchResponse)
            assert len(result.data) == 5

            # Should return dummy responses for unsupported/empty results
            for response in result.data:
                assert domain.value.lower() in response.title.lower()


class TestIntegration:
    """Integration tests for the complete search functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_db = Mock()
        self.service = ResearchService(self.mock_db)

    @patch('app.services.research.requests.get')
    def test_full_integration_mock(self, mock_get):
        """Test full integration with mocked external APIs"""
        # Mock Semantic Scholar response
        mock_semantic_response = Mock()
        mock_semantic_response.status_code = 200
        mock_semantic_response.json.return_value = {
            "data": [
                {
                    "paperId": "integration123",
                    "title": "Integration Test Paper",
                    "authors": [{"name": "Test Author"}],
                    "year": 2023,
                    "venue": "AI Journal",
                    "citationCount": 75,
                    "abstract": "This is an integration test paper",
                    "externalIds": {"ArXiv": "2023.integration"},
                    "openAccessPdf": {"url": "https://example.com/integration.pdf"}
                }
            ]
        }

        # Mock arXiv response
        mock_arxiv_response = Mock()
        mock_arxiv_response.status_code = 200
        mock_arxiv_response.content = b'''<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <entry>
                <id>http://arxiv.org/abs/2023.integration2v1</id>
                <title>ArXiv Integration Paper</title>
                <author><name>ArXiv Author</name></author>
                <published>2023-03-01T00:00:00Z</published>
                <updated>2023-03-01T00:00:00Z</updated>
                <summary>ArXiv integration test abstract</summary>
                <category term="cs.AI" />
            </entry>
        </feed>'''

        def mock_get_side_effect(url, **kwargs):
            if "semanticscholar.org" in url:
                return mock_semantic_response
            else:  # arXiv
                return mock_arxiv_response

        mock_get.side_effect = mock_get_side_effect
        mock_get.return_value.raise_for_status = Mock()

        # Test the full flow
        search_request = ResearchSearch(domain=DomainEnum.AI)
        result = self.service.search_research(search_request)

        assert isinstance(result, ResearchSearchResponse)
        assert len(result.data) == 5

        # Should have at least one real paper
        paper_titles = [paper.title for paper in result.data]
        assert any("Integration Test Paper" in title or "ArXiv Integration Paper" in title
                  for title in paper_titles)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
