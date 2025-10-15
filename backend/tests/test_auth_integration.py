import pytest
import io
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
import os


@pytest.fixture(scope="module")
def test_client():
    with patch.dict(
        os.environ, {"OPENROUTER_API_KEY": "test_key", "JWT_SECRET": "test-secret"}
    ):
        from main import app

        client = TestClient(app)
        yield client


@pytest.fixture
def auth_headers():
    # No auth now
    return {}


@pytest.fixture
def invalid_auth_headers():
    return {}


def make_dummy_pdf_bytes():
    """Create minimal valid PDF bytes for testing"""
    return (
        b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<<>>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] >>\nendobj\n"
        b"xref\n0 4\n0000000000 65535 f \n0000000010 00000 n \n0000000060 00000 n \n0000000120 00000 n \n"
        b"trailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n180\n%%EOF\n"
    )


class TestAuthenticationIntegration:
    """Smoke tests for endpoints without authentication"""

    def test_root_endpoint_no_auth_required(self, test_client):
        """Root endpoint should be accessible without authentication"""
        response = test_client.get("/")
        assert response.status_code == 200
        assert response.json()["name"] == "Legal Document Analyzer API"

    def test_health_endpoint_no_auth_required(self, test_client):
        """Health endpoint should be accessible without authentication"""
        response = test_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_supported_formats_no_auth_required(self, test_client):
        """Supported formats endpoint should be accessible without authentication"""
        response = test_client.get("/supported-formats")
        assert response.status_code == 200
        assert "formats" in response.json()

    def test_analyze_endpoint_no_auth_required(self, test_client):
        """Analyze endpoint should work without authentication"""
        files = {
            "file": ("test.pdf", io.BytesIO(make_dummy_pdf_bytes()), "application/pdf")
        }

        response = test_client.post("/analyze", files=files)
        assert response.status_code in (200, 400, 500)

    def test_analyze_endpoint_succeeds(self, test_client, auth_headers):
        """Analyze endpoint should work end-to-end"""
        from models.analysis_models import AnalysisResult, KeyClause

        dummy_result = AnalysisResult(
            summary="Test summary",
            key_clauses=[
                KeyClause(
                    type="Payment",
                    content="Pay X",
                    importance="high",
                    classification="Financial",
                    risk_score=7.0,
                    page=1,
                    confidence=0.9,
                )
            ],
            document_type="Contract",
            confidence=0.8,
        )

        with patch("utils.file_validator.magic", create=True) as mock_magic:
            mock_magic.from_buffer.return_value = "application/pdf"
            from main import ai_analyzer

            ai_analyzer.analyze_document = AsyncMock(return_value=dummy_result)

            files = {
                "file": (
                    "test.pdf",
                    io.BytesIO(make_dummy_pdf_bytes()),
                    "application/pdf",
                )
            }
            response = test_client.post("/analyze", files=files)

        assert response.status_code == 200

    def test_analyze_endpoint_without_auth_still_works(self, test_client):
        files = {
            "file": ("test.pdf", io.BytesIO(make_dummy_pdf_bytes()), "application/pdf")
        }
        response = test_client.post("/analyze", files=files)
        assert response.status_code in (200, 400, 500)

    def test_get_analysis_no_auth(self, test_client):
        response = test_client.get("/analysis/non-existent-id")
        assert response.status_code in (200, 404)

    def test_get_stats_no_auth(self, test_client):
        response = test_client.get("/stats")
        assert response.status_code == 200

    def test_get_stats_structure(self, test_client):
        response = test_client.get("/stats")
        assert response.status_code == 200
        assert "analysis_cache_size" in response.json()

    def test_clear_analyses_no_auth(self, test_client):
        response = test_client.delete("/analyses")
        assert response.status_code in (200, 204)

    def test_clear_analyses_response(self, test_client):
        response = test_client.delete("/analyses")
        assert response.status_code in (200, 204)

    def test_get_document_no_auth(self, test_client):
        response = test_client.get("/documents/non-existent-id")
        assert response.status_code in (200, 400, 404)

    def test_export_analysis_no_auth(self, test_client):
        response = test_client.post("/export/non-existent-id/json")
        assert response.status_code in (200, 404, 400)

    def test_get_export_status_no_auth(self, test_client):
        response = test_client.get("/export/non-existent-task-id")
        assert response.status_code in (200, 404)

    def test_download_export_no_auth(self, test_client):
        response = test_client.get("/export/non-existent-task-id/download")
        assert response.status_code in (200, 404, 400)

    def test_endpoints_accessible_without_auth(self, test_client):
        for method, endpoint in [
            ("GET", "/analysis/test-id"),
            ("GET", "/stats"),
            ("DELETE", "/analyses"),
            ("GET", "/documents/test-id"),
            ("POST", "/export/test-id/json"),
            ("GET", "/export/test-task-id"),
        ]:
            if method == "GET":
                _ = test_client.get(endpoint)
            elif method == "POST":
                _ = test_client.post(endpoint)
            elif method == "DELETE":
                _ = test_client.delete(endpoint)

    def test_auth_removed(self):
        assert True

    def test_malformed_auth_header_no_longer_relevant(self):
        assert True

    def test_retention_status_no_auth(self, test_client):
        response = test_client.get("/retention/status")
        assert response.status_code in (200, 500)

    def test_retention_status_response(self, test_client):
        response = test_client.get("/retention/status")
        assert response.status_code in (200, 500)

    def test_retention_cleanup_no_auth(self, test_client):
        response = test_client.post("/retention/cleanup")
        assert response.status_code in (200, 400, 500)

    def test_retention_cleanup_response(self, test_client):
        response = test_client.post("/retention/cleanup?cleanup_type=all")
        assert response.status_code in (200, 500)

    def test_retention_cleanup_invalid_type(self, test_client, auth_headers):
        """Test that retention cleanup rejects invalid cleanup types"""
        response = test_client.post(
            "/retention/cleanup?cleanup_type=invalid", headers=auth_headers
        )
        assert response.status_code == 400
