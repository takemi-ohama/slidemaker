"""Google Gemini API adapter."""

from typing import Any

from slidemaker.llm.adapters.api.base_api import APIAdapter


class GeminiAdapter(APIAdapter):
    """Adapter for Google Gemini API."""

    @property
    def api_base_url(self) -> str:
        """Get Gemini API base URL with dynamic model name."""
        return f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    def _get_headers(self) -> dict[str, str]:
        """Get Gemini-specific headers."""
        return {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key,
        }

    def _build_request_payload(
        self, prompt: str, system_prompt: str | None = None, **kwargs: Any
    ) -> dict[str, Any]:
        """Build Gemini API request payload."""
        # Combine system prompt and user prompt if system prompt exists
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        # Build contents in Gemini format
        payload: dict[str, Any] = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {
                "maxOutputTokens": kwargs.get("max_tokens", 4096),
            },
        }

        # Add optional parameters
        if "temperature" in kwargs:
            payload["generationConfig"]["temperature"] = kwargs["temperature"]

        return payload

    def _extract_text_response(self, response_data: dict[str, Any]) -> str:
        """Extract text from Gemini API response."""
        if (
            "candidates" in response_data
            and response_data["candidates"]
            and "content" in response_data["candidates"][0]
            and "parts" in response_data["candidates"][0]["content"]
            and response_data["candidates"][0]["content"]["parts"]
        ):
            return response_data["candidates"][0]["content"]["parts"][0]["text"]
        raise ValueError("Invalid Gemini API response format")
