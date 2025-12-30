"""Phase 2: Element identifier."""

import json
from typing import Any

import structlog
from PIL import Image

from slidemaker.image_processing.phase_models import (
    LayoutMetadata,
    RoughElement,
    RoughPosition,
    RoughSize,
)
from slidemaker.image_processing.prompts.phase2_elements import (
    create_element_identification_prompt,
)
from slidemaker.llm.manager import LLMManager


class ElementIdentifier:
    """Phase 2: Identify and roughly position elements.

    This identifier finds all text and image elements and assigns them
    to the correct structural location (column, zone, row group).
    """

    def __init__(self, llm_manager: LLMManager):
        """Initialize element identifier.

        Args:
            llm_manager: LLM manager for making API calls
        """
        self.llm_manager = llm_manager
        self.logger = structlog.get_logger(__name__)

    async def identify_elements(
        self,
        image: Image.Image,
        layout_metadata: LayoutMetadata,
        slide_dimensions: tuple[int, int],
    ) -> list[RoughElement]:
        """Identify elements and assign to structural locations.

        Args:
            image: PIL Image object
            layout_metadata: Layout structure from Phase 1
            slide_dimensions: Slide width and height in pixels

        Returns:
            List of RoughElement objects

        Raises:
            ValueError: If LLM response is invalid
        """
        self.logger.info(
            "phase2_element_identification_start",
            layout_type=layout_metadata.layout_type,
            num_columns=len(layout_metadata.columns),
        )

        # Convert layout_metadata to dict for serialization
        layout_dict = layout_metadata.model_dump()

        # Create prompts
        system_prompt, user_prompt = create_element_identification_prompt(
            layout_dict, slide_dimensions
        )
        
        # Add instructions for complex diagrams and strict bounding boxes
        system_prompt += """
        
        CRITICAL INSTRUCTIONS FOR IMAGE ELEMENTS:
        1. COMPLEX DIAGRAMS: If you see a complex diagram (e.g., flowcharts, process maps, gear diagrams, cycle charts, or any graphics with multiple interconnecting arrows and labels) that is highly integrated, DO NOT attempt to decompose it. You MUST treat the ENTIRE integrated diagram as a SINGLE 'image' element. Error on the side of making it an image if it looks hard to reconstruct.
        2. STRICT BOUNDING BOXES: When defining the 'rough_size' and position for an 'image' element, the bounding box must TIGHTLY enclose ONLY the graphic content. Do NOT include any slide titles or separate paragraph text. If labels are physically inside shapes, they stay in the image. If they are floating nearby, they are separate text elements.
        3. TEXT IN IMAGES: If text is inside a box, circle, or connected by arrows within a complex diagram, keep it as part of the 'image' element.
        4. BULLET POINTS: Group all consecutive bullet items (•, 1., etc.) into one 'text' element block.
        5. AVOID DUPLICATION: Never create both an image and a text element for the same visible content. If you include it in an image, do not create a text element for it.
        """

        # Call LLM
        try:
            response = await self.llm_manager.analyze_image(
                prompt=user_prompt,
                system_prompt=system_prompt,
                image=image,
            )

            # Parse response
            rough_elements = self._parse_elements_response(response)

            self.logger.info(
                "phase2_element_identification_success",
                num_elements=len(rough_elements),
                num_text=sum(1 for e in rough_elements if e.type == "text"),
                num_images=sum(1 for e in rough_elements if e.type == "image"),
            )

            return rough_elements

        except Exception as e:
            self.logger.error(
                "phase2_element_identification_error",
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

    def _parse_elements_response(self, response: dict[str, Any]) -> list[RoughElement]:
        """Parse LLM response into list of RoughElement.

        Args:
            response: LLM response dictionary

        Returns:
            List of RoughElement objects

        Raises:
            ValueError: If response format is invalid
        """
        # Log response for debugging
        self.logger.debug(
            "phase2_parsing_response",
            response_preview=json.dumps(response, ensure_ascii=False)[:500],
        )

        try:
            elements_data = response.get("elements", [])
            rough_elements = []

            for elem_data in elements_data:
                # Parse position
                pos_data = elem_data.get("rough_position", {})
                rough_position = RoughPosition(
                    x=pos_data.get("x", 0),
                    y=pos_data.get("y", 0),
                )

                # Parse size
                size_data = elem_data.get("rough_size", {})
                rough_size = RoughSize(
                    width=size_data.get("width", 10),
                    height=size_data.get("height", 10),
                )

                # Create RoughElement
                rough_element = RoughElement(
                    id=elem_data.get("id", "elem_unknown"),
                    type=elem_data.get("type", "text"),
                    content_preview=elem_data.get("content_preview", ""),
                    zone=elem_data.get("zone"),
                    column=elem_data.get("column"),
                    rough_position=rough_position,
                    rough_size=rough_size,
                    row_group=elem_data.get("row_group"),
                )

                rough_elements.append(rough_element)

            return rough_elements

        except (KeyError, TypeError, ValueError) as e:
            self.logger.error(
                "phase2_parse_error",
                error=str(e),
                response=response,
            )
            raise ValueError(f"Failed to parse elements response: {e}") from e
