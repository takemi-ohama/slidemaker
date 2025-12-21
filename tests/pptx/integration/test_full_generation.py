"""
PowerPoint生成の統合テスト.

エンドツーエンドでのスライドデッキ生成をテストします。
実際のPowerPointファイルを生成し、その内容を検証します。
"""

from pathlib import Path

import pytest
from PIL import Image
from pptx import Presentation

from slidemaker.core.models.common import Alignment, Color, FitMode, Position, Size
from slidemaker.core.models.element import FontConfig, ImageElement, TextElement
from slidemaker.core.models.page_definition import PageDefinition
from slidemaker.core.models.slide_config import SlideConfig
from slidemaker.pptx.generator import PowerPointGenerator


class TestSimpleSlideDeckGeneration:
    """シンプルなスライドデッキ生成の統合テスト."""

    def test_generate_single_page_text_only(self, tmp_path: Path) -> None:
        """テキストのみの1ページスライドが正しく生成されることを確認."""
        # Arrange
        config = SlideConfig.create_16_9()
        generator = PowerPointGenerator(config)

        text_element = TextElement(
            element_type="text",
            position=Position(x=914400, y=914400),  # 1インチ
            size=Size(width=8229600, height=1828800),  # 9インチ x 2インチ
            z_index=0,
            content="Hello, PowerPoint!",
            alignment=Alignment.CENTER,
        )

        pages = [
            PageDefinition(
                page_number=1,
                title="Simple Text Slide",
                background_color="#FFFFFF",
                elements=[text_element],
            )
        ]

        output_path = tmp_path / "simple_text.pptx"

        # Act
        result = generator.generate(pages, output_path)

        # Assert
        assert result.exists()
        assert result.stat().st_size > 0

        # 生成されたファイルを読み込んで検証
        presentation = Presentation(str(result))
        assert len(presentation.slides) == 1

        slide = presentation.slides[0]
        assert len(slide.shapes) >= 1  # テキストボックスが追加されている

        # テキスト内容を確認
        textbox = slide.shapes[0]
        assert "Hello, PowerPoint!" in textbox.text

    def test_generate_three_page_text_slides(self, tmp_path: Path) -> None:
        """3ページのテキストスライドが正しく生成されることを確認."""
        # Arrange
        config = SlideConfig.create_16_9()
        generator = PowerPointGenerator(config)

        pages = []
        for i in range(1, 4):
            text_element = TextElement(
                element_type="text",
                position=Position(x=914400, y=914400),
                size=Size(width=8229600, height=1828800),
                z_index=0,
                content=f"This is page {i}",
                alignment=Alignment.CENTER,
            )

            page = PageDefinition(
                page_number=i,
                title=f"Page {i}",
                background_color="#F0F0F0",
                elements=[text_element],
            )
            pages.append(page)

        output_path = tmp_path / "three_pages.pptx"

        # Act
        result = generator.generate(pages, output_path)

        # Assert
        assert result.exists()

        presentation = Presentation(str(result))
        assert len(presentation.slides) == 3

        # 各スライドのテキストを確認
        for i, slide in enumerate(presentation.slides, start=1):
            textbox = slide.shapes[0]
            assert f"This is page {i}" in textbox.text


