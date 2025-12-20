"""CLI-based LLM adapters."""

from slidemaker.llm.adapters.cli.base_cli import CLIAdapter
from slidemaker.llm.adapters.cli.claude_code import ClaudeCodeAdapter
from slidemaker.llm.adapters.cli.codex_cli import CodexCLIAdapter
from slidemaker.llm.adapters.cli.gemini_cli import GeminiCLIAdapter

__all__ = ["CLIAdapter", "ClaudeCodeAdapter", "CodexCLIAdapter", "GeminiCLIAdapter"]
