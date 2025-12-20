"""Prompts for image analysis and processing."""

IMAGE_ANALYSIS_SYSTEM_PROMPT = """You are an expert in analyzing presentation slides and images.
Your task is to identify and locate text and image elements within slides.

Output valid JSON with element positions, types, and properties."""

IMAGE_ANALYSIS_USER_PROMPT_TEMPLATE = """Analyze this presentation slide image and extract all elements.

For each element, identify:
- Type (text or image)
- Position (x, y coordinates)
- Size (width, height)
- Content (for text) or description (for images)
- Styling (font, colors, etc.)

Slide dimensions: {width}x{height}
Output the analysis as structured JSON."""


def create_image_analysis_prompt(width: int = 1920, height: int = 1080) -> tuple[str, str]:
    """
    Create prompts for image analysis.

    Args:
        width: Slide width in pixels
        height: Slide height in pixels

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    system = IMAGE_ANALYSIS_SYSTEM_PROMPT
    user = IMAGE_ANALYSIS_USER_PROMPT_TEMPLATE.format(width=width, height=height)
    return system, user


IMAGE_EXTRACTION_PROMPT_TEMPLATE = """Extract and clean this image element from the slide.

Requirements:
- Remove any overlapping text
- Crop to the main subject
- Remove background if needed
- Maintain image quality

Original position: ({x}, {y})
Target size: {width}x{height}"""


def create_image_extraction_prompt(x: int, y: int, width: int, height: int) -> str:
    """
    Create prompt for image extraction/cleaning.

    Args:
        x: X coordinate
        y: Y coordinate
        width: Target width
        height: Target height

    Returns:
        Image extraction prompt
    """
    return IMAGE_EXTRACTION_PROMPT_TEMPLATE.format(x=x, y=y, width=width, height=height)
