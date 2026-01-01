"""Phase 3: Precise coordinate measurer."""

import json
from collections import defaultdict
from typing import Any

import structlog
from PIL import Image

from slidemaker.image_processing.phase_models import (
    LayoutMetadata,
    PreciseElement,
    PrecisePosition,
    PreciseSize,
    RoughElement,
)
from slidemaker.image_processing.prompts.phase3_coordinates import (
    create_coordinate_measurement_prompt,
)
from slidemaker.llm.manager import LLMManager


class CoordinateMeasurer:
    """Phase 3: Measure precise coordinates for elements.

    This measurer determines exact positions (1% precision) and enforces
    critical alignment constraints (same row → same Y coordinate).
    """

    def __init__(self, llm_manager: LLMManager):
        """Initialize coordinate measurer.

        Args:
            llm_manager: LLM manager for making API calls
        """
        self.llm_manager = llm_manager
        self.logger = structlog.get_logger(__name__)

    async def measure_coordinates(
        self,
        image: Image.Image,
        layout_metadata: LayoutMetadata,
        rough_elements: list[RoughElement],
        slide_dimensions: tuple[int, int],
    ) -> list[PreciseElement]:
        """Measure precise coordinates for all elements.

        Args:
            image: PIL Image object
            layout_metadata: Layout structure from Phase 1
            rough_elements: Rough element list from Phase 2
            slide_dimensions: Slide width and height in pixels

        Returns:
            List of PreciseElement objects with enforced alignment

        Raises:
            ValueError: If LLM response is invalid
        """
        self.logger.info(
            "phase3_coordinate_measurement_start",
            num_elements=len(rough_elements),
        )

        # Convert to dicts for serialization
        layout_dict = layout_metadata.model_dump()
        elements_dict = [elem.model_dump() for elem in rough_elements]

        # Create prompts
        system_prompt, user_prompt = create_coordinate_measurement_prompt(
            layout_dict, elements_dict, slide_dimensions
        )

        # Call LLM
        try:
            response = await self.llm_manager.analyze_image(
                prompt=user_prompt,
                system_prompt=system_prompt,
                image=image,
            )

            # Parse response
            precise_elements = self._parse_coordinates_response(response)

            # Apply alignment constraints (enforce same Y for same row_group)
            precise_elements = self._apply_alignment_constraints(
                precise_elements, layout_metadata
            )

            # Verify no overlaps
            self._verify_no_overlaps(precise_elements, slide_dimensions)

            self.logger.info(
                "phase3_coordinate_measurement_success",
                num_elements=len(precise_elements),
            )

            return precise_elements

        except Exception as e:
            self.logger.error(
                "phase3_coordinate_measurement_error",
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

    def _parse_coordinates_response(self, response: dict[str, Any]) -> list[PreciseElement]:
        """Parse LLM response into list of PreciseElement.

        Args:
            response: LLM response dictionary

        Returns:
            List of PreciseElement objects

        Raises:
            ValueError: If response format is invalid
        """
        # Log response for debugging
        self.logger.debug(
            "phase3_parsing_response",
            response_preview=json.dumps(response, ensure_ascii=False)[:500],
        )

        try:
            elements_data = response.get("elements", [])
            precise_elements = []

            for elem_data in elements_data:
                # Parse position
                pos_data = elem_data.get("position", {})
                position = PrecisePosition(
                    x=pos_data.get("x", 0),
                    y=pos_data.get("y", 0),
                )

                # Parse size
                size_data = elem_data.get("size", {})
                size = PreciseSize(
                    width=size_data.get("width", 10),
                    height=size_data.get("height", 10),
                )

                # Create PreciseElement
                precise_element = PreciseElement(
                    id=elem_data.get("id", "elem_unknown"),
                    type=elem_data.get("type", "text"),
                    content_preview=elem_data.get("content_preview", ""),
                    position=position,
                    size=size,
                    alignment_group=elem_data.get("alignment_group"),
                    aligned_y=elem_data.get("aligned_y"),
                )

                precise_elements.append(precise_element)

            return precise_elements

        except (KeyError, TypeError, ValueError) as e:
            self.logger.error(
                "phase3_parse_error",
                error=str(e),
                response=response,
            )
            raise ValueError(f"Failed to parse coordinates response: {e}") from e

    def _apply_alignment_constraints(
        self, elements: list[PreciseElement], layout_metadata: LayoutMetadata
    ) -> list[PreciseElement]:
        """Apply alignment constraints to ensure same row → same Y.

        Args:
            elements: List of precise elements
            layout_metadata: Layout metadata with alignment rules

        Returns:
            List of elements with enforced alignment
        """
        if not layout_metadata.alignment_rules.same_row_elements_must_align:
            # No alignment enforcement needed
            return elements

        self.logger.info("phase3_applying_alignment_constraints")

        # Group elements by alignment_group
        groups: dict[str, list[PreciseElement]] = defaultdict(list)
        for elem in elements:
            if elem.alignment_group:
                groups[elem.alignment_group].append(elem)

        # For each group, enforce identical Y coordinate
        for group_name, group_elements in groups.items():
            if len(group_elements) <= 1:
                continue  # No alignment needed for single element

            # Calculate the median Y coordinate (most robust choice)
            y_values = [elem.position.y for elem in group_elements]
            y_values_sorted = sorted(y_values)
            median_y = y_values_sorted[len(y_values_sorted) // 2]

            # Use aligned_y if available, otherwise use median
            aligned_y = group_elements[0].aligned_y or median_y

            self.logger.info(
                "phase3_aligning_group",
                group=group_name,
                num_elements=len(group_elements),
                aligned_y=aligned_y,
                original_y_range=f"{min(y_values):.1f}-{max(y_values):.1f}",
            )

            # Force all elements in group to have the same Y
            for elem in group_elements:
                elem.position = PrecisePosition(x=elem.position.x, y=aligned_y)
                elem.aligned_y = aligned_y

        return elements

    def _verify_no_overlaps(
        self, elements: list[PreciseElement], slide_dimensions: tuple[int, int]
    ) -> None:
        """Verify that elements don't overlap vertically.

        Args:
            elements: List of precise elements
            slide_dimensions: Slide dimensions

        Raises:
            Warning if overlaps detected (logged, not raised)
        """
        slide_width, slide_height = slide_dimensions

        # Sort elements by Y coordinate
        elements_sorted = sorted(elements, key=lambda e: e.position.y)

        overlaps_detected = 0

        for i in range(len(elements_sorted) - 1):
            elem1 = elements_sorted[i]
            elem2 = elements_sorted[i + 1]

            # Calculate end Y coordinates
            elem1_end_y = elem1.position.y + elem1.size.height
            elem2_start_y = elem2.position.y

            # Check for overlap
            if elem1_end_y > elem2_start_y:
                gap = elem1_end_y - elem2_start_y
                self.logger.warning(
                    "phase3_overlap_detected",
                    elem1_id=elem1.id,
                    elem1_end_y=elem1_end_y,
                    elem2_id=elem2.id,
                    elem2_start_y=elem2_start_y,
                    overlap_percent=gap,
                )
                overlaps_detected += 1

        if overlaps_detected > 0:
            self.logger.warning(
                "phase3_overlaps_summary",
                total_overlaps=overlaps_detected,
                message="Some overlaps detected. Consider adjusting element sizes or positions.",
            )
