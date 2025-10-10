#!/usr/bin/env python3
"""
Pytest tests for CORS configuration
Tests that the FastAPI application properly handles CORS requests from localhost:3000
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestCORSConfiguration:
    """Test CORS middleware configuration"""

    def setup_method(self):
        """Set up test fixtures"""
        self.client = TestClient(app)
        self.frontend_origin = "http://localhost:3000"

    def test_cors_preflight_request(self):
        """Test CORS preflight OPTIONS request"""
        response = self.client.options(
            "/",
            headers={
                "Origin": self.frontend_origin,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )

        # Preflight requests should return 200
        assert response.status_code == 200

        # Check CORS headers are present
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == self.frontend_origin
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers

    def test_cors_simple_get_request(self):
        """Test simple GET request with CORS headers"""
        response = self.client.get(
            "/",
            headers={"Origin": self.frontend_origin},
        )

        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == self.frontend_origin

    def test_cors_allows_credentials(self):
        """Test that credentials are allowed"""
        response = self.client.get(
            "/",
            headers={"Origin": self.frontend_origin},
        )

        assert response.status_code == 200
        assert "access-control-allow-credentials" in response.headers
        assert response.headers["access-control-allow-credentials"] == "true"

    def test_cors_post_request(self):
        """Test POST request with CORS headers"""
        response = self.client.post(
            "/",
            headers={
                "Origin": self.frontend_origin,
                "Content-Type": "application/json",
            },
            json={"test": "data"},
        )

        # Even if endpoint doesn't exist, CORS headers should be present
        assert "access-control-allow-origin" in response.headers

    def test_cors_with_different_origin(self):
        """Test that requests from non-allowed origins are handled"""
        different_origin = "http://localhost:4000"

        response = self.client.get(
            "/",
            headers={"Origin": different_origin},
        )

        # Request should still succeed (CORS is a browser-level security)
        # But the Access-Control-Allow-Origin should not match the different origin
        assert response.status_code == 200

        # The CORS middleware will either not include the header or include only allowed origins
        if "access-control-allow-origin" in response.headers:
            assert response.headers["access-control-allow-origin"] != different_origin

    def test_cors_preflight_post_request(self):
        """Test CORS preflight for POST requests"""
        response = self.client.options(
            "/api/research/search",
            headers={
                "Origin": self.frontend_origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )

        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers

        # Check that POST is in allowed methods
        allowed_methods = response.headers.get("access-control-allow-methods", "")
        assert "POST" in allowed_methods.upper()

    def test_cors_preflight_with_custom_headers(self):
        """Test CORS preflight with custom headers"""
        response = self.client.options(
            "/",
            headers={
                "Origin": self.frontend_origin,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization,Content-Type,X-Custom-Header",
            },
        )

        assert response.status_code == 200
        assert "access-control-allow-headers" in response.headers

        # Since we allow all headers with ["*"], custom headers should be allowed
        allowed_headers = response.headers.get("access-control-allow-headers", "")
        assert allowed_headers  # Should have some value

    def test_cors_actual_api_endpoint(self):
        """Test CORS on an actual API endpoint"""
        response = self.client.get(
            "/",
            headers={"Origin": self.frontend_origin},
        )

        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == self.frontend_origin

        # Check response data
        data = response.json()
        assert data["message"] == "Hello, FastAPI with uv!"

    def test_cors_all_http_methods(self):
        """Test CORS works with various HTTP methods"""
        methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]

        for method in methods:
            # Test preflight
            response = self.client.options(
                "/",
                headers={
                    "Origin": self.frontend_origin,
                    "Access-Control-Request-Method": method,
                },
            )

            assert response.status_code == 200
            assert "access-control-allow-origin" in response.headers
            allowed_methods = response.headers.get("access-control-allow-methods", "")
            # All methods should be allowed since we use ["*"]
            assert method in allowed_methods.upper()

    def test_cors_without_origin_header(self):
        """Test request without Origin header (non-CORS request)"""
        response = self.client.get("/")

        # Should still work, just without CORS headers
        assert response.status_code == 200
        # CORS headers might not be present for same-origin requests

    def test_cors_headers_case_insensitive(self):
        """Test CORS with various header casing"""
        response = self.client.get(
            "/",
            headers={
                "origin": self.frontend_origin,  # lowercase
            },
        )

        assert response.status_code == 200
        # Headers in response are case-insensitive, so we check lowercase
        assert "access-control-allow-origin" in response.headers


class TestCORSWithSpecificEndpoints:
    """Test CORS on specific application endpoints"""

    def setup_method(self):
        """Set up test fixtures"""
        self.client = TestClient(app)
        self.frontend_origin = "http://localhost:3000"

    def test_cors_on_root_endpoint(self):
        """Test CORS on root endpoint"""
        response = self.client.get(
            "/",
            headers={"Origin": self.frontend_origin},
        )

        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == self.frontend_origin
        assert response.json() == {"message": "Hello, FastAPI with uv!"}

    def test_cors_preflight_on_research_endpoint(self):
        """Test CORS preflight on research endpoint"""
        response = self.client.options(
            "/api/research/search",
            headers={
                "Origin": self.frontend_origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )

        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == self.frontend_origin

    def test_cors_with_complex_request(self):
        """Test CORS with a complex request including custom headers"""
        response = self.client.options(
            "/api/research/search",
            headers={
                "Origin": self.frontend_origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type,Authorization,X-Requested-With",
            },
        )

        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == self.frontend_origin
        assert "access-control-allow-credentials" in response.headers


class TestCORSSecurityScenarios:
    """Test CORS security scenarios"""

    def setup_method(self):
        """Set up test fixtures"""
        self.client = TestClient(app)

    def test_allowed_origin_localhost_3000(self):
        """Test that localhost:3000 is explicitly allowed"""
        response = self.client.get(
            "/",
            headers={"Origin": "http://localhost:3000"},
        )

        assert response.status_code == 200
        assert (
            response.headers["access-control-allow-origin"] == "http://localhost:3000"
        )

    def test_127_0_0_1_origin_not_explicitly_allowed(self):
        """Test that 127.0.0.1 is different from localhost"""
        response = self.client.get(
            "/",
            headers={"Origin": "http://127.0.0.1:3000"},
        )

        # Request succeeds but CORS header won't match if not in allowed origins
        assert response.status_code == 200

        # Should not get the 127.0.0.1 origin back if not in allowed list
        if "access-control-allow-origin" in response.headers:
            origin = response.headers["access-control-allow-origin"]
            # It should either be the allowed origin or not present
            assert (
                origin != "http://127.0.0.1:3000" or origin == "http://localhost:3000"
            )

    def test_random_origin_not_allowed(self):
        """Test that random origins are not allowed"""
        response = self.client.get(
            "/",
            headers={"Origin": "http://evil-site.com"},
        )

        assert response.status_code == 200

        # Should not get the evil origin back
        if "access-control-allow-origin" in response.headers:
            assert (
                response.headers["access-control-allow-origin"]
                != "http://evil-site.com"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
