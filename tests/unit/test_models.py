"""Unit tests for core models."""

import pytest

from slidemaker.core.models import (
    Alignment,
    Color,
    FitMode,
    FontConfig,
    ImageElement,
    PageDefinition,
    Position,
    Size,
    SlideConfig,
    SlideSize,
    TextElement,
)


class TestColor:
    """Tests for Color model."""

    def test_color_from_hex(self):
        """Test creating color from hex value."""
        color = Color(hex_value="#ff8000")
        assert color.hex_value == "#ff8000"

    def test_color_from_rgb_valid(self):
        """Test creating color from valid RGB values."""
        color = Color.from_rgb(255, 128, 0)
        assert color.hex_value == "#ff8000"

    def test_color_from_rgb_black(self):
        """Test creating black color."""
        color = Color.from_rgb(0, 0, 0)
        assert color.hex_value == "#000000"

    def test_color_from_rgb_white(self):
        """Test creating white color."""
        color = Color.from_rgb(255, 255, 255)
        assert color.hex_value == "#ffffff"

    def test_color_from_rgb_invalid_too_high(self):
        """Test that RGB values > 255 raise ValueError."""
        with pytest.raises(ValueError, match="RGB values must be integers in range 0-255"):
            Color.from_rgb(256, 0, 0)

    def test_color_from_rgb_invalid_negative(self):
        """Test that negative RGB values raise ValueError."""
        with pytest.raises(ValueError, match="RGB values must be integers in range 0-255"):
            Color.from_rgb(-1, 0, 0)

    def test_color_from_rgb_invalid_float(self):
        """Test that float RGB values raise ValueError."""
        with pytest.raises(ValueError, match="RGB values must be integers in range 0-255"):
            Color.from_rgb(255.5, 0, 0)  # type: ignore

    def test_color_hex_validation(self):
        """Test that invalid hex values are rejected."""
        with pytest.raises(Exception):  # Pydantic validation error
            Color(hex_value="invalid")

    def test_color_immutable(self):
        """Test that Color is immutable."""
        color = Color(hex_value="#ff0000")
        with pytest.raises(Exception):  # Pydantic frozen model
            color.hex_value = "#00ff00"  # type: ignore


class TestPosition:
    """Tests for Position model."""

    def test_position_creation(self):
        """Test creating position."""
        pos = Position(x=10, y=20)
        assert pos.x == 10
        assert pos.y == 20

    def test_position_immutable(self):
        """Test that Position is immutable."""
        pos = Position(x=10, y=20)
        with pytest.raises(Exception):  # Pydantic frozen model
            pos.x = 30  # type: ignore


class TestSize:
    """Tests for Size model."""

    def test_size_creation(self):
        """Test creating size."""
        size = Size(width=100, height=50)
        assert size.width == 100
        assert size.height == 50

    def test_size_validation_positive(self):
        """Test that size dimensions must be positive."""
        with pytest.raises(Exception):  # Pydantic validation error
            Size(width=0, height=50)

        with pytest.raises(Exception):
            Size(width=100, height=-10)

    def test_size_immutable(self):
        """Test that Size is immutable."""
        size = Size(width=100, height=50)
        with pytest.raises(Exception):  # Pydantic frozen model
            size.width = 200  # type: ignore


class TestTextElement:
    """Tests for TextElement model."""

    def test_text_element_creation(self):
        """Test creating text element."""
        elem = TextElement(
            position=Position(x=0, y=0),
            size=Size(width=100, height=50),
            content="Hello, World!",
        )
        assert elem.element_type == "text"
        assert elem.content == "Hello, World!"
        assert elem.z_index == 0
        assert elem.opacity == 1.0

    def test_text_element_with_font(self):
        """Test text element with custom font."""
        font = FontConfig(family="Arial", size=24, bold=True)
        elem = TextElement(
            position=Position(x=0, y=0),
            size=Size(width=100, height=50),
            content="Bold Text",
            font=font,
        )
        assert elem.font.family == "Arial"
        assert elem.font.size == 24
        assert elem.font.bold is True

    def test_text_element_alignment(self):
        """Test text element alignment."""
        elem = TextElement(
            position=Position(x=0, y=0),
            size=Size(width=100, height=50),
            content="Centered",
            alignment=Alignment.CENTER,
        )
        assert elem.alignment == Alignment.CENTER


