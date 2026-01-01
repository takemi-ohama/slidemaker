"""API adapters for LLM providers."""

from slidemaker.llm.adapters.api.base_api import APIAdapter
from slidemaker.llm.adapters.api.bedrock_claude import BedrockClaudeAdapter
from slidemaker.llm.adapters.api.claude import ClaudeAdapter
from slidemaker.llm.adapters.api.gemini import GeminiAdapter
from slidemaker.llm.adapters.api.gpt import GPTAdapter
from slidemaker.llm.adapters.api.vertex_gemini import VertexGeminiAdapter

__all__ = [
    "APIAdapter",
    "BedrockClaudeAdapter",
    "ClaudeAdapter",
    "GeminiAdapter",
    "GPTAdapter",
    "VertexGeminiAdapter",
]
