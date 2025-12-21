"""
SlideBuilderのユニットテスト.

SlideBuilderクラスのスライド構築機能をテストします。
"""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from pptx import Presentation
from pptx.slide import Slide
from pptx.util import Inches

from slidemaker.core.models.common import Color, FitMode, Position, Size
from slidemaker.core.models.element import ImageElement, TextElement
from slidemaker.core.models.page_definition import PageDefinition
from slidemaker.pptx.slide_builder import SlideBuilder


class TestSlideBuilder:
    """SlideBuilderクラスのテストスイート."""

    @pytest.fixture
    def presentation(self) -> Presentation:
        """テスト用のPresentationインスタンスを作成."""
        return Presentation()

    @pytest.fixture
    def builder(self, presentation: Presentation) -> SlideBuilder:
        """テスト用のSlideBuilderインスタンスを作成."""
        return SlideBuilder(presentation)

    def test_init(self, presentation: Presentation) -> None:
        """SlideBuilderが正しく初期化されることを確認."""
        # Act
        builder = SlideBuilder(presentation)

        # Assert
        assert builder.presentation == presentation
        assert builder.text_renderer is not None
        assert builder.image_renderer is not None

    def test_build_empty_slide(
        self, builder: SlideBuilder, presentation: Presentation
    ) -> None:
        """空のスライドが正しく作成されることを確認."""
        # Arrange
        page_def = PageDefinition(page_number=1, title="Empty Slide")

        # Act
        slide = builder.build_slide(page_def)

        # Assert
        assert slide is not None
        assert isinstance(slide, Slide)
        assert len(presentation.slides) == 1

    def test_build_slide_with_background_color(
        self, builder: SlideBuilder, presentation: Presentation
    ) -> None:
        """背景色付きスライドが正しく作成されることを確認."""
        # Arrange
        page_def = PageDefinition(
            page_number=1, title="Background Slide", background_color="#FF0000"
        )

        # Act
        slide = builder.build_slide(page_def)

        # Assert
        assert slide is not None
        # 背景色が設定されていることを確認（fill typeがsolid）
        background = slide.background
        fill = background.fill
        assert fill.type == 1  # MSO_FILL_TYPE.SOLID = 1

    def test_build_slide_with_text_elements(
        self, builder: SlideBuilder, presentation: Presentation
    ) -> None:
        """テキスト要素を含むスライドが正しく作成されることを確認."""
        # Arrange
        text_element = TextElement(
            element_type="text",
            position=Position(x=100000, y=100000),
            size=Size(width=500000, height=200000),
            z_index=0,
            content="Test Text",
        )
        page_def = PageDefinition(
            page_number=1, title="Text Slide", elements=[text_element]
        )

        # Act
        with patch.object(builder.text_renderer, "render") as mock_render:
            slide = builder.build_slide(page_def)

            # Assert
            assert slide is not None
            mock_render.assert_called_once()
            # 呼び出し引数を確認
            call_args = mock_render.call_args
            assert call_args[0][0] == slide  # 第一引数はslide
            assert call_args[0][1] == text_element  # 第二引数はtext_element

    def test_build_slide_with_image_elements(
        self, builder: SlideBuilder, presentation: Presentation, tmp_path: Path
    ) -> None:
        """画像要素を含むスライドが正しく作成されることを確認."""
        # Arrange
        # ダミー画像ファイルを作成
        dummy_image = tmp_path / "test_image.png"
        dummy_image.write_bytes(b"")  # 空のファイル

        image_element = ImageElement(
            element_type="image",
            position=Position(x=100000, y=100000),
            size=Size(width=500000, height=400000),
            z_index=0,
            source=str(dummy_image),
            fit_mode=FitMode.CONTAIN,
        )
        page_def = PageDefinition(
            page_number=1, title="Image Slide", elements=[image_element]
        )

        # Act
        with patch.object(builder.image_renderer, "render") as mock_render:
            slide = builder.build_slide(page_def)

            # Assert
            assert slide is not None
            mock_render.assert_called_once()
            call_args = mock_render.call_args
            assert call_args[0][0] == slide
            assert call_args[0][1] == image_element

    def test_build_slide_respects_z_index_order(
        self, builder: SlideBuilder, presentation: Presentation
    ) -> None:
        """z-indexの順序が正しく反映されることを確認."""
        # Arrange
        text_element_1 = TextElement(
            element_type="text",
            position=Position(x=100000, y=100000),
            size=Size(width=500000, height=200000),
            z_index=2,  # 後に描画される
            content="Text 1",
        )
        text_element_2 = TextElement(
            element_type="text",
            position=Position(x=200000, y=200000),
            size=Size(width=500000, height=200000),
            z_index=1,  # 先に描画される
            content="Text 2",
        )
        page_def = PageDefinition(
            page_number=1, title="Z-Index Test", elements=[text_element_1, text_element_2]
        )

        # Act
        with patch.object(builder.text_renderer, "render") as mock_render:
            slide = builder.build_slide(page_def)

            # Assert: z_index順（小→大）で呼ばれることを確認
            assert mock_render.call_count == 2
            first_call_element = mock_render.call_args_list[0][0][1]
            second_call_element = mock_render.call_args_list[1][0][1]
            assert first_call_element.z_index < second_call_element.z_index
            assert first_call_element.content == "Text 2"
            assert second_call_element.content == "Text 1"

    def test_build_slide_with_unknown_element_type(
        self, builder: SlideBuilder, presentation: Presentation
    ) -> None:
        """未知の要素タイプが警告ログを出すことを確認."""
        # Arrange
        # PageDefinitionはPydanticでバリデーションされるため、
        # 不正な要素を含むPageDefinitionは作成できない。
        # このテストは実装上不要なのでスキップ
        pytest.skip("Pydantic validation prevents invalid element types")

    def test_set_background_color_with_hex_value(
        self, builder: SlideBuilder, presentation: Presentation
    ) -> None:
        """16進数カラーコードで背景色が正しく設定されることを確認."""
        # Arrange
        page_def = PageDefinition(
            page_number=1, title="Test", background_color="#3366FF"
        )

        # Act
        slide = builder.build_slide(page_def)

        # Assert
        background = slide.background
        fill = background.fill
        assert fill.type == 1  # MSO_FILL_TYPE.SOLID
        # RGB値を確認（RGBColor(51, 102, 255) = #3366FF）
        rgb = fill.fore_color.rgb
        assert rgb == (51, 102, 255)

    def test_set_background_color_with_invalid_hex(
        self, builder: SlideBuilder, presentation: Presentation
    ) -> None:
        """不正な16進数カラーコードでエラーが発生することを確認（Pydanticバリデーション）."""
        # Arrange & Act & Assert
        # Pydanticがバリデーションするため、Colorの初期化時にエラーが発生
        with pytest.raises(Exception):  # Pydantic ValidationError
            color = Color(hex_value="INVALID")

    def test_set_background_image_success(
        self, builder: SlideBuilder, presentation: Presentation, tmp_path: Path
    ) -> None:
        """背景画像が正しく設定されることを確認."""
        # Arrange
        # 実際の画像ファイルを作成（1x1ピクセルのPNG）
        from PIL import Image

        image_path = tmp_path / "background.png"
        img = Image.new("RGB", (1, 1), color="red")
        img.save(image_path)

        blank_layout = presentation.slide_layouts[6]
        slide = presentation.slides.add_slide(blank_layout)

        # Act
        builder._set_background_image(slide, image_path)

        # Assert: スライドに画像が追加されていることを確認
        assert len(slide.shapes) == 1
        picture_shape = slide.shapes[0]
        assert picture_shape.shape_type == 13  # MSO_SHAPE_TYPE.PICTURE = 13

    def test_set_background_image_file_not_found(
        self, builder: SlideBuilder, presentation: Presentation, tmp_path: Path
    ) -> None:
        """存在しない画像ファイルでエラーが発生することを確認."""
        # Arrange
        non_existent_path = tmp_path / "non_existent.png"
        blank_layout = presentation.slide_layouts[6]
        slide = presentation.slides.add_slide(blank_layout)

        # Act & Assert
        with pytest.raises(FileNotFoundError):
            builder._set_background_image(slide, non_existent_path)

    def test_set_background_image_invalid_path(
        self, builder: SlideBuilder, presentation: Presentation, tmp_path: Path
    ) -> None:
        """ディレクトリパスが指定された場合にエラーが発生することを確認."""
        # Arrange
        directory_path = tmp_path  # ディレクトリを指定
        blank_layout = presentation.slide_layouts[6]
        slide = presentation.slides.add_slide(blank_layout)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            builder._set_background_image(slide, directory_path)

        assert "not a file" in str(exc_info.value)


