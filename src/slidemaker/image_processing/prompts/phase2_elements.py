"""Phase 2: Element identification prompts."""

import json


ELEMENT_IDENTIFICATION_SYSTEM_PROMPT = """You are an element identification expert for presentation slides. Your task is to identify all text and image elements and assign them to the correct structural location based on the layout analysis.

Focus on:
- Identifying TEXT vs IMAGE elements
- Assigning elements to columns (if multi-column layout)
- Assigning elements to horizontal zones
- Grouping elements that appear on the same row
- Providing rough coordinates in PIXELS (e.g., x=100, width=300)

DO NOT worry about:
- Exact pixel-perfect coordinates (Phase 3 will handle this)
- Font sizes or styling (Phase 4 will handle this)
- Detailed measurements

Your goal is to create a complete inventory of elements with their structural relationships."""

ELEMENT_IDENTIFICATION_USER_PROMPT_TEMPLATE = """Identify all elements in this slide image based on the layout structure from Phase 1.

SLIDE DIMENSIONS: {width}px × {height}px (PowerPoint 96 DPI Basis)

PHASE 1 LAYOUT STRUCTURE:
{layout_json}

TASK: Identify all TEXT and IMAGE elements and assign them to the correct structural location.

OUTPUT FORMAT (JSON):
{{
  "elements": [
    {{
      "id": "elem_1",
      "type": "text",
      "content_preview": "First 50 characters of text...",
      "zone": "title",
      "column": null,
      "rough_position": {{"x": 100, "y": 80}},
      "rough_size": {{"width": 760, "height": 50}},
      "row_group": null
    }},
    {{
      "id": "elem_2",
      "type": "image",
      "content_preview": "Brain icon representing AI",
      "zone": "icons",
      "column": 1,
      "rough_position": {{"x": 150, "y": 200}},
      "rough_size": {{"width": 80, "height": 100}},
      "row_group": "icon_row"
    }},
    {{
      "id": "elem_3",
      "type": "text",
      "content_preview": "1. 「AIといえばナイル」",
      "zone": "headers",
      "column": 1,
      "rough_position": {{"x": 100, "y": 320}},
      "rough_size": {{"width": 250, "height": 40}},
      "row_group": "headers"
    }},
    ...
  ],
  "row_groups": {{
    "headers": ["elem_3", "elem_4", "elem_5"],
    "descriptions": ["elem_6", "elem_7", "elem_8"]
  }}
}}

IDENTIFICATION GUIDELINES:

1. **Element Type**:
   - TEXT: Standalone text (titles, headers, paragraphs, captions)
   - IMAGE: Graphics, photos, icons, diagrams, charts
   - **IMPORTANT**: Text embedded in graphics should be IMAGE, not TEXT

2. **Zone Assignment**:
   - Match element to the horizontal zone from Phase 1
   - Use zone names like "title", "headers", "descriptions", etc.

3. **Column Assignment**:
   - For multi-column layouts, assign element to column 1, 2, 3, etc.
   - For single-column or full-width elements, set column to null

4. **Row Grouping**:
   - Elements visually on the same horizontal line should have the same row_group
   - Example: Three column headers → row_group="headers"
   - Example: Three description blocks → row_group="descriptions"
   - This is CRITICAL for Phase 3 alignment

5. **Rough Coordinates (PIXELS)**:
   - Use approximate PIXEL coordinates (e.g., x=100, y=200)
   - Based on the layout zones from Phase 1
   - **DO NOT use percentages**

6. **Content Preview**:
   - For TEXT: Extract first 50 characters
   - For IMAGE: Provide brief description

Now identify all elements in this slide image and output ONLY the JSON structure above."""


def create_element_identification_prompt(
    layout_metadata: dict[str, Any], slide_dimensions: tuple[int, int] = (960, 540)
) -> tuple[str, str]:
    """Create Phase 2 element identification prompts.

    Args:
        layout_metadata: Layout structure from Phase 1 (as dict for serialization)
        slide_dimensions: Slide width and height in pixels

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    width, height = slide_dimensions
    layout_json = json.dumps(layout_metadata, ensure_ascii=False, indent=2)

    system = ELEMENT_IDENTIFICATION_SYSTEM_PROMPT
    user = ELEMENT_IDENTIFICATION_USER_PROMPT_TEMPLATE.format(
        width=width, height=height, layout_json=layout_json
    )
    return system, user