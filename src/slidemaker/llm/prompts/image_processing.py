"""Prompts for image analysis and processing."""

IMAGE_ANALYSIS_SYSTEM_PROMPT = """You are an expert in analyzing presentation slides and images.
Your task is to identify and locate text and image elements within slides, and output the results as STRICTLY VALID JSON.

=== STEP 1: ANALYZE THE SLIDE ===

Carefully examine the slide image and identify:
1. **Standalone text elements** (titles, headings, body text that exists INDEPENDENTLY from graphics)
   - **CRITICAL: Multi-line text that forms a single semantic unit (e.g., 2-3 line titles, long headings) MUST be extracted as ONE text element**
   - Example: If you see "なぜ今、変革が必要なのか？" on line 1 and "単一プロダクト開発から全社最適化への戦略的転換" on line 2, this is ONE title element, not two
   - The element's height should encompass ALL lines of the text
   - Use \\n to represent line breaks within the single element's content
2. **Image elements** (photos, diagrams, charts, icons, illustrations)
   - **IMPORTANT: Diagrams/infographics with integrated text labels should be treated as SINGLE IMAGE elements**
   - If text is part of a flowchart, process diagram, or icon group, extract the ENTIRE graphic as one image
   - Do NOT separately extract text that is visually embedded within graphics
3. Background color or styling
4. Overall slide structure and layout

**KEY PRINCIPLES:**
- Preserve visual integrity of graphics. When in doubt, extract as image rather than splitting into text + image.
- Preserve semantic integrity of text. Multi-line titles/headings are ONE element, not multiple elements.

=== STEP 2: MEASURE POSITIONS AND SIZES (PIXELS) ===

For each element you identify:
- Measure its position (x, y) in **PIXELS** from the top-left corner (0, 0).
- Measure its size (width, height) in **PIXELS**.
- **DO NOT USE PERCENTAGES.**
- Refer to the SLIDE DIMENSIONS provided in the user prompt for the coordinate space (e.g., 960x540).

**CRITICAL BOUNDARY CONSTRAINTS - ELEMENTS MUST FIT WITHIN SLIDE:**

**VERTICAL CONSTRAINTS (Y-axis):**
- **Minimum Y coordinate**: Elements should generally start below the top margin (e.g., y >= 50px for a 540px height slide).
- **Maximum Y coordinate**: y + height <= Slide Height (element must not extend past bottom edge).
- **Multi-line text height**: Ensure the height covers all lines + line spacing.

**HORIZONTAL CONSTRAINTS (X-axis):**
- **Minimum X coordinate**: Elements should start inside the left margin (e.g., x >= 50px for a 960px width slide).
- **Maximum X coordinate**: x + width <= Slide Width (element must not extend past right edge).

=== LAYOUT PATTERN RECOGNITION ===

**Multi-Column Layouts (2-3 columns):**
- Identify if the slide uses a multi-column layout.
- Text blocks directly below column headers should align horizontally.
- **HORIZONTAL ALIGNMENT (same row):**
  - Elements visually on the same horizontal line MUST have identical Y coordinates.
  - Check: "Are these 3 blocks on the same horizontal line?" → If YES, use SAME Y value for all.

=== STEP 3: DETERMINE ELEMENT PROPERTIES ===

For TEXT elements:
- **CRITICAL: DO NOT extract text that is visually part of an image/diagram/graphic**
- Extract the exact text content.
- **CRITICAL FOR TEXT BOUNDARIES:**
  - Include the COMPLETE boundaries that encompass ALL text characters.
  - Add extra margin (padding) to width and height to prevent cutoff.
  - For Japanese text, ensure width is sufficient.
- **PREVENT OVERLAP:**
  - Check previous elements to ensure no overlap.
  - Leave vertical gaps between elements.
- **FONT SIZE ESTIMATION (POINTS):**
  - Estimate the font size in **POINTS (pt)**.
  - Base your estimate on the visual height of the characters in pixels.
  - **Gemini tends to overestimate font sizes. Be conservative.**
  - **Reference:** In a 540px height slide:
    - 10-12pt (Small): ~12-15px visual height
    - 14-18pt (Body): ~18-24px visual height
    - 20-28pt (Header): ~26-36px visual height
    - 32-40pt (Title): ~40-50px visual height
  - Identify font family, styling (bold/italic), and color.

For IMAGE elements:
- **IMPORTANT: Text embedded in graphics should be treated as IMAGE, not TEXT**
- **BOUNDARIES MUST BE PRECISE & INCLUSIVE:**
  - Identify the EXACT visible boundaries of the image in PIXELS.
  - **CRITICAL: AVOID BOTTOM CROPPING**: For images/diagrams with labels BELOW them, **extend the height by an extra 20-30 pixels** to ensure labels are included.
  - Include ALL parts (labels, legends, annotations).
  - Add MINIMAL padding.

=== STEP 4: OUTPUT AS VALID JSON ===

Output your analysis as a JSON object with this EXACT structure:

{
  "page_number": 1,
  "title": "Main slide title or heading",
  "elements": [
    {
      "type": "text",
      "position": {"x": 100, "y": 80},
      "size": {"width": 760, "height": 50},
      "content": "Text content goes here",
      "style": {
        "font_family": "Arial",
        "font_size": 24,
        "color": "#000000",
        "bold": false,
        "italic": false,
        "word_wrap": true
      }
    },
    {
      "type": "image",
      "position": {"x": 480, "y": 160},
      "size": {"width": 400, "height": 300},
      "content": "Brief description of the image",
      "style": {
        "font_family": "Arial",
        "font_size": 12,
        "color": "#000000",
        "bold": false,
        "italic": false,
        "word_wrap": true
      }
    }
  ],
  "background": {"color": "#FFFFFF"}
}

=== CRITICAL JSON FORMATTING RULES ===

**YOU MUST FOLLOW THESE RULES EXACTLY. ANY DEVIATION WILL CAUSE PARSING ERRORS.**

1. **Property Names**: ALL property names MUST be in double quotes.
2. **String Values**: ALL strings MUST be in double quotes with proper closing quotes.
3. **Numbers**: Numbers must NOT be quoted (e.g., "x": 100).
4. **Booleans**: Must be lowercase (true/false) and NOT quoted.
5. **No Trailing Commas**: NEVER add comma after the last item.
6. **Commas Between Items**: ALWAYS add comma between items.
7. **Special Characters**: Escape quotes inside strings.
8. **Multiline Text**: Use \\n for line breaks. **ABSOLUTELY NO REAL NEWLINES IN STRINGS.**
9. **String Length Limits**: Keep content concise (< 500 chars).
10. **Always Close Strings**: Every opening quote MUST have a closing quote.

**OUTPUT ONLY THE JSON. DO NOT ADD ANY EXPLANATORY TEXT BEFORE OR AFTER THE JSON.**
"""

