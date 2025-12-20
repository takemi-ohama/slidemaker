"""Unit tests for LLM Manager."""

from unittest.mock import AsyncMock, patch

import pytest

from slidemaker.llm.manager import LLMManager
from slidemaker.utils.config_loader import LLMConfig


class TestLLMManager:
    """Tests for LLMManager class."""

    def test_initialization_single_llm(self):
        """Test initializing manager with single LLM for both tasks."""
        composition_config = LLMConfig(
            type="api",
            provider="claude",
            model="claude-3-5-sonnet-20241022",
            api_key="test-api-key",
        )

        manager = LLMManager(composition_config=composition_config)

        assert manager.composition_llm is not None
        assert manager.image_llm is not None
        # Same LLM used for both when image_generation_config is None
        assert manager.composition_llm == manager.image_llm

    def test_initialization_separate_llms(self):
        """Test initializing manager with separate LLMs."""
        composition_config = LLMConfig(
            type="api", provider="claude", model="claude-3-5-sonnet-20241022", api_key="key1"
        )
        image_config = LLMConfig(
            type="api", provider="gemini", model="gemini-2.0-flash-exp", api_key="key2"
        )

        manager = LLMManager(
            composition_config=composition_config, image_generation_config=image_config
        )

        assert manager.composition_llm is not None
        assert manager.image_llm is not None
        # Different LLMs
        assert manager.composition_llm != manager.image_llm

    def test_create_api_adapter_claude(self):
        """Test creating Claude API adapter."""
        config = LLMConfig(
            type="api", provider="claude", model="claude-3-5-sonnet-20241022", api_key="test-key"
        )

        manager = LLMManager(composition_config=config)
        adapter = manager.composition_llm

        # Check that it's a Claude adapter
        assert adapter.__class__.__name__ == "ClaudeAdapter"

    def test_create_api_adapter_gpt(self):
        """Test creating GPT API adapter."""
        config = LLMConfig(type="api", provider="gpt", model="gpt-4o-mini", api_key="test-key")

        manager = LLMManager(composition_config=config)
        adapter = manager.composition_llm

        assert adapter.__class__.__name__ == "GPTAdapter"

    def test_create_api_adapter_openai_alias(self):
        """Test creating GPT adapter using 'openai' alias."""
        config = LLMConfig(type="api", provider="openai", model="gpt-4o-mini", api_key="test-key")

        manager = LLMManager(composition_config=config)
        adapter = manager.composition_llm

        assert adapter.__class__.__name__ == "GPTAdapter"

    def test_create_api_adapter_gemini(self):
        """Test creating Gemini API adapter."""
        config = LLMConfig(
            type="api", provider="gemini", model="gemini-2.0-flash-exp", api_key="test-key"
        )

        manager = LLMManager(composition_config=config)
        adapter = manager.composition_llm

        assert adapter.__class__.__name__ == "GeminiAdapter"

    def test_create_api_adapter_google_alias(self):
        """Test creating Gemini adapter using 'google' alias."""
        config = LLMConfig(
            type="api", provider="google", model="gemini-2.0-flash-exp", api_key="test-key"
        )

        manager = LLMManager(composition_config=config)
        adapter = manager.composition_llm

        assert adapter.__class__.__name__ == "GeminiAdapter"

    def test_create_api_adapter_missing_api_key(self):
        """Test that missing API key raises ValueError."""
        config = LLMConfig(
            type="api",
            provider="claude",
            model="claude-3-5-sonnet-20241022",
            api_key=None,  # Missing API key
        )

        with pytest.raises(ValueError, match="API key required"):
            LLMManager(composition_config=config)

    def test_create_api_adapter_unsupported_provider(self):
        """Test that unsupported provider raises ValueError."""
        config = LLMConfig(
            type="api", provider="unsupported-provider", model="model-name", api_key="test-key"
        )

        with pytest.raises(ValueError, match="Unsupported API provider"):
            LLMManager(composition_config=config)

    def test_create_cli_adapter_claude_code(self):
        """Test creating Claude Code CLI adapter."""
        config = LLMConfig(type="cli", provider="claude-code", model="claude-sonnet-4")

        manager = LLMManager(composition_config=config)
        adapter = manager.composition_llm

        assert adapter.__class__.__name__ == "ClaudeCodeAdapter"

    def test_create_cli_adapter_codex(self):
        """Test creating Codex CLI adapter."""
        config = LLMConfig(type="cli", provider="codex", model="claude-sonnet-4")

        manager = LLMManager(composition_config=config)
        adapter = manager.composition_llm

        assert adapter.__class__.__name__ == "CodexCLIAdapter"

    def test_create_cli_adapter_gemini(self):
        """Test creating Gemini CLI adapter."""
        config = LLMConfig(type="cli", provider="gemini-cli", model="gemini-2.0-flash-exp")

        manager = LLMManager(composition_config=config)
        adapter = manager.composition_llm

        assert adapter.__class__.__name__ == "GeminiCLIAdapter"

    def test_create_cli_adapter_unsupported_provider(self):
        """Test that unsupported CLI provider raises ValueError."""
        config = LLMConfig(type="cli", provider="unsupported-cli", model="model-name")

        with pytest.raises(ValueError, match="Unsupported CLI provider"):
            LLMManager(composition_config=config)

    def test_create_adapter_unsupported_type(self):
        """Test that unsupported adapter type raises ValueError."""
        config = LLMConfig(
            type="unsupported-type",  # type: ignore
            provider="claude",
            model="claude-3-5-sonnet-20241022",
            api_key="test-key",
        )

        with pytest.raises(ValueError, match="Unsupported LLM type"):
            LLMManager(composition_config=config)

    @pytest.mark.asyncio
    async def test_generate_composition(self):
        """Test generating composition."""
        config = LLMConfig(
            type="api", provider="claude", model="claude-3-5-sonnet-20241022", api_key="test-key"
        )
        manager = LLMManager(composition_config=config)

        mock_result = {"title": "Test Slide", "content": "Test content"}

        with patch.object(
            manager.composition_llm, "generate_structured", new_callable=AsyncMock
        ) as mock_generate:
            mock_generate.return_value = mock_result
            result = await manager.generate_composition("Test prompt")

        assert result == mock_result
        mock_generate.assert_called_once_with(
            prompt="Test prompt", system_prompt=None
        )

    @pytest.mark.asyncio
    async def test_generate_composition_with_system_prompt(self):
        """Test generating composition with system prompt."""
        config = LLMConfig(
            type="api", provider="claude", model="claude-3-5-sonnet-20241022", api_key="test-key"
        )
        manager = LLMManager(composition_config=config)

        mock_result = {"title": "Test Slide"}

        with patch.object(
            manager.composition_llm, "generate_structured", new_callable=AsyncMock
        ) as mock_generate:
            mock_generate.return_value = mock_result
            result = await manager.generate_composition(
                "Test prompt", system_prompt="You are a slide designer"
            )

        assert result == mock_result
        mock_generate.assert_called_once_with(
            prompt="Test prompt", system_prompt="You are a slide designer"
        )

    @pytest.mark.asyncio
    async def test_generate_image_description(self):
        """Test generating image description."""
        config = LLMConfig(
            type="api", provider="gemini", model="gemini-2.0-flash-exp", api_key="test-key"
        )
        manager = LLMManager(composition_config=config)

        mock_result = "A beautiful landscape with mountains"

        with patch.object(
            manager.image_llm, "generate_text", new_callable=AsyncMock
        ) as mock_generate:
            mock_generate.return_value = mock_result
            result = await manager.generate_image_description("Describe a landscape")

        assert result == mock_result
        mock_generate.assert_called_once_with(
            prompt="Describe a landscape", system_prompt=None
        )

    @pytest.mark.asyncio
    async def test_generate_image_description_with_system_prompt(self):
        """Test generating image description with system prompt."""
        config = LLMConfig(
            type="api", provider="gemini", model="gemini-2.0-flash-exp", api_key="test-key"
        )
        manager = LLMManager(composition_config=config)

        mock_result = "Detailed description"

        with patch.object(
            manager.image_llm, "generate_text", new_callable=AsyncMock
        ) as mock_generate:
            mock_generate.return_value = mock_result
            result = await manager.generate_image_description(
                "Describe", system_prompt="Be detailed"
            )

        assert result == mock_result
        mock_generate.assert_called_once_with(
            prompt="Describe", system_prompt="Be detailed"
        )

    @pytest.mark.asyncio
    async def test_analyze_image(self):
        """Test analyzing image."""
        config = LLMConfig(
            type="api", provider="claude", model="claude-3-5-sonnet-20241022", api_key="test-key"
        )
        manager = LLMManager(composition_config=config)

        mock_result = {
            "objects": ["person", "car"],
            "description": "A person standing next to a car",
        }

        with patch.object(
            manager.composition_llm, "generate_structured", new_callable=AsyncMock
        ) as mock_generate:
            mock_generate.return_value = mock_result
            result = await manager.analyze_image("Analyze this image")

        assert result == mock_result
        mock_generate.assert_called_once_with(
            prompt="Analyze this image", system_prompt=None
        )

    @pytest.mark.asyncio
    async def test_analyze_image_with_system_prompt(self):
        """Test analyzing image with system prompt."""
        config = LLMConfig(
            type="api", provider="claude", model="claude-3-5-sonnet-20241022", api_key="test-key"
        )
        manager = LLMManager(composition_config=config)

        mock_result = {"objects": ["tree"]}

        with patch.object(
            manager.composition_llm, "generate_structured", new_callable=AsyncMock
        ) as mock_generate:
            mock_generate.return_value = mock_result
            result = await manager.analyze_image("Analyze", system_prompt="Focus on nature")

        assert result == mock_result
        mock_generate.assert_called_once_with(
            prompt="Analyze", system_prompt="Focus on nature"
        )