class TestImageElement:
    """Tests for ImageElement model."""

    def test_image_element_creation(self):
        """Test creating image element."""
        elem = ImageElement(
            position=Position(x=10, y=10),
            size=Size(width=200, height=150),
            source="image.png",
        )
        assert elem.element_type == "image"
        assert elem.source == "image.png"
        assert elem.fit_mode == FitMode.CONTAIN

    def test_image_element_with_alt_text(self):
        """Test image element with alt text."""
        elem = ImageElement(
            position=Position(x=0, y=0),
            size=Size(width=100, height=100),
            source="logo.png",
            alt_text="Company Logo",
        )
        assert elem.alt_text == "Company Logo"


class TestPageDefinition:
    """Tests for PageDefinition model."""

    def test_page_definition_creation(self):
        """Test creating page definition."""
        page = PageDefinition(page_number=1, title="Welcome")
        assert page.page_number == 1
        assert page.title == "Welcome"
        assert len(page.elements) == 0

    def test_page_add_element(self):
        """Test adding elements to page."""
        page = PageDefinition(page_number=1)
        text = TextElement(
            position=Position(x=0, y=0),
            size=Size(width=100, height=50),
            content="Text",
        )
        page.add_element(text)
        assert len(page.elements) == 1
        assert page.elements[0] == text

    def test_page_get_text_elements(self):
        """Test filtering text elements."""
        page = PageDefinition(page_number=1)
        text = TextElement(
            position=Position(x=0, y=0),
            size=Size(width=100, height=50),
            content="Text",
        )
        image = ImageElement(
            position=Position(x=0, y=0), size=Size(width=100, height=50), source="img.png"
        )
        page.add_element(text)
        page.add_element(image)

        text_elements = page.get_text_elements()
        assert len(text_elements) == 1
        assert text_elements[0] == text

    def test_page_get_image_elements(self):
        """Test filtering image elements."""
        page = PageDefinition(page_number=1)
        text = TextElement(
            position=Position(x=0, y=0),
            size=Size(width=100, height=50),
            content="Text",
        )
        image = ImageElement(
            position=Position(x=0, y=0), size=Size(width=100, height=50), source="img.png"
        )
        page.add_element(text)
        page.add_element(image)

        image_elements = page.get_image_elements()
        assert len(image_elements) == 1
        assert image_elements[0] == image

    def test_page_sort_elements_by_z_index(self):
        """Test sorting elements by z-index."""
        page = PageDefinition(page_number=1)
        elem1 = TextElement(
            position=Position(x=0, y=0),
            size=Size(width=100, height=50),
            content="Back",
            z_index=0,
        )
        elem2 = TextElement(
            position=Position(x=0, y=0),
            size=Size(width=100, height=50),
            content="Front",
            z_index=10,
        )
        elem3 = TextElement(
            position=Position(x=0, y=0),
            size=Size(width=100, height=50),
            content="Middle",
            z_index=5,
        )

        page.add_element(elem2)
        page.add_element(elem1)
        page.add_element(elem3)

        page.sort_elements_by_z_index()

        assert page.elements[0].z_index == 0
        assert page.elements[1].z_index == 5
        assert page.elements[2].z_index == 10


class TestSlideConfig:
    """Tests for SlideConfig model."""

    def test_slide_config_default(self):
        """Test default slide configuration."""
        config = SlideConfig()
        assert config.size == SlideSize.WIDESCREEN_16_9
        assert config.width == 1920
        assert config.height == 1080

    def test_slide_config_16_9(self):
        """Test 16:9 configuration factory."""
        config = SlideConfig.create_16_9()
        assert config.size == SlideSize.WIDESCREEN_16_9
        assert config.width == 1920
        assert config.height == 1080

    def test_slide_config_4_3(self):
        """Test 4:3 configuration factory."""
        config = SlideConfig.create_4_3()
        assert config.size == SlideSize.STANDARD_4_3
        assert config.width == 1024
        assert config.height == 768

    def test_slide_config_custom_output(self):
        """Test custom output filename."""
        config = SlideConfig(output_filename="custom.pptx")
        assert config.output_filename == "custom.pptx"
