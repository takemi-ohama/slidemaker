"""Phase 4: Style estimator."""

import json
from typing import Any

import structlog
from PIL import Image

from slidemaker.image_processing.phase_models import (
    ElementStyle,
    PreciseElement,
    StyledElement,
)
from slidemaker.image_processing.prompts.phase4_styles import create_style_estimation_prompt
from slidemaker.llm.manager import LLMManager


class StyleEstimator:
    """Phase 4: Estimate styling attributes for elements.

    This estimator determines font sizes, colors, and other style
    attributes for text elements.
    """

    def __init__(self, llm_manager: LLMManager):
        """Initialize style estimator.

        Args:
            llm_manager: LLM manager for making API calls
        """
        self.llm_manager = llm_manager
        self.logger = structlog.get_logger(__name__)

    async def estimate_styles(
        self,
        image: Image.Image,
        precise_elements: list[PreciseElement],
        slide_dimensions: tuple[int, int],
    ) -> list[StyledElement]:
        """Estimate styling attributes for all elements.

        Args:
            image: PIL Image object
            precise_elements: Precise element list from Phase 3
            slide_dimensions: Slide width and height in pixels

        Returns:
            List of StyledElement objects with complete styling

        Raises:
            ValueError: If LLM response is invalid
        """
        self.logger.info(
            "phase4_style_estimation_start",
            num_elements=len(precise_elements),
        )

        # Convert to dicts for serialization
        elements_dict = [elem.model_dump() for elem in precise_elements]

        # Create prompts
        system_prompt, user_prompt = create_style_estimation_prompt(elements_dict, slide_dimensions)

        # Call LLM
        try:
            response = await self.llm_manager.analyze_image(
                prompt=user_prompt,
                system_prompt=system_prompt,
                image=image,
            )

            # Parse response and merge with precise_elements
            styled_elements = self._parse_styles_response(response, precise_elements)

            self.logger.info(
                "phase4_style_estimation_success",
                num_elements=len(styled_elements),
            )

            return styled_elements

        except Exception as e:
            self.logger.error(
                "phase4_style_estimation_error",
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

    def _parse_styles_response(
        self, response: dict[str, Any], precise_elements: list[PreciseElement]
    ) -> list[StyledElement]:
        """Parse LLM response and merge with precise elements.

        Args:
            response: LLM response dictionary
            precise_elements: Precise elements from Phase 3

        Returns:
            List of StyledElement objects

        Raises:
            ValueError: If response format is invalid
        """
        # Log response for debugging
        self.logger.debug(
            "phase4_parsing_response",
            response_preview=json.dumps(response, ensure_ascii=False)[:500],
        )

        try:
            # Create a mapping of element_id → style_data
            style_map: dict[str, dict[str, Any]] = {}
            alt_text_map: dict[str, str] = {}

            elements_data = response.get("elements", [])
            for elem_data in elements_data:
                elem_id = elem_data.get("id")
                if not elem_id:
                    continue

                # Extract style data
                if "style" in elem_data:
                    style_map[elem_id] = elem_data["style"]

                # Extract alt_text for images
                if "alt_text" in elem_data:
                    alt_text_map[elem_id] = elem_data["alt_text"]

            # Merge styles with precise elements
            styled_elements = []

            for precise_elem in precise_elements:
                # Get style data for this element
                style_data = style_map.get(precise_elem.id, {})

                # Parse style
                style = ElementStyle(
                    font_family=style_data.get("font_family", "Arial"),
                    font_size=style_data.get("font_size", 18),
                    color=style_data.get("color", "#000000"),
                    bold=style_data.get("bold", False),
                    italic=style_data.get("italic", False),
                    underline=style_data.get("underline", False),
                    word_wrap=style_data.get("word_wrap", True),
                    alignment=style_data.get("alignment", "left"),
                )

                # Get alt_text for images
                alt_text = alt_text_map.get(precise_elem.id)

                # Create StyledElement
                styled_element = StyledElement(
                    id=precise_elem.id,
                    type=precise_elem.type,
                    content=precise_elem.content_preview,
                    position=precise_elem.position,
                    size=precise_elem.size,
                    style=style,
                    alt_text=alt_text,
                )

                styled_elements.append(styled_element)

            return styled_elements

        except (KeyError, TypeError, ValueError) as e:
            self.logger.error(
                "phase4_parse_error",
                error=str(e),
                response=response,
            )
            raise ValueError(f"Failed to parse styles response: {e}") from e
