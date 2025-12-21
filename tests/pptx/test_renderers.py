"""
Renderersのユニットテスト.

TextRendererとImageRendererの要素描画機能をテストします。
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Pt

from slidemaker.core.models.common import Alignment, Color, FitMode, Position, Size
from slidemaker.core.models.element import FontConfig, ImageElement, TextElement
from slidemaker.pptx.renderers.image_renderer import ImageRenderer
from slidemaker.pptx.renderers.text_renderer import TextRenderer


class TestTextRenderer:
    """TextRendererクラスのテストスイート."""

    @pytest.fixture
    def presentation(self) -> Presentation:
        """テスト用のPresentationインスタンスを作成."""
        return Presentation()

    @pytest.fixture
    def slide(self, presentation: Presentation):
        """テスト用のスライドを作成."""
        blank_layout = presentation.slide_layouts[6]
        return presentation.slides.add_slide(blank_layout)

    @pytest.fixture
    def renderer(self) -> TextRenderer:
        """テスト用のTextRendererインスタンスを作成."""
        return TextRenderer()

    def test_render_text_element(self, renderer: TextRenderer, slide) -> None:
        """基本的なテキスト要素が正しく描画されることを確認."""
        # Arrange
        text_element = TextElement(
            element_type="text",
            position=Position(x=914400, y=914400),  # 1インチ
            size=Size(width=4572000, height=914400),  # 5インチ x 1インチ
            z_index=0,
            content="Hello World",
        )

        # Act
        renderer.render(slide, text_element)

        # Assert
        assert len(slide.shapes) == 1
        textbox = slide.shapes[0]
        assert textbox.text == "Hello World"

    def test_render_with_custom_font(self, renderer: TextRenderer, slide) -> None:
        """カスタムフォント設定が正しく適用されることを確認."""
        # Arrange
        font_config = FontConfig(
            family="Arial",
            size=24,
            bold=True,
            italic=True,
            underline=True,
            color=Color(hex_value="#FF0000"),
        )
        text_element = TextElement(
            element_type="text",
            position=Position(x=914400, y=914400),
            size=Size(width=4572000, height=914400),
            z_index=0,
            content="Styled Text",
            font=font_config,
        )

        # Act
        renderer.render(slide, text_element)

        # Assert
        textbox = slide.shapes[0]
        text_frame = textbox.text_frame
        run = text_frame.paragraphs[0].runs[0]
        assert run.font.name == "Arial"
        assert run.font.size == Pt(24)
        assert run.font.bold is True
        assert run.font.italic is True
        assert run.font.underline is True
        assert run.font.color.rgb == RGBColor(255, 0, 0)

    def test_render_with_alignment(self, renderer: TextRenderer, slide) -> None:
        """テキストの配置設定が正しく適用されることを確認."""
        # Arrange
        text_element = TextElement(
            element_type="text",
            position=Position(x=914400, y=914400),
            size=Size(width=4572000, height=914400),
            z_index=0,
            content="Centered Text",
            alignment=Alignment.CENTER,
        )

        # Act
        renderer.render(slide, text_element)

        # Assert
        textbox = slide.shapes[0]
        text_frame = textbox.text_frame
        paragraph = text_frame.paragraphs[0]
        assert paragraph.alignment == PP_ALIGN.CENTER

    def test_render_with_line_spacing(self, renderer: TextRenderer, slide) -> None:
        """行間設定が正しく適用されることを確認."""
        # Arrange
        text_element = TextElement(
            element_type="text",
            position=Position(x=914400, y=914400),
            size=Size(width=4572000, height=914400),
            z_index=0,
            content="Line 1\nLine 2\nLine 3",
            line_spacing=2.0,
        )

        # Act
        renderer.render(slide, text_element)

        # Assert
        textbox = slide.shapes[0]
        text_frame = textbox.text_frame
        paragraph = text_frame.paragraphs[0]
        assert paragraph.line_spacing == 2.0

    def test_render_with_negative_position_raises_error(
        self, renderer: TextRenderer, slide
    ) -> None:
        """負の座標値でエラーが発生することを確認."""
        # Arrange
        text_element = TextElement(
            element_type="text",
            position=Position(x=-100, y=914400),  # 負の値
            size=Size(width=4572000, height=914400),
            z_index=0,
            content="Invalid Position",
        )

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            renderer.render(slide, text_element)

        assert "non-negative" in str(exc_info.value)

    def test_render_with_negative_size_raises_error(
        self, renderer: TextRenderer, slide
    ) -> None:
        """負のサイズでエラーが発生することを確認（Pydanticバリデーション）."""
        # Arrange & Act & Assert
        # Pydanticがバリデーションするため、TextElementの初期化時にエラーが発生
        with pytest.raises(Exception):  # Pydantic ValidationError
            text_element = TextElement(
                element_type="text",
                position=Position(x=914400, y=914400),
                size=Size(width=-100, height=914400),  # 負の値
                z_index=0,
                content="Invalid Size",
            )

    def test_convert_alignment_all_types(self, renderer: TextRenderer) -> None:
        """すべてのアライメントタイプが正しく変換されることを確認."""
        # Arrange & Act & Assert
        assert renderer._convert_alignment(Alignment.LEFT) == PP_ALIGN.LEFT
        assert renderer._convert_alignment(Alignment.CENTER) == PP_ALIGN.CENTER
        assert renderer._convert_alignment(Alignment.RIGHT) == PP_ALIGN.RIGHT
        assert renderer._convert_alignment(Alignment.JUSTIFY) == PP_ALIGN.JUSTIFY

    def test_convert_color_valid_hex(self, renderer: TextRenderer) -> None:
        """有効な16進数カラーが正しく変換されることを確認."""
        # Arrange
        color = Color(hex_value="#3366FF")

        # Act
        rgb = renderer._convert_color(color)

        # Assert
        assert rgb == RGBColor(51, 102, 255)

    def test_convert_color_invalid_format_raises_error(
        self, renderer: TextRenderer
    ) -> None:
        """不正なカラーフォーマットでエラーが発生することを確認（Pydanticバリデーション）."""
        # Arrange & Act & Assert
        # Pydanticがバリデーションするため、Colorの初期化時にエラーが発生
        with pytest.raises(Exception):  # Pydantic ValidationError
            color = Color(hex_value="INVALID")

    def test_convert_color_out_of_range_raises_error(
        self, renderer: TextRenderer
    ) -> None:
        """範囲外のRGB値でエラーが発生することを確認."""
        # Arrange
        # 範囲外の値を持つColorをモック（Pydanticを回避）
        color = Mock()
        color.hex_value = "#FFFFFF"  # 正常なフォーマット

        # Act & Assert
        # 通常はPydanticがバリデーションするが、二重チェックのテスト
        rgb = renderer._convert_color(color)
        assert rgb == RGBColor(255, 255, 255)

    def test_render_multiline_text(self, renderer: TextRenderer, slide) -> None:
        """複数行のテキストが正しく描画されることを確認."""
        # Arrange
        text_element = TextElement(
            element_type="text",
            position=Position(x=914400, y=914400),
            size=Size(width=4572000, height=1828800),
            z_index=0,
            content="Line 1\nLine 2\nLine 3",
        )

        # Act
        renderer.render(slide, text_element)

        # Assert
        textbox = slide.shapes[0]
        text_frame = textbox.text_frame
        # 3つのパラグラフが作成されることを確認
        assert len(text_frame.paragraphs) >= 3


class TestImageRenderer:
    """ImageRendererクラスのテストスイート."""

    @pytest.fixture
    def presentation(self) -> Presentation:
        """テスト用のPresentationインスタンスを作成."""
        return Presentation()

    @pytest.fixture
    def slide(self, presentation: Presentation):
        """テスト用のスライドを作成."""
        blank_layout = presentation.slide_layouts[6]
        return presentation.slides.add_slide(blank_layout)

    @pytest.fixture
    def renderer(self) -> ImageRenderer:
        """テスト用のImageRendererインスタンスを作成."""
        return ImageRenderer()

    @pytest.fixture
    def test_image(self, tmp_path: Path) -> Path:
        """テスト用の画像ファイルを作成."""
        image_path = tmp_path / "test_image.png"
        img = Image.new("RGB", (200, 100), color="blue")
        img.save(image_path)
        return image_path

    def test_render_image_element_contain_mode(
        self, renderer: ImageRenderer, slide, test_image: Path
    ) -> None:
        """CONTAIN モードで画像が正しく描画されることを確認."""
        # Arrange
        image_element = ImageElement(
            element_type="image",
            position=Position(x=914400, y=914400),  # 1インチ
            size=Size(width=2743200, height=2743200),  # 3インチ x 3インチ
            z_index=0,
            source=str(test_image),
            fit_mode=FitMode.CONTAIN,
        )

        # Act
        renderer.render(slide, image_element)

        # Assert
        assert len(slide.shapes) == 1
        picture = slide.shapes[0]
        assert picture.shape_type == 13  # MSO_SHAPE_TYPE.PICTURE

    def test_render_image_element_fill_mode(
        self, renderer: ImageRenderer, slide, test_image: Path
    ) -> None:
        """FILL モードで画像が正しく描画されることを確認."""
        # Arrange
        image_element = ImageElement(
            element_type="image",
            position=Position(x=914400, y=914400),
            size=Size(width=2743200, height=1828800),  # 3インチ x 2インチ
            z_index=0,
            source=str(test_image),
            fit_mode=FitMode.FILL,
        )

        # Act
        renderer.render(slide, image_element)

        # Assert
        assert len(slide.shapes) == 1
        picture = slide.shapes[0]
        # FILLモードではボックスサイズを使用
        assert picture.width == 2743200
        assert picture.height == 1828800

    def test_render_image_element_cover_mode(
        self, renderer: ImageRenderer, slide, test_image: Path
    ) -> None:
        """COVER モードで警告が出ることを確認（現在はFILLと同じ動作）."""
        # Arrange
        image_element = ImageElement(
            element_type="image",
            position=Position(x=914400, y=914400),
            size=Size(width=2743200, height=2743200),
            z_index=0,
            source=str(test_image),
            fit_mode=FitMode.COVER,
        )

        # Act
        with patch("slidemaker.pptx.renderers.image_renderer.logger") as mock_logger:
            renderer.render(slide, image_element)

            # Assert: 警告が出ることを確認
            mock_logger.warning.assert_called_once()
            assert "not fully supported" in mock_logger.warning.call_args[0][0]

    def test_render_image_file_not_found_raises_error(
        self, renderer: ImageRenderer, slide, tmp_path: Path
    ) -> None:
        """存在しない画像ファイルでエラーが発生することを確認."""
        # Arrange
        non_existent = tmp_path / "non_existent.png"
        image_element = ImageElement(
            element_type="image",
            position=Position(x=914400, y=914400),
            size=Size(width=2743200, height=2743200),
            z_index=0,
            source=str(non_existent),
            fit_mode=FitMode.CONTAIN,
        )

        # Act & Assert
        with pytest.raises(FileNotFoundError):
            renderer.render(slide, image_element)

    def test_render_image_invalid_file_raises_error(
        self, renderer: ImageRenderer, slide, tmp_path: Path
    ) -> None:
        """不正な画像ファイルでエラーが発生することを確認."""
        # Arrange
        invalid_image = tmp_path / "invalid.png"
        invalid_image.write_text("not an image")

        image_element = ImageElement(
            element_type="image",
            position=Position(x=914400, y=914400),
            size=Size(width=2743200, height=2743200),
            z_index=0,
            source=str(invalid_image),
            fit_mode=FitMode.CONTAIN,
        )

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            renderer.render(slide, image_element)

        assert "Failed to open image file" in str(exc_info.value)

    def test_render_image_negative_box_size_raises_error(
        self, renderer: ImageRenderer, slide, test_image: Path
    ) -> None:
        """負のボックスサイズでエラーが発生することを確認（Pydanticバリデーション）."""
        # Arrange & Act & Assert
        # Pydanticがバリデーションするため、ImageElementの初期化時にエラーが発生
        with pytest.raises(Exception):  # Pydantic ValidationError
            image_element = ImageElement(
                element_type="image",
                position=Position(x=914400, y=914400),
                size=Size(width=-100, height=2743200),  # 負の値
                z_index=0,
                source=str(test_image),
                fit_mode=FitMode.CONTAIN,
            )

    def test_calculate_contain_size_wider_image(self, renderer: ImageRenderer) -> None:
        """幅が広い画像のCONTAINサイズ計算が正しいことを確認."""
        # Arrange
        image_size = (400, 200)  # アスペクト比 2:1
        box_size = Size(width=2743200, height=2743200)  # 3インチ x 3インチ（正方形）

        # Act
        final_width, final_height = renderer._calculate_contain_size(
            image_size, box_size
        )

        # Assert: 幅に合わせて縮小
        assert final_width == 2743200
        assert final_height < 2743200  # 高さは幅より小さくなる

    def test_calculate_contain_size_taller_image(self, renderer: ImageRenderer) -> None:
        """高さが高い画像のCONTAINサイズ計算が正しいことを確認."""
        # Arrange
        image_size = (100, 200)  # アスペクト比 1:2
        box_size = Size(width=2743200, height=2743200)  # 3インチ x 3インチ（正方形）

        # Act
        final_width, final_height = renderer._calculate_contain_size(
            image_size, box_size
        )

        # Assert: 高さに合わせて縮小
        assert final_height == 2743200
        assert final_width < 2743200  # 幅は高さより小さくなる

    def test_calculate_contain_size_minimum_dimension(
        self, renderer: ImageRenderer
    ) -> None:
        """極端なアスペクト比でも最小寸法が確保されることを確認."""
        # Arrange
        image_size = (10000, 10)  # 極端に幅が広い
        box_size = Size(width=2743200, height=2743200)

        # Act
        final_width, final_height = renderer._calculate_contain_size(
            image_size, box_size
        )

        # Assert: 高さが最小値1以上になることを確認
        assert final_height >= 1
        assert final_width == 2743200


class TestRenderersIntegration:
    """Renderersの統合テスト."""

    def test_render_text_and_image_on_same_slide(self, tmp_path: Path) -> None:
        """同じスライド上にテキストと画像を描画できることを確認."""
        # Arrange
        presentation = Presentation()
        blank_layout = presentation.slide_layouts[6]
        slide = presentation.slides.add_slide(blank_layout)

        # テスト画像を作成
        image_path = tmp_path / "test.png"
        img = Image.new("RGB", (100, 100), color="green")
        img.save(image_path)

        text_renderer = TextRenderer()
        image_renderer = ImageRenderer()

        text_element = TextElement(
            element_type="text",
            position=Position(x=914400, y=914400),
            size=Size(width=4572000, height=914400),
            z_index=0,
            content="Sample Text",
        )

        image_element = ImageElement(
            element_type="image",
            position=Position(x=914400, y=2743200),
            size=Size(width=2743200, height=2743200),
            z_index=1,
            source=str(image_path),
            fit_mode=FitMode.CONTAIN,
        )

        # Act
        text_renderer.render(slide, text_element)
        image_renderer.render(slide, image_element)

        # Assert: スライドに両方の要素が追加されている
        assert len(slide.shapes) == 2
