"""
PowerPointGeneratorのユニットテスト.

PowerPointGeneratorクラスの初期化、スライド生成、ファイル保存等の機能をテストします。
"""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from pptx import Presentation
from pptx.util import Inches

from slidemaker.core.models.page_definition import PageDefinition
from slidemaker.core.models.slide_config import SlideConfig, SlideSize
from slidemaker.pptx.generator import PowerPointGenerator, PowerPointGeneratorError


class TestPowerPointGenerator:
    """PowerPointGeneratorクラスのテストスイート."""

    def test_init_with_4_3_size(self) -> None:
        """4:3サイズでの初期化が成功することを確認."""
        # Arrange
        config = SlideConfig.create_4_3()

        # Act
        generator = PowerPointGenerator(config)

        # Assert
        assert generator.config == config
        assert generator.presentation is not None
        # 4:3サイズは10インチ x 7.5インチ
        assert generator.presentation.slide_width == Inches(10)
        assert generator.presentation.slide_height == Inches(7.5)

    def test_init_with_16_9_size(self) -> None:
        """16:9サイズでの初期化が成功することを確認."""
        # Arrange
        config = SlideConfig.create_16_9()

        # Act
        generator = PowerPointGenerator(config)

        # Assert
        assert generator.config == config
        assert generator.presentation is not None
        # 16:9サイズは10インチ x 5.625インチ
        assert generator.presentation.slide_width == Inches(10)
        assert generator.presentation.slide_height == Inches(5.625)

    def test_init_with_custom_size(self) -> None:
        """カスタムサイズでの初期化が成功することを確認."""
        # Arrange
        # 標準サイズを使用（16:9）
        config = SlideConfig.create_16_9()

        # Act
        generator = PowerPointGenerator(config)

        # Assert
        assert generator.config == config
        assert generator.presentation is not None
        # 16:9の場合は標準サイズが適用される
        assert generator.presentation.slide_width == Inches(10)
        assert generator.presentation.slide_height == Inches(5.625)

    @patch("slidemaker.pptx.generator.Presentation")
    def test_init_failure(self, mock_presentation: Mock) -> None:
        """Presentation初期化失敗時にエラーが発生することを確認."""
        # Arrange
        config = SlideConfig.create_16_9()
        mock_presentation.side_effect = Exception("Presentation init failed")

        # Act & Assert
        with pytest.raises(PowerPointGeneratorError) as exc_info:
            PowerPointGenerator(config)

        assert "Presentation initialization failed" in str(exc_info.value)

    def test_generate_single_page(self, tmp_path: Path) -> None:
        """単一ページのスライド生成が成功することを確認."""
        # Arrange
        config = SlideConfig.create_16_9()
        generator = PowerPointGenerator(config)
        pages = [
            PageDefinition(
                page_number=1,
                title="Test Slide",
            )
        ]
        output_path = tmp_path / "single_page.pptx"

        # Act
        result = generator.generate(pages, output_path)

        # Assert
        assert result.exists()
        assert result.suffix == ".pptx"
        assert result.is_absolute()
        assert len(generator.presentation.slides) == 1

    def test_generate_multiple_pages(self, tmp_path: Path) -> None:
        """複数ページのスライド生成が成功することを確認."""
        # Arrange
        config = SlideConfig.create_16_9()
        generator = PowerPointGenerator(config)
        pages = [
            PageDefinition(page_number=1, title="Slide 1"),
            PageDefinition(page_number=2, title="Slide 2"),
            PageDefinition(page_number=3, title="Slide 3"),
        ]
        output_path = tmp_path / "multi_page.pptx"

        # Act
        result = generator.generate(pages, output_path)

        # Assert
        assert result.exists()
        assert len(generator.presentation.slides) == 3

    def test_generate_empty_pages_list(self, tmp_path: Path) -> None:
        """空のページリストでエラーが発生することを確認."""
        # Arrange
        config = SlideConfig.create_16_9()
        generator = PowerPointGenerator(config)
        pages: list[PageDefinition] = []
        output_path = tmp_path / "empty.pptx"

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            generator.generate(pages, output_path)

        assert "Pages list cannot be empty" in str(exc_info.value)

    def test_generate_invalid_output_extension(self, tmp_path: Path) -> None:
        """不正な拡張子でエラーが発生することを確認."""
        # Arrange
        config = SlideConfig.create_16_9()
        generator = PowerPointGenerator(config)
        pages = [PageDefinition(page_number=1, title="Test")]
        output_path = tmp_path / "output.txt"  # .pptxではない

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            generator.generate(pages, output_path)

        assert "Output path must have .pptx extension" in str(exc_info.value)

    def test_generate_creates_parent_directory(self, tmp_path: Path) -> None:
        """親ディレクトリが自動作成されることを確認."""
        # Arrange
        config = SlideConfig.create_16_9()
        generator = PowerPointGenerator(config)
        pages = [PageDefinition(page_number=1, title="Test")]
        # 存在しないディレクトリパス
        output_path = tmp_path / "subdir1" / "subdir2" / "output.pptx"

        # Act
        result = generator.generate(pages, output_path)

        # Assert
        assert result.exists()
        assert result.parent.exists()
        assert result.parent == output_path.parent

    @patch("slidemaker.pptx.generator.SlideBuilder")
    def test_generate_slide_builder_error(
        self, mock_slide_builder: Mock, tmp_path: Path
    ) -> None:
        """SlideBuilder実行時のエラーが適切にハンドリングされることを確認."""
        # Arrange
        config = SlideConfig.create_16_9()
        generator = PowerPointGenerator(config)
        pages = [PageDefinition(page_number=1, title="Test")]
        output_path = tmp_path / "output.pptx"

        # SlideBuilder.build_slideでエラーを発生させる
        mock_builder_instance = MagicMock()
        mock_builder_instance.build_slide.side_effect = Exception("Build failed")
        mock_slide_builder.return_value = mock_builder_instance

        # Act & Assert
        with pytest.raises(PowerPointGeneratorError) as exc_info:
            generator.generate(pages, output_path)

        assert "Failed to generate PowerPoint" in str(exc_info.value)

    @patch("pathlib.Path.mkdir")
    def test_generate_permission_error(self, mock_mkdir: Mock, tmp_path: Path) -> None:
        """ファイル保存時のパーミッションエラーが適切にハンドリングされることを確認."""
        # Arrange
        config = SlideConfig.create_16_9()
        generator = PowerPointGenerator(config)
        pages = [PageDefinition(page_number=1, title="Test")]
        output_path = tmp_path / "output.pptx"

        # mkdir()でPermissionErrorを発生させる
        mock_mkdir.side_effect = PermissionError("Permission denied")

        # Act & Assert
        with pytest.raises(PowerPointGeneratorError) as exc_info:
            generator.generate(pages, output_path)

        assert "Permission denied" in str(exc_info.value)

    def test_save_presentation_returns_absolute_path(self, tmp_path: Path) -> None:
        """保存されたファイルパスが絶対パスであることを確認."""
        # Arrange
        config = SlideConfig.create_16_9()
        generator = PowerPointGenerator(config)
        pages = [PageDefinition(page_number=1, title="Test")]
        # 相対パスを指定
        output_path = Path("relative_output.pptx")

        # tmp_pathをカレントディレクトリとして使用
        with patch("pathlib.Path.cwd", return_value=tmp_path):
            # Act
            result = generator.generate(pages, output_path)

            # Assert
            assert result.is_absolute()


