"""Image Loader Module

PDF/画像ファイルの読み込みと正規化機能を提供します。

このモジュールは以下の機能を提供します:
- PDFページをpdf2imageで画像リストに変換
- 各種画像形式の読み込み（PNG, JPEG, GIF, BMP）
- 画像正規化（1920x1080、RGB変換）
- セキュリティ対策（ファイルサイズ制限、ページ数制限）

Classes:
    ImageLoader: PDF/画像ファイルの読み込みと正規化
"""

import os
from pathlib import Path
from typing import Any

import structlog
from pdf2image import convert_from_path, pdfinfo_from_path
from pdf2image.exceptions import PDFPageCountError, PDFSyntaxError
from PIL import Image, ImageOps

from slidemaker.image_processing.exceptions import ImageProcessingError
from slidemaker.utils.file_manager import FileManager

logger = structlog.get_logger(__name__)

# 定数
SUPPORTED_IMAGE_FORMATS = {".png", ".jpg", ".jpeg", ".gif", ".bmp"}
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
MAX_PDF_PAGES = 50
DEFAULT_DPI = 200
TARGET_WIDTH = 1920
TARGET_HEIGHT = 1080


class ImageLoadError(ImageProcessingError):
    """画像読み込みエラー

    画像またはPDFファイルの読み込みが失敗した場合に発生します。

    Attributes:
        file_path: 読み込みに失敗したファイルのパス
    """

    def __init__(
        self,
        message: str,
        file_path: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """ImageLoadErrorの初期化

        Args:
            message: エラーメッセージ
            file_path: 読み込みに失敗したファイルのパス（オプション）
            details: 追加の詳細情報（オプション）
        """
        super().__init__(message, details)
        self.file_path = file_path

    def __str__(self) -> str:
        """エラーメッセージの文字列表現

        Returns:
            str: ファイルパスを含むエラーメッセージ
        """
        parts = [self.message]
        if self.file_path is not None:
            parts.append(f"file_path='{self.file_path}'")
        if self.details:
            parts.append(f"details={self.details}")
        return " | ".join(parts)


class ImageLoader:
    """PDF/画像ファイルの読み込みと正規化

    主な機能:
    - PDFページをpdf2imageで画像リストに変換（DPI=200-300）
    - 各種画像形式の読み込み（PNG, JPEG, GIF, BMP）
    - 画像正規化（1920x1080、RGB変換）
    - セキュリティ対策（FileManager使用、ファイルサイズ制限10MB、PDF最大50ページ）

    Attributes:
        file_manager: ファイル管理用のFileManagerインスタンス
        logger: structlogロガー
    """

    def __init__(self, file_manager: FileManager) -> None:
        """ImageLoaderの初期化

        Args:
            file_manager: ファイル管理用のFileManagerインスタンス
        """
        self.file_manager = file_manager
        self.logger = logger.bind(component="ImageLoader")
        self.logger.info("ImageLoader initialized")

    async def load_from_pdf(
        self, pdf_path: Path | str, dpi: int = DEFAULT_DPI
    ) -> list[Image.Image]:
        """PDFから画像リストを生成

        PDFファイルの各ページを画像に変換します。pdf2imageライブラリを使用し、
        指定されたDPIで変換します。

        Args:
            pdf_path: PDFファイルパス（PathまたはstrString）
            dpi: 解像度（デフォルト200、品質と速度のバランス）

        Returns:
            list[Image.Image]: ページごとの画像リスト（PIL.Image形式）

        Raises:
            FileNotFoundError: PDFファイルが存在しない
            ValueError: PDFページ数が50を超える、ファイルサイズが10MBを超える、またはDPIが不正
            ImageLoadError: PDF変換失敗
        """
        self.logger.info("Loading PDF", pdf_path=str(pdf_path), dpi=dpi)

        # ファイルパスのバリデーション
        pdf_file = Path(pdf_path) if isinstance(pdf_path, str) else pdf_path
        if not pdf_file.exists():
            error_msg = f"PDF file not found: {pdf_path}"
            self.logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        if not pdf_file.is_file():
            error_msg = f"Path is not a file: {pdf_path}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        if pdf_file.suffix.lower() != ".pdf":
            error_msg = f"File is not a PDF: {pdf_path}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        # DPIのバリデーション
        if dpi <= 0 or dpi > 600:
            error_msg = f"Invalid DPI value: {dpi}. Must be between 1 and 600."
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        # ファイルサイズチェック（変換前に実施）
        file_size = os.path.getsize(pdf_file)
        if file_size > MAX_FILE_SIZE_BYTES:
            error_msg = (
                f"PDF file size exceeds limit: {file_size} bytes "
                f"({file_size / 1024 / 1024:.2f} MB) > {MAX_FILE_SIZE_MB} MB"
            )
            self.logger.error(error_msg, file_size=file_size)
            raise ValueError(error_msg)

        # PDFページ数チェック（変換前に実施）
        try:
            info = pdfinfo_from_path(str(pdf_file))
            page_count = info.get("Pages", 0)
            if page_count > MAX_PDF_PAGES:
                error_msg = (
                    f"PDF has too many pages: {page_count}. "
                    f"Maximum allowed is {MAX_PDF_PAGES}."
                )
                self.logger.error(error_msg, page_count=page_count)
                raise ValueError(error_msg)

            self.logger.info(
                "PDF validation passed",
                page_count=page_count,
                file_size_mb=f"{file_size / 1024 / 1024:.2f}",
            )

        except PDFPageCountError as e:
            error_msg = f"Failed to determine PDF page count: {e}"
            self.logger.error(error_msg, pdf_path=str(pdf_path))
            raise ImageLoadError(
                error_msg, file_path=str(pdf_path), details={"error": str(e)}
            ) from e

        except PDFSyntaxError as e:
            error_msg = f"PDF syntax error or corrupted file: {e}"
            self.logger.error(error_msg, pdf_path=str(pdf_path))
            raise ImageLoadError(
                error_msg, file_path=str(pdf_path), details={"error": str(e)}
            ) from e

        # PDFを画像に変換（非同期実行）
        import asyncio

        loop = asyncio.get_event_loop()
        images = await loop.run_in_executor(
            None,
            lambda: convert_from_path(
                pdf_file,
                dpi=dpi,
                fmt="PNG",
                thread_count=2,  # メモリ効率とパフォーマンスのバランス
            ),
        )

        self.logger.info(
            "PDF loaded successfully",
            page_count=len(images),
            pdf_path=str(pdf_path),
        )
        return images

    async def load_from_image(self, image_path: Path | str) -> Image.Image:
        """画像ファイルを読み込み

        指定された画像ファイルを読み込みます。対応形式はPNG, JPEG, GIF, BMPです。
        ファイルサイズは10MBまでに制限されています。

        Args:
            image_path: 画像ファイルパス（PathまたはstrString）

        Returns:
            Image.Image: 読み込んだ画像（PIL.Image形式）

        Raises:
            FileNotFoundError: 画像ファイルが存在しない
            ValueError: 非対応形式、またはファイルサイズ10MB超過
            ImageLoadError: 画像読み込み失敗
        """
        self.logger.info("Loading image", image_path=str(image_path))

        # ファイルパスのバリデーション
        image_file = Path(image_path) if isinstance(image_path, str) else image_path
        if not image_file.exists():
            error_msg = f"Image file not found: {image_path}"
            self.logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        if not image_file.is_file():
            error_msg = f"Path is not a file: {image_path}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        # 拡張子チェック
        file_extension = image_file.suffix.lower()
        if file_extension not in SUPPORTED_IMAGE_FORMATS:
            error_msg = (
                f"Unsupported image format: {file_extension}. "
                f"Supported formats: {', '.join(SUPPORTED_IMAGE_FORMATS)}"
            )
            self.logger.error(error_msg, image_path=str(image_path))
            raise ValueError(error_msg)

        # ファイルサイズチェック
        file_size = os.path.getsize(image_file)
        if file_size > MAX_FILE_SIZE_BYTES:
            file_size_mb = file_size / 1024 / 1024
            error_msg = (
                f"Image file too large: {file_size_mb:.2f}MB. "
                f"Maximum allowed is {MAX_FILE_SIZE_MB}MB."
            )
            self.logger.error(error_msg, image_path=str(image_path), file_size_mb=file_size_mb)
            raise ValueError(error_msg)

        try:
            # 画像を読み込み（非同期実行）
            import asyncio
            loop = asyncio.get_event_loop()

            def load_image() -> Image.Image:
                img = Image.open(image_file)
                # 遅延読み込みを強制的に実行（破損チェック）
                img.load()
                return img

            image = await loop.run_in_executor(None, load_image)

            self.logger.info(
                "Image loaded successfully",
                image_path=str(image_path),
                size=image.size,
                mode=image.mode,
            )
            return image

        except OSError as e:
            error_msg = f"Failed to load image (corrupted or invalid format): {e}"
            self.logger.error(error_msg, image_path=str(image_path))
            raise ImageLoadError(
                error_msg,
                file_path=str(image_path),
                details={"error": str(e)},
            ) from e

        except Exception as e:
            error_msg = f"Unexpected error while loading image: {e}"
            self.logger.error(error_msg, image_path=str(image_path), error_type=type(e).__name__)
            raise ImageLoadError(
                error_msg,
                file_path=str(image_path),
                details={"error": str(e)},
            ) from e

    def normalize_image(self, image: Image.Image) -> Image.Image:
        """画像を正規化（1920x1080にリサイズ、RGBモード変換）

        画像を指定されたサイズ（1920x1080）にリサイズし、RGBモードに変換します。
        アスペクト比を維持してリサイズし、余白は透明または白背景で埋められます。

        Args:
            image: 元画像（PIL.Image）

        Returns:
            Image.Image: 正規化された画像（1920x1080、RGB）

        Notes:
            - アスペクト比を維持してリサイズ
            - RGBAの場合はRGBに変換（白背景で合成）
            - EXIF回転情報を適用
        """
        self.logger.info(
            "Normalizing image",
            original_size=image.size,
            original_mode=image.mode,
        )

        try:
            # EXIF回転情報を適用
            image = ImageOps.exif_transpose(image)

            # RGBモードに変換
            if image.mode == "RGBA":
                # 白背景で合成
                background = Image.new("RGB", image.size, (255, 255, 255))
                # アルファチャンネルをマスクとして使用
                background.paste(image, mask=image.split()[3])
                image = background
            elif image.mode != "RGB":
                image = image.convert("RGB")

            # アスペクト比を維持してリサイズ
            image.thumbnail((TARGET_WIDTH, TARGET_HEIGHT), Image.Resampling.LANCZOS)

            # 中央配置で余白を白背景で埋める
            normalized_image = Image.new("RGB", (TARGET_WIDTH, TARGET_HEIGHT), (255, 255, 255))
            x_offset = (TARGET_WIDTH - image.width) // 2
            y_offset = (TARGET_HEIGHT - image.height) // 2
            normalized_image.paste(image, (x_offset, y_offset))

            self.logger.info(
                "Image normalized successfully",
                normalized_size=normalized_image.size,
                normalized_mode=normalized_image.mode,
            )
            return normalized_image

        except Exception as e:
            error_msg = f"Failed to normalize image: {e}"
            self.logger.error(error_msg, error_type=type(e).__name__)
            raise ImageProcessingError(error_msg, details={"error": str(e)}) from e