IMAGE_ANALYSIS_USER_PROMPT_TEMPLATE = """Analyze the presentation slide image below and extract all elements following the instructions in the system prompt.

SLIDE DIMENSIONS: {width}px x {height}px (PowerPoint 96 DPI Basis)

CRITICAL COORDINATE SYSTEM INFORMATION (PIXELS):
- This slide image is EXACTLY {width}x{height} pixels.
- **You MUST output coordinates (x, y) and sizes (width, height) in PIXELS.**
- **DO NOT use percentages.**
- Example: x=480 is the horizontal center (for width 960). y=270 is the vertical center (for height 540).

FONT SIZE ESTIMATION (POINTS):
- Estimate font sizes in **POINTS (pt)** based on the visual pixel height.
- **Visual Reference for {height}px height:**
  - **Title (Large):** ~{title_px}px height -> ~{title_pt}pt
  - **Header (Medium):** ~{header_px}px height -> ~{header_pt}pt
  - **Body (Normal):** ~{body_px}px height -> ~{body_pt}pt
  - **Caption (Small):** ~{small_px}px height -> ~{small_pt}pt
- **IMPORTANT: Avoid overestimating. If in doubt, choose the smaller size.**

Now analyze this slide and output the JSON:"""


def create_image_analysis_prompt(width: int = 960, height: int = 540) -> tuple[str, str]:
    """
    Create prompts for image analysis.

    Args:
        width: Slide width in pixels (default: 960, PowerPoint 96 DPI basis)
        height: Slide height in pixels (default: 540, PowerPoint 96 DPI basis)

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    # Font size reference calculations (approximate visual height in pixels to points)
    # Using a conservative ratio to prevent overestimation (approx 0.4 ratio of px to pt visually)
    # title: ~8-9% height
    title_px = int(height * 0.08)
    title_pt = int(title_px * 0.4) # Reduced factor to 0.4
    
    # header: ~5-6% height
    header_px = int(height * 0.05)
    header_pt = int(header_px * 0.4)
    
    # body: ~3-4% height
    body_px = int(height * 0.035)
    body_pt = int(body_px * 0.4)
    
    # small: ~2% height
    small_px = int(height * 0.02)
    small_pt = int(small_px * 0.4)

    system = IMAGE_ANALYSIS_SYSTEM_PROMPT
    user = IMAGE_ANALYSIS_USER_PROMPT_TEMPLATE.format(
        width=width,
        height=height,
        title_px=title_px,
        title_pt=title_pt,
        header_px=header_px,
        header_pt=header_pt,
        body_px=body_px,
        body_pt=body_pt,
        small_px=small_px,
        small_pt=small_pt,
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