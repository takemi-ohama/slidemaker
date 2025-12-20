"""Unit tests for GPT adapter."""

import pytest
from unittest.mock import AsyncMock, patch

from slidemaker.llm.adapters.api.gpt import GPTAdapter
from slidemaker.llm.base import LLMAuthenticationError, LLMRateLimitError


class TestGPTAdapter:
    """Tests for GPTAdapter class."""

    def test_api_base_url(self):
        """Test that API base URL is correct."""
        adapter = GPTAdapter(api_key="test-key", model="gpt-4o-mini")
        assert adapter.api_base_url == "https://api.openai.com/v1/chat/completions"

    def test_get_headers(self):
        """Test that headers are formatted correctly."""
        adapter = GPTAdapter(api_key="test-api-key", model="gpt-4o-mini")
        headers = adapter._get_headers()

        assert headers["Content-Type"] == "application/json"
        assert headers["Authorization"] == "Bearer test-api-key"

    def test_build_request_payload_with_system_prompt(self):
        """Test building request payload with system prompt."""
        adapter = GPTAdapter(api_key="test-key", model="gpt-4o-mini")
        payload = adapter._build_request_payload(
            prompt="Hello, world!",
            system_prompt="You are a helpful assistant.",
            temperature=0.7,
        )

        assert payload["model"] == "gpt-4o-mini"
        assert len(payload["messages"]) == 2
        assert payload["messages"][0]["role"] == "system"
        assert payload["messages"][0]["content"] == "You are a helpful assistant."
        assert payload["messages"][1]["role"] == "user"
        assert payload["messages"][1]["content"] == "Hello, world!"
        assert payload["max_tokens"] == 4096
        assert payload["temperature"] == 0.7

    def test_build_request_payload_without_system_prompt(self):
        """Test building request payload without system prompt."""
        adapter = GPTAdapter(api_key="test-key", model="gpt-4o-mini")
        payload = adapter._build_request_payload(
            prompt="Hello, world!",
            max_tokens=2048,
        )

        assert payload["model"] == "gpt-4o-mini"
        assert len(payload["messages"]) == 1
        assert payload["messages"][0]["role"] == "user"
        assert payload["messages"][0]["content"] == "Hello, world!"
        assert payload["max_tokens"] == 2048
        assert "temperature" not in payload

    def test_extract_text_response(self):
        """Test extracting text from API response."""
        adapter = GPTAdapter(api_key="test-key", model="gpt-4o-mini")
        response_data = {
            "choices": [{"message": {"content": "Generated text response"}}]
        }

        result = adapter._extract_text_response(response_data)
        assert result == "Generated text response"

    def test_extract_text_response_empty_choices(self):
        """Test extracting text from response with empty choices."""
        adapter = GPTAdapter(api_key="test-key", model="gpt-4o-mini")
        response_data = {"choices": []}

        with pytest.raises(ValueError, match="Invalid OpenAI API response format"):
            adapter._extract_text_response(response_data)

    def test_extract_text_response_missing_choices(self):
        """Test extracting text from response with missing choices."""
        adapter = GPTAdapter(api_key="test-key", model="gpt-4o-mini")
        response_data = {}

        with pytest.raises(ValueError, match="Invalid OpenAI API response format"):
            adapter._extract_text_response(response_data)

    @pytest.mark.asyncio
    async def test_generate_text_success(self):
        """Test successful text generation."""
        adapter = GPTAdapter(api_key="test-key", model="gpt-4o-mini")

        mock_response = {
            "choices": [{"message": {"content": "Generated response"}}]
        }

        with patch.object(adapter, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            result = await adapter.generate_text("Test prompt")

        assert result == "Generated response"
        mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_structured_success(self):
        """Test successful structured generation."""
        adapter = GPTAdapter(api_key="test-key", model="gpt-4o-mini")

        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": '{"key": "value", "number": 42}'
                    }
                }
            ]
        }

        with patch.object(adapter, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            result = await adapter.generate_structured("Test prompt")

        assert result == {"key": "value", "number": 42}
        mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_close(self):
        """Test closing the adapter."""
        adapter = GPTAdapter(api_key="test-key", model="gpt-4o-mini")

        with patch.object(adapter.client, "aclose", new_callable=AsyncMock) as mock_close:
            await adapter.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test using adapter as async context manager."""
        adapter = GPTAdapter(api_key="test-key", model="gpt-4o-mini")

        async with adapter as ctx_adapter:
            assert ctx_adapter == adapter

        # Client should be closed after context exit
        # (We don't test the actual close since it requires mocking)
