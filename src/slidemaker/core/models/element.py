"""Element models for slide content."""

from typing import Literal

from pydantic import BaseModel, Field

from slidemaker.core.models.common import Alignment, Color, FitMode, Position, Size


class FontConfig(BaseModel):
    """Font configuration for text elements."""

    family: str = Field(default="Arial", description="Font family name")
    size: int = Field(default=18, gt=0, le=200, description="Font size in points")
    color: Color = Field(default_factory=lambda: Color(hex_value="#000000"))
    bold: bool = Field(default=False, description="Bold text")
    italic: bool = Field(default=False, description="Italic text")
    underline: bool = Field(default=False, description="Underline text")


class ElementDefinition(BaseModel):
    """Base class for slide elements."""

    element_type: str = Field(..., description="Type of element: 'text' or 'image'")
    position: Position = Field(..., description="Position on slide")
    size: Size = Field(..., description="Size of element")
    z_index: int = Field(default=0, description="Layer order (higher = on top)")
    opacity: float = Field(default=1.0, ge=0.0, le=1.0, description="Opacity (0=transparent, 1=opaque)")


class TextElement(ElementDefinition):
    """Text element on a slide."""

    element_type: Literal["text"] = "text"
    content: str = Field(..., description="Text content")
    font: FontConfig = Field(default_factory=FontConfig)
    alignment: Alignment = Field(default=Alignment.LEFT, description="Text alignment")
    line_spacing: float = Field(default=1.0, gt=0, le=3.0, description="Line spacing multiplier")


class ImageElement(ElementDefinition):
    """Image element on a slide."""

    element_type: Literal["image"] = "image"
    source: str = Field(..., description="Image file path or URL")
    fit_mode: FitMode = Field(default=FitMode.FIT, description="How image fits in the area")
    alt_text: str = Field(default="", description="Alternative text for accessibility")
