"""Base class for CLI-based LLM adapters."""

import json
import subprocess
from abc import abstractmethod
from typing import Any, cast

from slidemaker.llm.base import LLMAdapter, LLMError, LLMTimeoutError
from slidemaker.utils.logger import get_logger

logger = get_logger(__name__)


class CLIAdapter(LLMAdapter):
    """Base class for CLI-based LLM adapters."""

    def __init__(self, cli_path: str, model: str, timeout: int = 300) -> None:
        """
        Initialize CLI adapter.

        Args:
            cli_path: Path to CLI executable
            model: Model identifier
            timeout: Command timeout in seconds
        """
        super().__init__(model=model, timeout=timeout)
        self.cli_path = cli_path
        logger.info(
            "CLI adapter initialized",
            cli_path=cli_path,
            model=model,
            timeout=timeout,
        )

    @abstractmethod
    def _build_command(
        self, prompt: str, system_prompt: str | None = None, **kwargs: Any
    ) -> list[str]:
        """
        Build CLI command with arguments.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional CLI-specific parameters

        Returns:
            Command line as list of strings (for subprocess)

        Note:
            Subclasses must implement this to construct CLI commands
            appropriate for their specific tool (e.g., llm, aichat).
        """
        pass

    def _run_cli(self, command: list[str]) -> str:
        """
        Execute CLI command and return output.

        Args:
            command: Command line as list of strings

        Returns:
            Raw standard output from CLI

        Raises:
            LLMTimeoutError: If command times out
            LLMError: If command fails

        Security:
            Command is executed with shell=False (default) to prevent
            command injection vulnerabilities. The command argument must
            be a list of strings, not a single string.
        """
        try:
            logger.debug("Executing CLI command", command=" ".join(command))

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=True,
                shell=False,  # Explicitly disable shell to prevent command injection
            )

            logger.debug(
                "CLI command completed",
                stdout_length=len(result.stdout),
                stderr_length=len(result.stderr),
            )

            return result.stdout

        except subprocess.TimeoutExpired as e:
            logger.error(
                "CLI command timed out",
                timeout=self.timeout,
                command=" ".join(command),
            )
            raise LLMTimeoutError(
                f"CLI command timed out after {self.timeout}s"
            ) from e

        except subprocess.CalledProcessError as e:
            logger.error(
                "CLI command failed",
                returncode=e.returncode,
                stderr=e.stderr,
                command=" ".join(command),
            )
            raise LLMError(
                f"CLI command failed (exit code {e.returncode}): {e.stderr}"
            ) from e

        except Exception as e:
            logger.error("Unexpected error running CLI", error=str(e))
            raise LLMError(f"Failed to execute CLI command: {e}") from e

    @abstractmethod
    def _parse_output(self, raw_output: str) -> str:
        """
        Parse CLI output and extract text.

        Args:
            raw_output: Raw standard output from CLI

        Returns:
            Extracted text content

        Note:
            Subclasses must implement this to handle their specific
            output format (e.g., plain text, JSON, YAML).
        """
        pass

    async def generate_text(
        self, prompt: str, system_prompt: str | None = None, **kwargs: Any
    ) -> str:
        """
        Generate text completion using CLI.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional CLI-specific parameters

        Returns:
            Generated text

        Raises:
            LLMTimeoutError: If command times out
            LLMError: If generation fails
        """
        try:
            command = self._build_command(prompt, system_prompt, **kwargs)
            raw_output = self._run_cli(command)
            parsed_text = self._parse_output(raw_output)

            logger.info(
                "Text generation completed",
                model=self.model,
                output_length=len(parsed_text),
            )

            return parsed_text

        except (LLMTimeoutError, LLMError):
            raise
        except Exception as e:
            logger.error("Text generation failed", error=str(e), model=self.model)
            raise LLMError(f"Failed to generate text: {e}") from e

    async def generate_structured(
        self,
        prompt: str,
        system_prompt: str | None = None,
        schema: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Generate structured JSON output using CLI.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            schema: Optional JSON schema for validation
                (currently unused, reserved for future implementation)

        Returns:
            Structured output as dictionary

        Raises:
            LLMTimeoutError: If command times out
            LLMError: If generation or parsing fails

        Note:
            The schema parameter is currently not used for validation.
            This is reserved for future implementation with jsonschema library.
        """
        try:
            # Add JSON instruction to prompt
            json_prompt = f"{prompt}\n\nOutput valid JSON only."

            # Generate text response
            text_response = await self.generate_text(json_prompt, system_prompt)

            # Extract and parse JSON
            json_str = self._extract_json(text_response)
            parsed_json = json.loads(json_str)

            # Validate that output is a dictionary
            if not isinstance(parsed_json, dict):
                raise LLMError(
                    f"Expected JSON object (dict), got {type(parsed_json).__name__}. "
                    f"Response preview: {str(parsed_json)[:200]}"
                )

            structured_output = cast(dict[str, Any], parsed_json)

            logger.info(
                "Structured generation completed",
                model=self.model,
                keys=list(structured_output.keys()),
            )

            return structured_output

        except json.JSONDecodeError as e:
            logger.error(
                "Failed to parse JSON response",
                error=str(e),
                response_preview=text_response[:200],
            )
            raise LLMError(f"Invalid JSON in response: {e}") from e
        except (LLMTimeoutError, LLMError):
            raise
        except Exception as e:
            logger.error("Structured generation failed", error=str(e), model=self.model)
            raise LLMError(f"Failed to generate structured output: {e}") from e

    @staticmethod
    def _extract_json(text: str) -> str:
        """
        Extract JSON from text response.

        Args:
            text: Text containing JSON

        Returns:
            Extracted JSON string

        Note:
            This method tries multiple strategies to extract JSON:
            1. Markdown code blocks (```json or ```)
            2. First JSON object ({...})
            3. Raw text (as fallback)
        """
        # Try to find JSON in markdown code blocks
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end != -1:
                return text[start:end].strip()

        if "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end != -1:
                return text[start:end].strip()

        # Try to find JSON object
        if "{" in text and "}" in text:
            start = text.find("{")
            end = text.rfind("}") + 1
            return text[start:end]

        # Fallback: return as-is
        return text.strip()
