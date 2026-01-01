"""Phase 1: Layout structure analyzer."""

import json
from typing import Any

import structlog
from PIL import Image

from slidemaker.image_processing.phase_models import (
    AlignmentRules,
    ColumnDefinition,
    HorizontalZone,
    LayoutMetadata,
)
from slidemaker.image_processing.prompts.phase1_layout import create_layout_analysis_prompt
from slidemaker.llm.manager import LLMManager


class LayoutAnalyzer:
    """Phase 1: Analyze slide layout structure.

    This analyzer identifies the grid structure, column boundaries,
    and horizontal zones of a slide layout.
    """

    def __init__(self, llm_manager: LLMManager):
        """Initialize layout analyzer.

        Args:
            llm_manager: LLM manager for making API calls
        """
        self.llm_manager = llm_manager
        self.logger = structlog.get_logger(__name__)

    async def analyze_layout(
        self, image: Image.Image, slide_dimensions: tuple[int, int]
    ) -> LayoutMetadata:
        """Analyze the layout structure of a slide image.

        Args:
            image: PIL Image object
            slide_dimensions: Slide width and height in pixels

        Returns:
            LayoutMetadata: Parsed layout structure

        Raises:
            ValueError: If LLM response is invalid
        """
        self.logger.info(
            "phase1_layout_analysis_start",
            slide_dimensions=slide_dimensions,
        )

        # Create prompts
        system_prompt, user_prompt = create_layout_analysis_prompt(slide_dimensions)

        # Call LLM
        try:
            response = await self.llm_manager.analyze_image(
                prompt=user_prompt,
                system_prompt=system_prompt,
                image=image,
            )

            # Parse response
            layout_metadata = self._parse_layout_response(response)

            self.logger.info(
                "phase1_layout_analysis_success",
                layout_type=layout_metadata.layout_type,
                num_columns=len(layout_metadata.columns),
                num_zones=len(layout_metadata.horizontal_zones),
            )

            return layout_metadata

        except Exception as e:
            self.logger.error(
                "phase1_layout_analysis_error",
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

    def _parse_layout_response(self, response: dict[str, Any]) -> LayoutMetadata:
        """Parse LLM response into LayoutMetadata.

        Args:
            response: LLM response dictionary

        Returns:
            LayoutMetadata: Parsed layout metadata

        Raises:
            ValueError: If response format is invalid
        """
        # Log response for debugging
        self.logger.debug(
            "phase1_parsing_response",
            response_preview=json.dumps(response, ensure_ascii=False)[:500],
        )

        try:
            # Parse columns
            columns_data = response.get("columns", [])
            columns = [
                ColumnDefinition(
                    index=col["index"],
                    x_start=col["x_start"],
                    x_end=col["x_end"],
                    width=col["width"],
                )
                for col in columns_data
            ]

            # Parse horizontal zones
            zones_data = response.get("horizontal_zones", [])
            zones = [
                HorizontalZone(
                    name=zone["name"],
                    y_start=zone["y_start"],
                    y_end=zone["y_end"],
                )
                for zone in zones_data
            ]

            # Parse alignment rules
            rules_data = response.get("alignment_rules", {})
            alignment_rules = AlignmentRules(
                same_row_elements_must_align=rules_data.get("same_row_elements_must_align", True),
                column_headers_at_y=rules_data.get("column_headers_at_y"),
                column_descriptions_at_y=rules_data.get("column_descriptions_at_y"),
            )

            # Create LayoutMetadata
            layout_metadata = LayoutMetadata(
                layout_type=response.get("layout_type", "single_column"),
                columns=columns,
                horizontal_zones=zones,
                alignment_rules=alignment_rules,
                title=response.get("title"),
                background_color=response.get("background_color", "#FFFFFF"),
            )

            return layout_metadata

        except (KeyError, TypeError, ValueError) as e:
            self.logger.error(
                "phase1_parse_error",
                error=str(e),
                response=response,
            )
            raise ValueError(f"Failed to parse layout response: {e}") from e
