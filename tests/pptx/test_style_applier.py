"""Tests for StyleApplier class."""

from pathlib import Path

import pytest
from pptx import Presentation

from slidemaker.pptx.style_applier import StyleApplier, StyleApplierError, TemplateNotFoundError


class TestStyleApplierInit:
    """Tests for StyleApplier initialization."""

    def test_init_without_template(self) -> None:
        """Test initialization without template path."""
        applier = StyleApplier()
        assert applier.template_path is None

    def test_init_with_valid_template(self, tmp_path: Path) -> None:
        """Test initialization with valid template file."""
        # Create a dummy template file
        template_path = tmp_path / "template.pptx"
        prs = Presentation()
        prs.save(str(template_path))

        applier = StyleApplier(template_path=template_path)
        assert applier.template_path == template_path

    def test_init_with_nonexistent_template(self, tmp_path: Path) -> None:
        """Test initialization with non-existent template file."""
        template_path = tmp_path / "nonexistent.pptx"

        with pytest.raises(TemplateNotFoundError) as exc_info:
            StyleApplier(template_path=template_path)

        assert "Template file not found" in str(exc_info.value)
        assert str(template_path) in str(exc_info.value)


class TestStyleApplierApplyTheme:
    """Tests for apply_theme method."""

    def test_apply_theme_without_template(self) -> None:
        """Test apply_theme when no template is configured."""
        applier = StyleApplier()
        prs = Presentation()

        # Should not raise an error, just log a warning
        applier.apply_theme(prs)

    def test_apply_theme_with_template(self, tmp_path: Path) -> None:
        """Test apply_theme when template is configured."""
        # Create a dummy template file
        template_path = tmp_path / "template.pptx"
        template_prs = Presentation()
        template_prs.save(str(template_path))

        applier = StyleApplier(template_path=template_path)
        prs = Presentation()

        # Should not raise an error
        applier.apply_theme(prs)


class TestStyleApplierSetDefaultFont:
    """Tests for set_default_font method."""

    def test_set_default_font_name_only(self) -> None:
        """Test set_default_font with font name only."""
        applier = StyleApplier()
        prs = Presentation()

        # Should not raise an error
        applier.set_default_font(prs, "Arial")

    def test_set_default_font_with_size(self) -> None:
        """Test set_default_font with font name and size."""
        applier = StyleApplier()
        prs = Presentation()

        # Should not raise an error
        applier.set_default_font(prs, "Calibri", 18)

    def test_set_default_font_various_fonts(self) -> None:
        """Test set_default_font with various font names."""
        applier = StyleApplier()
        prs = Presentation()

        fonts = ["Arial", "Calibri", "Times New Roman", "MS Gothic", "Verdana"]
        for font_name in fonts:
            applier.set_default_font(prs, font_name, 16)


class TestStyleApplierLoadTemplate:
    """Tests for _load_template private method."""

    def test_load_valid_template(self, tmp_path: Path) -> None:
        """Test loading a valid template file."""
        # Create a dummy template file
        template_path = tmp_path / "template.pptx"
        template_prs = Presentation()
        template_prs.slides.add_slide(template_prs.slide_layouts[0])
        template_prs.save(str(template_path))

        applier = StyleApplier()
        loaded_prs = applier._load_template(template_path)

        assert loaded_prs is not None
        assert len(loaded_prs.slides) == 1

    def test_load_nonexistent_template(self, tmp_path: Path) -> None:
        """Test loading a non-existent template file."""
        template_path = tmp_path / "nonexistent.pptx"

        applier = StyleApplier()

        with pytest.raises(TemplateNotFoundError) as exc_info:
            applier._load_template(template_path)

        assert "Template file not found" in str(exc_info.value)

    def test_load_invalid_template(self, tmp_path: Path) -> None:
        """Test loading an invalid template file."""
        # Create a text file with .pptx extension
        template_path = tmp_path / "invalid.pptx"
        template_path.write_text("This is not a valid PowerPoint file")

        applier = StyleApplier()

        with pytest.raises(StyleApplierError) as exc_info:
            applier._load_template(template_path)

        assert "Failed to load template" in str(exc_info.value)


class TestStyleApplierIntegration:
    """Integration tests for StyleApplier."""

    def test_full_workflow_with_template(self, tmp_path: Path) -> None:
        """Test complete workflow: init with template, apply theme, set font."""
        # Create a template
        template_path = tmp_path / "corporate_template.pptx"
        template_prs = Presentation()
        template_prs.slides.add_slide(template_prs.slide_layouts[0])
        template_prs.save(str(template_path))

        # Initialize with template
        applier = StyleApplier(template_path=template_path)

        # Create new presentation
        prs = Presentation()

        # Apply theme
        applier.apply_theme(prs)

        # Set default font
        applier.set_default_font(prs, "Arial", 18)

        # Should complete without errors

    def test_load_template_and_use(self, tmp_path: Path) -> None:
        """Test loading template and using it."""
        # Create a template with custom slides
        template_path = tmp_path / "template.pptx"
        template_prs = Presentation()
        template_prs.slides.add_slide(template_prs.slide_layouts[0])
        template_prs.slides.add_slide(template_prs.slide_layouts[1])
        template_prs.save(str(template_path))

        # Load template
        applier = StyleApplier()
        loaded_prs = applier._load_template(template_path)

        # Verify loaded presentation has correct number of slides
        assert len(loaded_prs.slides) == 2

        # Add more slides to loaded presentation
        loaded_prs.slides.add_slide(loaded_prs.slide_layouts[6])
        assert len(loaded_prs.slides) == 3

        # Save modified presentation
        output_path = tmp_path / "output.pptx"
        loaded_prs.save(str(output_path))
        assert output_path.exists()
