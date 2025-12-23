"""Image Processor Module

画像要素の切り出し、保存、クリーニング機能を提供します。

このモジュールは、スライド画像から特定の要素を抽出し、
編集可能な形式で保存する機能を実装します。
"""

import re

import structlog
from PIL import Image, ImageEnhance, ImageFilter

from slidemaker.image_processing.exceptions import ImageCropError, ImageSaveError
from slidemaker.utils.file_manager import FileManager

logger = structlog.get_logger(__name__)

# サポートする画像形式
SUPPORTED_FORMATS = {"PNG", "JPEG"}


class ImageProcessor:
    """画像要素の処理クラス

    画像の切り出し、保存、クリーニング機能を提供します。

    Attributes:
        file_manager: ファイル管理インスタンス
    """

    def __init__(self, file_manager: FileManager) -> None:
        """ImageProcessorの初期化

        Args:
            file_manager: ファイル管理インスタンス
        """
        self.file_manager = file_manager
        logger.info("ImageProcessor initialized")

    def crop_element(
        self, image: Image.Image, bbox: tuple[int, int, int, int]
    ) -> Image.Image:
        """指定座標で画像を切り出し

        Args:
            image: 元画像（PIL.Image.Image）
            bbox: 切り出し領域の座標 (x, y, width, height)

        Returns:
            Image.Image: 切り出された画像

        Raises:
            ImageCropError: 座標が不正な場合
        """
        x, y, width, height = bbox

        # 座標のバリデーション
        if x < 0 or y < 0 or width <= 0 or height <= 0:
            logger.error(
                "Invalid bbox: negative values or zero dimensions",
                bbox=bbox,
            )
            raise ImageCropError(
                "Invalid bbox: coordinates must be non-negative and dimensions positive",
                bbox=bbox,
                details={
                    "x": x,
                    "y": y,
                    "width": width,
                    "height": height,
                },
            )

        # 画像境界チェック
        image_width, image_height = image.size
        if x + width > image_width or y + height > image_height:
            logger.error(
                "Bbox exceeds image boundaries",
                bbox=bbox,
                image_size=(image_width, image_height),
            )
            raise ImageCropError(
                "Bbox exceeds image boundaries",
                bbox=bbox,
                details={
                    "image_size": (image_width, image_height),
                    "crop_end": (x + width, y + height),
                },
            )

        # PIL.Image.crop uses (left, top, right, bottom) format
        crop_box = (x, y, x + width, y + height)

        try:
            cropped = image.crop(crop_box)
            logger.info(
                "Image cropped successfully",
                bbox=bbox,
                original_size=image.size,
                cropped_size=cropped.size,
            )
            return cropped
        except Exception as e:
            logger.error("Failed to crop image", error=str(e), bbox=bbox)
            raise ImageCropError(
                f"Failed to crop image: {e}",
                bbox=bbox,
                details={"original_error": str(e)},
            ) from e

    def save_image(
        self,
        image: Image.Image,
        output_path: str,
        format: str = "PNG",
    ) -> str:
        """画像を保存

        Args:
            image: 保存する画像（PIL.Image.Image）
            output_path: 保存先のパス（相対パスまたは絶対パス）
            format: 画像形式（"PNG" または "JPEG"、デフォルト: "PNG"）

        Returns:
            str: 保存されたファイルの絶対パス

        Raises:
            ImageSaveError: 保存に失敗した場合
        """
        # 形式のバリデーション
        format_upper = format.upper()
        if format_upper not in SUPPORTED_FORMATS:
            logger.error(
                "Unsupported image format",
                format=format,
                supported_formats=list(SUPPORTED_FORMATS),
            )
            raise ImageSaveError(
                f"Unsupported format: {format}. Supported formats: {SUPPORTED_FORMATS}",
                output_path=output_path,
                format=format,
            )

        # ファイル名のサニタイズ
        sanitized_path = self._sanitize_filename(output_path)

        try:
            # 画像をバイトストリームに保存
            from io import BytesIO

            buffer = BytesIO()

            # JPEG形式の場合、RGB変換が必要
            if format_upper == "JPEG" and image.mode in ("RGBA", "LA", "P"):
                # 透過を白背景に変換
                rgb_image = Image.new("RGB", image.size, (255, 255, 255))
                if image.mode == "P" or image.mode == "LA":
                    image = image.convert("RGBA")
                rgb_image.paste(image, mask=image.split()[-1] if image.mode == "RGBA" else None)
                rgb_image.save(buffer, format=format_upper, quality=95)
            else:
                image.save(buffer, format=format_upper)

            # FileManagerを使用して保存（パストラバーサル対策）
            buffer.seek(0)
            saved_path = self.file_manager.save_file(
                content=buffer.getvalue(),
                output_path=sanitized_path,
            )

            logger.info(
                "Image saved successfully",
                output_path=str(saved_path),
                format=format_upper,
                size=image.size,
            )
            return str(saved_path)

        except Exception as e:
            logger.error(
                "Failed to save image",
                error=str(e),
                output_path=output_path,
                format=format,
            )
            raise ImageSaveError(
                f"Failed to save image: {e}",
                output_path=output_path,
                format=format,
                details={"original_error": str(e)},
            ) from e

    def clean_image(self, image: Image.Image) -> Image.Image:
        """画像のクリーニング（ノイズ除去、コントラスト調整）

        Args:
            image: クリーニングする画像（PIL.Image.Image）

        Returns:
            Image.Image: クリーニングされた画像
        """
        try:
            # ノイズ除去（メディアンフィルタ）
            cleaned = image.filter(ImageFilter.MedianFilter(size=3))

            # コントラスト調整（10%向上）
            enhancer = ImageEnhance.Contrast(cleaned)
            enhanced = enhancer.enhance(1.1)

            logger.info(
                "Image cleaned successfully",
                size=image.size,
            )
            return enhanced

        except Exception as e:
            # クリーニング失敗時は元画像を返す（フォールバック）
            logger.warning(
                "Failed to clean image, returning original",
                error=str(e),
            )
            return image

    def _sanitize_filename(self, filename: str) -> str:
        """ファイル名のサニタイズ

        Args:
            filename: サニタイズするファイル名

        Returns:
            str: サニタイズされたファイル名
        """
        # 危険な文字を置換
        # パスセパレータを除去（FileManagerが処理）
        sanitized = re.sub(r'[<>:"|?*]', "_", filename)

        # 連続するアンダースコアを1つに
        sanitized = re.sub(r"_+", "_", sanitized)

        logger.debug("Filename sanitized", original=filename, sanitized=sanitized)
        return sanitized
