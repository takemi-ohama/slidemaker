"""LLM manager for handling multiple LLM adapters."""

from typing import Any, cast

from slidemaker.llm.base import LLMAdapter
from slidemaker.utils.config_loader import LLMConfig
from slidemaker.utils.logger import get_logger

logger = get_logger(__name__)


class LLMManager:
    """Manages LLM adapters for composition and image generation."""

    def __init__(
        self, composition_config: LLMConfig, image_generation_config: LLMConfig | None = None
    ) -> None:
        """
        Initialize LLM manager.

        Args:
            composition_config: Configuration for composition LLM
            image_generation_config: Optional configuration for image generation LLM.
                                   If None, uses composition_config.
        """
        self.composition_llm = self._create_adapter(composition_config)
        self.image_llm = (
            self._create_adapter(image_generation_config)
            if image_generation_config
            else self.composition_llm
        )

        logger.info(
            "LLM manager initialized",
            composition_provider=composition_config.provider,
            image_provider=(
                image_generation_config.provider
                if image_generation_config
                else composition_config.provider
            ),
        )

    def _create_adapter(self, config: LLMConfig) -> LLMAdapter:
        """
        Create LLM adapter from configuration.

        Args:
            config: LLM configuration

        Returns:
            Configured LLM adapter

        Raises:
            ValueError: If adapter type or provider is unsupported
        """
        if config.type == "api":
            return self._create_api_adapter(config)
        elif config.type == "cli":
            return self._create_cli_adapter(config)
        else:
            raise ValueError(f"Unsupported LLM type: {config.type}")

    def _create_api_adapter(self, config: LLMConfig) -> LLMAdapter:
        """Create API-based LLM adapter."""
        from slidemaker.llm.adapters.api import (
            BedrockClaudeAdapter,
            ClaudeAdapter,
            GeminiAdapter,
            GPTAdapter,
        )

        provider_map = {
            "bedrock-claude": BedrockClaudeAdapter,
            "bedrock": BedrockClaudeAdapter,  # Alias
            "claude": ClaudeAdapter,
            "gpt": GPTAdapter,
            "openai": GPTAdapter,  # Alias
            "gemini": GeminiAdapter,
            "google": GeminiAdapter,  # Alias
        }

        adapter_class = provider_map.get(config.provider.lower())
        if not adapter_class:
            raise ValueError(
                f"Unsupported API provider: {config.provider}. "
                f"Supported: {list(provider_map.keys())}"
            )

        # Bedrock-specific initialization
        if adapter_class == BedrockClaudeAdapter:
            region = config.extra_params.get("region", "us-east-1")
            max_tokens = config.extra_params.get("max_tokens", 4096)
            temperature = config.extra_params.get("temperature", 0.7)

            return BedrockClaudeAdapter(
                model=config.model,
                region=region,
                timeout=config.timeout,
                max_tokens=max_tokens,
                temperature=temperature,
            )

        # Standard API adapters require API key
        if not config.api_key:
            raise ValueError(f"API key required for provider: {config.provider}")

        return adapter_class(api_key=config.api_key, model=config.model, timeout=config.timeout)

    def _create_cli_adapter(self, config: LLMConfig) -> LLMAdapter:
        """Create CLI-based LLM adapter."""
        from slidemaker.llm.adapters.cli import (
            ClaudeCodeAdapter,
            CodexCLIAdapter,
            GeminiCLIAdapter,
        )

        provider_map = {
            "claude-code": ClaudeCodeAdapter,
            "claude_code": ClaudeCodeAdapter,
            "codex": CodexCLIAdapter,
            "codex-cli": CodexCLIAdapter,
            "gemini-cli": GeminiCLIAdapter,
            "gemini_cli": GeminiCLIAdapter,
        }

        adapter_class = provider_map.get(config.provider.lower())
        if not adapter_class:
            raise ValueError(
                f"Unsupported CLI provider: {config.provider}. "
                f"Supported: {list(provider_map.keys())}"
            )

        cli_path = config.cli_command or config.provider.lower()
        return adapter_class(
            cli_path=cli_path, model=config.model, timeout=config.timeout
        )

    async def generate_composition(
        self, prompt: str, system_prompt: str | None = None, **kwargs: Any
    ) -> dict[str, Any]:
        """
        Generate slide composition using composition LLM.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional parameters

        Returns:
            Structured composition data
        """
        logger.info("Generating composition", llm=self.composition_llm.__class__.__name__)
        return await self.composition_llm.generate_structured(
            prompt=prompt, system_prompt=system_prompt, **kwargs
        )

    async def generate_image_description(
        self, prompt: str, system_prompt: str | None = None, **kwargs: Any
    ) -> str:
        """
        Generate image description or prompt using image LLM.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional parameters

        Returns:
            Generated text
        """
        logger.info("Generating image description", llm=self.image_llm.__class__.__name__)
        return await self.image_llm.generate_text(
            prompt=prompt, system_prompt=system_prompt, **kwargs
        )

    async def analyze_image(
        self, prompt: str, system_prompt: str | None = None, **kwargs: Any
    ) -> dict[str, Any]:
        """
        Analyze image and extract structured data.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional parameters (including image_data for Bedrock)

        Returns:
            Structured analysis data
        """
        logger.info("Analyzing image", llm=self.image_llm.__class__.__name__)

        # Check if adapter has analyze_image method (e.g., BedrockClaudeAdapter)
        if hasattr(self.image_llm, "analyze_image") and callable(
            getattr(self.image_llm, "analyze_image")
        ):
            # Use adapter's specialized analyze_image method
            analyze_method = getattr(self.image_llm, "analyze_image")
            result = await analyze_method(prompt=prompt, system_prompt=system_prompt, **kwargs)
            return cast(dict[str, Any], result)
        else:
            # Fallback to generate_structured for other adapters (e.g., ClaudeAdapter)
            return await self.image_llm.generate_structured(
                prompt=prompt, system_prompt=system_prompt, **kwargs
            )
