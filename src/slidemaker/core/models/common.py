"""Common data types and models for slidemaker."""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class SlideSize(str, Enum):
    """Standard slide sizes."""

    WIDESCREEN_16_9 = "16:9"
    STANDARD_4_3 = "4:3"
    A4 = "A4"
    LETTER = "letter"
    CUSTOM = "custom"


class Position(BaseModel):
    """Position in slide coordinates (pixels or units)."""

    x: int = Field(..., description="X coordinate from top-left")
    y: int = Field(..., description="Y coordinate from top-left")

    class Config:
        """Pydantic config."""

        frozen = True


class Size(BaseModel):
    """Size dimensions."""

    width: int = Field(..., gt=0, description="Width in pixels or units")
    height: int = Field(..., gt=0, description="Height in pixels or units")

    class Config:
        """Pydantic config."""

        frozen = True


class Color(BaseModel):
    """RGB color representation."""

    hex_value: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$", description="Hex color code")

    @classmethod
    def from_rgb(cls, r: int, g: int, b: int) -> "Color":
        """
        Create color from RGB values.

        Args:
            r: Red value (0-255)
            g: Green value (0-255)
            b: Blue value (0-255)

        Returns:
            Color instance

        Raises:
            ValueError: If any RGB value is not in range 0-255
        """
        if not all(isinstance(val, int) and 0 <= val <= 255 for val in (r, g, b)):
            raise ValueError(
                f"RGB values must be integers in range 0-255, got: r={r}, g={g}, b={b}"
            )
        return cls(hex_value=f"#{r:02x}{g:02x}{b:02x}")

    class Config:
        """Pydantic config."""

        frozen = True


class Alignment(str, Enum):
    """Text alignment options."""

    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    JUSTIFY = "justify"


class FitMode(str, Enum):
    """Image fit modes."""

    CONTAIN = "contain"  # Fit within area, maintain aspect ratio (with margins)
    COVER = "cover"  # Cover entire area, maintain aspect ratio (may crop)
    FILL = "fill"  # Fill the area, ignore aspect ratio (may distort)  # Stretch to fill, may distort


BackgroundType = Literal["color", "image", "gradient", "none"]
