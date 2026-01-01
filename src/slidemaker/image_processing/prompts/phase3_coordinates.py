"""Phase 3: Precise coordinate measurement prompts."""

import json


COORDINATE_MEASUREMENT_SYSTEM_PROMPT = """You are a precise coordinate measurement expert for presentation slides. Your task is to measure exact positions and sizes of all elements in PIXELS.

MOST IMPORTANT RULE (overrides all others):
- Elements in the same row_group MUST have IDENTICAL Y coordinates (in pixels)
- This is NON-NEGOTIABLE and has ABSOLUTE priority
- Example: If elem_3, elem_4, elem_5 are all in row_group="headers", they MUST have the exact same Y value (e.g., y=260)

Focus on:
- Measuring precise coordinates in **PIXELS** (e.g., x=100, y=260)
- Applying the same Y coordinate to all elements in a row_group
- Ensuring elements fit within slide boundaries
- Detecting and fixing overlaps (but row alignment takes priority)

Your measurements will be used directly for PowerPoint generation, so accuracy is critical."""

COORDINATE_MEASUREMENT_USER_PROMPT_TEMPLATE = """Measure precise coordinates for all elements based on Phase 1 layout and Phase 2 element list.

SLIDE DIMENSIONS: {width}px × {height}px (PowerPoint 96 DPI Basis)

PHASE 1 LAYOUT:
{layout_json}

PHASE 2 ELEMENTS:
{elements_json}

TASK: Measure exact positions and sizes (in PIXELS) for all elements.

OUTPUT FORMAT (JSON):
{{
  "elements": [
    {{
      "id": "elem_1",
      "type": "text",
      "content_preview": "Element content preview",
      "position": {{"x": 50, "y": 40}},
      "size": {{"width": 800, "height": 60}},
      "alignment_group": null,
      "aligned_y": null
    }},
    {{
      "id": "elem_3",
      "type": "text",
      "content_preview": "Header 1",
      "position": {{"x": 50, "y": 260}},
      "size": {{"width": 250, "height": 40}},
      "alignment_group": "headers",
      "aligned_y": 260
    }},
    {{
      "id": "elem_4",
      "type": "text",
      "content_preview": "Header 2",
      "position": {{"x": 350, "y": 260}},
      "size": {{"width": 250, "height": 40}},
      "alignment_group": "headers",
      "aligned_y": 260
    }},
    ...
  ],
  "alignment_verification": {{
    "headers_aligned": true,
    "descriptions_aligned": true,
    "no_overlaps": true
  }}
}}

MEASUREMENT GUIDELINES (PIXELS):

1. **ROW ALIGNMENT (HIGHEST PRIORITY)**:
   - Find all elements with the same row_group
   - Measure the Y coordinate of the first element in the group
   - **FORCE all other elements in the group to use the EXACT SAME Y coordinate**
   - Example:
     * elem_3 (row_group="headers") → y=260
     * elem_4 (row_group="headers") → y=260 (FORCED TO MATCH)
     * elem_5 (row_group="headers") → y=260 (FORCED TO MATCH)
   - Set alignment_group and aligned_y for all grouped elements

2. **Coordinate Precision**:
   - Use integer PIXEL values (e.g., 50, 260, 480)
   - Be accurate to within 1-2 pixels

3. **Column Boundaries**:
   - Respect column x_start and x_end from Phase 1 (in pixels)
   - Element x position should match its column's x_start
   - Element width should fit within column width

4. **Boundary Constraints**:
   - All elements must fit within slide dimensions (0-{width}, 0-{height})
   - x + width <= {width}
   - y + height <= {height}

5. **Overlap Detection**:
   - Check for vertical overlaps AFTER applying row alignment
   - If overlap detected, adjust the LOWER element's Y coordinate
   - Never break row alignment to fix overlaps

6. **Text Element Sizing**:
   - Include generous margins (20-40px) to prevent text cutoff
   - Multi-line text needs extra height

CRITICAL REMINDER:
**USE PIXELS ONLY (0-{width}). DO NOT USE PERCENTAGES.**
Same row_group → Same Y coordinate. No exceptions.

Now measure all element coordinates and output ONLY the JSON structure above."""


def create_coordinate_measurement_prompt(
    layout_metadata: dict[str, Any],
    rough_elements: list[dict[str, Any]],
    slide_dimensions: tuple[int, int] = (960, 540),
) -> tuple[str, str]:
    """Create Phase 3 coordinate measurement prompts.

    Args:
        layout_metadata: Layout structure from Phase 1 (as dict)
        rough_elements: Rough element list from Phase 2 (as dict list)
        slide_dimensions: Slide width and height in pixels

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    width, height = slide_dimensions
    layout_json = json.dumps(layout_metadata, ensure_ascii=False, indent=2)
    elements_json = json.dumps(rough_elements, ensure_ascii=False, indent=2)

    system = COORDINATE_MEASUREMENT_SYSTEM_PROMPT
    user = COORDINATE_MEASUREMENT_USER_PROMPT_TEMPLATE.format(
        width=width, height=height, layout_json=layout_json, elements_json=elements_json
    )
    return system, user