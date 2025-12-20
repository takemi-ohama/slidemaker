"""Base classes for LLM adapters."""

from abc import ABC, abstractmethod
from typing import Any

from slidemaker.utils.logger import get_logger

logger = get_logger(__name__)


class LLMAdapter(ABC):
    """Abstract base class for LLM adapters."""

    def __init__(self, model: str, timeout: int = 300) -> None:
        """
        Initialize LLM adapter.

        Args:
            model: Model name/identifier
            timeout: Request timeout in seconds
        """
        self.model = model
        self.timeout = timeout
        logger.info("LLM adapter initialized", model=model, adapter_type=self.__class__.__name__)

    @abstractmethod
    async def generate_text(
        self, prompt: str, system_prompt: str | None = None, **kwargs: Any
    ) -> str:
        """
        Generate text completion from prompt.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated text

        Raises:
            LLMError: If generation fails
        """
        pass

    @abstractmethod
    async def generate_structured(
        self, prompt: str, system_prompt: str | None = None, schema: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Generate structured output (JSON) from prompt.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            schema: Optional JSON schema for validation

        Returns:
            Structured output as dictionary

        Raises:
            LLMError: If generation fails
        """
        pass


class LLMError(Exception):
    """Base exception for LLM-related errors."""

    pass


class LLMTimeoutError(LLMError):
    """Raised when LLM request times out."""

    pass


class LLMRateLimitError(LLMError):
    """Raised when rate limit is exceeded."""

    pass


class LLMAuthenticationError(LLMError):
    """Raised when authentication fails."""

    pass
