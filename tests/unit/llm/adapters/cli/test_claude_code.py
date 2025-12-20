"""Tests for Claude Code CLI adapter."""

import pytest

from slidemaker.llm.adapters.cli.claude_code import ClaudeCodeAdapter


class TestClaudeCodeAdapter:
    """Test suite for ClaudeCodeAdapter."""

    def test_init_default_values(self) -> None:
        """Test initialization with default values."""
        adapter = ClaudeCodeAdapter()

        assert adapter.cli_path == "claude-code"
        assert adapter.model == "claude-3-5-sonnet-20241022"
        assert adapter.timeout == 300

    def test_init_custom_values(self) -> None:
        """Test initialization with custom values."""
        adapter = ClaudeCodeAdapter(
            cli_path="/custom/path/claude-code",
            model="claude-3-opus-20240229",
            timeout=600,
        )

        assert adapter.cli_path == "/custom/path/claude-code"
        assert adapter.model == "claude-3-opus-20240229"
        assert adapter.timeout == 600

    def test_build_command_basic(self) -> None:
        """Test basic command building."""
        adapter = ClaudeCodeAdapter()
        command = adapter._build_command("Hello, world!")

        assert command[0] == "claude-code"
        assert "--model" in command
        assert "claude-3-5-sonnet-20241022" in command
        assert "--max-tokens" in command
        assert "4096" in command
        assert "--prompt" in command
        assert "Hello, world!" in command

    def test_build_command_with_system_prompt(self) -> None:
        """Test command building with system prompt."""
        adapter = ClaudeCodeAdapter()
        command = adapter._build_command(
            "User message", system_prompt="System instructions"
        )

        # System prompt should be prepended to user prompt
        prompt_index = command.index("--prompt") + 1
        full_prompt = command[prompt_index]

        assert "System instructions" in full_prompt
        assert "User message" in full_prompt
        assert full_prompt.startswith("System instructions")

    def test_build_command_with_max_tokens(self) -> None:
        """Test command building with custom max_tokens."""
        adapter = ClaudeCodeAdapter()
        command = adapter._build_command("Test", max_tokens=2000)

        assert "--max-tokens" in command
        max_tokens_index = command.index("--max-tokens") + 1
        assert command[max_tokens_index] == "2000"

    def test_build_command_with_temperature(self) -> None:
        """Test command building with temperature."""
        adapter = ClaudeCodeAdapter()
        command = adapter._build_command("Test", temperature=0.5)

        assert "--temperature" in command
        temp_index = command.index("--temperature") + 1
        assert command[temp_index] == "0.5"

    def test_build_command_temperature_clamping_high(self) -> None:
        """Test temperature clamping for values > 1.0."""
        adapter = ClaudeCodeAdapter()
        command = adapter._build_command("Test", temperature=1.5)

        assert "--temperature" in command
        temp_index = command.index("--temperature") + 1
        assert command[temp_index] == "1.0"

    def test_build_command_temperature_clamping_low(self) -> None:
        """Test temperature clamping for values < 0.0."""
        adapter = ClaudeCodeAdapter()
        command = adapter._build_command("Test", temperature=-0.5)

        assert "--temperature" in command
        temp_index = command.index("--temperature") + 1
        assert command[temp_index] == "0.0"

    def test_parse_output_plain_text(self) -> None:
        """Test parsing plain text output."""
        adapter = ClaudeCodeAdapter()
        raw_output = "  This is a test response.  \n"

        parsed = adapter._parse_output(raw_output)

        assert parsed == "This is a test response."

    def test_parse_output_with_error_marker(self) -> None:
        """Test parsing output with ERROR marker."""
        adapter = ClaudeCodeAdapter()
        raw_output = "ERROR: Something went wrong"

        parsed = adapter._parse_output(raw_output)

        # Error marker should be preserved in output
        assert parsed == "ERROR: Something went wrong"

    def test_parse_output_with_warning_marker(self) -> None:
        """Test parsing output with WARNING marker."""
        adapter = ClaudeCodeAdapter()
        raw_output = "WARNING: Potential issue detected"

        parsed = adapter._parse_output(raw_output)

        # Warning marker should be preserved in output
        assert parsed == "WARNING: Potential issue detected"

    def test_parse_output_multiline(self) -> None:
        """Test parsing multiline output."""
        adapter = ClaudeCodeAdapter()
        raw_output = """
Line 1
Line 2
Line 3
        """

        parsed = adapter._parse_output(raw_output)

        assert "Line 1" in parsed
        assert "Line 2" in parsed
        assert "Line 3" in parsed
        # Leading/trailing whitespace should be stripped
        assert not parsed.startswith("\n")
        assert not parsed.endswith("\n" * 2)
