#!/usr/bin/env python3
"""
Pytest tests for PDF download and file serving functionality
Tests the /research_download and /research/files/{filename} endpoints
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests
from fastapi.testclient import TestClient

from app.main import app


class TestPDFDownloadEndpoint:
    """Test PDF download endpoint"""

    def setup_method(self):
        """Set up test fixtures"""
        self.client = TestClient(app)
        self.output_dir = Path("output/research")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        """Clean up test files"""
        # Clean up any test PDFs created during tests
        if self.output_dir.exists():
            for file in self.output_dir.glob("Test_*.pdf"):
                file.unlink()

    @patch("app.services.research.requests.get")
    def test_download_research_success(self, mock_get):
        """Test successful PDF download"""
        # Mock the PDF content
        mock_pdf_content = b"%PDF-1.4\n%EOF"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/pdf"}
        mock_response.iter_content = lambda chunk_size: [mock_pdf_content]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Make the request
        response = self.client.post(
            "/research_download",
            json={
                "pdf_url": "https://arxiv.org/pdf/2304.04949v1.pdf",
                "arxiv_url": "https://arxiv.org/abs/2304.04949v1",
                "title": "Test Paper Download",
            },
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "output_path" in data
        assert "download_url" in data
        assert "filename" in data
        assert data["filename"] == "Test_Paper_Download.pdf"
        assert data["download_url"] == "/research/files/Test_Paper_Download.pdf"
        assert "output/research/Test_Paper_Download.pdf" in data["output_path"]

        # Verify the file was created
        file_path = self.output_dir / "Test_Paper_Download.pdf"
        assert file_path.exists()
        assert file_path.stat().st_size > 0

    @patch("app.services.research.requests.get")
    def test_download_research_with_special_characters_in_title(self, mock_get):
        """Test PDF download with special characters in title"""
        mock_pdf_content = b"%PDF-1.4\n%EOF"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/pdf"}
        mock_response.iter_content = lambda chunk_size: [mock_pdf_content]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        response = self.client.post(
            "/research_download",
            json={
                "pdf_url": "https://arxiv.org/pdf/2304.04949v1.pdf",
                "arxiv_url": "https://arxiv.org/abs/2304.04949v1",
                "title": "Test: Paper! with @Special #Characters & More",
            },
        )

        assert response.status_code == 200
        data = response.json()
        # Special characters should be removed
        assert "Test_Paper_with_Special_Characters_More" in data["filename"]

    @patch("app.services.research.requests.get")
    def test_download_research_cached_file(self, mock_get):
        """Test that cached files are not re-downloaded"""
        # Create a cached file first
        test_file = self.output_dir / "Test_Cached_Paper.pdf"
        test_file.write_bytes(b"%PDF-1.4\n%EOF")

        # Make request without mocking requests.get since it shouldn't be called
        response = self.client.post(
            "/research_download",
            json={
                "pdf_url": "https://arxiv.org/pdf/2304.04949v1.pdf",
                "arxiv_url": "https://arxiv.org/abs/2304.04949v1",
                "title": "Test Cached Paper",
            },
        )

        # Should return success without downloading
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "Test_Cached_Paper.pdf"
        # mock_get should not have been called
        mock_get.assert_not_called()

    @patch("app.services.research.requests.get")
    def test_download_research_without_title(self, mock_get):
        """Test PDF download using arXiv ID as filename when no title provided"""
        mock_pdf_content = b"%PDF-1.4\n%EOF"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/pdf"}
        mock_response.iter_content = lambda chunk_size: [mock_pdf_content]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        response = self.client.post(
            "/research_download",
            json={
                "pdf_url": "https://arxiv.org/pdf/2304.04949v1.pdf",
                "arxiv_url": "https://arxiv.org/abs/2304.04949v1",
                # No title provided
            },
        )

        assert response.status_code == 200
        data = response.json()
        # Should use arXiv ID
        assert "2304.04949v1" in data["filename"]

    @patch("app.services.research.requests.get")
    def test_download_research_missing_pdf_url(self, mock_get):
        """Test PDF download with missing PDF URL"""
        response = self.client.post(
            "/research_download",
            json={
                "arxiv_url": "https://arxiv.org/abs/2304.04949v1",
                "title": "Test Paper",
                # pdf_url is missing
            },
        )

        # Should return 422 for validation error
        assert response.status_code == 422

    @patch("app.services.research.requests.get")
    def test_download_research_timeout(self, mock_get):
        """Test PDF download with timeout"""
        mock_get.side_effect = requests.exceptions.Timeout()

        # Use try-except since FastAPI will wrap the ValueError in an HTTP exception
        with pytest.raises(
            Exception
        ):  # Will raise ValueError wrapped in HTTP exception
            self.client.post(
                "/research_download",
                json={
                    "pdf_url": "https://arxiv.org/pdf/2304.04949v1.pdf",
                    "arxiv_url": "https://arxiv.org/abs/2304.04949v1",
                    "title": "Test Timeout",
                },
            )

    @patch("app.services.research.requests.get")
    def test_download_research_invalid_pdf(self, mock_get):
        """Test PDF download with invalid PDF content"""
        # Mock HTML content instead of PDF
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/html"}
        # Fix: iter_content should return an iterator, not a list
        mock_response.iter_content = lambda chunk_size: iter(
            [b"<html>Not a PDF</html>"]
        )
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Should raise an exception since the content is not a valid PDF
        with pytest.raises(
            Exception
        ):  # Will raise ValueError wrapped in HTTP exception
            self.client.post(
                "/research_download",
                json={
                    "pdf_url": "https://example.com/not-a-pdf",
                    "arxiv_url": "https://arxiv.org/abs/2304.04949v1",
                    "title": "Test Invalid PDF",
                },
            )


class TestPDFFileServingEndpoint:
    """Test PDF file serving endpoint"""

    def setup_method(self):
        """Set up test fixtures"""
        self.client = TestClient(app)
        self.output_dir = Path("output/research")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        """Clean up test files"""
        # Clean up any test PDFs created during tests
        test_files = [
            "test_serve_pdf.pdf",
            "test_headers.pdf",
            "test_file.txt",
            "../../../etc/passwd",
        ]
        for filename in test_files:
            file_path = self.output_dir / filename
            if file_path.exists():
                file_path.unlink()

    def test_serve_pdf_success(self):
        """Test successfully serving a PDF file"""
        # Create a test PDF file
        test_file = self.output_dir / "test_serve_pdf.pdf"
        test_content = b"%PDF-1.4\nTest PDF Content\n%EOF"
        test_file.write_bytes(test_content)

        # Request the file
        response = self.client.get("/research/files/test_serve_pdf.pdf")

        # Assertions
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "content-disposition" in response.headers
        assert (
            'filename="test_serve_pdf.pdf"' in response.headers["content-disposition"]
        )
        assert response.content == test_content

    def test_serve_pdf_not_found(self):
        """Test serving a non-existent PDF file"""
        response = self.client.get("/research/files/nonexistent.pdf")

        assert response.status_code == 404
        assert response.json()["detail"] == "File not found"

    def test_serve_pdf_path_traversal_attempt(self):
        """Test that path traversal attempts are blocked"""
        # Try to access a file outside the output/research directory
        response = self.client.get("/research/files/../../../etc/passwd")

        # Should be blocked
        assert response.status_code in [403, 404]

    def test_serve_pdf_double_dot_in_filename(self):
        """Test that double dots in filename are handled securely"""
        response = self.client.get("/research/files/../../test.pdf")

        # Should be blocked
        assert response.status_code in [403, 404]

    def test_serve_non_pdf_file(self):
        """Test that non-PDF files are rejected"""
        # Create a non-PDF file
        test_file = self.output_dir / "test_file.txt"
        test_file.write_text("Not a PDF")

        # Try to download it
        response = self.client.get("/research/files/test_file.txt")

        # Should be rejected
        assert response.status_code == 400
        assert response.json()["detail"] == "Only PDF files are allowed"

    def test_serve_pdf_proper_headers(self):
        """Test that proper download headers are set"""
        # Create a test PDF
        test_file = self.output_dir / "test_headers.pdf"
        test_file.write_bytes(b"%PDF-1.4\n%EOF")

        response = self.client.get("/research/files/test_headers.pdf")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "content-disposition" in response.headers
        # Check that it's set as attachment for download
        assert "attachment" in response.headers["content-disposition"]

    def test_serve_pdf_with_spaces_in_filename(self):
        """Test serving a PDF with spaces in filename"""
        # Create a test PDF with spaces
        test_file = self.output_dir / "test file with spaces.pdf"
        test_file.write_bytes(b"%PDF-1.4\n%EOF")

        # URL encode the spaces
        response = self.client.get("/research/files/test%20file%20with%20spaces.pdf")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    def test_serve_pdf_case_insensitive_extension(self):
        """Test that .PDF (uppercase) extension is also accepted"""
        # Create a test PDF with uppercase extension
        test_file = self.output_dir / "test_uppercase.PDF"
        test_file.write_bytes(b"%PDF-1.4\n%EOF")

        response = self.client.get("/research/files/test_uppercase.PDF")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"


class TestPDFDownloadIntegration:
    """Integration tests for the complete download flow"""

    def setup_method(self):
        """Set up test fixtures"""
        self.client = TestClient(app)
        self.output_dir = Path("output/research")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        """Clean up test files"""
        if self.output_dir.exists():
            for file in self.output_dir.glob("Integration_Test_*.pdf"):
                file.unlink()

    @patch("app.services.research.requests.get")
    def test_full_download_and_serve_flow(self, mock_get):
        """Test the complete flow: download then serve"""
        # Step 1: Mock PDF download
        mock_pdf_content = b"%PDF-1.4\nIntegration Test Content\n%EOF"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/pdf"}
        mock_response.iter_content = lambda chunk_size: [mock_pdf_content]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Step 2: Download the PDF
        download_response = self.client.post(
            "/research_download",
            json={
                "pdf_url": "https://arxiv.org/pdf/2304.04949v1.pdf",
                "arxiv_url": "https://arxiv.org/abs/2304.04949v1",
                "title": "Integration Test Paper",
            },
        )

        assert download_response.status_code == 200
        download_data = download_response.json()
        download_url = download_data["download_url"]
        filename = download_data["filename"]

        # Step 3: Serve the downloaded PDF
        serve_response = self.client.get(download_url)

        assert serve_response.status_code == 200
        assert serve_response.headers["content-type"] == "application/pdf"
        assert serve_response.content == mock_pdf_content
        assert f'filename="{filename}"' in serve_response.headers["content-disposition"]

    @patch("app.services.research.requests.get")
    def test_cors_headers_on_file_serving(self, mock_get):
        """Test that CORS headers are properly set for file serving"""
        # Create a test PDF
        test_file = self.output_dir / "Integration_Test_CORS.pdf"
        test_file.write_bytes(b"%PDF-1.4\n%EOF")

        # Request with Origin header
        response = self.client.get(
            "/research/files/Integration_Test_CORS.pdf",
            headers={"Origin": "http://localhost:3000"},
        )

        assert response.status_code == 200
        # CORS headers should be present due to global CORS middleware
        assert "access-control-allow-origin" in response.headers


class TestPDFResponseSchema:
    """Test the ResearchDownloadResponse schema"""

    def setup_method(self):
        """Set up test fixtures"""
        self.client = TestClient(app)
        self.output_dir = Path("output/research")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        """Clean up test files"""
        if self.output_dir.exists():
            for file in self.output_dir.glob("Schema_Test_*.pdf"):
                file.unlink()

    @patch("app.services.research.requests.get")
    def test_response_schema_has_all_required_fields(self, mock_get):
        """Test that response includes all required fields"""
        mock_pdf_content = b"%PDF-1.4\n%EOF"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/pdf"}
        mock_response.iter_content = lambda chunk_size: [mock_pdf_content]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        response = self.client.post(
            "/research_download",
            json={
                "pdf_url": "https://arxiv.org/pdf/2304.04949v1.pdf",
                "arxiv_url": "https://arxiv.org/abs/2304.04949v1",
                "title": "Schema Test Paper",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Check all required fields are present
        required_fields = ["output_path", "download_url", "filename"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
            assert data[field], f"Field {field} should not be empty"

    @patch("app.services.research.requests.get")
    def test_download_url_format(self, mock_get):
        """Test that download_url has correct format"""
        mock_pdf_content = b"%PDF-1.4\n%EOF"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/pdf"}
        mock_response.iter_content = lambda chunk_size: [mock_pdf_content]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        response = self.client.post(
            "/research_download",
            json={
                "pdf_url": "https://arxiv.org/pdf/2304.04949v1.pdf",
                "arxiv_url": "https://arxiv.org/abs/2304.04949v1",
                "title": "URL Format Test",
            },
        )

        data = response.json()
        download_url = data["download_url"]

        # URL should start with /research/files/
        assert download_url.startswith("/research/files/")
        # URL should end with .pdf
        assert download_url.endswith(".pdf")
        # Filename in URL should match filename field
        assert data["filename"] in download_url
