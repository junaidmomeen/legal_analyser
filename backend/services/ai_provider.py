import os
import logging
import httpx
from typing import Protocol
from openai import OpenAI
from openai import APIStatusError


logger = logging.getLogger(__name__)


class AIProvider(Protocol):
    def generate(self, prompt: str, model: str) -> str: ...


class OpenRouterProvider:
    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not key:
            logger.critical(
                "CRITICAL: OPENROUTER_API_KEY not found. The application cannot start without it."
            )
            raise SystemExit("OPENROUTER_API_KEY not set.")

        try:
            self.client = OpenAI(
                base_url=base_url or "https://openrouter.ai/api/v1",
                api_key=key,
                default_headers={
                    "HTTP-Referer": os.getenv("HTTP_REFERER", "http://localhost:3000"),
                    "X-Title": os.getenv("APP_TITLE", "Legal Analyser"),
                },
                timeout=30.0,  # Add timeout to prevent hanging requests
            )
            logger.info("OpenRouter provider initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenRouter provider: {e}")
            raise

    def generate(self, prompt: str, model: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4000,  # Limit response size
                temperature=0.1,  # Lower temperature for more consistent JSON
            )
            if not response or not response.choices:
                raise ValueError("Empty response from OpenRouter")

            content = response.choices[0].message.content
            if not content or not content.strip():
                raise ValueError("Empty content in OpenRouter response")

            return content.strip()

        except APIStatusError as e:
            # Graceful fallback for auth/availability errors
            status = getattr(e, "status_code", None)
            if status == 401:
                logger.warning("OpenRouter 401 Unauthorized - API key may be invalid")
                raise ValueError("Invalid API key or unauthorized access")
            elif status == 429:
                logger.warning("OpenRouter rate limit exceeded")
                raise ValueError("Rate limit exceeded - please try again later")
            elif status >= 500:
                logger.warning(f"OpenRouter server error: {status}")
                raise ValueError("OpenRouter service temporarily unavailable")

            logger.error(f"OpenRouter API status error: {e}")
            raise ValueError(f"OpenRouter API error: {e}")

        except httpx.RequestError as e:
            logger.warning(f"OpenRouter network error: {e}")
            raise ValueError("Network error connecting to OpenRouter")

        except Exception as e:
            logger.error(f"OpenRouter unexpected error: {e}")
            raise ValueError(f"OpenRouter service error: {e}")
