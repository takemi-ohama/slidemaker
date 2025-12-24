"""Request schemas for the Slidemaker API.

This module defines Pydantic models for validating incoming API requests.
All models include comprehensive validation to ensure data integrity and security.
"""

from __future__ import annotations

import base64
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, Field, field_validator

from slidemaker.core.models.common import SlideSize
from slidemaker.core.models.slide_config import BackgroundConfig

if TYPE_CHECKING:
    from slidemaker.core.models.slide_config import SlideConfig


class SlideConfigSchema(BaseModel):
    """Simplified slide configuration schema for API requests.

    This schema provides a subset of SlideConfig fields commonly used in API requests,
    with sensible defaults for omitted fields.
    """

    size: SlideSize = Field(
        default=SlideSize.WIDESCREEN_16_9,
        description="Slide size format (16:9 widescreen or 4:3 standard)",
    )
    width: int = Field(
        default=1920, gt=0, le=10000, description="Slide width in pixels (1-10000)"
    )
    height: int = Field(
        default=1080, gt=0, le=10000, description="Slide height in pixels (1-10000)"
    )
    background_color: str = Field(
        default="#FFFFFF", description="Background color in hex format (e.g., '#FFFFFF')"
    )
    default_font_family: str = Field(
        default="Arial", min_length=1, max_length=100, description="Default font family name"
    )
    default_font_size: int = Field(
        default=18, gt=0, le=100, description="Default font size in points (1-100)"
    )

    @field_validator("background_color")
    @classmethod
    def validate_hex_color(cls, v: str) -> str:
        """Validate hex color format.

        Args:
            v: Hex color string

        Returns:
            Validated hex color string

        Raises:
            ValueError: If color format is invalid
        """
        if not v.startswith("#") or len(v) not in (4, 7):
            raise ValueError(
                "Invalid hex color format. Must be '#RGB' or '#RRGGBB' (e.g., '#FFF' or '#FFFFFF')"
            )
        try:
            # Validate hex digits
            int(v[1:], 16)
        except ValueError as e:
            raise ValueError(
                f"Invalid hex color value: {v}. Must contain only hex digits (0-9, A-F)"
            ) from e
        return v.upper()

    def to_slide_config(self) -> SlideConfig:
        """Convert to SlideConfig model.

        Returns:
            SlideConfig: Core domain model for slide configuration
        """
        from slidemaker.core.models.slide_config import SlideConfig

        return SlideConfig(
            size=self.size,
            width=self.width,
            height=self.height,
            background=BackgroundConfig.from_color(self.background_color),
            default_font_family=self.default_font_family,
            default_font_size=self.default_font_size,
        )


class CreateSlideRequest(BaseModel):
    """Request schema for creating slides from Markdown content.

    This endpoint generates PowerPoint slides from Markdown text using LLM composition.
    """

    content: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="Markdown content for slide generation (1-50000 characters)",
    )
    config: SlideConfigSchema | None = Field(
        default=None,
        description="Optional slide configuration. If omitted, defaults are used.",
    )
    output_filename: str | None = Field(
        default=None,
        max_length=255,
        description="Optional output filename (max 255 characters). Auto-generated if omitted.",
    )

    @field_validator("output_filename")
    @classmethod
    def validate_output_filename(cls, v: str | None) -> str | None:
        """Validate output filename to prevent path traversal attacks.

        Args:
            v: Output filename

        Returns:
            Validated filename

        Raises:
            ValueError: If filename contains path traversal characters
        """
        if v is None:
            return v

        # Security: Prevent path traversal
        if ".." in v:
            raise ValueError(
                "Invalid output filename: path traversal characters (..) are not allowed"
            )

        # Security: Prevent absolute paths
        if v.startswith("/") or v.startswith("\\"):
            raise ValueError("Invalid output filename: absolute paths are not allowed")

        # Security: Prevent directory separators
        if "/" in v or "\\" in v:
            raise ValueError(
                "Invalid output filename: directory separators (/ or \\) are not allowed"
            )

        return v


class ConvertSlideRequest(BaseModel):
    """Request schema for converting PDF/images to PowerPoint slides.

    This endpoint analyzes PDF or image files using LLM and reconstructs them
    as editable PowerPoint presentations.
    """

    file_data: str = Field(
        ..., min_length=1, description="Base64-encoded file data (PDF or image)"
    )
    file_type: Literal["pdf", "image"] = Field(
        ..., description="File type: 'pdf' for PDF files, 'image' for image files"
    )
    config: SlideConfigSchema | None = Field(
        default=None,
        description="Optional slide configuration. If omitted, defaults are used.",
    )
    output_filename: str | None = Field(
        default=None,
        max_length=255,
        description="Optional output filename (max 255 characters). Auto-generated if omitted.",
    )

    @field_validator("file_data")
    @classmethod
    def validate_base64_and_size(cls, v: str) -> str:
        """Validate Base64 format and decoded file size.

        Args:
            v: Base64-encoded file data

        Returns:
            Validated Base64 string

        Raises:
            ValueError: If Base64 format is invalid or file size exceeds limit
        """
        # Security: Validate Base64 format
        try:
            decoded = base64.b64decode(v, validate=True)
        except Exception as e:
            raise ValueError(
                f"Invalid Base64 encoding: {e}. File data must be properly Base64-encoded."
            ) from e

        # Security: Check file size limit (50MB)
        max_size = 50 * 1024 * 1024  # 50MB in bytes
        if len(decoded) > max_size:
            raise ValueError(
                f"File size exceeds limit: {len(decoded)} bytes "
                f"(maximum allowed: {max_size} bytes / 50MB)"
            )

        return v

    @field_validator("output_filename")
    @classmethod
    def validate_output_filename(cls, v: str | None) -> str | None:
        """Validate output filename to prevent path traversal attacks.

        Args:
            v: Output filename

        Returns:
            Validated filename

        Raises:
            ValueError: If filename contains path traversal characters
        """
        if v is None:
            return v

        # Security: Prevent path traversal
        if ".." in v:
            raise ValueError(
                "Invalid output filename: path traversal characters (..) are not allowed"
            )

        # Security: Prevent absolute paths
        if v.startswith("/") or v.startswith("\\"):
            raise ValueError("Invalid output filename: absolute paths are not allowed")

        # Security: Prevent directory separators
        if "/" in v or "\\" in v:
            raise ValueError(
                "Invalid output filename: directory separators (/ or \\) are not allowed"
            )

        return v


class TaskStatusRequest(BaseModel):
    """Request schema for querying task status.

    This endpoint retrieves the status of an asynchronous slide generation task.
    """

    task_id: str = Field(
        ...,
        min_length=36,
        max_length=36,
        description="Task ID in UUID format (36 characters)",
    )

    @field_validator("task_id")
    @classmethod
    def validate_uuid_format(cls, v: str) -> str:
        """Validate UUID format.

        Args:
            v: Task ID string

        Returns:
            Validated task ID

        Raises:
            ValueError: If task ID is not a valid UUID format
        """
        import uuid

        try:
            # Parse as UUID to validate format
            uuid.UUID(v)
        except ValueError as e:
            raise ValueError(
                f"Invalid task ID format: {v}. Must be a valid UUID (e.g., "
                "'550e8400-e29b-41d4-a716-446655440000')"
            ) from e

        return v
