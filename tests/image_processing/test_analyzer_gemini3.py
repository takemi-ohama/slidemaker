import pytest
from unittest.mock import AsyncMock, MagicMock
from PIL import Image
from slidemaker.image_processing.analyzer import ImageAnalyzer
from slidemaker.core.models.page_definition import PageDefinition
from slidemaker.core.models.element import TextElement
from slidemaker.llm.base import LLMAdapter
from slidemaker.image_processing.phase_models import (
    LayoutMetadata, ColumnDefinition, HorizontalZone, 
    StyledElement, PrecisePosition, PreciseSize, ElementStyle
)

@pytest.fixture
def mock_llm_manager():
    manager = MagicMock()
    manager.composition_llm = MagicMock(spec=LLMAdapter)
    manager.image_llm = MagicMock(spec=LLMAdapter)
    return manager

@pytest.fixture
def sample_image():
    return Image.new('RGB', (960, 540), color='white')

@pytest.mark.asyncio
async def test_analyzer_gemini3_config(mock_llm_manager, sample_image):
    """Test that analyzer uses 960x540 dimensions by default."""
    analyzer = ImageAnalyzer(mock_llm_manager)
    assert analyzer.slide_dimensions == (960, 540)

@pytest.mark.asyncio
async def test_analyzer_pipeline_integration(mock_llm_manager, sample_image):
    """Test the full 4-phase pipeline integration."""
    analyzer = ImageAnalyzer(mock_llm_manager)
    
    # Mock Phase 1: Layout Analysis
    layout_meta = LayoutMetadata(
        layout_type="single_column",
        columns=[ColumnDefinition(index=1, x_start=5, x_end=95, width=90)],
        horizontal_zones=[HorizontalZone(name="title", y_start=5, y_end=15)],
        alignment_rules={},
        title="Test Slide",
        background_color="#FFFFFF"
    )
    analyzer.layout_analyzer.analyze_layout = AsyncMock(return_value=layout_meta)
    
    # Mock Phase 2: Element Identification
    rough_elements = [
        {"id": "elem1", "type": "text", "rough_position": {"x": 10, "y": 10}}
    ]
    analyzer.element_identifier.identify_elements = AsyncMock(return_value=rough_elements)
    
    # Mock Phase 3: Coordinate Measurement
    precise_elements = [
        {"id": "elem1", "type": "text", "position": {"x": 10.5, "y": 10.5}, "size": {"width": 80, "height": 10}}
    ]
    analyzer.coordinate_measurer.measure_coordinates = AsyncMock(return_value=precise_elements)
    
    # Mock Phase 4: Style Estimation
    styled_elements = [
        StyledElement(
            id="elem1",
            type="text",
            content="Test Content",
            position=PrecisePosition(x=10.5, y=10.5),
            size=PreciseSize(width=80, height=10),
            style=ElementStyle(
                font_family="Arial",
                font_size=24,
                color="#000000",
                bold=True
            )
        )
    ]
    analyzer.style_estimator.estimate_styles = AsyncMock(return_value=styled_elements)
    
    # Execute
    result = await analyzer.analyze_slide_image(sample_image)
    
    # Verify
    assert isinstance(result, PageDefinition)
    assert len(result.elements) == 1
    assert isinstance(result.elements[0], TextElement)
    assert result.elements[0].content == "Test Content"
    
    # Verify method calls
    analyzer.layout_analyzer.analyze_layout.assert_called_once()
    analyzer.element_identifier.identify_elements.assert_called_once()
    analyzer.coordinate_measurer.measure_coordinates.assert_called_once()
    analyzer.style_estimator.estimate_styles.assert_called_once()

@pytest.mark.asyncio
async def test_font_size_scaling(mock_llm_manager):
    """Test that font size scaling matches the new 0.5 factor logic."""
    # This indirectly tests the logic in prompts/image_processing.py by checking the prompt generation
    from slidemaker.llm.prompts.image_processing import create_image_analysis_prompt
    
    system_prompt, user_prompt = create_image_analysis_prompt(960, 540)
    
    # Check that the prompt contains the new reduced font size estimates
    # Header: 5% of 540 is 27px. 27 * 0.4 = 10.8 -> 10pt
    assert "**Header (Medium):** ~27px height -> ~10pt" in user_prompt
    
    # Body: 3.5% of 540 is 18.9px -> 18px. 18 * 0.4 = 7.2 -> 7pt
    assert "**Body (Normal):** ~18px height -> ~7pt" in user_prompt