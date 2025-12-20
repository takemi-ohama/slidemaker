"""Prompts for image generation."""

IMAGE_GENERATION_TEMPLATE = """Create a professional image for a presentation slide.

Slide context: {slide_title}
Image purpose: {image_description}

Style requirements:
- Professional and clean design
- Suitable for business presentations
- High contrast and clarity
- {additional_requirements}

The image will be used in a {slide_size} presentation slide."""


def create_image_generation_prompt(
    slide_title: str,
    image_description: str,
    slide_size: str = "16:9",
    additional_requirements: str = "Modern and minimalist style",
) -> str:
    """
    Create prompt for image generation.

    Args:
        slide_title: Title of the slide
        image_description: Description of what the image should show
        slide_size: Slide dimensions
        additional_requirements: Additional style requirements

    Returns:
        Image generation prompt
    """
    return IMAGE_GENERATION_TEMPLATE.format(
        slide_title=slide_title,
        image_description=image_description,
        slide_size=slide_size,
        additional_requirements=additional_requirements,
    )
