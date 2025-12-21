"""Tests for CompositionParser."""

import pytest
from pydantic import ValidationError

from slidemaker.core.models.common import Alignment, FitMode
from slidemaker.core.models.element import FontConfig, ImageElement, TextElement
from slidemaker.workflows.composition_parser import CompositionParser
from slidemaker.workflows.exceptions import WorkflowValidationError


class TestCompositionParser:
    """Tests for CompositionParser."""

    @pytest.fixture
    def parser(self):
        """Create a CompositionParser instance."""
        return CompositionParser()

    def test_parse_slide_config_minimal(self, parser):
        """Test parsing minimal slide config."""
        config_data = {}
        config = parser.parse_slide_config(config_data)

        assert config.size == "16:9"  # default
        assert config.theme == "default"  # default

    def test_parse_slide_config_complete(self, parser):
        """Test parsing complete slide config."""
        config_data = {
            "size": "4:3",
            "theme": "corporate",
        }
        config = parser.parse_slide_config(config_data)

        assert config.size == "4:3"
        assert config.theme == "corporate"

    def test_parse_slide_config_with_extra_fields(self, parser):
        """Test parsing slide config with extra fields (should be ignored)."""
        config_data = {
            "size": "16:9",
            "theme": "modern",
            "extra_field": "ignored",
        }
        config = parser.parse_slide_config(config_data)

        assert config.size == "16:9"
        assert config.theme == "modern"

    def test_parse_pages_empty(self, parser):
        """Test parsing empty pages list."""
        pages_data = []
        pages = parser.parse_pages(pages_data)

        assert pages == []

    def test_parse_pages_single_page_with_text(self, parser):
        """Test parsing a single page with text element."""
        pages_data = [
            {
                "title": "Slide 1",
                "background_color": "#FFFFFF",
                "elements": [
                    {
                        "type": "text",
                        "position": {"x": 100, "y": 200},
                        "size": {"width": 800, "height": 100},
                        "content": "Hello World",
                        "font": {
                            "family": "Arial",
                            "size": 24,
                            "color": "#000000",
                            "bold": True,
                        },
                        "alignment": "center",
                        "z_index": 1,
                    }
                ],
            }
        ]
        pages = parser.parse_pages(pages_data)

        assert len(pages) == 1
        page = pages[0]
        assert page.page_number == 1
        assert page.title == "Slide 1"
        assert page.background_color == "#FFFFFF"
        assert len(page.elements) == 1

        element = page.elements[0]
        assert isinstance(element, TextElement)
        assert element.content == "Hello World"
        assert element.position.x == 100
        assert element.position.y == 200
        assert element.size.width == 800
        assert element.size.height == 100
        assert element.font.family == "Arial"
        assert element.font.size == 24
        assert element.font.bold is True
        assert element.alignment == Alignment.CENTER
        assert element.z_index == 1

    def test_parse_pages_single_page_with_image(self, parser):
        """Test parsing a single page with image element."""
        pages_data = [
            {
                "title": "Image Slide",
                "elements": [
                    {
                        "type": "image",
                        "position": {"x": 50, "y": 50},
                        "size": {"width": 400, "height": 300},
                        "source": "/path/to/image.png",
                        "fit_mode": "contain",
                        "z_index": 0,
                    }
                ],
            }
        ]
        pages = parser.parse_pages(pages_data)

        assert len(pages) == 1
        page = pages[0]
        assert page.page_number == 1
        assert page.title == "Image Slide"
        assert len(page.elements) == 1

        element = page.elements[0]
        assert isinstance(element, ImageElement)
        assert element.source == "/path/to/image.png"
        assert element.position.x == 50
        assert element.position.y == 50
        assert element.size.width == 400
        assert element.size.height == 300
        assert element.fit_mode == FitMode.CONTAIN
        assert element.z_index == 0

    def test_parse_pages_multiple_elements(self, parser):
        """Test parsing a page with multiple elements."""
        pages_data = [
            {
                "title": "Mixed Slide",
                "elements": [
                    {
                        "type": "text",
                        "position": {"x": 100, "y": 100},
                        "size": {"width": 800, "height": 50},
                        "content": "Title",
                    },
                    {
                        "type": "image",
                        "position": {"x": 200, "y": 200},
                        "size": {"width": 400, "height": 300},
                        "source": "image.png",
                    },
                    {
                        "type": "text",
                        "position": {"x": 100, "y": 550},
                        "size": {"width": 800, "height": 30},
                        "content": "Caption",
                    },
                ],
            }
        ]
        pages = parser.parse_pages(pages_data)

        assert len(pages) == 1
        page = pages[0]
        assert len(page.elements) == 3
        assert isinstance(page.elements[0], TextElement)
        assert isinstance(page.elements[1], ImageElement)
        assert isinstance(page.elements[2], TextElement)

    def test_parse_pages_multiple_pages(self, parser):
        """Test parsing multiple pages."""
        pages_data = [
            {
                "title": "Page 1",
                "elements": [
                    {
                        "type": "text",
                        "position": {"x": 100, "y": 100},
                        "size": {"width": 800, "height": 50},
                        "content": "Page 1 content",
                    }
                ],
            },
            {
                "title": "Page 2",
                "elements": [
                    {
                        "type": "text",
                        "position": {"x": 100, "y": 100},
                        "size": {"width": 800, "height": 50},
                        "content": "Page 2 content",
                    }
                ],
            },
        ]
        pages = parser.parse_pages(pages_data)

        assert len(pages) == 2
        assert pages[0].page_number == 1
        assert pages[0].title == "Page 1"
        assert pages[1].page_number == 2
        assert pages[1].title == "Page 2"

    def test_parse_text_element_with_defaults(self, parser):
        """Test parsing text element with default values."""
        pages_data = [
            {
                "title": "Test",
                "elements": [
                    {
                        "type": "text",
                        "position": {"x": 100, "y": 100},
                        "size": {"width": 800, "height": 50},
                        "content": "Test with defaults",
                        # font, alignment, z_index will use defaults
                    }
                ],
            }
        ]
        pages = parser.parse_pages(pages_data)

        element = pages[0].elements[0]
        assert isinstance(element, TextElement)
        assert element.font.family == "Arial"  # default
        assert element.font.size == 18  # default
        assert element.font.color.hex_value == "#000000"  # default (Color instance)
        assert element.font.bold is False  # default
        assert element.alignment == Alignment.LEFT  # default
        assert element.z_index == 0  # default

    def test_parse_image_element_with_defaults(self, parser):
        """Test parsing image element with default values."""
        pages_data = [
            {
                "title": "Test",
                "elements": [
                    {
                        "type": "image",
                        "position": {"x": 100, "y": 100},
                        "size": {"width": 400, "height": 300},
                        "source": "image.png",
                        # fit_mode, z_index will use defaults
                    }
                ],
            }
        ]
        pages = parser.parse_pages(pages_data)

        element = pages[0].elements[0]
        assert isinstance(element, ImageElement)
        assert element.fit_mode == FitMode.CONTAIN  # default
        assert element.z_index == 0  # default

    def test_parse_pages_with_invalid_alignment(self, parser):
        """Test parsing page with invalid alignment (should fallback to default)."""
        pages_data = [
            {
                "title": "Test",
                "elements": [
                    {
                        "type": "text",
                        "position": {"x": 100, "y": 100},
                        "size": {"width": 800, "height": 50},
                        "content": "Test",
                        "alignment": "invalid_alignment",  # invalid
                    }
                ],
            }
        ]
        pages = parser.parse_pages(pages_data)

        element = pages[0].elements[0]
        assert isinstance(element, TextElement)
        assert element.alignment == Alignment.LEFT  # fallback to default

    def test_parse_pages_with_invalid_fit_mode(self, parser):
        """Test parsing page with invalid fit mode (should fallback to default)."""
        pages_data = [
            {
                "title": "Test",
                "elements": [
                    {
                        "type": "image",
                        "position": {"x": 100, "y": 100},
                        "size": {"width": 400, "height": 300},
                        "source": "image.png",
                        "fit_mode": "invalid_mode",  # invalid
                    }
                ],
            }
        ]
        pages = parser.parse_pages(pages_data)

        element = pages[0].elements[0]
        assert isinstance(element, ImageElement)
        assert element.fit_mode == FitMode.CONTAIN  # fallback to default

    def test_parse_pages_with_unknown_element_type(self, parser):
        """Test parsing page with unknown element type (should be skipped)."""
        pages_data = [
            {
                "title": "Test",
                "elements": [
                    {
                        "type": "text",
                        "position": {"x": 100, "y": 100},
                        "size": {"width": 800, "height": 50},
                        "content": "Valid text",
                    },
                    {
                        "type": "video",  # unknown type
                        "position": {"x": 200, "y": 200},
                        "size": {"width": 400, "height": 300},
                        "source": "video.mp4",
                    },
                ],
            }
        ]
        pages = parser.parse_pages(pages_data)

        # Unknown element should be skipped
        assert len(pages[0].elements) == 1
        assert isinstance(pages[0].elements[0], TextElement)

    def test_parse_pages_with_missing_required_fields(self, parser):
        """Test parsing page with missing required fields (should raise error)."""
        pages_data = [
            {
                "title": "Test",
                "elements": [
                    {
                        "type": "text",
                        "position": {"x": 100, "y": 100},
                        "size": {"width": 800, "height": 50},
                        # missing "content"
                    }
                ],
            }
        ]

        with pytest.raises(WorkflowValidationError) as exc_info:
            parser.parse_pages(pages_data)

        assert "Failed to parse page 1" in str(exc_info.value)

    def test_parse_pages_with_background_image(self, parser):
        """Test parsing page with background image."""
        pages_data = [
            {
                "title": "Test",
                "background_image": "/path/to/background.png",
                "elements": [],
            }
        ]
        pages = parser.parse_pages(pages_data)

        assert len(pages) == 1
        assert pages[0].background_image == "/path/to/background.png"