class TestComplexSlideDeckGeneration:
    """複雑なスライドデッキ生成の統合テスト."""

    @pytest.fixture
    def test_image(self, tmp_path: Path) -> Path:
        """テスト用の画像ファイルを作成."""
        image_path = tmp_path / "test_image.png"
        img = Image.new("RGB", (400, 300), color="blue")
        img.save(image_path)
        return image_path

    def test_generate_slide_with_text_and_image(
        self, tmp_path: Path, test_image: Path
    ) -> None:
        """テキストと画像を含むスライドが正しく生成されることを確認."""
        # Arrange
        config = SlideConfig.create_16_9()
        generator = PowerPointGenerator(config)

        title_text = TextElement(
            element_type="text",
            position=Position(x=914400, y=457200),  # 1インチ, 0.5インチ
            size=Size(width=8229600, height=914400),  # 9インチ x 1インチ
            z_index=1,
            content="Slide with Image",
            font=FontConfig(family="Arial", size=32, bold=True),
            alignment=Alignment.CENTER,
        )

        image_element = ImageElement(
            element_type="image",
            position=Position(x=2743200, y=1828800),  # 3インチ, 2インチ
            size=Size(width=3657600, height=2743200),  # 4インチ x 3インチ
            z_index=0,
            source=str(test_image),
            fit_mode=FitMode.CONTAIN,
        )

        body_text = TextElement(
            element_type="text",
            position=Position(x=914400, y=4800600),  # 1インチ, 5.25インチ
            size=Size(width=8229600, height=457200),  # 9インチ x 0.5インチ
            z_index=1,
            content="Image caption text",
            alignment=Alignment.CENTER,
        )

        pages = [
            PageDefinition(
                page_number=1,
                title="Complex Slide",
                background_color="#FFFFFF",
                elements=[title_text, image_element, body_text],
            )
        ]

        output_path = tmp_path / "complex_slide.pptx"

        # Act
        result = generator.generate(pages, output_path)

        # Assert
        assert result.exists()

        presentation = Presentation(str(result))
        assert len(presentation.slides) == 1

        slide = presentation.slides[0]
        # テキスト2つ + 画像1つ = 3つのシェイプ
        assert len(slide.shapes) == 3

    def test_generate_multipage_mixed_content(
        self, tmp_path: Path, test_image: Path
    ) -> None:
        """複数ページでテキストと画像が混在するスライドデッキが生成されることを確認."""
        # Arrange
        config = SlideConfig.create_16_9()
        generator = PowerPointGenerator(config)

        # Page 1: テキストのみ
        page1_text = TextElement(
            element_type="text",
            position=Position(x=914400, y=2743200),
            size=Size(width=8229600, height=1828800),
            z_index=0,
            content="Page 1: Text Only",
            font=FontConfig(size=44, bold=True),
            alignment=Alignment.CENTER,
        )

        page1 = PageDefinition(
            page_number=1,
            title="Text Page",
            background_color="#E0E0E0",
            elements=[page1_text],
        )

        # Page 2: 画像のみ
        page2_image = ImageElement(
            element_type="image",
            position=Position(x=2286000, y=1371600),
            size=Size(width=4572000, height=3429000),
            z_index=0,
            source=str(test_image),
            fit_mode=FitMode.CONTAIN,
        )

        page2 = PageDefinition(
            page_number=2,
            title="Image Page",
            background_color="#FFFFFF",
            elements=[page2_image],
        )

        # Page 3: テキスト + 画像
        page3_text = TextElement(
            element_type="text",
            position=Position(x=914400, y=457200),
            size=Size(width=8229600, height=914400),
            z_index=1,
            content="Page 3: Mixed Content",
            font=FontConfig(size=36, bold=True),
            alignment=Alignment.CENTER,
        )

        page3_image = ImageElement(
            element_type="image",
            position=Position(x=2743200, y=2286000),
            size=Size(width=3657600, height=2743200),
            z_index=0,
            source=str(test_image),
            fit_mode=FitMode.FILL,
        )

        page3 = PageDefinition(
            page_number=3,
            title="Mixed Page",
            background_color="#F5F5F5",
            elements=[page3_text, page3_image],
        )

        pages = [page1, page2, page3]
        output_path = tmp_path / "multipage_mixed.pptx"

        # Act
        result = generator.generate(pages, output_path)

        # Assert
        assert result.exists()

        presentation = Presentation(str(result))
        assert len(presentation.slides) == 3

        # 各ページのシェイプ数を確認
        assert len(presentation.slides[0].shapes) == 1  # Page 1: テキスト1つ
        assert len(presentation.slides[1].shapes) == 1  # Page 2: 画像1つ
        assert len(presentation.slides[2].shapes) == 2  # Page 3: テキスト1つ + 画像1つ


