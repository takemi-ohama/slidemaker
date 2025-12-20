"""
Codex CLI adapter for LLM integration.

This module provides the CodexCLIAdapter class, which integrates with
the Codex CLI tool (https://github.com/anthropics/claude-code) for
LLM text generation.
"""

from typing import Any

from slidemaker.llm.adapters.cli.base_cli import CLIAdapter
from slidemaker.llm.base import LLMError
from slidemaker.utils.logger import get_logger

logger = get_logger(__name__)


class CodexCLIAdapter(CLIAdapter):
    """Adapter for Codex CLI tool."""

    def __init__(
        self,
        cli_path: str = "codex",
        model: str = "claude-3-5-sonnet-20241022",
        timeout: int = 300,
    ) -> None:
        """
        Initialize Codex CLI adapter.

        Args:
            cli_path: Path to codex executable (default: "codex")
            model: Model identifier (default: "claude-3-5-sonnet-20241022")
            timeout: Command timeout in seconds (default: 300)

        Note:
            Codex CLI supports various Claude models. Common models:
            - claude-3-5-sonnet-20241022 (default, balanced)
            - claude-3-opus-20240229 (most capable)
            - claude-3-haiku-20240307 (fastest)
        """
        super().__init__(cli_path=cli_path, model=model, timeout=timeout)
        logger.info(
            "Codex CLI adapter initialized",
            cli_path=cli_path,
            model=model,
            timeout=timeout,
        )

    def _build_command(
        self, prompt: str, system_prompt: str | None = None, **kwargs: Any
    ) -> list[str]:
        """
        Build codex CLI command with arguments.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt (prepended to user prompt)
            **kwargs: Additional parameters:
                - sandbox: Sandbox mode ("read-only", "workspace-write",
                  "danger-full-access")
                - dangerously_bypass_approvals: Skip confirmations
                  (default: True for non-interactive)
                - skip_git_repo_check: Allow running outside Git repo
                  (default: True)
                - json_output: Enable JSON output format (default: False)

        Returns:
            Command line as list of strings

        Example:
            >>> adapter._build_command("Hello", system_prompt="You are helpful")
            ["codex", "exec", "--model", "claude-3-5-sonnet-20241022",
             "--dangerously-bypass-approvals-and-sandbox",
             "--skip-git-repo-check", "You are helpful\\n\\nHello"]
        """
        command = [
            self.cli_path,
            "exec",
            "--model",
            self.model,
        ]

        # Sandbox mode (default: danger-full-access for non-interactive use)
        sandbox = kwargs.get("sandbox")
        if sandbox:
            command.extend(["--sandbox", sandbox])

        # Bypass approvals and sandbox for non-interactive execution
        # (required for automated use)
        if kwargs.get("dangerously_bypass_approvals", True):
            command.append("--dangerously-bypass-approvals-and-sandbox")

        # Skip git repo check (allow running outside Git repositories)
        if kwargs.get("skip_git_repo_check", True):
            command.append("--skip-git-repo-check")

        # JSON output format
        if kwargs.get("json_output", False):
            command.append("--json")

        # Combine system prompt and user prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        command.append(full_prompt)

        logger.debug(
            "Built Codex command",
            command_length=len(command),
            has_system_prompt=system_prompt is not None,
        )

        return command

    def _parse_output(self, raw_output: str) -> str:
        """
        Parse Codex CLI output and extract text.

        Args:
            raw_output: Raw standard output from codex CLI

        Returns:
            Extracted text content

        Raises:
            LLMError: If output is empty or parsing fails

        Note:
            Codex CLI outputs plain text by default. If --json flag is used,
            the output is JSONL format with events, and we need to extract
            the final agent message. For simplicity, this implementation
            assumes plain text output (no --json flag).

            The output may contain:
            - Agent responses
            - Tool execution logs
            - System messages

            We extract only the meaningful agent responses by filtering
            out system/tool messages (lines starting with special markers).
        """
        # Validate input
        if not raw_output.strip():
            logger.error("Empty output from Codex CLI")
            raise LLMError("Empty output from Codex CLI")

        # For plain text output (no --json flag)
        lines = raw_output.strip().split("\n")
        meaningful_lines = []

        for line in lines:
            # Skip empty lines
            if not line.strip():
                continue

            # Skip system messages and tool execution logs
            # (these typically start with special prefixes or brackets)
            if line.startswith(("[", "▸", "▹", "►", ">")):
                continue

            # Keep meaningful agent responses
            meaningful_lines.append(line)

        # Validate extracted content
        if not meaningful_lines:
            logger.warning(
                "No meaningful content extracted from Codex output",
                original_lines=len(lines),
            )
            # Fallback: return original output if no meaningful lines found
            return raw_output.strip()

        extracted_text = "\n".join(meaningful_lines).strip()

        logger.debug(
            "Parsed Codex output",
            original_lines=len(lines),
            extracted_lines=len(meaningful_lines),
            extracted_length=len(extracted_text),
        )

        return extracted_text
