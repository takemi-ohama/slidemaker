"""Phase 1: Layout structure analysis prompts."""

LAYOUT_ANALYSIS_SYSTEM_PROMPT = """You are a slide layout structure expert. Your task is to analyze the overall grid structure and layout patterns of presentation slides.

Focus ONLY on structural analysis:
- How many columns does the slide have?
- Where are the column boundaries (in pixels)?
- What are the main horizontal zones (title, headers, body, footer) in pixels?
- Are elements in the same row aligned?

DO NOT analyze:
- Individual element content
- Exact coordinates (rough estimates are fine, but must be in pixels)
- Font sizes or styling
- Detailed measurements

Your goal is to provide a high-level structural blueprint that subsequent phases will use."""

LAYOUT_ANALYSIS_USER_PROMPT_TEMPLATE = """Analyze the layout structure of this slide image ({width}×{height} px).

SLIDE DIMENSIONS: {width}px × {height}px (PowerPoint 96 DPI Basis)

TASK: Identify the grid structure and major layout zones.

OUTPUT FORMAT (JSON):
{{
  "layout_type": "single_column | two_column | three_column | grid | custom",
  "columns": [
    {{
      "index": 1,
      "x_start": 50.0,
      "x_end": 300.0,
      "width": 250.0
    }},
    ...
  ],
  "horizontal_zones": [
    {{
      "name": "title",
      "y_start": 40.0,
      "y_end": 100.0
    }},
    {{
      "name": "icons",
      "y_start": 120.0,
      "y_end": 200.0
    }},
    {{
      "name": "headers",
      "y_start": 210.0,
      "y_end": 250.0
    }},
    {{
      "name": "descriptions",
      "y_start": 260.0,
      "y_end": 400.0
    }},
    ...
  ],
  "alignment_rules": {{
    "same_row_elements_must_align": true,
    "column_headers_at_y": 210.0,
    "column_descriptions_at_y": 260.0
  }},
  "title": "Main slide title if visible",
  "background_color": "#FFFFFF"
}}

ANALYSIS GUIDELINES:

1. **Column Detection (PIXELS)**:
   - Look for vertical alignment of elements
   - Common patterns: 1 column (full width), 2 columns (50/50), 3 columns (33/33/33)
   - Estimate column boundaries in **PIXELS** (e.g., 0 to {half_width} for col 1).

2. **Horizontal Zone Detection (PIXELS)**:
   - Title zone: Usually top 10-20% (e.g., y=0 to {title_zone_end})
   - Headers/section titles: e.g., y={header_zone_start}
   - Body/descriptions: e.g., y={body_zone_start}
   - Footer: Bottom edge

3. **Alignment Rules**:
   - If you see 3 headers in a row → they should have the same Y coordinate (in pixels)
   - If you see 3 description blocks below headers → they should have the same Y coordinate
   - Set `same_row_elements_must_align: true` if this pattern exists

4. **Be Conservative**:
   - Use approximate pixel values.
   - Focus on major structural patterns, not pixel-perfect accuracy

Now analyze this slide image and output ONLY the JSON structure above."""


def create_layout_analysis_prompt(
    slide_dimensions: tuple[int, int] = (960, 540)
) -> tuple[str, str]:
    """Create Phase 1 layout analysis prompts.

    Args:
        slide_dimensions: Slide width and height in pixels

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    width, height = slide_dimensions
    
    # Calculate rough pixel values for examples
    half_width = int(width / 2)
    title_zone_end = int(height * 0.2)
    header_zone_start = int(height * 0.4)
    body_zone_start = int(height * 0.5)
    
    system = LAYOUT_ANALYSIS_SYSTEM_PROMPT
    user = LAYOUT_ANALYSIS_USER_PROMPT_TEMPLATE.format(
        width=width, 
        height=height,
        half_width=half_width,
        title_zone_end=title_zone_end,
        header_zone_start=header_zone_start,
        body_zone_start=body_zone_start
    )
    return system, user