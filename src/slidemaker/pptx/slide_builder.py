"""Individual slide construction module.

This module provides the SlideBuilder class for constructing individual PowerPoint slides
from PageDefinition objects.
"""

from pathlib import Path

import structlog
from pptx.presentation import Presentation
from pptx.slide import Slide
from pptx.util import Inches

from slidemaker.core.models.common import Color
from slidemaker.core.models.element import ImageElement, TextElement
from slidemaker.core.models.page_definition import PageDefinition
from slidemaker.pptx.renderers.image_renderer import ImageRenderer
from slidemaker.pptx.renderers.text_renderer import TextRenderer

logger = structlog.get_logger(__name__)


class SlideBuilder:
    """Individual slide construction class.

    This class is responsible for constructing individual slides from PageDefinition objects.
    It handles:
    - Creating blank slides
    - Setting background colors
    - Setting background images
    - Placing elements (text and images) using renderers
    - Z-order control (managed by addition order)

    Attributes:
        presentation: The python-pptx Presentation object to add slides to.
        text_renderer: Renderer for text elements.
        image_renderer: Renderer for image elements.
    """

    def __init__(self, presentation: Presentation) -> None:
        """Initialize SlideBuilder.

        Args:
            presentation: The python-pptx Presentation object to add slides to.
        """
        self.presentation = presentation
        self.text_renderer = TextRenderer()
        self.image_renderer = ImageRenderer()
        logger.debug("SlideBuilder initialized")

    def build_slide(self, page_def: PageDefinition) -> Slide:
        """Build a slide from a PageDefinition.

        This method creates a blank slide and applies the page definition settings:
        1. Creates a blank slide using the Blank layout (index 6)
        2. Sets background color if specified
        3. Places elements in order (respecting z-index)

        Note:
            Background image support is not yet implemented in PageDefinition.
            The _set_background_image method is prepared for future use.

        Args:
            page_def: The page definition containing slide content and settings.

        Returns:
            Slide: The constructed python-pptx Slide object.

        Raises:
            ValueError: If page_def is invalid or contains invalid settings.

        Example:
            >>> builder = SlideBuilder(presentation)
            >>> page_def = PageDefinition(
            ...     page_number=1,
            ...     title="Sample Slide",
            ...     background_color="#FFFFFF"
            ... )
            >>> slide = builder.build_slide(page_def)
        """
        logger.info("Building slide", page_number=page_def.page_number, title=page_def.title)

        # Create a blank slide (layout index 6 is typically Blank)
        blank_layout = self.presentation.slide_layouts[6]
        slide = self.presentation.slides.add_slide(blank_layout)

        # Set background color if specified
        if page_def.background_color:
            self._set_background_color(slide, Color(hex_value=page_def.background_color))
            logger.debug("Background color set", color=page_def.background_color)

        # Sort elements by z-index before placing them
        page_def.sort_elements_by_z_index()

        # Place elements using renderers
        for element in page_def.elements:
            element_type = element.element_type
            if element_type == "text":
                # Type check: ensure element is TextElement before rendering
                if isinstance(element, TextElement):
                    self.text_renderer.render(slide, element)
                    logger.debug("Text element rendered", element_type=element_type)
            elif element_type == "image":
                # Type check: ensure element is ImageElement before rendering
                if isinstance(element, ImageElement):
                    self.image_renderer.render(slide, element)
                    logger.debug("Image element rendered", element_type=element_type)
            else:
                logger.warning("Unknown element type", element_type=element_type)

        logger.info("Slide built successfully", page_number=page_def.page_number)
        # Type assertion for mypy: slide is guaranteed to be Slide type from add_slide
        return slide  # type: ignore[no-any-return]

    def _set_background_color(self, slide: Slide, color: Color) -> None:
        """Set the background color of a slide.

        This is a private method that applies a solid color background to the slide.
        It disables master background inheritance and sets a solid fill color.

        Args:
            slide: The python-pptx Slide object to set the background color for.
            color: The Color object containing RGB values.

        Raises:
            ValueError: If color is invalid.

        Example:
            >>> color = Color(hex_value="#FFFFFF")
            >>> builder._set_background_color(slide, color)
        """
        if not color.hex_value:
            raise ValueError("Color hex_value must be provided")

        # Get the background fill
        background = slide.background
        fill = background.fill

        # Set solid fill
        fill.solid()

        # Convert hex to RGB
        hex_value = color.hex_value.lstrip("#")
        r = int(hex_value[0:2], 16)
        g = int(hex_value[2:4], 16)
        b = int(hex_value[4:6], 16)

        # Import here to avoid circular dependency
        from pptx.dml.color import RGBColor

        fill.fore_color.rgb = RGBColor(r, g, b)  # type: ignore[no-untyped-call]

        logger.debug(
            "Background color applied",
            hex_value=color.hex_value,
            rgb=(r, g, b),
        )

    def _set_background_image(self, slide: Slide, image_path: Path) -> None:
        """Set a background image on a slide.

        This is a private method that adds an image covering the entire slide as a background.
        The image is added as the first element (bottom of z-order) and sized to fill the slide.

        Note:
            python-pptx doesn't support direct background image setting via API.
            This implementation adds an image covering the entire slide area as a workaround.

            This method is currently not called by build_slide() as PageDefinition doesn't
            support background images yet. It is prepared for future extension when a
            separate background_image field is added to PageDefinition.

        Args:
            slide: The python-pptx Slide object to set the background image for.
            image_path: Path to the image file.

        Raises:
            FileNotFoundError: If the image file doesn't exist.
            ValueError: If image_path is invalid.

        Example:
            >>> image_path = Path("background.jpg")
            >>> builder._set_background_image(slide, image_path)
        """
        if not image_path.exists():
            raise FileNotFoundError(f"Background image not found: {image_path}")

        if not image_path.is_file():
            raise ValueError(f"Background image path is not a file: {image_path}")

        # Add image covering the entire slide
        left = top = Inches(0)
        slide.shapes.add_picture(
            str(image_path),
            left,
            top,
            width=self.presentation.slide_width,
            height=self.presentation.slide_height,
        )

        logger.debug(
            "Background image added",
            image_path=str(image_path),
            width=self.presentation.slide_width,
            height=self.presentation.slide_height,
        )
