"""Core data models for slidemaker."""

from slidemaker.core.models.common import (
    Alignment,
    Color,
    FitMode,
    Position,
    Size,
    SlideSize,
)
from slidemaker.core.models.element import (
    ElementDefinition,
    FontConfig,
    ImageElement,
    TextElement,
)
from slidemaker.core.models.page_definition import PageDefinition
from slidemaker.core.models.slide_config import BackgroundConfig, SlideConfig

__all__ = [
    # Common types
    "Alignment",
    "Color",
    "FitMode",
    "Position",
    "Size",
    "SlideSize",
    # Elements
    "ElementDefinition",
    "FontConfig",
    "ImageElement",
    "TextElement",
    # Page
    "PageDefinition",
    # Config
    "BackgroundConfig",
    "SlideConfig",
]
