"""Google Vertex AI Gemini adapter."""

from typing import Any

import google.auth
from google.auth.transport.requests import Request

from slidemaker.llm.adapters.api.base_api import APIAdapter


class VertexGeminiAdapter(APIAdapter):
    """Adapter for Google Vertex AI Gemini.

    Uses Application Default Credentials (ADC) for authentication.
    Requires GOOGLE_APPLICATION_CREDENTIALS environment variable or
    gcloud auth application-default login.

    Attributes:
        project_id: GCP project ID
        location: GCP location (e.g., 'us-central1', 'asia-northeast1')
        model: Model name (e.g., 'gemini-2.0-flash-exp', 'gemini-1.5-pro')
    """

    def __init__(
        self,
        model: str,
        api_key: str = "",  # Not used for Vertex AI
        timeout: int = 300,
        **extra_params: Any,
    ) -> None:
        """Initialize VertexGeminiAdapter.

        Args:
            model: Model name (e.g., 'gemini-3-pro-image-preview')
            api_key: Ignored for Vertex AI (uses ADC)
            timeout: Request timeout in seconds
            **extra_params: Additional parameters:
                - project_id: GCP project ID (required)
                - location: GCP location (default: 'us-central1', use 'global' for preview models)
                - api_version: API version (default: 'v1', use 'v1beta1' for preview models)
                - use_global_endpoint: Use global endpoint instead of regional (default: False)
                - max_tokens: Max output tokens
                - temperature: Temperature setting
        """
        # Extract Vertex AI specific params before calling super().__init__
        self.project_id = extra_params.pop("project_id", None)
        if not self.project_id:
            raise ValueError("project_id is required for Vertex AI Gemini")

        self.location = extra_params.pop("location", "us-central1")
        self.api_version = extra_params.pop("api_version", "v1")
        self.use_global_endpoint = extra_params.pop("use_global_endpoint", False)

        # Store generation params for later use
        self.max_tokens = extra_params.pop("max_tokens", 8192)
        self.temperature = extra_params.pop("temperature", 0.7)

        # Get credentials using Application Default Credentials with proper scopes
        self.credentials, _ = google.auth.default(
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )

        # Call parent constructor with only the parameters it accepts
        super().__init__(model=model, api_key=api_key, timeout=timeout)

    @property
    def api_base_url(self) -> str:
        """Get Vertex AI Gemini API base URL.
        
        Returns regional endpoint by default, or global endpoint if configured.
        """
        if self.use_global_endpoint:
            # Global endpoint (no region prefix in domain)
            return (
                f"https://aiplatform.googleapis.com/{self.api_version}/"
                f"projects/{self.project_id}/locations/{self.location}/"
                f"publishers/google/models/{self.model}:generateContent"
            )
        else:
            # Regional endpoint
            return (
                f"https://{self.location}-aiplatform.googleapis.com/{self.api_version}/"
                f"projects/{self.project_id}/locations/{self.location}/"
                f"publishers/google/models/{self.model}:generateContent"
            )

    def _get_headers(self) -> dict[str, str]:
        """Get Vertex AI Gemini headers with OAuth2 token."""
        # Refresh credentials if needed
        if not self.credentials.valid:
            self.credentials.refresh(Request())

        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.credentials.token}",
        }

    def _build_request_payload(
        self, prompt: str, system_prompt: str | None = None, **kwargs: Any
    ) -> dict[str, Any]:
        """Build Vertex AI Gemini request payload.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional parameters (max_tokens, temperature, image_data)

        Returns:
            Request payload dict
        """
        # Build contents
        contents = []

        # Add system instruction if provided
        system_instruction = None
        if system_prompt:
            system_instruction = {"parts": [{"text": system_prompt}]}

        # Build user message parts
        parts = []

        # Add image if provided (for vision tasks)
        if "image_data" in kwargs:
            image_data = kwargs["image_data"]
            parts.append({
                "inline_data": {
                    "mime_type": "image/png",
                    "data": image_data
                }
            })

        # Add text prompt
        parts.append({"text": prompt})

        contents.append({
            "role": "user",
            "parts": parts
        })

        # Build generation config
        generation_config = {
            "maxOutputTokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", self.temperature),
        }

        # Build payload
        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": generation_config,
        }

        # Add system instruction if provided
        if system_instruction:
            payload["systemInstruction"] = system_instruction

        return payload

    def _extract_text_response(self, response_data: dict[str, Any]) -> str:
        """Extract text from Vertex AI Gemini response.

        Args:
            response_data: API response data

        Returns:
            Extracted text content

        Raises:
            ValueError: If response format is invalid
        """
        if (
            "candidates" in response_data
            and response_data["candidates"]
            and "content" in response_data["candidates"][0]
            and "parts" in response_data["candidates"][0]["content"]
        ):
            parts = response_data["candidates"][0]["content"]["parts"]
            # Filter out thought parts and concatenate remaining text parts
            # Some models (like gemini-3-pro-image-preview) include 'thought': true parts
            text_parts = [
                part["text"] for part in parts 
                if "text" in part and not part.get("thought", False)
            ]
            
            if text_parts:
                return "".join(text_parts)

        raise ValueError(
            f"Invalid Vertex AI Gemini response format or no text content: {response_data}"
        )

    def _fix_json_errors(self, json_str: str) -> str:
        """Attempt to fix common JSON formatting errors.

        Args:
            json_str: Potentially malformed JSON string

        Returns:
            Fixed JSON string (best effort)
        """
        import re

        from slidemaker.utils.logger import get_logger

        logger = get_logger(__name__)
        original = json_str
        fixed = json_str

        # Fix 1: Remove trailing commas before closing brackets/braces
        # {"a": 1,} -> {"a": 1}
        # [1, 2,] -> [1, 2]
        fixed = re.sub(r',\s*([}\]])', r'\1', fixed)

        # Fix 2: Add missing colons between property names and values
        # "property" "value" -> "property": "value"
        # Only match if clearly a property name (in quotes) followed by a value
        fixed = re.sub(r'("\w+")\s+(["{[])', r'\1: \2', fixed)

        # Fix 3: Add missing commas between objects in arrays
        # [{"a":1}{"b":2}] -> [{"a":1},{"b":2}]
        fixed = re.sub(r'}\s*{', r'},{', fixed)

        # Fix 4: Add missing commas between properties
        # {"a":1"b":2} -> {"a":1,"b":2}
        fixed = re.sub(r'(["\d])\s*("[a-zA-Z_]+")\s*:', r'\1,\2:', fixed)

        # Fix 5: Fix unterminated strings at line endings
        # Look for lines ending with an odd number of quotes
        lines = fixed.split('\n')
        fixed_lines = []
        for line in lines:
            # Count unescaped quotes
            quote_count = len(re.findall(r'(?<!\\)"', line))
            # If odd number of quotes, string is unterminated
            if quote_count % 2 == 1:
                # Add closing quote before any trailing comma or bracket
                line = re.sub(r'(.*[^"])(\s*[,\]}]?\s*)$', r'\1"\2', line)
            fixed_lines.append(line)
        fixed = '\n'.join(fixed_lines)

        # Fix 6: Escape unescaped quotes in strings
        # This is complex and risky, so we only handle obvious cases
        # "content": "He said "hello"" -> "content": "He said \"hello\""
        # Pattern: inside strings, replace unescaped quotes with escaped quotes
        # We look for patterns like: "...text"text"..."
        fixed = re.sub(r'(:\s*"[^"]*)"([^"]*")', r'\1\"\2', fixed)

        # Fix 7: Balance braces and brackets (add missing closing ones)
        open_braces = fixed.count('{')
        close_braces = fixed.count('}')
        open_brackets = fixed.count('[')
        close_brackets = fixed.count(']')

        if open_braces > close_braces:
            fixed += '}' * (open_braces - close_braces)
        if open_brackets > close_brackets:
            fixed += ']' * (open_brackets - close_brackets)

        if fixed != original:
            logger.warning(
                "Attempted JSON auto-fix",
                fixes_applied=[
                    "trailing_commas",
                    "missing_colons",
                    "missing_commas",
                    "unterminated_strings",
                    "bracket_balancing"
                ]
            )

        return fixed

    async def generate_structured(
        self,
        prompt: str,
        system_prompt: str | None = None,
        schema: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generate structured JSON output with optional image data.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            schema: Optional JSON schema (not used by Gemini)
            **kwargs: Additional parameters including image_data

        Returns:
            Parsed JSON response

        Raises:
            LLMError: If generation or parsing fails
        """
        import json

        from slidemaker.llm.base import LLMError
        from slidemaker.utils.logger import get_logger

        logger = get_logger(__name__)

        try:
            # Add JSON instruction to prompt
            json_prompt = f"{prompt}\n\nOutput valid JSON only."

            # Pass through image_data if provided
            text_response = await self.generate_text(
                json_prompt, system_prompt, **kwargs
            )

            # Extract JSON from response
            json_str = self._extract_json(text_response)

            # Try to parse JSON
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as parse_error:
                # Attempt to fix common JSON errors
                logger.warning(
                    "JSON parse failed, attempting auto-fix",
                    error=str(parse_error),
                    json_excerpt=json_str[:200] if len(json_str) > 200 else json_str
                )

                fixed_json_str = self._fix_json_errors(json_str)

                try:
                    # Try parsing the fixed JSON
                    result = json.loads(fixed_json_str)
                    logger.info("JSON auto-fix successful")
                    return result
                except json.JSONDecodeError as fixed_error:
                    # Both original and fixed JSON failed
                    logger.error(
                        "JSON auto-fix failed",
                        original_error=str(parse_error),
                        fixed_error=str(fixed_error)
                    )
                    raise LLMError(f"Invalid JSON in response: {parse_error}") from parse_error

        except LLMError:
            # Re-raise LLMError as-is
            raise
        except Exception as e:
            logger.error("Structured generation failed", error=str(e), model=self.model)
            raise LLMError(f"Failed to generate structured output: {e}") from e