class TestBackgroundSlideDeckGeneration:
    """背景付きスライドデッキ生成の統合テスト."""

    def test_generate_slides_with_different_background_colors(
        self, tmp_path: Path
    ) -> None:
        """異なる背景色を持つスライドが正しく生成されることを確認."""
        # Arrange
        config = SlideConfig.create_16_9()
        generator = PowerPointGenerator(config)

        colors = ["#FF0000", "#00FF00", "#0000FF"]  # Red, Green, Blue
        pages = []

        for i, color in enumerate(colors, start=1):
            text_element = TextElement(
                element_type="text",
                position=Position(x=914400, y=2743200),
                size=Size(width=8229600, height=1828800),
                z_index=0,
                content=f"Background Color: {color}",
                font=FontConfig(size=36, color=Color(hex_value="#FFFFFF")),  # 白色テキスト
                alignment=Alignment.CENTER,
            )

            page = PageDefinition(
                page_number=i,
                title=f"Color {i}",
                background_color=color,
                elements=[text_element],
            )
            pages.append(page)

        output_path = tmp_path / "colored_backgrounds.pptx"

        # Act
        result = generator.generate(pages, output_path)

        # Assert
        assert result.exists()

        presentation = Presentation(str(result))
        assert len(presentation.slides) == 3

        # 各スライドの背景がsolid fillであることを確認
        for slide in presentation.slides:
            background = slide.background
            fill = background.fill
            assert fill.type == 1  # MSO_FILL_TYPE.SOLID

    def test_generate_slide_with_background_image(self, tmp_path: Path) -> None:
        """背景画像付きスライドが正しく生成されることを確認."""
        # Arrange
        # 背景画像を作成
        bg_image_path = tmp_path / "background.jpg"
        bg_img = Image.new("RGB", (1920, 1080), color="lightblue")
        bg_img.save(bg_image_path)

        config = SlideConfig.create_16_9()
        generator = PowerPointGenerator(config)

        # 背景画像要素（z_index=0で最背面）
        background_element = ImageElement(
            element_type="image",
            position=Position(x=0, y=0),
            size=Size(width=9144000, height=5143500),  # 16:9の全画面
            z_index=0,
            source=str(bg_image_path),
            fit_mode=FitMode.FILL,
        )

        # 前景テキスト
        text_element = TextElement(
            element_type="text",
            position=Position(x=914400, y=2743200),
            size=Size(width=8229600, height=1828800),
            z_index=1,
            content="Text on Background Image",
            font=FontConfig(size=48, bold=True, color=Color(hex_value="#FFFFFF")),
            alignment=Alignment.CENTER,
        )

        pages = [
            PageDefinition(
                page_number=1,
                title="Background Image Slide",
                elements=[background_element, text_element],  # 背景→テキストの順
            )
        ]

        output_path = tmp_path / "background_image.pptx"

        # Act
        result = generator.generate(pages, output_path)

        # Assert
        assert result.exists()

        presentation = Presentation(str(result))
        assert len(presentation.slides) == 1

        slide = presentation.slides[0]
        # 背景画像1つ + テキスト1つ = 2つのシェイプ
        assert len(slide.shapes) == 2

        # 最初のシェイプが画像（背景）であることを確認
        first_shape = slide.shapes[0]
        assert first_shape.shape_type == 13  # MSO_SHAPE_TYPE.PICTURE


class TestFileValidation:
    """生成されたファイルの検証テスト."""

    def test_generated_file_has_reasonable_size(self, tmp_path: Path) -> None:
        """生成されたファイルサイズが妥当な範囲であることを確認."""
        # Arrange
        config = SlideConfig.create_16_9()
        generator = PowerPointGenerator(config)

        pages = []
        for i in range(1, 11):  # 10ページ
            text_element = TextElement(
                element_type="text",
                position=Position(x=914400, y=2743200),
                size=Size(width=8229600, height=1828800),
                z_index=0,
                content=f"Page {i} Content" * 10,  # ある程度のテキスト量
            )
            page = PageDefinition(
                page_number=i, title=f"Page {i}", elements=[text_element]
            )
            pages.append(page)

        output_path = tmp_path / "size_test.pptx"

        # Act
        result = generator.generate(pages, output_path)

        # Assert
        file_size = result.stat().st_size
        # 10ページのテキストスライド: 10KB ~ 5MB
        assert 10 * 1024 <= file_size <= 5 * 1024 * 1024

    def test_generated_file_can_be_reopened(self, tmp_path: Path) -> None:
        """生成されたファイルが再度開けることを確認."""
        # Arrange
        config = SlideConfig.create_4_3()
        generator = PowerPointGenerator(config)

        text_element = TextElement(
            element_type="text",
            position=Position(x=914400, y=914400),
            size=Size(width=6858000, height=5486400),
            z_index=0,
            content="Reopen Test",
        )

        pages = [
            PageDefinition(page_number=1, title="Test", elements=[text_element])
        ]

        output_path = tmp_path / "reopen_test.pptx"

        # Act
        result = generator.generate(pages, output_path)

        # Assert: ファイルを閉じて再度開ける
        presentation1 = Presentation(str(result))
        assert len(presentation1.slides) == 1

        # もう一度開く
        presentation2 = Presentation(str(result))
        assert len(presentation2.slides) == 1
        assert presentation2.slides[0].shapes[0].text == "Reopen Test"

    def test_generated_file_metadata(self, tmp_path: Path) -> None:
        """生成されたファイルのメタデータが正しいことを確認."""
        # Arrange
        config = SlideConfig.create_16_9()
        generator = PowerPointGenerator(config)

        pages = [PageDefinition(page_number=1, title="Metadata Test")]
        output_path = tmp_path / "metadata_test.pptx"

        # Act
        result = generator.generate(pages, output_path)

        # Assert
        presentation = Presentation(str(result))

        # スライドサイズを確認
        # 16:9は10インチ x 5.625インチ = 9144000 EMU x 5143500 EMU
        assert presentation.slide_width == 9144000
        assert presentation.slide_height == 5143500
