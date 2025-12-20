"""API adapters for LLM providers."""

from slidemaker.llm.adapters.api.base_api import APIAdapter
from slidemaker.llm.adapters.api.claude import ClaudeAdapter
from slidemaker.llm.adapters.api.gemini import GeminiAdapter
from slidemaker.llm.adapters.api.gpt import GPTAdapter

__all__ = ["APIAdapter", "ClaudeAdapter", "GeminiAdapter", "GPTAdapter"]