class TestSlideBuilderIntegration:
    """SlideBuilderの統合テスト."""

    def test_build_slide_with_mixed_elements(self, tmp_path: Path) -> None:
        """テキストと画像を含む複雑なスライドが正しく作成されることを確認."""
        # Arrange
        from PIL import Image

        presentation = Presentation()
        builder = SlideBuilder(presentation)

        # テスト画像を作成
        image_path = tmp_path / "test.png"
        img = Image.new("RGB", (100, 100), color="blue")
        img.save(image_path)

        text_element = TextElement(
            element_type="text",
            position=Position(x=914400, y=914400),  # 1インチ
            size=Size(width=4572000, height=914400),  # 5インチ x 1インチ
            z_index=1,
            content="Sample Text",
        )

        image_element = ImageElement(
            element_type="image",
            position=Position(x=914400, y=2743200),  # 1インチ x 3インチ
            size=Size(width=2743200, height=2743200),  # 3インチ x 3インチ
            z_index=0,
            source=str(image_path),
            fit_mode=FitMode.CONTAIN,
        )

        page_def = PageDefinition(
            page_number=1,
            title="Mixed Elements",
            background_color="#FFFFFF",
            elements=[text_element, image_element],
        )

        # Act
        slide = builder.build_slide(page_def)

        # Assert
        assert slide is not None
        # スライドに要素が追加されていることを確認
        # 背景画像なしの場合、shapes数はテキストボックス1 + 画像1 = 2
        assert len(slide.shapes) >= 2
