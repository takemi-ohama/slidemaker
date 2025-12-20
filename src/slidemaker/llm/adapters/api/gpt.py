"""GPT (OpenAI) API adapter."""

from typing import Any

from slidemaker.llm.adapters.api.base_api import APIAdapter


class GPTAdapter(APIAdapter):
    """Adapter for OpenAI GPT API."""

    @property
    def api_base_url(self) -> str:
        """Get OpenAI API base URL."""
        return "https://api.openai.com/v1/chat/completions"

    def _get_headers(self) -> dict[str, str]:
        """Get OpenAI-specific headers."""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def _build_request_payload(
        self, prompt: str, system_prompt: str | None = None, **kwargs: Any
    ) -> dict[str, Any]:
        """Build OpenAI API request payload."""
        messages: list[dict[str, str]] = []

        # Add system message if provided
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # Add user message
        messages.append({"role": "user", "content": prompt})

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 4096),
        }

        # Add optional parameters
        if "temperature" in kwargs:
            payload["temperature"] = kwargs["temperature"]

        return payload

    def _extract_text_response(self, response_data: dict[str, Any]) -> str:
        """Extract text from OpenAI API response."""
        if "choices" in response_data and response_data["choices"]:
            return response_data["choices"][0]["message"]["content"]
        raise ValueError("Invalid OpenAI API response format")
