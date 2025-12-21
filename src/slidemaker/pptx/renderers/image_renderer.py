"""Image element renderer for PowerPoint slides.

This module provides the ImageRenderer class for rendering ImageElement instances
onto PowerPoint slides with various fit modes (contain, cover, fill).
"""

from __future__ import annotations

from pathlib import Path

import structlog
from PIL import Image
from pptx.slide import Slide

from slidemaker.core.models.common import FitMode, Size
from slidemaker.core.models.element import ImageElement

logger = structlog.get_logger(__name__)


class ImageRenderer:
    """Image element renderer.

    Renders ImageElement instances onto PowerPoint slides, handling:
    - Image placement with position and size
    - Fit modes (contain, cover, fill)
    - Aspect ratio calculations

    Note:
        Due to python-pptx limitations, COVER mode is currently implemented
        as FILL mode. True cover behavior (maintaining aspect ratio and cropping)
        requires preprocessing images with Pillow before adding to slides.
    """

    def render(self, slide: Slide, image_element: ImageElement) -> None:
        """Render an image element onto a slide.

        Args:
            slide: Target slide to render on
            image_element: Image element definition to render

        Raises:
            FileNotFoundError: If the image file does not exist
            ValueError: If position or size values are invalid, or image cannot be opened

        Note:
            Due to python-pptx limitations, COVER mode currently behaves the same as FILL mode.
            True cover behavior (crop to fill) requires image preprocessing with Pillow.
        """
        logger.info(
            "Rendering image element",
            source=image_element.source,
            position=image_element.position,
            size=image_element.size,
            fit_mode=image_element.fit_mode,
        )

        # Validate image file exists
        image_path = Path(image_element.source)
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image_element.source}")

        # Validate box size is positive
        box_size = image_element.size
        if box_size.width <= 0 or box_size.height <= 0:
            raise ValueError(
                f"Box size must be positive: width={box_size.width}, height={box_size.height}"
            )

        # Get original image dimensions
        try:
            with Image.open(image_path) as img:
                original_width, original_height = img.size
        except Exception as e:
            raise ValueError(
                f"Failed to open image file {image_element.source}: {e}"
            ) from e

        # Validate image dimensions are positive
        if original_width <= 0 or original_height <= 0:
            raise ValueError(
                f"Image dimensions must be positive: "
                f"width={original_width}, height={original_height}"
            )

        logger.debug(
            "Image dimensions retrieved",
            original_size=(original_width, original_height),
        )

        # Calculate position and size based on fit mode
        if image_element.fit_mode == FitMode.CONTAIN:
            final_width, final_height = self._calculate_contain_size(
                (original_width, original_height), box_size
            )
            # Center the image within the box
            left = image_element.position.x + (box_size.width - final_width) // 2
            top = image_element.position.y + (box_size.height - final_height) // 2
        elif image_element.fit_mode == FitMode.COVER:
            # Note: python-pptx does not support image cropping natively.
            # True cover behavior would require preprocessing the image with Pillow
            # to crop it before adding to the slide. For now, we use FILL behavior.
            logger.warning(
                "COVER mode is not fully supported by python-pptx, using FILL behavior. "
                "Consider preprocessing images with Pillow for true cover behavior.",
                fit_mode=image_element.fit_mode,
            )
            final_width, final_height = box_size.width, box_size.height
            left = image_element.position.x
            top = image_element.position.y
        elif image_element.fit_mode == FitMode.FILL:
            # Use box size as-is (ignore aspect ratio)
            final_width, final_height = box_size.width, box_size.height
            left = image_element.position.x
            top = image_element.position.y
        else:
            raise ValueError(f"Unsupported fit mode: {image_element.fit_mode}")

        # Convert to int (EMU values)
        left = int(left)
        top = int(top)
        width = int(final_width)
        height = int(final_height)

        # Validate values are non-negative and dimensions are positive
        if not all(val >= 0 for val in [left, top]):
            raise ValueError(
                f"Position must be non-negative: left={left}, top={top}"
            )
        if width <= 0 or height <= 0:
            raise ValueError(
                f"Image dimensions must be positive: width={width}, height={height}"
            )

        # Add picture to slide (python-pptx accepts int as EMU despite type hints)
        try:
            slide.shapes.add_picture(
                str(image_path),
                left,  # type: ignore[arg-type]
                top,  # type: ignore[arg-type]
                width,  # type: ignore[arg-type]
                height,  # type: ignore[arg-type]
            )
        except Exception as e:
            raise ValueError(
                f"Failed to add picture to slide: {e}"
            ) from e

        logger.debug(
            "Image element rendered successfully",
            position=(left, top),
            size=(width, height),
            fit_mode=image_element.fit_mode,
        )

    def _calculate_contain_size(
        self, image_size: tuple[int, int], box_size: Size
    ) -> tuple[int, int]:
        """Calculate size for contain mode (fit within box, maintain aspect ratio).

        Args:
            image_size: Original image size (width, height) in pixels
            box_size: Target box size (width, height) in EMU

        Returns:
            tuple[int, int]: Adjusted size (width, height) in EMU

        Note:
            This is a private method called internally by render().
        """
        original_width, original_height = image_size
        box_width, box_height = box_size.width, box_size.height

        # Calculate aspect ratios
        image_aspect = original_width / original_height
        box_aspect = box_width / box_height

        # Fit within box, maintaining aspect ratio
        if image_aspect > box_aspect:
            # Image is wider - constrain by width
            final_width = box_width
            final_height = max(1, int(box_width / image_aspect))
        else:
            # Image is taller - constrain by height
            final_height = box_height
            final_width = max(1, int(box_height * image_aspect))

        logger.debug(
            "Contain mode size calculated",
            original_size=(original_width, original_height),
            box_size=(box_width, box_height),
            final_size=(final_width, final_height),
        )

        return final_width, final_height
