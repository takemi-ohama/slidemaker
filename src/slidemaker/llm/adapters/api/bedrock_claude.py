"""AWS Bedrock adapter for Claude models."""

import asyncio
import json
from typing import Any

import boto3

from slidemaker.llm.base import (
    LLMAdapter,
    LLMAuthenticationError,
    LLMError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from slidemaker.utils.logger import get_logger

logger = get_logger(__name__)


class BedrockClaudeAdapter(LLMAdapter):
    """Adapter for Claude models via AWS Bedrock."""

    # Bedrock model ID mapping
    MODEL_ID_MAPPING = {
        "claude-3-5-sonnet-20241022": "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "claude-3-5-haiku-20241022": "anthropic.claude-3-5-haiku-20241022-v1:0",
        "claude-3-opus-20240229": "anthropic.claude-3-opus-20240229-v1:0",
        "claude-3-sonnet-20240229": "anthropic.claude-3-sonnet-20240229-v1:0",
        "claude-3-haiku-20240307": "anthropic.claude-3-haiku-20240307-v1:0",
    }

    def __init__(
        self,
        model: str,
        region: str = "us-east-1",
        timeout: int = 300,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> None:
        """
        Initialize Bedrock Claude adapter.

        Args:
            model: Model identifier (e.g., "claude-3-5-sonnet-20241022")
            region: AWS region name
            timeout: Request timeout in seconds
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            **kwargs: Additional parameters

        Raises:
            ValueError: If model is not supported for Bedrock
        """
        super().__init__(model=model, timeout=timeout)
        self.region = region
        self.max_tokens = max_tokens
        self.temperature = temperature

        # Initialize Bedrock Runtime client
        self.bedrock_runtime = boto3.client(
            service_name="bedrock-runtime",
            region_name=self.region,
        )

        # Validate and get Bedrock model ID
        self.bedrock_model_id = self._get_bedrock_model_id()

        logger.info(
            "BedrockClaudeAdapter initialized",
            model=model,
            bedrock_model_id=self.bedrock_model_id,
            region=region,
        )

    def _get_bedrock_model_id(self) -> str:
        """
        Convert model name to Bedrock-compatible model ID.

        Returns:
            Bedrock model ID

        Raises:
            ValueError: If model is not supported
        """
        # Check if already in Bedrock format
        if self.model.startswith("anthropic."):
            return self.model

        # Check mapping
        if self.model in self.MODEL_ID_MAPPING:
            return self.MODEL_ID_MAPPING[self.model]

        raise ValueError(
            f"Unsupported model for Bedrock: {self.model}. "
            f"Supported models: {list(self.MODEL_ID_MAPPING.keys())}"
        )

    async def generate_text(
        self,
        prompt: str,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Generate text completion using Bedrock.

        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            **kwargs: Additional parameters (max_tokens, temperature, etc.)

        Returns:
            Generated text

        Raises:
            LLMTimeoutError: If request times out
            LLMAuthenticationError: If authentication fails
            LLMRateLimitError: If rate limit exceeded
            LLMError: For other errors
        """
        try:
            # Build request body
            request_body = self._build_request_body(prompt, system_prompt, **kwargs)

            # Invoke model via Bedrock
            response = await self._invoke_model(request_body)

            # Extract text from response
            return self._extract_text_response(response)

        except TimeoutError as e:
            raise LLMTimeoutError(f"Request timed out after {self.timeout}s") from e
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
        Generate structured JSON output using Bedrock.

        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            schema: JSON schema for validation (optional, not enforced by Bedrock)

        Returns:
            Parsed JSON response

        Raises:
            LLMError: If JSON parsing fails or generation fails
        """
        try:
            # Add JSON instruction to prompt
            json_prompt = f"{prompt}\n\nOutput valid JSON only."
            text_response = await self.generate_text(json_prompt, system_prompt)

            # Extract JSON from response
            json_str = self._extract_json(text_response)
            return json.loads(json_str)

        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON response", error=str(e))
            raise LLMError(f"Invalid JSON in response: {e}") from e
        except Exception as e:
            logger.error("Structured generation failed", error=str(e), model=self.model)
            raise LLMError(f"Failed to generate structured output: {e}") from e

    async def analyze_image(
        self,
        image_data: bytes | str,
        prompt: str,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Analyze image using Bedrock Claude Vision API.

        Args:
            image_data: Image bytes (PNG/JPEG) or Base64-encoded string
            prompt: Analysis prompt
            system_prompt: Optional system prompt
            **kwargs: Additional parameters

        Returns:
            Parsed JSON response

        Raises:
            LLMError: If analysis fails
        """
        import base64

        try:
            # Handle both bytes and base64 string
            if isinstance(image_data, str):
                # Decode base64 string to bytes for format detection
                image_bytes = base64.b64decode(image_data)
                image_base64 = image_data
            else:
                # Raw bytes - detect format and encode
                image_bytes = image_data
                image_base64 = base64.b64encode(image_data).decode("utf-8")

            # Detect image format from bytes
            media_type = self._detect_image_type(image_bytes)

            # Build request body with image
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                "temperature": kwargs.get("temperature", self.temperature),
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_base64,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt,
                            },
                        ],
                    }
                ],
            }

            # Add system prompt if provided
            if system_prompt:
                request_body["system"] = system_prompt

            # Invoke model
            response = await self._invoke_model(request_body)

            # Parse JSON response
            text_response = self._extract_text_response(response)
            logger.debug(
                "LLM response extracted",
                text_length=len(text_response),
                text_preview=text_response[:200] if text_response else "(empty)",
            )

            # Try to parse as JSON
            if not text_response or not text_response.strip():
                raise ValueError("Empty response from LLM")

            # Remove markdown code block if present
            cleaned_response = text_response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]  # Remove ```json
            elif cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:]  # Remove ```

            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]  # Remove trailing ```

            cleaned_response = cleaned_response.strip()

            try:
                return json.loads(cleaned_response)
            except json.JSONDecodeError as json_error:
                logger.error(
                    "JSON parsing failed",
                    error=str(json_error),
                    model=self.model,
                    response_length=len(cleaned_response),
                    response_sample=cleaned_response[:500] + "..."
                    if len(cleaned_response) > 500
                    else cleaned_response,
                )
                raise

        except Exception as e:
            logger.error("Image analysis failed", error=str(e), model=self.model)
            raise LLMError(f"Failed to analyze image: {e}") from e

    def _build_request_body(
        self,
        prompt: str,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Build Bedrock request body.

        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            **kwargs: Additional parameters

        Returns:
            Request body dictionary
        """
        request_body: dict[str, Any] = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", self.temperature),
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        }

        if system_prompt:
            request_body["system"] = system_prompt

        return request_body

    async def _invoke_model(self, request_body: dict[str, Any]) -> dict[str, Any]:
        """
        Invoke Bedrock model.

        Args:
            request_body: Request body dictionary

        Returns:
            Response body dictionary

        Raises:
            LLMAuthenticationError: If authentication fails
            LLMRateLimitError: If rate limit exceeded
            LLMError: For other errors
        """
        try:
            # Run boto3 call in thread pool (boto3 is synchronous)
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.bedrock_runtime.invoke_model,
                    modelId=self.bedrock_model_id,
                    body=json.dumps(request_body),
                ),
                timeout=self.timeout,
            )

            # Parse response body
            response_body = json.loads(response["body"].read())
            return response_body

        except TimeoutError:
            raise
        except Exception as e:
            error_message = str(e)

            # Map AWS errors to LLM exceptions
            if (
                "UnrecognizedClientException" in error_message
                or "AccessDeniedException" in error_message
            ):
                raise LLMAuthenticationError(
                    f"AWS authentication failed: {error_message}"
                ) from e
            elif (
                "ThrottlingException" in error_message
                or "TooManyRequestsException" in error_message
            ):
                raise LLMRateLimitError(
                    f"Bedrock rate limit exceeded: {error_message}"
                ) from e
            else:
                raise LLMError(f"Bedrock API error: {error_message}") from e

    def _extract_text_response(self, response_body: dict[str, Any]) -> str:
        """
        Extract text from Bedrock response.

        Args:
            response_body: Response body dictionary

        Returns:
            Generated text

        Raises:
            ValueError: If response format is invalid
        """
        if "content" in response_body and response_body["content"]:
            return response_body["content"][0]["text"]
        raise ValueError("Invalid Bedrock response format")

    @staticmethod
    def _extract_json(text: str) -> str:
        """
        Extract JSON from text response.

        Args:
            text: Text containing JSON

        Returns:
            Extracted JSON string
        """
        # Try to find JSON in markdown code blocks
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            return text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            return text[start:end].strip()
        # Try to find JSON object
        elif "{" in text and "}" in text:
            start = text.find("{")
            end = text.rfind("}") + 1
            return text[start:end]
        return text.strip()

    @staticmethod
    def _detect_image_type(image_data: bytes) -> str:
        """
        Detect image media type from bytes.

        Args:
            image_data: Image bytes

        Returns:
            Media type string (e.g., "image/png")

        Raises:
            ValueError: If image format is not supported
        """
        # PNG signature
        if image_data[:8] == b"\x89PNG\r\n\x1a\n":
            return "image/png"
        # JPEG signature
        elif image_data[:2] == b"\xff\xd8":
            return "image/jpeg"
        else:
            raise ValueError("Unsupported image format. Only PNG and JPEG are supported.")

    async def close(self) -> None:
        """Close resources (boto3 client doesn't require explicit closing)."""
        logger.debug("BedrockClaudeAdapter closed")

    async def __aenter__(self) -> "BedrockClaudeAdapter":
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()
