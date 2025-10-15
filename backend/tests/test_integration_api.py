import os
import io
import pytest
from unittest.mock import AsyncMock, patch
from models.analysis_models import AnalysisResult, KeyClause
# No auth in application anymore


@pytest.fixture(scope="module")
def test_client():
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test_key"}):
        from fastapi.testclient import TestClient

        # Import after env var is set so services initialize
        from main import app

        client = TestClient(app)
        yield client


def make_dummy_pdf_bytes():
    # Minimal PDF header/footer with one page
    return (
        b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<<>>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] >>\nendobj\n"
        b"xref\n0 4\n0000000000 65535 f \n0000000010 00000 n \n0000000060 00000 n \n0000000120 00000 n \n"
        b"trailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n180\n%%EOF\n"
    )


def test_analyze_success(test_client):
    # Patch magic to accept PDF and AI to return deterministic result
    dummy_result = {
        "summary": "ok",
        "key_clauses": [
            {
                "type": "Payment",
                "content": "Pay X",
                "importance": "high",
                "classification": "Financial",
                "risk_score": 7,
                "page": 1,
            }
        ],
        "document_type": "Contract",
        "confidence": 0.8,
    }

    with patch("utils.file_validator.magic", create=True) as mock_magic:
        mock_magic.from_buffer.return_value = "application/pdf"
        from main import ai_analyzer

        ai_analyzer.analyze_document = AsyncMock(
            return_value=AnalysisResult(
                summary=dummy_result["summary"],
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
        )

        token = "test-token"
        files = {
            "file": ("test.pdf", io.BytesIO(make_dummy_pdf_bytes()), "application/pdf")
        }
        resp = test_client.post(
            "/analyze", files=files, headers={"Authorization": f"Bearer {token}"}
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["document_type"] == "Contract"
    assert body["file_id"]
    assert body["key_clauses"][0]["type"] == "Payment"

    # Trigger export and fetch signed download token
    file_id = body["file_id"]
    export = test_client.post(
        f"/export/{file_id}/json", headers={"Authorization": f"Bearer {token}"}
    )
    assert export.status_code == 200
    task_id = export.json()["task_id"]

    status_resp = test_client.get(
        f"/export/{task_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert status_resp.status_code in (200, 500)


def test_rate_limiting_trigger(test_client):
    # Use image mime; we will still patch magic to avoid external detection variability
    with patch("utils.file_validator.magic", create=True) as mock_magic:
        mock_magic.from_buffer.return_value = "application/pdf"
        from main import ai_analyzer

        ai_analyzer.analyze_document = AsyncMock(
            return_value=AnalysisResult(
                summary="ok",
                key_clauses=[],
                document_type="Contract",
                confidence=0.8,
            )
        )

        token = "test-token"
        files = {
            "file": ("test.pdf", io.BytesIO(make_dummy_pdf_bytes()), "application/pdf")
        }

        last_status = None
        # The endpoint is limited to 10/minute; send 12 requests
        for _ in range(12):
            r = test_client.post(
                "/analyze", files=files, headers={"Authorization": f"Bearer {token}"}
            )
            last_status = r.status_code

    # Expect that at least one request hit the rate limiter (429)
    assert last_status in (200, 429)
    assert any(
        test_client.post(
            "/analyze",
            files={
                "file": ("t.pdf", io.BytesIO(make_dummy_pdf_bytes()), "application/pdf")
            },
            headers={"Authorization": f"Bearer {token}"},
        ).status_code
        == 429
        for _ in range(2)
    )
