"""
Unit tests for CodexCLIAdapter.
"""

import pytest

from slidemaker.llm.adapters.cli.codex_cli import CodexCLIAdapter
from slidemaker.llm.base import LLMError


class TestCodexCLIAdapter:
    """Test suite for CodexCLIAdapter."""

    def test_init_default_parameters(self) -> None:
        """Test initialization with default parameters."""
        adapter = CodexCLIAdapter()

        assert adapter.cli_path == "codex"
        assert adapter.model == "claude-3-5-sonnet-20241022"
        assert adapter.timeout == 300

    def test_init_custom_parameters(self) -> None:
        """Test initialization with custom parameters."""
        adapter = CodexCLIAdapter(
            cli_path="/usr/local/bin/codex",
            model="claude-3-opus-20240229",
            timeout=600,
        )

        assert adapter.cli_path == "/usr/local/bin/codex"
        assert adapter.model == "claude-3-opus-20240229"
        assert adapter.timeout == 600

    def test_build_command_basic(self) -> None:
        """Test _build_command with basic prompt."""
        adapter = CodexCLIAdapter()
        command = adapter._build_command("Hello, world!")

        assert command[0] == "codex"
        assert command[1] == "exec"
        assert "--model" in command
        assert "claude-3-5-sonnet-20241022" in command
        assert "--dangerously-bypass-approvals-and-sandbox" in command
        assert "--skip-git-repo-check" in command
        assert command[-1] == "Hello, world!"

    def test_build_command_with_system_prompt(self) -> None:
        """Test _build_command with system prompt."""
        adapter = CodexCLIAdapter()
        command = adapter._build_command(
            "User prompt", system_prompt="System prompt"
        )

        # System prompt should be prepended to user prompt
        assert command[-1] == "System prompt\n\nUser prompt"

    def test_build_command_with_sandbox(self) -> None:
        """Test _build_command with sandbox parameter."""
        adapter = CodexCLIAdapter()
        command = adapter._build_command(
            "Hello", sandbox="workspace-write"
        )

        assert "--sandbox" in command
        assert "workspace-write" in command

    def test_build_command_with_json_output(self) -> None:
        """Test _build_command with json_output parameter."""
        adapter = CodexCLIAdapter()
        command = adapter._build_command("Hello", json_output=True)

        assert "--json" in command

    def test_parse_output_plain_text(self) -> None:
        """Test _parse_output with plain text output."""
        adapter = CodexCLIAdapter()
        raw_output = "Hello, this is the response.\nSecond line."

        result = adapter._parse_output(raw_output)

        assert result == "Hello, this is the response.\nSecond line."

    def test_parse_output_with_system_messages(self) -> None:
        """Test _parse_output filtering out system messages."""
        adapter = CodexCLIAdapter()
        raw_output = (
            "[System] Starting...\n"
            "Hello, this is the response.\n"
            "▸ Tool execution log\n"
            "Second line of response."
        )

        result = adapter._parse_output(raw_output)

        # System messages should be filtered out
        assert "[System]" not in result
        assert "▸" not in result
        assert "Hello, this is the response." in result
        assert "Second line of response." in result

    def test_parse_output_empty_raises_error(self) -> None:
        """Test _parse_output with empty output raises LLMError."""
        adapter = CodexCLIAdapter()

        with pytest.raises(LLMError, match="Empty output from Codex CLI"):
            adapter._parse_output("")

    def test_parse_output_only_system_messages(self) -> None:
        """Test _parse_output with only system messages (fallback)."""
        adapter = CodexCLIAdapter()
        raw_output = "[System] Starting...\n▸ Tool execution log"

        # Should fallback to original output when no meaningful lines
        result = adapter._parse_output(raw_output)

        assert result == raw_output.strip()

    def test_parse_output_with_empty_lines(self) -> None:
        """Test _parse_output handles empty lines correctly."""
        adapter = CodexCLIAdapter()
        raw_output = (
            "First line.\n"
            "\n"
            "Second line.\n"
            "\n\n"
            "Third line."
        )

        result = adapter._parse_output(raw_output)

        # Empty lines should be preserved in meaningful content
        assert "First line." in result
        assert "Second line." in result
        assert "Third line." in result
