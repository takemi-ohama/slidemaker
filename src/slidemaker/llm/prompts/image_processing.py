"""Prompts for image analysis and processing."""

IMAGE_ANALYSIS_SYSTEM_PROMPT = """You are an expert in analyzing presentation slides and images.
Your task is to identify and locate text and image elements within slides.

Output valid JSON with element positions, types, and properties.
The JSON MUST be a dictionary (object) with the following structure:
{
  "page_number": 1,
  "title": "Slide Title",
  "elements": [
    {
      "type": "text",
      "position": {"x": 0, "y": 0},
      "size": {"width": 100, "height": 50},
      "content": "Text content",
      "style": {"font_family": "Arial", "font_size": 18, "color": "#000000"}
    }
  ],
  "background": {"color": "#FFFFFF"}
}

IMPORTANT: font_size must be an integer (e.g., 12, 18, 24), NOT a string like "large"."""

IMAGE_ANALYSIS_USER_PROMPT_TEMPLATE = """Analyze this presentation slide image and extract all \
elements.

IMPORTANT: Specify all coordinates and sizes as PERCENTAGES (0-100) of the image dimensions.
- x and y positions: 0-100 (percentage of width and height from top-left corner)
- width and height sizes: 0-100 (percentage of image width and height)

For each element, identify:
- Type (text or image)
- Position (x, y as percentages: 0=left/top edge, 100=right/bottom edge)
- Size (width, height as percentages of image dimensions)
- Content (for text) or description (for images)
- Styling (font, colors, etc.)

Examples:
- Element at top-left corner covering 50% width and 25% height:
  position: {{"x": 0, "y": 0}}, size: {{"width": 50, "height": 25}}
- Element centered (horizontally and vertically):
  position: {{"x": 25, "y": 37.5}}, size: {{"width": 50, "height": 25}}
- Full-slide background element:
  position: {{"x": 0, "y": 0}}, size: {{"width": 100, "height": 100}}

Output the analysis as structured JSON with all coordinates as percentages (0-100).\
"""


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
    center_x = width // 2
    center_y = height // 2
    user = IMAGE_ANALYSIS_USER_PROMPT_TEMPLATE.format(
        width=width, height=height, center_x=center_x, center_y=center_y
    )
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
