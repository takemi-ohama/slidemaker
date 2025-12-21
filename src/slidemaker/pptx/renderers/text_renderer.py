"""Text element renderer for PowerPoint slides."""

import structlog
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.slide import Slide
from pptx.text.text import _Run
from pptx.util import Pt

from slidemaker.core.models.common import Alignment, Color
from slidemaker.core.models.element import FontConfig, TextElement

logger = structlog.get_logger(__name__)


class TextRenderer:
    """Text element renderer.

    Renders TextElement instances onto PowerPoint slides, handling:
    - Text box creation with position and size
    - Font settings (name, size, color, bold, italic)
    - Text alignment (left, center, right, justify)
    """

    def render(self, slide: Slide, text_element: TextElement) -> None:
        """Render a text element onto a slide.

        Args:
            slide: Target slide to render on
            text_element: Text element definition to render

        Raises:
            ValueError: If position or size values are invalid
        """
        logger.info(
            "Rendering text element",
            position=text_element.position,
            size=text_element.size,
            content_length=len(text_element.content),
        )

        # Convert Position and Size (EMU) to python-pptx values
        # Position and Size models store EMU values directly as integers
        # python-pptx accepts int values as EMU, but type hints expect Length
        # We cast to int to satisfy both runtime and type checking
        left = int(text_element.position.x)
        top = int(text_element.position.y)
        width = int(text_element.size.width)
        height = int(text_element.size.height)

        # Validate values are positive
        if not all(val >= 0 for val in [left, top, width, height]):
            raise ValueError(
                f"Position and size must be non-negative: "
                f"left={left}, top={top}, width={width}, height={height}"
            )

        # Add text box to slide (python-pptx accepts int as EMU despite type hints)
        textbox = slide.shapes.add_textbox(left, top, width, height)  # type: ignore[arg-type]
        text_frame = textbox.text_frame

        # Set text content
        text_frame.text = text_element.content

        # Apply font settings and alignment to ALL paragraphs
        # (text_element.content may contain newlines, creating multiple paragraphs)
        for paragraph in text_frame.paragraphs:
            # Apply alignment
            paragraph.alignment = self._convert_alignment(text_element.alignment)

            # Apply line spacing
            paragraph.line_spacing = text_element.line_spacing

            # Apply font settings to all runs in this paragraph
            for run in paragraph.runs:
                self._apply_font_settings(run, text_element.font)

        logger.debug(
            "Text element rendered successfully",
            position=(left, top),
            size=(width, height),
            alignment=text_element.alignment,
            line_spacing=text_element.line_spacing,
        )

    def _apply_font_settings(self, run: _Run, font_config: FontConfig) -> None:
        """Apply font settings to a text run.

        Args:
            run: Text run object (pptx.text.text._Run)
            font_config: Font configuration to apply

        Note:
            This is a private method called internally by render().
        """
        font = run.font

        # Font family
        font.name = font_config.family

        # Font size (convert points to EMU)
        font.size = Pt(font_config.size)

        # Font style
        font.bold = font_config.bold
        font.italic = font_config.italic
        font.underline = font_config.underline

        # Font color
        rgb = self._convert_color(font_config.color)
        font.color.rgb = rgb

    def _convert_alignment(self, alignment: Alignment) -> PP_ALIGN:
        """Convert Alignment enum to python-pptx PP_ALIGN enum.

        Args:
            alignment: Alignment enum value

        Returns:
            PP_ALIGN: Corresponding python-pptx alignment constant

        Raises:
            ValueError: If alignment value is not supported
        """
        alignment_map = {
            Alignment.LEFT: PP_ALIGN.LEFT,
            Alignment.CENTER: PP_ALIGN.CENTER,
            Alignment.RIGHT: PP_ALIGN.RIGHT,
            Alignment.JUSTIFY: PP_ALIGN.JUSTIFY,
        }

        if alignment not in alignment_map:
            raise ValueError(f"Unsupported alignment: {alignment}")

        return alignment_map[alignment]

    def _convert_color(self, color: Color) -> RGBColor:
        """Convert Color model to python-pptx RGBColor.

        Args:
            color: Color model with hex_value

        Returns:
            RGBColor: python-pptx RGB color object

        Raises:
            ValueError: If hex color value is invalid format

        Note:
            Color model validates hex format (#RRGGBB) via Pydantic,
            but we validate RGB range (0-255) here for robustness.
        """
        # Parse hex color (format: #RRGGBB)
        hex_value = color.hex_value
        if not hex_value.startswith("#") or len(hex_value) != 7:
            raise ValueError(f"Invalid hex color format: {hex_value}")

        try:
            r = int(hex_value[1:3], 16)
            g = int(hex_value[3:5], 16)
            b = int(hex_value[5:7], 16)
        except ValueError as e:
            raise ValueError(f"Invalid hex color value: {hex_value}") from e

        # Validate RGB range (0-255) - already validated by Pydantic but double-check
        if not all(0 <= val <= 255 for val in [r, g, b]):
            raise ValueError(f"RGB values must be in range 0-255: r={r}, g={g}, b={b}")

        # RGBColor constructor is untyped in python-pptx stubs
        return RGBColor(r, g, b)  # type: ignore[no-untyped-call]
