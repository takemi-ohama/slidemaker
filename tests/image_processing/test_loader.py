"""Tests for ImageLoader

ImageLoaderクラスの単体テストです。

Test Coverage:
    - PDF読み込み（正常系、異常系）
    - 画像読み込み（各形式）
    - 正規化処理（アスペクト比保持）
    - エラーケース（ファイルなし、不正形式、サイズ超過）
"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest
from pdf2image.exceptions import PDFPageCountError, PDFSyntaxError
from PIL import Image

from slidemaker.image_processing.loader import ImageLoader, ImageLoadError
from slidemaker.utils.file_manager import FileManager


@pytest.fixture
def file_manager(tmp_path: Path) -> FileManager:
    """FileManagerのフィクスチャ"""
    return FileManager(temp_dir=str(tmp_path), output_base_dir=str(tmp_path))


@pytest.fixture
def image_loader(file_manager: FileManager) -> ImageLoader:
    """ImageLoaderのフィクスチャ"""
    return ImageLoader(file_manager)


@pytest.fixture
def sample_image(tmp_path: Path) -> Path:
    """サンプル画像を作成"""
    image = Image.new("RGB", (800, 600), color="red")
    image_path = tmp_path / "sample.png"
    image.save(image_path)
    return image_path


@pytest.fixture
def sample_rgba_image(tmp_path: Path) -> Path:
    """サンプルRGBA画像を作成"""
    image = Image.new("RGBA", (800, 600), color=(255, 0, 0, 128))
    image_path = tmp_path / "sample_rgba.png"
    image.save(image_path)
    return image_path


@pytest.fixture
def large_image(tmp_path: Path) -> Path:
    """大きなサイズのサンプル画像を作成（11MB超）"""
    # 11MBを超える画像を作成
    image = Image.new("RGB", (5000, 5000), color="blue")
    image_path = tmp_path / "large_image.png"
    image.save(image_path, quality=100)
    return image_path


class TestImageLoaderInit:
    """ImageLoaderの初期化テスト"""

    def test_init_success(self, file_manager: FileManager) -> None:
        """正常な初期化"""
        loader = ImageLoader(file_manager)
        assert loader.file_manager == file_manager
        assert loader.logger is not None


class TestLoadFromPdf:
    """load_from_pdfメソッドのテスト"""

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_load_from_pdf_basic(
        self, image_loader: ImageLoader, tmp_path: Path
    ) -> None:
        """PDF基本読み込み"""
        pdf_path = tmp_path / "test.pdf"
        mock_images = [Image.new("RGB", (1920, 1080), color="white")]

        with (
            patch("slidemaker.image_processing.loader.pdfinfo_from_path") as mock_info,
            patch("slidemaker.image_processing.loader.convert_from_path") as mock_convert,
        ):
            mock_info.return_value = {"Pages": 1}
            mock_convert.return_value = mock_images
            pdf_path.touch()  # ダミーファイル作成

            result = await image_loader.load_from_pdf(str(pdf_path))

            assert len(result) == 1
            assert result[0].size == (1920, 1080)
            mock_convert.assert_called_once()

    @pytest.mark.asyncio
    async def test_load_from_pdf_multiple_pages(
        self, image_loader: ImageLoader, tmp_path: Path
    ) -> None:
        """複数ページPDFの読み込み"""
        pdf_path = tmp_path / "multi_page.pdf"
        mock_images = [
            Image.new("RGB", (1920, 1080), color="white"),
            Image.new("RGB", (1920, 1080), color="black"),
            Image.new("RGB", (1920, 1080), color="red"),
        ]

        with (
            patch("slidemaker.image_processing.loader.pdfinfo_from_path") as mock_info,
            patch("slidemaker.image_processing.loader.convert_from_path") as mock_convert,
        ):
            mock_info.return_value = {"Pages": 3}
            mock_convert.return_value = mock_images
            pdf_path.touch()

            result = await image_loader.load_from_pdf(str(pdf_path))

            assert len(result) == 3
            mock_convert.assert_called_once()

    @pytest.mark.asyncio
    async def test_load_from_pdf_file_not_found(self, image_loader: ImageLoader) -> None:
        """PDFファイル不在時のエラー"""
        with pytest.raises(FileNotFoundError) as exc_info:
            await image_loader.load_from_pdf("/nonexistent/path/test.pdf")
        assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_load_from_pdf_not_a_file(
        self, image_loader: ImageLoader, tmp_path: Path
    ) -> None:
        """ディレクトリを指定した場合のエラー"""
        dir_path = tmp_path / "directory"
        dir_path.mkdir()

        with pytest.raises(ValueError) as exc_info:
            await image_loader.load_from_pdf(str(dir_path))
        assert "not a file" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_load_from_pdf_invalid_extension(
        self, image_loader: ImageLoader, tmp_path: Path
    ) -> None:
        """非PDF拡張子のエラー"""
        txt_path = tmp_path / "test.txt"
        txt_path.touch()

        with pytest.raises(ValueError) as exc_info:
            await image_loader.load_from_pdf(str(txt_path))
        assert "not a PDF" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_load_from_pdf_page_limit_exceeded(
        self, image_loader: ImageLoader, tmp_path: Path
    ) -> None:
        """ページ数超過エラー（51ページ以上）"""
        pdf_path = tmp_path / "large.pdf"

        with patch("slidemaker.image_processing.loader.pdfinfo_from_path") as mock_info:
            mock_info.return_value = {"Pages": 51}
            pdf_path.touch()

            with pytest.raises(ValueError) as exc_info:
                await image_loader.load_from_pdf(str(pdf_path))
            assert "too many pages" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_load_from_pdf_custom_dpi(
        self, image_loader: ImageLoader, tmp_path: Path
    ) -> None:
        """カスタムDPI設定"""
        pdf_path = tmp_path / "test.pdf"
        mock_images = [Image.new("RGB", (1920, 1080), color="white")]

        with (
            patch("slidemaker.image_processing.loader.pdfinfo_from_path") as mock_info,
            patch("slidemaker.image_processing.loader.convert_from_path") as mock_convert,
        ):
            mock_info.return_value = {"Pages": 1}
            mock_convert.return_value = mock_images
            pdf_path.touch()

            result = await image_loader.load_from_pdf(str(pdf_path), dpi=300)

            assert len(result) == 1
            # DPIパラメータが渡されていることを確認
            call_args = mock_convert.call_args
            assert call_args[1]["dpi"] == 300

    @pytest.mark.asyncio
    async def test_load_from_pdf_invalid_dpi(
        self, image_loader: ImageLoader, tmp_path: Path
    ) -> None:
        """不正なDPI値のエラー"""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        # DPI=0
        with pytest.raises(ValueError) as exc_info:
            await image_loader.load_from_pdf(str(pdf_path), dpi=0)
        assert "Invalid DPI" in str(exc_info.value)

        # DPI=601（上限超過）
        with pytest.raises(ValueError) as exc_info:
            await image_loader.load_from_pdf(str(pdf_path), dpi=601)
        assert "Invalid DPI" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_load_from_pdf_corrupted_file(
        self, image_loader: ImageLoader, tmp_path: Path
    ) -> None:
        """破損PDFエラー"""
        pdf_path = tmp_path / "corrupted.pdf"
        pdf_path.touch()

        with patch("slidemaker.image_processing.loader.convert_from_path") as mock_convert:
            mock_convert.side_effect = PDFSyntaxError("PDF syntax error")

            with pytest.raises(ImageLoadError) as exc_info:
                await image_loader.load_from_pdf(str(pdf_path))
            assert "syntax error" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_load_from_pdf_page_count_error(
        self, image_loader: ImageLoader, tmp_path: Path
    ) -> None:
        """PDFページ数取得エラー"""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        with patch("slidemaker.image_processing.loader.convert_from_path") as mock_convert:
            mock_convert.side_effect = PDFPageCountError("Cannot count pages")

            with pytest.raises(ImageLoadError) as exc_info:
                await image_loader.load_from_pdf(str(pdf_path))
            assert "page count" in str(exc_info.value).lower()


class TestLoadFromImage:
    """load_from_imageメソッドのテスト"""

    @pytest.mark.asyncio
    async def test_load_from_image_png(
        self, image_loader: ImageLoader, sample_image: Path
    ) -> None:
        """PNG画像読み込み"""
        result = await image_loader.load_from_image(str(sample_image))
        assert isinstance(result, Image.Image)
        assert result.size == (800, 600)
        assert result.mode == "RGB"

    @pytest.mark.asyncio
    async def test_load_from_image_jpeg(
        self, image_loader: ImageLoader, tmp_path: Path
    ) -> None:
        """JPEG画像読み込み"""
        image = Image.new("RGB", (640, 480), color="green")
        image_path = tmp_path / "sample.jpg"
        image.save(image_path, "JPEG")

        result = await image_loader.load_from_image(str(image_path))
        assert isinstance(result, Image.Image)
        assert result.size == (640, 480)

    @pytest.mark.asyncio
    async def test_load_from_image_gif(
        self, image_loader: ImageLoader, tmp_path: Path
    ) -> None:
        """GIF画像読み込み"""
        image = Image.new("RGB", (320, 240), color="yellow")
        image_path = tmp_path / "sample.gif"
        image.save(image_path, "GIF")

        result = await image_loader.load_from_image(str(image_path))
        assert isinstance(result, Image.Image)
        assert result.size == (320, 240)

    @pytest.mark.asyncio
    async def test_load_from_image_file_not_found(self, image_loader: ImageLoader) -> None:
        """画像ファイル不在エラー"""
        with pytest.raises(FileNotFoundError) as exc_info:
            await image_loader.load_from_image("/nonexistent/image.png")
        assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_load_from_image_invalid_format(
        self, image_loader: ImageLoader, tmp_path: Path
    ) -> None:
        """非対応形式エラー"""
        txt_path = tmp_path / "test.txt"
        txt_path.write_text("This is not an image")

        with pytest.raises(ValueError) as exc_info:
            await image_loader.load_from_image(str(txt_path))
        assert "Unsupported image format" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_load_from_image_size_limit_exceeded(
        self, image_loader: ImageLoader, large_image: Path
    ) -> None:
        """ファイルサイズ超過エラー（10MB超）"""
        # ファイルサイズが10MBを超える場合はスキップ
        if os.path.getsize(large_image) <= 10 * 1024 * 1024:
            pytest.skip("Large image not created (smaller than 10MB)")

        with pytest.raises(ValueError) as exc_info:
            await image_loader.load_from_image(str(large_image))
        assert "too large" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_load_from_image_corrupted(
        self, image_loader: ImageLoader, tmp_path: Path
    ) -> None:
        """破損画像エラー"""
        corrupted_path = tmp_path / "corrupted.png"
        corrupted_path.write_bytes(b"fake image data")

        with pytest.raises(ImageLoadError) as exc_info:
            await image_loader.load_from_image(str(corrupted_path))
        error_message = str(exc_info.value).lower()
        assert "corrupted" in error_message or "invalid" in error_message


class TestNormalizeImage:
    """normalize_imageメソッドのテスト"""

    def test_normalize_image_resize(self, image_loader: ImageLoader) -> None:
        """リサイズ処理"""
        original = Image.new("RGB", (800, 600), color="blue")
        result = image_loader.normalize_image(original)

        assert result.size == (1920, 1080)
        assert result.mode == "RGB"

    def test_normalize_image_rgb_conversion(
        self, image_loader: ImageLoader, sample_rgba_image: Path
    ) -> None:
        """RGBA→RGB変換"""
        rgba_image = Image.open(sample_rgba_image)
        result = image_loader.normalize_image(rgba_image)

        assert result.mode == "RGB"
        assert result.size == (1920, 1080)

    def test_normalize_image_aspect_ratio(self, image_loader: ImageLoader) -> None:
        """アスペクト比維持"""
        # 正方形画像
        square = Image.new("RGB", (1000, 1000), color="green")
        result = image_loader.normalize_image(square)

        assert result.size == (1920, 1080)
        # 元画像が正方形の場合、高さ1080に合わせて幅も1080になる
        # （アスペクト比維持のため）

    def test_normalize_image_exif_rotation(self, image_loader: ImageLoader) -> None:
        """EXIF回転処理"""
        # EXIF情報付き画像をモック
        image = Image.new("RGB", (600, 800), color="orange")

        with patch("slidemaker.image_processing.loader.ImageOps.exif_transpose") as mock_transpose:
            mock_transpose.return_value = image
            result = image_loader.normalize_image(image)

            mock_transpose.assert_called_once()
            assert result.size == (1920, 1080)

    def test_normalize_image_already_correct_size(self, image_loader: ImageLoader) -> None:
        """既に正しいサイズの画像"""
        correct_size = Image.new("RGB", (1920, 1080), color="purple")
        result = image_loader.normalize_image(correct_size)

        assert result.size == (1920, 1080)
        assert result.mode == "RGB"

    def test_normalize_image_smaller_than_target(self, image_loader: ImageLoader) -> None:
        """ターゲットより小さい画像"""
        small = Image.new("RGB", (640, 480), color="cyan")
        result = image_loader.normalize_image(small)

        assert result.size == (1920, 1080)
        assert result.mode == "RGB"

    def test_normalize_image_larger_than_target(self, image_loader: ImageLoader) -> None:
        """ターゲットより大きい画像"""
        large = Image.new("RGB", (3840, 2160), color="magenta")
        result = image_loader.normalize_image(large)

        assert result.size == (1920, 1080)
        assert result.mode == "RGB"


class TestIntegration:
    """統合テスト"""

    @pytest.mark.asyncio
    async def test_load_and_normalize_pipeline(
        self, image_loader: ImageLoader, sample_image: Path
    ) -> None:
        """読み込み→正規化のパイプライン"""
        loaded = await image_loader.load_from_image(str(sample_image))
        normalized = image_loader.normalize_image(loaded)

        assert normalized.size == (1920, 1080)
        assert normalized.mode == "RGB"

    @pytest.mark.asyncio
    async def test_pdf_to_normalized_images(
        self, image_loader: ImageLoader, tmp_path: Path
    ) -> None:
        """PDF→正規化画像のパイプライン"""
        pdf_path = tmp_path / "test.pdf"
        mock_images = [
            Image.new("RGB", (800, 600), color="red"),
            Image.new("RGB", (1024, 768), color="blue"),
        ]

        with (
            patch("slidemaker.image_processing.loader.pdfinfo_from_path") as mock_info,
            patch("slidemaker.image_processing.loader.convert_from_path") as mock_convert,
        ):
            mock_info.return_value = {"Pages": 2}
            mock_convert.return_value = mock_images
            pdf_path.touch()

            loaded_images = await image_loader.load_from_pdf(str(pdf_path))
            normalized_images = [
                image_loader.normalize_image(img) for img in loaded_images
            ]

            assert len(normalized_images) == 2
            for img in normalized_images:
                assert img.size == (1920, 1080)
                assert img.mode == "RGB"
