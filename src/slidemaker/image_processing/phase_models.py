"""Data models for multi-phase image analysis."""

from typing import Any

from pydantic import BaseModel, Field


class ColumnDefinition(BaseModel):
    """Column definition in a multi-column layout."""

    index: int = Field(..., description="Column index (1-based)")
    x_start: float = Field(..., ge=0, description="Start X coordinate (pixels)")
    x_end: float = Field(..., ge=0, description="End X coordinate (pixels)")
    width: float = Field(..., ge=0, description="Column width (pixels)")


class HorizontalZone(BaseModel):
    """Horizontal zone in slide layout."""

    name: str = Field(..., description="Zone name (e.g., 'title', 'headers', 'descriptions')")
    y_start: float = Field(..., ge=0, description="Start Y coordinate (pixels)")
    y_end: float = Field(..., ge=0, description="End Y coordinate (pixels)")


class AlignmentRules(BaseModel):
    """Alignment rules for the layout."""

    same_row_elements_must_align: bool = Field(
        default=True, description="Elements in the same row must have identical Y coordinates"
    )
    column_headers_at_y: float | None = Field(
        default=None, ge=0, description="Y coordinate for column headers (pixels)"
    )
    column_descriptions_at_y: float | None = Field(
        default=None, ge=0, description="Y coordinate for column descriptions (pixels)"
    )


class LayoutMetadata(BaseModel):
    """Phase 1 output: Layout structure metadata."""

    layout_type: str = Field(
        ..., description="Layout type (e.g., 'single_column', 'two_column', 'three_column')"
    )
    columns: list[ColumnDefinition] = Field(default_factory=list, description="Column definitions")
    horizontal_zones: list[HorizontalZone] = Field(
        default_factory=list, description="Horizontal zones"
    )
    alignment_rules: AlignmentRules = Field(
        default_factory=AlignmentRules, description="Alignment rules"
    )
    title: str | None = Field(default=None, description="Detected slide title")
    background_color: str | None = Field(default=None, description="Background color hex code")


class RoughPosition(BaseModel):
    """Rough position."""

    x: float = Field(..., ge=0, description="X coordinate (pixels)")
    y: float = Field(..., ge=0, description="Y coordinate (pixels)")


class RoughSize(BaseModel):
    """Rough size."""

    width: float = Field(..., ge=0, description="Width (pixels)")
    height: float = Field(..., ge=0, description="Height (pixels)")


class RoughElement(BaseModel):
    """Phase 2 output: Element with rough positioning."""

    id: str = Field(..., description="Element ID (e.g., 'elem_1')")
    type: str = Field(..., description="Element type ('text' or 'image')")
    content_preview: str = Field(..., description="Content preview or description")
    zone: str | None = Field(default=None, description="Horizontal zone name")
    column: int | None = Field(default=None, ge=1, description="Column index (1-based)")
    rough_position: RoughPosition = Field(..., description="Rough position")
    rough_size: RoughSize = Field(..., description="Rough size")
    row_group: str | None = Field(
        default=None, description="Row group identifier for elements in the same row"
    )


class PrecisePosition(BaseModel):
    """Precise position."""

    x: float = Field(..., ge=0, description="X coordinate (pixels)")
    y: float = Field(..., ge=0, description="Y coordinate (pixels)")


class PreciseSize(BaseModel):
    """Precise size."""

    width: float = Field(..., ge=0, description="Width (pixels)")
    height: float = Field(..., ge=0, description="Height (pixels)")


class PreciseElement(BaseModel):
    """Phase 3 output: Element with precise coordinates."""

    id: str = Field(..., description="Element ID (from Phase 2)")
    type: str = Field(..., description="Element type ('text' or 'image')")
    content_preview: str = Field(..., description="Content preview or description")
    position: PrecisePosition = Field(..., description="Precise position")
    size: PreciseSize = Field(..., description="Precise size")
    alignment_group: str | None = Field(
        default=None, description="Alignment group (elements with same Y coordinate)"
    )
    aligned_y: float | None = Field(
        default=None, ge=0, description="Aligned Y coordinate for the group (pixels)"
    )


class ElementStyle(BaseModel):
    """Phase 4 output: Element style attributes."""

    font_family: str | None = Field(default=None, description="Font family")
    font_size: int | None = Field(default=None, gt=0, description="Font size (pt)")
    color: str | None = Field(default=None, description="Color hex code")
    bold: bool | None = Field(default=None, description="Bold flag")
    italic: bool | None = Field(default=None, description="Italic flag")
    underline: bool | None = Field(default=None, description="Underline flag")
    word_wrap: bool | None = Field(default=None, description="Word wrap flag")
    alignment: str | None = Field(default=None, description="Text alignment")
    line_spacing: float | None = Field(default=1.0, description="Line spacing multiplier (1.0-2.0)")


class StyledElement(BaseModel):
    """Complete element with style (final output)."""

    id: str = Field(..., description="Element ID")
    type: str = Field(..., description="Element type ('text' or 'image')")
    content: str = Field(..., description="Full content or description")
    position: PrecisePosition = Field(..., description="Position")
    size: PreciseSize = Field(..., description="Size")
    style: ElementStyle = Field(..., description="Style attributes")
    alt_text: str | None = Field(default=None, description="Alt text for images")
