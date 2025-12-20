"""Claude Code CLI adapter."""

from typing import Any

from slidemaker.llm.adapters.cli.base_cli import CLIAdapter
from slidemaker.utils.logger import get_logger

logger = get_logger(__name__)


class ClaudeCodeAdapter(CLIAdapter):
    """Adapter for Claude Code CLI tool."""

    def __init__(
        self,
        cli_path: str = "claude-code",
        model: str = "claude-3-5-sonnet-20241022",
        timeout: int = 300,
    ) -> None:
        """
        Initialize Claude Code adapter.

        Args:
            cli_path: Path to claude-code executable (default: "claude-code")
            model: Claude model identifier (default: claude-3-5-sonnet-20241022)
            timeout: Command timeout in seconds (default: 300)
        """
        super().__init__(cli_path=cli_path, model=model, timeout=timeout)
        logger.info(
            "Claude Code adapter initialized",
            cli_path=cli_path,
            model=model,
            timeout=timeout,
        )

    def _build_command(
        self, prompt: str, system_prompt: str | None = None, **kwargs: Any
    ) -> list[str]:
        """
        Build Claude Code CLI command with arguments.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt (not directly supported by claude-code,
                will be prepended to prompt if provided)
            **kwargs: Additional CLI-specific parameters:
                - max_tokens (int): Maximum tokens to generate (default: 4096)
                - temperature (float): Sampling temperature (0.0-1.0, default: 1.0)

        Returns:
            Command line as list of strings for subprocess

        Example:
            >>> adapter._build_command("Hello", max_tokens=1000)
            ["claude-code", "--model", "claude-3-5-sonnet-20241022",
             "--max-tokens", "1000", "--prompt", "Hello"]
        """
        command = [self.cli_path]

        # Add model parameter
        command.extend(["--model", self.model])

        # Add optional max_tokens parameter
        max_tokens = kwargs.get("max_tokens", 4096)
        command.extend(["--max-tokens", str(max_tokens)])

        # Add optional temperature parameter
        if "temperature" in kwargs:
            temperature = kwargs["temperature"]
            if not 0.0 <= temperature <= 1.0:
                logger.warning(
                    "Temperature out of range, clamping to [0.0, 1.0]",
                    temperature=temperature,
                )
                temperature = max(0.0, min(1.0, temperature))
            command.extend(["--temperature", str(temperature)])

        # Combine system prompt with user prompt if provided
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
            logger.debug("System prompt prepended to user prompt")

        # Add prompt (must be last argument)
        command.extend(["--prompt", full_prompt])

        logger.debug(
            "Command built",
            command_length=len(command),
            prompt_length=len(full_prompt),
        )

        return command

    def _parse_output(self, raw_output: str) -> str:
        """
        Parse Claude Code CLI output and extract response text.

        Args:
            raw_output: Raw standard output from claude-code CLI

        Returns:
            Extracted text content

        Note:
            Claude Code CLI returns the response text directly without
            additional formatting or metadata. This method strips whitespace
            and returns the cleaned output.

            If the output contains error messages or warnings prefixed with
            special markers (e.g., "ERROR:", "WARNING:"), they are logged
            but not removed from the output. Callers should handle errors
            via subprocess exceptions before reaching this method.
        """
        # Claude Code returns plain text response directly
        cleaned_output = raw_output.strip()

        # Log potential error/warning markers (defensive programming)
        if cleaned_output.startswith("ERROR:"):
            logger.error(
                "Claude Code CLI returned error in output", output=cleaned_output[:200]
            )
        elif cleaned_output.startswith("WARNING:"):
            logger.warning(
                "Claude Code CLI returned warning in output", output=cleaned_output[:200]
            )

        logger.debug("Output parsed", output_length=len(cleaned_output))

        return cleaned_output
