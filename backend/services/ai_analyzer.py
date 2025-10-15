import os
import httpx
import logging
from typing import List, Optional
from models.analysis_models import AnalysisResult, KeyClause
import json
import asyncio
from services.ai_provider import OpenRouterProvider, AIProvider
from utils.circuit_breaker import circuit_breaker

logger = logging.getLogger(__name__)


class AIAnalyzer:
    """Service for AI-powered legal document analysis using OpenRouter with retry and fallback logic"""

    def __init__(self, provider: Optional[AIProvider] = None):
        self.provider: AIProvider = provider or OpenRouterProvider()
        self.model = "openai/gpt-4o-mini"

        # Retry configuration
        self.max_retries = 3
        self.retry_delay = int(os.getenv("RETRY_DELAY", "2"))  # seconds
        self.fallback_chunk_size = 8000  # characters for fallback mode

    def clean_json_response(self, raw_text: str) -> str:
        """Clean and extract JSON from AI response with improved error handling"""
        if not raw_text or not raw_text.strip():
            logger.error("Empty response from AI model")
            return '{"summary":"Analysis failed due to empty AI response.","key_clauses":[],"document_type":"Unknown","confidence":0.0}'

        # Remove markdown code blocks
        if "```json" in raw_text:
            start = raw_text.find("```json") + 7
            end = raw_text.find("```", start)
            if end != -1:
                raw_text = raw_text[start:end].strip()
        elif "```" in raw_text:
            # Handle cases where it's just ``` without json
            start = raw_text.find("```") + 3
            end = raw_text.find("```", start)
            if end != -1:
                raw_text = raw_text[start:end].strip()

        # Find the JSON object boundaries
        json_start = raw_text.find("{")
        json_end = raw_text.rfind("}") + 1

        if json_start == -1 or json_end == 0:
            logger.error(f"No JSON found in AI response: {raw_text[:100]}...")
            return '{"summary":"Analysis failed due to invalid response format.","key_clauses":[],"document_type":"Unknown","confidence":0.0}'

        raw_text = raw_text[json_start:json_end]

        # Validate JSON before returning
        try:
            json.loads(raw_text.strip())  # Test if it's valid JSON
            return raw_text.strip()
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON after cleaning: {str(e)}")
            return '{"summary":"Analysis failed due to malformed response.","key_clauses":[],"document_type":"Unknown","confidence":0.0}'

    def create_analysis_prompt(self, text: str, is_fallback: bool = False) -> str:
        """Create the analysis prompt with optional fallback mode"""
        base_prompt = """
        You are an AI trained to analyze **legal documents**.
        Read the following text and return a structured JSON object with:

        {
          "summary": {
            "overview": "A brief 2-3 sentence overview of what this document is about and its main purpose",
            "key_points": [
              "• First key point in simple language",
              "• Second important point explained clearly", 
              "• Third critical aspect to understand",
              "• Fourth key consideration"
            ],
            "obligations": [
              "• Main obligation or requirement 1",
              "• Main obligation or requirement 2",
              "• Main obligation or requirement 3"
            ],
            "risks": [
              "• Primary risk or concern 1",
              "• Primary risk or concern 2", 
              "• Primary risk or concern 3"
            ],
            "recommendations": [
              "• Key recommendation or action item 1",
              "• Key recommendation or action item 2",
              "• Key recommendation or action item 3"
            ]
          },
          "key_clauses": [
            {
              "type": "Clause type (e.g., Payment Terms, Termination, Confidentiality)",
              "content": "Full text of the clause (first 200 chars if too long)",
              "importance": "high | medium | low",
              "classification": "Contractual | Compliance | Financial | Termination | Confidentiality | Miscellaneous",
              "risk_score": "A score from 1 to 10, where 10 is the highest risk",
              "page": "Estimated page number (if possible, else null)"
            }
          ],
          "document_type": "Type of document (contract/agreement/policy/etc)",
          "confidence": "Number between 0.5 and 0.98"
        }

        IMPORTANT: 
        - ONLY return valid JSON
        - Do not include explanations or markdown
        - Write all summary content in simple, easy-to-understand language for non-lawyers
        - Make bullet points specific and actionable
        - If text is truncated, focus on the most important clauses
        - Ensure all JSON keys are present
        - Keep summary points concise but informative (2-4 items per section)
        """

        if is_fallback:
            base_prompt += (
                "\n\nNOTE: This is a partial document analysis due to size limits."
            )

        return base_prompt + f"\n\nDocument text:\n{text}"

    def create_fallback_result(
        self, document_type: str, error_msg: str
    ) -> AnalysisResult:
        """Create a fallback result when AI analysis completely fails"""
        return AnalysisResult(
            summary=f"Analysis failed: {error_msg}. Please try uploading a smaller document or contact support.",
            key_clauses=[
                KeyClause(
                    type="Error",
                    content="Could not analyze document due to processing error.",
                    importance="high",
                    classification="Miscellaneous",
                    risk_score=10.0,
                    page=None,
                    confidence=0.0,
                )
            ],
            document_type=document_type or "Unknown Document",
            confidence=0.0,
        )

    @circuit_breaker(
        name="openrouter_api",
        failure_threshold=3,
        recovery_timeout=120.0,
        expected_exception=(
            ValueError,
            httpx.RequestError,
            httpx.HTTPStatusError,
            Exception,
        ),
    )
    async def analyze_with_openrouter(self, prompt: str, attempt: int = 1) -> str:
        """Make API call to OpenRouter with circuit breaker protection"""
        try:
            logger.info(
                f"Making OpenRouter API call (attempt {attempt}/{self.max_retries})"
            )

            # Make the call synchronous since the provider.generate is synchronous
            import asyncio

            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, self.provider.generate, prompt, self.model
            )

        except ValueError as e:
            # Handle specific error messages from the provider
            logger.error(f"OpenRouter API validation error (attempt {attempt}): {e}")
            raise Exception(f"AI service error: {e}")

        except httpx.RequestError as e:
            logger.error(f"OpenRouter API request failed: {e}")
            raise Exception(
                "Network error connecting to AI service. Please try again later."
            )

        except Exception as e:
            logger.error(f"OpenRouter API error (attempt {attempt}): {str(e)}")
            raise Exception(f"AI analysis failed: {str(e)}")

    async def analyze_document(
        self, text: str, document_type: str = "", filename: str = ""
    ) -> AnalysisResult:
        """
        Analyze the document using OpenRouter AI with retry and fallback logic.
        Extracts summary + key clauses into structured format.
        """
        logger.info(f"Starting analysis for document: {filename} ({len(text)} chars)")

        # Truncate text if too long for primary analysis
        analysis_text = text[:12000] if len(text) > 12000 else text

        for attempt in range(1, self.max_retries + 1):
            try:
                prompt = self.create_analysis_prompt(analysis_text)
                raw_output = await self.analyze_with_openrouter(prompt, attempt)

                # Clean and parse JSON
                clean_json = self.clean_json_response(raw_output)

                try:
                    data = json.loads(clean_json)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parsing failed on attempt {attempt}: {str(e)}")
                    if attempt == self.max_retries:
                        return self.create_fallback_result(
                            document_type, "Failed to parse AI response"
                        )
                    await asyncio.sleep(self.retry_delay)
                    continue

                # Validate required fields
                required_fields = [
                    "summary",
                    "key_clauses",
                    "document_type",
                    "confidence",
                ]
                missing_fields = [
                    field for field in required_fields if field not in data
                ]
                if missing_fields:
                    logger.warning(
                        f"Missing required fields in AI response: {missing_fields}"
                    )
                    if attempt == self.max_retries:
                        return self.create_fallback_result(
                            document_type,
                            f"Incomplete response: missing {', '.join(missing_fields)}",
                        )
                    await asyncio.sleep(self.retry_delay)
                    continue

                # Transform into AnalysisResult
                key_clauses: List[KeyClause] = []
                for clause in data.get("key_clauses", []):
                    key_clauses.append(
                        KeyClause(
                            type=clause.get("type", "Unknown"),
                            content=clause.get("content", "")[
                                :500
                            ],  # Limit content length
                            importance=clause.get("importance", "low"),
                            classification=clause.get(
                                "classification", "Miscellaneous"
                            ),
                            risk_score=float(clause.get("risk_score", 0.0)),
                            page=clause.get("page"),
                            confidence=0.9,
                        )
                    )

                # Handle both old and new summary formats
                summary_data = data.get("summary", "No summary provided.")
                if isinstance(summary_data, dict):
                    # New structured format - convert to JSON string for frontend
                    summary_json = json.dumps(summary_data)
                else:
                    # Old string format - keep as is for backward compatibility
                    summary_json = summary_data

                result = AnalysisResult(
                    summary=summary_json,
                    key_clauses=key_clauses,
                    document_type=data.get(
                        "document_type", document_type or "Legal Document"
                    ),
                    confidence=min(float(data.get("confidence", 0.8)), 0.98),
                )

                logger.info(
                    f"Analysis completed successfully for {filename} (attempt {attempt})"
                )
                return result

            except json.JSONDecodeError as e:
                logger.warning(f"JSON parsing failed (attempt {attempt}): {e}")

                if attempt == self.max_retries:
                    # Try fallback with smaller chunks
                    logger.info("Attempting fallback analysis with smaller chunks...")
                    return await self.fallback_analysis(text, document_type, filename)
                else:
                    await asyncio.sleep(self.retry_delay)
                    continue

            except Exception as e:
                logger.error(f"Analysis attempt {attempt} failed: {str(e)}")

                if attempt == self.max_retries:
                    # Final fallback
                    return self.create_fallback_result(document_type, str(e))
                else:
                    await asyncio.sleep(
                        self.retry_delay * attempt
                    )  # Exponential backoff

        # Should not reach here, but just in case
        return self.create_fallback_result(document_type, "Maximum retries exceeded")

    async def fallback_analysis(
        self, text: str, document_type: str, filename: str
    ) -> AnalysisResult:
        """Fallback analysis with smaller chunks when main analysis fails"""
        try:
            logger.info(f"Starting fallback analysis for {filename}")

            # Use smaller chunk for fallback
            fallback_text = text[: self.fallback_chunk_size]
            prompt = self.create_analysis_prompt(fallback_text, is_fallback=True)

            raw_output = await self.analyze_with_openrouter(prompt)

            # Simple parsing for fallback
            try:
                clean_json = self.clean_json_response(raw_output)
                data = json.loads(clean_json)
            except Exception:
                # Ultra-fallback: create minimal result
                return AnalysisResult(
                    summary="Document processed with limited analysis due to processing constraints.",
                    key_clauses=[
                        KeyClause(
                            type="General Content",
                            content=fallback_text[:200] + "..."
                            if len(fallback_text) > 200
                            else fallback_text,
                            importance="medium",
                            classification="Miscellaneous",
                            risk_score=5.0,
                            page=1,
                            confidence=0.5,
                        )
                    ],
                    document_type=document_type or "Legal Document",
                    confidence=0.5,
                )

            # Build result from fallback data
            key_clauses = []
            for clause in data.get("key_clauses", []):
                key_clauses.append(
                    KeyClause(
                        type=clause.get("type", "Unknown"),
                        content=clause.get("content", "")[:200],
                        importance=clause.get("importance", "low"),
                        classification=clause.get("classification", "Miscellaneous"),
                        risk_score=float(clause.get("risk_score", 0.0)),
                        page=clause.get("page"),
                        confidence=0.6,  # Lower confidence for fallback
                    )
                )

            # Handle both old and new summary formats for fallback
            summary_data = data.get("summary", "Limited analysis completed.")
            if isinstance(summary_data, dict):
                # Add fallback prefix to overview if it's a structured summary
                if "overview" in summary_data:
                    summary_data["overview"] = (
                        f"[Partial Analysis] {summary_data['overview']}"
                    )
                summary_json = json.dumps(summary_data)
            else:
                summary_json = f"[Partial Analysis] {summary_data}"

            result = AnalysisResult(
                summary=summary_json,
                key_clauses=key_clauses,
                document_type=data.get("document_type", document_type),
                confidence=min(
                    float(data.get("confidence", 0.6)), 0.7
                ),  # Cap fallback confidence
            )

            logger.info(f"Fallback analysis completed for {filename}")
            return result

        except Exception as e:
            logger.error(f"Fallback analysis also failed: {str(e)}")
            return self.create_fallback_result(
                document_type, f"Fallback failed: {str(e)}"
            )
