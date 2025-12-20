"""LLM prompts for various tasks."""

from slidemaker.llm.prompts.composition import create_composition_prompt
from slidemaker.llm.prompts.image_generation import create_image_generation_prompt
from slidemaker.llm.prompts.image_processing import (
    create_image_analysis_prompt,
    create_image_extraction_prompt,
)

__all__ = [
    "create_composition_prompt",
    "create_image_generation_prompt",
    "create_image_analysis_prompt",
    "create_image_extraction_prompt",
]
