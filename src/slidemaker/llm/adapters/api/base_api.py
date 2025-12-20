"""Base class for API-based LLM adapters."""

import json
from abc import abstractmethod
from typing import Any

import httpx

from slidemaker.llm.base import (
    LLMAdapter,
    LLMAuthenticationError,
    LLMError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from slidemaker.utils.logger import get_logger

logger = get_logger(__name__)


class APIAdapter(LLMAdapter):
    """Base class for API-based LLM adapters."""

    def __init__(self, api_key: str, model: str, timeout: int = 300):
        """
        Initialize API adapter.

        Args:
            api_key: API key for authentication
            model: Model identifier
            timeout: Request timeout in seconds
        """
        super().__init__(model=model, timeout=timeout)
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=timeout)

    @property
    @abstractmethod
    def api_base_url(self) -> str:
        """Get API base URL."""
        pass

    @abstractmethod
    def _build_request_payload(
        self, prompt: str, system_prompt: str | None = None, **kwargs: Any
    ) -> dict[str, Any]:
        """Build API request payload."""
        pass

    @abstractmethod
    def _extract_text_response(self, response_data: dict[str, Any]) -> str:
        """Extract text from API response."""
        pass

    async def generate_text(
        self, prompt: str, system_prompt: str | None = None, **kwargs: Any
    ) -> str:
        """Generate text completion."""
        try:
            payload = self._build_request_payload(prompt, system_prompt, **kwargs)
            response = await self._make_request(payload)
            return self._extract_text_response(response)
        except httpx.TimeoutException as e:
            raise LLMTimeoutError(f"Request timed out after {self.timeout}s") from e
        except Exception as e:
            logger.error("Text generation failed", error=str(e), model=self.model)
            raise LLMError(f"Failed to generate text: {e}") from e

    async def generate_structured(
        self, prompt: str, system_prompt: str | None = None, schema: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Generate structured JSON output."""
        try:
            # Add JSON instruction to prompt
            json_prompt = f"{prompt}\n\nOutput valid JSON only."
            text_response = await self.generate_text(json_prompt, system_prompt)

            # Extract JSON from response
            json_str = self._extract_json(text_response)
            return json.loads(json_str)

        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON response", error=str(e))
            raise LLMError(f"Invalid JSON in response: {e}") from e
        except Exception as e:
            logger.error("Structured generation failed", error=str(e), model=self.model)
            raise LLMError(f"Failed to generate structured output: {e}") from e

    async def _make_request(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Make API request with error handling."""
        headers = self._get_headers()

        try:
            response = await self.client.post(
                self.api_base_url, json=payload, headers=headers
            )

            if response.status_code == 401:
                raise LLMAuthenticationError("Invalid API key")
            elif response.status_code == 429:
                raise LLMRateLimitError("Rate limit exceeded")
            elif response.status_code >= 400:
                raise LLMError(
                    f"API error: {response.status_code} - {response.text}"
                )

            return response.json()

        except httpx.TimeoutException:
            raise
        except Exception as e:
            raise LLMError(f"Request failed: {e}") from e

    def _get_headers(self) -> dict[str, str]:
        """Get request headers."""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    @staticmethod
    def _extract_json(text: str) -> str:
        """Extract JSON from text response."""
        # Try to find JSON in markdown code blocks
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            return text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            return text[start:end].strip()
        # Try to find JSON object
        elif "{" in text and "}" in text:
            start = text.find("{")
            end = text.rfind("}") + 1
            return text[start:end]
        return text.strip()

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()

    async def __aenter__(self) -> "APIAdapter":
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()
