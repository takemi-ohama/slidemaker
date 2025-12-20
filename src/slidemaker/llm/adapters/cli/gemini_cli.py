"""Gemini CLI adapter."""

import json
from typing import Any

from slidemaker.llm.adapters.cli.base_cli import CLIAdapter
from slidemaker.llm.base import LLMError
from slidemaker.utils.logger import get_logger

logger = get_logger(__name__)


class GeminiCLIAdapter(CLIAdapter):
    """Adapter for Google Gemini CLI (gcloud ai or gemini-cli)."""

    def __init__(
        self,
        cli_path: str = "gcloud",
        model: str = "gemini-2.0-flash-exp",
        timeout: int = 300,
        use_gcloud: bool = True,
    ) -> None:
        """
        Initialize Gemini CLI adapter.

        Args:
            cli_path: Path to CLI executable (default: "gcloud")
            model: Gemini model identifier (default: "gemini-2.0-flash-exp")
            timeout: Command timeout in seconds
            use_gcloud: Use gcloud ai command (True) or gemini-cli (False)

        Note:
            Two CLI options:
            1. gcloud ai (Google Cloud SDK): requires `gcloud` installed
            2. gemini-cli (standalone): requires separate installation

            This adapter supports both with `use_gcloud` parameter.
        """
        super().__init__(cli_path=cli_path, model=model, timeout=timeout)
        self.use_gcloud = use_gcloud
        logger.info(
            "Gemini CLI adapter initialized",
            use_gcloud=use_gcloud,
            cli_path=cli_path,
            model=model,
        )

    def _build_command(
        self, prompt: str, system_prompt: str | None = None, **kwargs: Any
    ) -> list[str]:
        """
        Build Gemini CLI command with arguments.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt (concatenated to prompt)
            **kwargs: Additional parameters (temperature, max_tokens)

        Returns:
            Command line as list of strings

        Note:
            gcloud ai syntax:
            gcloud ai models generate-text --model=MODEL --prompt=PROMPT [--temperature=TEMP]

            gemini-cli syntax (hypothetical):
            gemini-cli generate --model MODEL --prompt PROMPT [--temperature TEMP]

            System prompt is concatenated to user prompt as Gemini CLI
            doesn't have separate system prompt parameter.
        """
        if self.use_gcloud:
            return self._build_gcloud_command(prompt, system_prompt, **kwargs)
        else:
            return self._build_gemini_cli_command(prompt, system_prompt, **kwargs)

    def _build_gcloud_command(
        self, prompt: str, system_prompt: str | None = None, **kwargs: Any
    ) -> list[str]:
        """
        Build gcloud ai command.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional parameters

        Returns:
            gcloud command as list of strings

        Example:
            ["gcloud", "ai", "models", "generate-text",
             "--model=gemini-2.0-flash-exp",
             "--prompt=What is AI?",
             "--temperature=0.7",
             "--format=json"]
        """
        # Concatenate system prompt if provided
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        command = [
            self.cli_path,
            "ai",
            "models",
            "generate-text",
            f"--model={self.model}",
            f"--prompt={full_prompt}",
            "--format=json",  # Request JSON output for easier parsing
        ]

        # Add optional parameters
        if "temperature" in kwargs:
            command.append(f"--temperature={kwargs['temperature']}")

        if "max_tokens" in kwargs:
            command.append(f"--max-output-tokens={kwargs['max_tokens']}")

        return command

    def _build_gemini_cli_command(
        self, prompt: str, system_prompt: str | None = None, **kwargs: Any
    ) -> list[str]:
        """
        Build gemini-cli command (hypothetical standalone CLI).

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional parameters

        Returns:
            gemini-cli command as list of strings

        Example:
            ["gemini-cli", "generate",
             "--model", "gemini-2.0-flash-exp",
             "--prompt", "What is AI?",
             "--temperature", "0.7"]

        Note:
            This is a hypothetical CLI interface. Adjust based on actual
            gemini-cli implementation if it becomes available.
        """
        # Concatenate system prompt if provided
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        command = [
            self.cli_path,
            "generate",
            "--model",
            self.model,
            "--prompt",
            full_prompt,
        ]

        # Add optional parameters
        if "temperature" in kwargs:
            command.extend(["--temperature", str(kwargs["temperature"])])

        if "max_tokens" in kwargs:
            command.extend(["--max-tokens", str(kwargs["max_tokens"])])

        return command

    def _parse_output(self, raw_output: str) -> str:
        """
        Parse Gemini CLI output and extract text.

        Args:
            raw_output: Raw standard output from CLI

        Returns:
            Extracted text content

        Raises:
            LLMError: If output parsing fails

        Note:
            gcloud ai output format (--format=json):
            {
              "candidates": [
                {
                  "content": {
                    "parts": [
                      {"text": "Generated text here"}
                    ]
                  }
                }
              ]
            }

            gemini-cli output format (hypothetical):
            Plain text or JSON with "text" field
        """
        if not raw_output.strip():
            raise LLMError("Empty output from Gemini CLI")

        try:
            if self.use_gcloud:
                return self._parse_gcloud_output(raw_output)
            else:
                return self._parse_gemini_cli_output(raw_output)

        except Exception as e:
            logger.error(
                "Failed to parse Gemini CLI output",
                error=str(e),
                output_preview=raw_output[:200],
            )
            raise LLMError(f"Failed to parse Gemini CLI output: {e}") from e

    def _parse_gcloud_output(self, raw_output: str) -> str:
        """
        Parse gcloud ai JSON output.

        Args:
            raw_output: Raw JSON output from gcloud

        Returns:
            Extracted text

        Raises:
            LLMError: If JSON parsing fails or format is invalid
        """
        try:
            data = json.loads(raw_output)

            # Navigate JSON structure: candidates[0].content.parts[0].text
            if "candidates" not in data or not data["candidates"]:
                raise LLMError("No candidates in gcloud response")

            candidate = data["candidates"][0]

            if "content" not in candidate:
                raise LLMError("No content in gcloud response candidate")

            content = candidate["content"]

            if "parts" not in content or not content["parts"]:
                raise LLMError("No parts in gcloud response content")

            part = content["parts"][0]

            if "text" not in part:
                raise LLMError("No text in gcloud response part")

            text_value = part["text"]
            if not isinstance(text_value, str):
                raise LLMError(f"Expected text to be str, got {type(text_value).__name__}")

            return text_value

        except json.JSONDecodeError as e:
            raise LLMError(f"Invalid JSON from gcloud: {e}") from e

    def _parse_gemini_cli_output(self, raw_output: str) -> str:
        """
        Parse gemini-cli output (hypothetical).

        Args:
            raw_output: Raw output from gemini-cli

        Returns:
            Extracted text

        Note:
            Assumes plain text output. If gemini-cli uses JSON,
            adjust parsing logic accordingly.
        """
        # Try JSON first
        try:
            data = json.loads(raw_output)
            if isinstance(data, dict):
                if "text" in data:
                    text_value = data["text"]
                    if isinstance(text_value, str):
                        return text_value
                elif "response" in data:
                    response_value = data["response"]
                    if isinstance(response_value, str):
                        return response_value
        except json.JSONDecodeError:
            pass

        # Fallback: treat as plain text
        return raw_output.strip()
