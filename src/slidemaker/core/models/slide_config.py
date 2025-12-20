"""Slide configuration models."""

from typing import Any

from pydantic import BaseModel, Field

from slidemaker.core.models.common import BackgroundType, SlideSize


class BackgroundConfig(BaseModel):
    """Background configuration for slides."""

    type: BackgroundType = Field(default="color", description="Background type")
    value: str | dict[str, Any] = Field(
        default="#FFFFFF", description="Background value (color hex, image path, or gradient config)"
    )

    @classmethod
    def from_color(cls, hex_color: str) -> "BackgroundConfig":
        """Create background from solid color."""
        return cls(type="color", value=hex_color)

    @classmethod
    def from_image(cls, image_path: str) -> "BackgroundConfig":
        """Create background from image."""
        return cls(type="image", value=image_path)


class SlideConfig(BaseModel):
    """Global configuration for the slide deck."""

    size: SlideSize = Field(default=SlideSize.WIDESCREEN_16_9, description="Slide size format")
    width: int = Field(default=1920, gt=0, description="Slide width in pixels (for 16:9)")
    height: int = Field(default=1080, gt=0, description="Slide height in pixels (for 16:9)")
    background: BackgroundConfig = Field(
        default_factory=lambda: BackgroundConfig.from_color("#FFFFFF"), description="Default background"
    )
    output_filename: str = Field(default="presentation.pptx", description="Output file name")
    theme: str | None = Field(default=None, description="Optional theme name")
    default_font_family: str = Field(default="Arial", description="Default font family")
    default_font_size: int = Field(default=18, gt=0, description="Default font size")

    @classmethod
    def create_16_9(cls, **kwargs: Any) -> "SlideConfig":
        """Create 16:9 widescreen configuration."""
        return cls(size=SlideSize.WIDESCREEN_16_9, width=1920, height=1080, **kwargs)

    @classmethod
    def create_4_3(cls, **kwargs: Any) -> "SlideConfig":
        """Create 4:3 standard configuration."""
        return cls(size=SlideSize.STANDARD_4_3, width=1024, height=768, **kwargs)
