"""Prompts for slide composition generation."""

COMPOSITION_SYSTEM_PROMPT = """You are an expert presentation designer. Your task is to analyze content and create professional PowerPoint slide compositions.

You must output valid JSON following this schema:
- slide_config: Global slide settings
- pages: Array of page definitions with elements

Each page contains text and image elements with precise positioning, sizing, and styling."""

COMPOSITION_USER_PROMPT_TEMPLATE = """Create a professional PowerPoint presentation from the following content:

{content}

Requirements:
- Slide size: {slide_size}
- Number of slides: Generate appropriate number based on content
- Design: {theme} theme
- Layout: Follow best practices for visual hierarchy

For each slide:
1. Determine appropriate layout (title, content, images)
2. Position text and image elements with coordinates
3. Set appropriate font sizes and colors
4. Ensure visual balance and readability

Output the complete presentation structure as JSON."""


def create_composition_prompt(
    content: str, slide_size: str = "16:9", theme: str = "professional"
) -> tuple[str, str]:
    """
    Create prompts for composition generation.

    Args:
        content: Input content (markdown or text)
        slide_size: Target slide size
        theme: Visual theme

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    system = COMPOSITION_SYSTEM_PROMPT
    user = COMPOSITION_USER_PROMPT_TEMPLATE.format(
        content=content, slide_size=slide_size, theme=theme
    )
    return system, user
