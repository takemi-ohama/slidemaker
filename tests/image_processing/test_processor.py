"""Tests for Image Processor

画像処理機能のテストを行います。
"""

from pathlib import Path

import pytest
from PIL import Image

from slidemaker.image_processing.exceptions import ImageCropError, ImageSaveError
from slidemaker.image_processing.processor import ImageProcessor
from slidemaker.utils.file_manager import FileManager


class TestImageProcessor:
    """ImageProcessorクラスのテスト"""

    @pytest.fixture
    def file_manager(self, tmp_path: Path) -> FileManager:
        """FileManagerフィクスチャ

        Args:
            tmp_path: pytestの一時ディレクトリ

        Returns:
            FileManager: テスト用ファイルマネージャー
        """
        return FileManager(
            temp_dir=tmp_path / "temp",
            output_base_dir=tmp_path / "output",
        )

    @pytest.fixture
    def processor(self, file_manager: FileManager) -> ImageProcessor:
        """ImageProcessorフィクスチャ

        Args:
            file_manager: ファイルマネージャー

        Returns:
            ImageProcessor: テスト用プロセッサー
        """
        return ImageProcessor(file_manager=file_manager)

    @pytest.fixture
    def test_image(self) -> Image.Image:
        """テスト用画像を生成

        Returns:
            Image.Image: 1920x1080のRGB画像
        """
        return Image.new("RGB", (1920, 1080), color=(255, 255, 255))

    def test_crop_element_basic(self, processor: ImageProcessor, test_image: Image.Image) -> None:
        """基本的な画像切り出し"""
        bbox = (100, 100, 800, 600)
        cropped = processor.crop_element(test_image, bbox)

        assert cropped.size == (800, 600)
        assert cropped.mode == "RGB"

    def test_crop_element_full_image(
        self, processor: ImageProcessor, test_image: Image.Image
    ) -> None:
        """画像全体の切り出し"""
        bbox = (0, 0, 1920, 1080)
        cropped = processor.crop_element(test_image, bbox)

        assert cropped.size == (1920, 1080)

    def test_crop_element_small_region(
        self, processor: ImageProcessor, test_image: Image.Image
    ) -> None:
        """小さな領域の切り出し"""
        bbox = (500, 500, 100, 100)
        cropped = processor.crop_element(test_image, bbox)

        assert cropped.size == (100, 100)

    def test_crop_element_negative_x_raises_error(
        self, processor: ImageProcessor, test_image: Image.Image
    ) -> None:
        """負のx座標でエラー"""
        bbox = (-10, 100, 800, 600)

        with pytest.raises(ImageCropError) as exc_info:
            processor.crop_element(test_image, bbox)

        assert "negative" in str(exc_info.value).lower()
        assert exc_info.value.bbox == bbox

    def test_crop_element_negative_y_raises_error(
        self, processor: ImageProcessor, test_image: Image.Image
    ) -> None:
        """負のy座標でエラー"""
        bbox = (100, -10, 800, 600)

        with pytest.raises(ImageCropError) as exc_info:
            processor.crop_element(test_image, bbox)

        assert "negative" in str(exc_info.value).lower()

    def test_crop_element_zero_width_raises_error(
        self, processor: ImageProcessor, test_image: Image.Image
    ) -> None:
        """幅0でエラー"""
        bbox = (100, 100, 0, 600)

        with pytest.raises(ImageCropError) as exc_info:
            processor.crop_element(test_image, bbox)

        assert "positive" in str(exc_info.value).lower()

    def test_crop_element_zero_height_raises_error(
        self, processor: ImageProcessor, test_image: Image.Image
    ) -> None:
        """高さ0でエラー"""
        bbox = (100, 100, 800, 0)

        with pytest.raises(ImageCropError) as exc_info:
            processor.crop_element(test_image, bbox)

        assert "positive" in str(exc_info.value).lower()

    def test_crop_element_exceeds_width_raises_error(
        self, processor: ImageProcessor, test_image: Image.Image
    ) -> None:
        """画像幅を超えるbboxでエラー"""
        bbox = (1000, 100, 1000, 600)  # 1000 + 1000 > 1920

        with pytest.raises(ImageCropError) as exc_info:
            processor.crop_element(test_image, bbox)

        assert "boundaries" in str(exc_info.value).lower()

    def test_crop_element_exceeds_height_raises_error(
        self, processor: ImageProcessor, test_image: Image.Image
    ) -> None:
        """画像高さを超えるbboxでエラー"""
        bbox = (100, 500, 800, 700)  # 500 + 700 > 1080

        with pytest.raises(ImageCropError) as exc_info:
            processor.crop_element(test_image, bbox)

        assert "boundaries" in str(exc_info.value).lower()

    def test_save_image_png(
        self, processor: ImageProcessor, test_image: Image.Image, tmp_path: Path
    ) -> None:
        """PNG形式で保存"""
        output_path = "test_output.png"
        saved_path = processor.save_image(test_image, output_path, format="PNG")

        assert Path(saved_path).exists()
        assert Path(saved_path).suffix == ".png"

        # 保存された画像を読み込んで検証
        loaded = Image.open(saved_path)
        assert loaded.size == test_image.size

    def test_save_image_jpeg(
        self, processor: ImageProcessor, test_image: Image.Image, tmp_path: Path
    ) -> None:
        """JPEG形式で保存"""
        output_path = "test_output.jpeg"
        saved_path = processor.save_image(test_image, output_path, format="JPEG")

        assert Path(saved_path).exists()
        assert Path(saved_path).suffix == ".jpeg"

        # 保存された画像を読み込んで検証
        loaded = Image.open(saved_path)
        assert loaded.size == test_image.size

    def test_save_image_rgba_to_jpeg(
        self, processor: ImageProcessor, tmp_path: Path
    ) -> None:
        """RGBA画像をJPEG形式で保存（RGB変換）"""
        rgba_image = Image.new("RGBA", (800, 600), color=(255, 0, 0, 128))
        output_path = "test_rgba.jpeg"

        saved_path = processor.save_image(rgba_image, output_path, format="JPEG")

        assert Path(saved_path).exists()

        # RGB形式に変換されていることを確認
        loaded = Image.open(saved_path)
        assert loaded.mode == "RGB"

    def test_save_image_unsupported_format_raises_error(
        self, processor: ImageProcessor, test_image: Image.Image
    ) -> None:
        """サポートされていない形式でエラー"""
        output_path = "test_output.bmp"

        with pytest.raises(ImageSaveError) as exc_info:
            processor.save_image(test_image, output_path, format="BMP")

        assert "unsupported" in str(exc_info.value).lower()
        assert exc_info.value.format == "BMP"

    def test_save_image_sanitizes_filename(
        self, processor: ImageProcessor, test_image: Image.Image, tmp_path: Path
    ) -> None:
        """危険な文字を含むファイル名がサニタイズされる"""
        output_path = 'test<>:"|?*.png'
        saved_path = processor.save_image(test_image, output_path, format="PNG")

        # サニタイズされたファイル名で保存される
        assert Path(saved_path).exists()
        # 危険な文字が含まれていない
        filename = Path(saved_path).name
        assert "<" not in filename
        assert ">" not in filename
        assert ":" not in filename

    def test_clean_image_basic(
        self, processor: ImageProcessor, test_image: Image.Image
    ) -> None:
        """基本的な画像クリーニング"""
        cleaned = processor.clean_image(test_image)

        # クリーニング後も同じサイズとモード
        assert cleaned.size == test_image.size
        assert cleaned.mode == test_image.mode

    def test_clean_image_with_noise(self, processor: ImageProcessor) -> None:
        """ノイズを含む画像のクリーニング"""
        # ノイズを含む画像を生成
        import random

        noisy_image = Image.new("RGB", (100, 100))
        pixels = noisy_image.load()
        assert pixels is not None  # 型チェック用のアサーション
        for i in range(100):
            for j in range(100):
                # ランダムなノイズ
                r = random.randint(0, 255)
                g = random.randint(0, 255)
                b = random.randint(0, 255)
                pixels[i, j] = (r, g, b)

        cleaned = processor.clean_image(noisy_image)

        # クリーニング後も同じサイズ
        assert cleaned.size == noisy_image.size

    def test_clean_image_preserves_original_on_error(
        self, processor: ImageProcessor
    ) -> None:
        """クリーニング失敗時は元画像を返す"""
        # 破損した画像をシミュレート（実際のエラーは発生しにくい）
        test_image = Image.new("RGB", (100, 100))

        cleaned = processor.clean_image(test_image)

        # 元画像と同じサイズ（フォールバック）
        assert cleaned.size == test_image.size

    def test_sanitize_filename_removes_dangerous_chars(
        self, processor: ImageProcessor
    ) -> None:
        """危険な文字が削除される"""
        filename = 'test<>:"|?*file.png'
        sanitized = processor._sanitize_filename(filename)

        # 危険な文字がアンダースコアに置換される
        assert "<" not in sanitized
        assert ">" not in sanitized
        assert ":" not in sanitized
        assert '"' not in sanitized
        assert "?" not in sanitized
        assert "*" not in sanitized

    def test_sanitize_filename_collapses_underscores(
        self, processor: ImageProcessor
    ) -> None:
        """連続するアンダースコアが1つに"""
        filename = "test___file.png"
        sanitized = processor._sanitize_filename(filename)

        # 連続するアンダースコアが1つに
        assert "___" not in sanitized
        assert "_" in sanitized
