"""Claude (Anthropic) API adapter."""

from typing import Any

from slidemaker.llm.adapters.api.base_api import APIAdapter


class ClaudeAdapter(APIAdapter):
    """Adapter for Anthropic Claude API."""

    @property
    def api_base_url(self) -> str:
        """Get Claude API base URL."""
        return "https://api.anthropic.com/v1/messages"

    def _get_headers(self) -> dict[str, str]:
        """Get Claude-specific headers."""
        return {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }

    def _build_request_payload(
        self, prompt: str, system_prompt: str | None = None, **kwargs: Any
    ) -> dict[str, Any]:
        """Build Claude API request payload."""
        messages = [{"role": "user", "content": prompt}]

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 4096),
        }

        if system_prompt:
            payload["system"] = system_prompt

        # Add optional parameters
        if "temperature" in kwargs:
            payload["temperature"] = kwargs["temperature"]

        return payload

    def _extract_text_response(self, response_data: dict[str, Any]) -> str:
        """Extract text from Claude API response."""
        if "content" in response_data and response_data["content"]:
            return response_data["content"][0]["text"]
        raise ValueError("Invalid Claude API response format")
