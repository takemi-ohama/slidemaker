"""Phase 4: Style estimation prompts."""

import json


STYLE_ESTIMATION_SYSTEM_PROMPT = """You are a font and style estimation expert for presentation slides. Your task is to accurately estimate font sizes, colors, and other styling attributes for text elements.

Focus on:
- Conservative font size estimates (avoid overestimating)
- Font attributes (family, bold, italic, color)
- Text alignment and word wrapping
- Image descriptions (alt text)

CRITICAL: Font size estimation must be CONSERVATIVE. When in doubt, choose the smaller size. Overestimating causes layout issues."""

STYLE_ESTIMATION_USER_PROMPT_TEMPLATE = """Estimate styles for all elements based on their precise coordinates from Phase 3.

SLIDE DIMENSIONS: {width}px × {height}px

PHASE 3 COORDINATES:
{coordinates_json}

TASK: Estimate font sizes and styling attributes for all elements.

OUTPUT FORMAT (JSON):
{{
  "elements": [
    {{
      "id": "elem_1",
      "style": {{
        "font_family": "Arial",
        "font_size": 32,
        "color": "#333333",
        "bold": true,
        "italic": false,
        "underline": false,
        "word_wrap": false,
        "alignment": "left"
      }}
    }},
    {{
      "id": "elem_2",
      "alt_text": "Brain icon representing AI"
    }},
    ...
  ]]
}}

STYLE ESTIMATION GUIDELINES:

1. **Font Size Estimation (CONSERVATIVE)**:
   - Formula: font_size_pt ≈ (element_height_% / 100) × {height}px × 0.75
   - Common sizes for {height}px slide:
     * 4% height → 28-32pt (main titles)
     * 3% height → 18-22pt (section headers)
     * 2% height → 14-16pt (body text)
     * 1.2% height → 10-12pt (captions, footnotes)
   - **IMPORTANT**: When in doubt, choose the SMALLER size
   - **Common mistake**: Estimating 44pt for titles when 32pt is correct
   - Visual verification: Does the text look extra large? If not, use smaller estimate

2. **Font Family**:
   - Default to "Arial" for sans-serif
   - Use "Times New Roman" for serif fonts
   - Use "Courier" or "Courier New" for monospace

3. **Font Attributes**:
   - bold: true for headers, titles, emphasis
   - italic: true for quotes, emphasis
   - underline: false (rarely used in modern presentations)

4. **Color**:
   - Estimate as hex code (e.g., "#000000" for black)
   - Common colors: #000000 (black), #FFFFFF (white), #333333 (dark gray)
   - If unsure, use #000000 (black)

5. **Text Alignment**:
   - "left": Most common, default
   - "center": Titles, centered text
   - "right": Less common

6. **Word Wrap & Spacing**:
   - true: Multi-line text, paragraphs, descriptions
   - false: Single-line titles, headers
   - **Line Spacing**: Estimate line spacing multiplier (1.0 = tight, 1.2 = normal, 1.5 = loose). Titles often 1.0-1.1, Body 1.2-1.3.

7. **Image Alt Text**:
   - For image elements, provide brief descriptive alt_text
   - Example: "Brain icon representing AI"
   - Keep it concise (1-2 sentences)

FONT SIZE EXAMPLES (for {height}px = 1024px):
- Title "MDX変革を駆動する3つの戦略的柱" (height ~4%) → 24pt
- Header "1. 「AIといえばナイル」" (height ~3%) → 16pt
- Description paragraph (height ~2%) → 12pt
- Footer "NotebookLM" (height ~1%) → 10pt

CRITICAL REMINDER:
Be conservative with font sizes. Overestimation causes text overflow. Start small and only increase if visually obviously larger.

Now estimate styles for all elements and output ONLY the JSON structure above."""


def create_style_estimation_prompt(
    precise_elements: list[dict[str, Any]], slide_dimensions: tuple[int, int] = (1835, 1024)
) -> tuple[str, str]:
    """Create Phase 4 style estimation prompts.

    Args:
        precise_elements: Precise element list from Phase 3 (as dict list)
        slide_dimensions: Slide width and height in pixels

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    width, height = slide_dimensions
    coordinates_json = json.dumps(precise_elements, ensure_ascii=False, indent=2)

    system = STYLE_ESTIMATION_SYSTEM_PROMPT
    user = STYLE_ESTIMATION_USER_PROMPT_TEMPLATE.format(
        width=width, height=height, coordinates_json=coordinates_json
    )
    return system, user
