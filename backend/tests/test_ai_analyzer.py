import pytest
from unittest.mock import AsyncMock, patch
from services.ai_analyzer import AIAnalyzer
from models.analysis_models import AnalysisResult
import os
import json

# No auth in application anymore


@pytest.fixture
def ai_analyzer():
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test_key"}):
        with patch("openai.OpenAI"):
            return AIAnalyzer()


@pytest.mark.asyncio
async def test_analyze_document_success(ai_analyzer):
    mock_response_data = {
        "summary": "This is a test summary.",
        "key_clauses": [
            {
                "type": "Test Clause",
                "content": "This is a test clause.",
                "importance": "high",
                "classification": "Contractual",
                "risk_score": 8.0,
                "page": 1,
            }
        ],
        "document_type": "Test Document",
        "total_pages": 1,
        "confidence": 0.9,
    }

    # Mock the low-level OpenRouter call wrapper to return JSON string
    ai_analyzer.analyze_with_openrouter = AsyncMock(
        return_value=json.dumps(mock_response_data)
    )

    result = await ai_analyzer.analyze_document(
        text="This is a test document.", filename="test.pdf"
    )

    assert isinstance(result, AnalysisResult)
    assert result.summary == "This is a test summary."
    assert len(result.key_clauses) == 1
    assert result.key_clauses[0].type == "Test Clause"


@pytest.mark.asyncio
async def test_analyze_document_fallback(ai_analyzer):
    # Force analyze_with_openrouter to raise to trigger fallback path
    ai_analyzer.analyze_with_openrouter = AsyncMock(side_effect=Exception("API Error"))

    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        result = await ai_analyzer.analyze_document(
            text="This is a test document.", filename="test.pdf"
        )
        assert mock_sleep.await_count > 0

    assert isinstance(result, AnalysisResult)
    assert "Analysis failed" in result.summary
    assert len(result.key_clauses) == 1
    assert result.key_clauses[0].type == "Error"