class TestPowerPointGeneratorIntegration:
    """PowerPointGeneratorの統合テスト（実際のファイル生成）."""

    def test_generate_and_load_presentation(self, tmp_path: Path) -> None:
        """生成されたPowerPointファイルが正常に読み込めることを確認."""
        # Arrange
        config = SlideConfig.create_16_9()
        generator = PowerPointGenerator(config)
        pages = [
            PageDefinition(page_number=1, title="Title Slide"),
            PageDefinition(page_number=2, title="Content Slide"),
        ]
        output_path = tmp_path / "test_presentation.pptx"

        # Act
        result = generator.generate(pages, output_path)

        # Assert: ファイルが存在し、python-pptxで読み込める
        assert result.exists()
        loaded_presentation = Presentation(str(result))
        assert len(loaded_presentation.slides) == 2

    def test_generate_file_size_is_reasonable(self, tmp_path: Path) -> None:
        """生成されたファイルサイズが妥当な範囲であることを確認."""
        # Arrange
        config = SlideConfig.create_16_9()
        generator = PowerPointGenerator(config)
        pages = [PageDefinition(page_number=1, title="Test")]
        output_path = tmp_path / "size_test.pptx"

        # Act
        result = generator.generate(pages, output_path)

        # Assert: ファイルサイズが1KB以上、1MB以下（空のスライドデッキ想定）
        file_size = result.stat().st_size
        assert 1024 <= file_size <= 1024 * 1024
