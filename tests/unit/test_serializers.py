"""Unit tests for serializers."""

import json
from pathlib import Path

import pytest

from slidemaker.core.models import PageDefinition, Position, Size, SlideConfig, TextElement
from slidemaker.core.serializers import JSONSerializer, MarkdownSerializer


class TestJSONSerializer:
    """Tests for JSONSerializer."""

    def test_serialize_config(self):
        """Test serializing SlideConfig."""
        config = SlideConfig.create_16_9()
        data = JSONSerializer.serialize_config(config)

        assert isinstance(data, dict)
        assert data["size"] == "16:9"
        assert data["width"] == 1920
        assert data["height"] == 1080

    def test_deserialize_config(self):
        """Test deserializing SlideConfig."""
        data = {
            "size": "16:9",
            "width": 1920,
            "height": 1080,
            "background": {"type": "color", "value": "#FFFFFF"},
            "output_filename": "test.pptx",
            "theme": None,
            "default_font_family": "Arial",
            "default_font_size": 18,
        }
        config = JSONSerializer.deserialize_config(data)

        assert config.size.value == "16:9"
        assert config.width == 1920
        assert config.height == 1080

    def test_serialize_page(self):
        """Test serializing PageDefinition."""
        page = PageDefinition(page_number=1, title="Test Page")
        text = TextElement(
            position=Position(x=10, y=20), size=Size(width=100, height=50), content="Hello"
        )
        page.add_element(text)

        data = JSONSerializer.serialize_page(page)

        assert isinstance(data, dict)
        assert data["page_number"] == 1
        assert data["title"] == "Test Page"
        assert len(data["elements"]) == 1

    def test_roundtrip_serialization(self, tmp_path):
        """Test full roundtrip: save to file and load back."""
        config = SlideConfig.create_16_9(output_filename="test.pptx")
        page = PageDefinition(page_number=1, title="Test Slide")
        text = TextElement(
            position=Position(x=100, y=100),
            size=Size(width=800, height=100),
            content="Test content",
        )
        page.add_element(text)

        file_path = tmp_path / "test_presentation.json"
        JSONSerializer.save_to_file(config, [page], file_path)

        assert file_path.exists()

        loaded_config, loaded_pages = JSONSerializer.load_from_file(file_path)

        assert loaded_config.size == config.size
        assert loaded_config.output_filename == config.output_filename
        assert len(loaded_pages) == 1
        assert loaded_pages[0].page_number == 1
        assert loaded_pages[0].title == "Test Slide"
        assert len(loaded_pages[0].elements) == 1

    def test_load_from_nonexistent_file(self):
        """Test loading from non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="Presentation file not found"):
            JSONSerializer.load_from_file("nonexistent.json")

    def test_load_from_invalid_json(self, tmp_path):
        """Test loading invalid JSON raises ValueError."""
        file_path = tmp_path / "invalid.json"
        file_path.write_text("{ invalid json }")

        with pytest.raises(ValueError, match="Invalid JSON format"):
            JSONSerializer.load_from_file(file_path)

    def test_load_from_missing_fields(self, tmp_path):
        """Test loading JSON with missing required fields."""
        file_path = tmp_path / "missing_fields.json"
        file_path.write_text(json.dumps({"slide_config": {}}))

        with pytest.raises(ValueError, match="missing 'pages' field"):
            JSONSerializer.load_from_file(file_path)

    def test_load_from_non_dict(self, tmp_path):
        """Test loading JSON that is not a dictionary."""
        file_path = tmp_path / "non_dict.json"
        file_path.write_text(json.dumps([1, 2, 3]))

        with pytest.raises(ValueError, match="expected object"):
            JSONSerializer.load_from_file(file_path)


class TestMarkdownSerializer:
    """Tests for MarkdownSerializer."""

    def test_serialize_page_with_title(self):
        """Test serializing page with title."""
        page = PageDefinition(page_number=1, title="Test Page")
        md = MarkdownSerializer.serialize_page(page)

        assert "## Test Page" in md

    def test_serialize_page_with_text_elements(self):
        """Test serializing page with text elements."""
        page = PageDefinition(page_number=1)
        text1 = TextElement(
            position=Position(x=0, y=0), size=Size(width=100, height=50), content="First point"
        )
        text2 = TextElement(
            position=Position(x=0, y=0), size=Size(width=100, height=50), content="Second point"
        )
        page.add_element(text1)
        page.add_element(text2)

        md = MarkdownSerializer.serialize_page(page)

        assert "- First point" in md
        assert "- Second point" in md

    def test_serialize_page_with_image_elements(self):
        """Test serializing page with image elements."""
        from slidemaker.core.models import ImageElement

        page = PageDefinition(page_number=1)
        image = ImageElement(
            position=Position(x=0, y=0),
            size=Size(width=100, height=50),
            source="test.png",
            alt_text="Test Image",
        )
        page.add_element(image)

        md = MarkdownSerializer.serialize_page(page)

        assert "![Test Image](test.png)" in md

    def test_serialize_presentation(self):
        """Test serializing entire presentation."""
        config = SlideConfig(output_filename="my_presentation.pptx")
        page1 = PageDefinition(page_number=1, title="First Slide")
        page2 = PageDefinition(page_number=2, title="Second Slide")

        md = MarkdownSerializer.serialize_presentation(config, [page1, page2])

        assert "# My Presentation" in md
        assert "## First Slide" in md
        assert "## Second Slide" in md

    def test_save_to_file(self, tmp_path):
        """Test saving presentation to markdown file."""
        config = SlideConfig()
        page = PageDefinition(page_number=1, title="Test")

        file_path = tmp_path / "test.md"
        MarkdownSerializer.save_to_file(config, [page], file_path)

        assert file_path.exists()
        content = file_path.read_text()
        assert "## Test" in content

    def test_parse_markdown_basic(self):
        """Test parsing basic markdown."""
        content = """# Presentation Title

## Slide 1
- Point 1
- Point 2

## Slide 2
- Point 3
"""
        pages = MarkdownSerializer.parse_markdown(content)

        assert len(pages) == 2
        assert pages[0]["title"] == "Slide 1"
        assert "Point 1" in pages[0]["content"]
        assert pages[1]["title"] == "Slide 2"
        assert "Point 3" in pages[1]["content"]

    def test_parse_markdown_empty(self):
        """Test parsing empty markdown."""
        pages = MarkdownSerializer.parse_markdown("")
        assert len(pages) == 0

    def test_parse_markdown_no_h2(self):
        """Test parsing markdown without H2 headings."""
        content = """# Title
Some content
More content"""
        pages = MarkdownSerializer.parse_markdown(content)
        assert len(pages) == 0

    def test_load_from_file(self, tmp_path):
        """Test loading and parsing markdown file."""
        file_path = tmp_path / "test.md"
        file_path.write_text(
            """## Slide 1
Content here

## Slide 2
More content"""
        )

        pages = MarkdownSerializer.load_from_file(file_path)

        assert len(pages) == 2
        assert pages[0]["title"] == "Slide 1"
        assert pages[1]["title"] == "Slide 2"
