"""PowerPoint generation module."""

from pathlib import Path

import structlog
from pptx.util import Inches

from pptx import Presentation
from slidemaker.core.models.common import SlideSize
from slidemaker.core.models.page_definition import PageDefinition
from slidemaker.core.models.slide_config import SlideConfig
from slidemaker.pptx.slide_builder import SlideBuilder

logger = structlog.get_logger(__name__)


class PowerPointGeneratorError(Exception):
    """Base exception for PowerPoint generation errors."""


class PowerPointGenerator:
    """
    PowerPoint生成のメインクラス.

    python-pptxのPresentationオブジェクトをラップし、
    SlideConfigとPageDefinitionリストからPowerPointファイルを生成します。

    Examples:
        >>> config = SlideConfig.create_16_9()
        >>> generator = PowerPointGenerator(config)
        >>> pages = [PageDefinition(page_number=1, title="Sample")]
        >>> output = generator.generate(pages, Path("output.pptx"))
    """

    def __init__(self, config: SlideConfig) -> None:
        """
        PowerPointGeneratorを初期化します.

        Args:
            config: スライド設定（サイズ、デフォルトフォント等）

        Raises:
            PowerPointGeneratorError: Presentation初期化に失敗した場合
        """
        self.config = config

        try:
            self.presentation = Presentation()
            self._set_slide_size(config.size)
            logger.info(
                "PowerPointGenerator initialized",
                slide_size=config.size.value,
                width=config.width,
                height=config.height,
            )
        except Exception as e:
            logger.error("Failed to initialize Presentation", error=str(e))
            raise PowerPointGeneratorError(f"Presentation initialization failed: {e}") from e

    def generate(self, pages: list[PageDefinition], output_path: str | Path) -> Path:
        """
        スライドデッキを生成してファイルに保存します.

        Args:
            pages: ページ定義のリスト（page_numberでソート済みを想定）
            output_path: 出力先ファイルパス（.pptx拡張子）

        Returns:
            Path: 生成されたPowerPointファイルの絶対パス

        Raises:
            PowerPointGeneratorError: スライド生成またはファイル保存に失敗した場合
            ValueError: pagesが空の場合、または出力パスが無効な場合

        Examples:
            >>> pages = [
            ...     PageDefinition(page_number=1, title="Title Slide"),
            ...     PageDefinition(page_number=2, title="Content Slide"),
            ... ]
            >>> output = generator.generate(pages, "presentation.pptx")
        """
        if not pages:
            raise ValueError("Pages list cannot be empty")

        output_path = Path(output_path)
        if output_path.suffix.lower() != ".pptx":
            raise ValueError(f"Output path must have .pptx extension: {output_path}")

        logger.info(
            "Starting PowerPoint generation",
            page_count=len(pages),
            output_path=str(output_path),
        )

        try:
            # SlideBuilderを使用してスライドを構築
            builder = SlideBuilder(self.presentation)

            for page in pages:
                builder.build_slide(page)
                logger.debug("Built slide", page_number=page.page_number, title=page.title)

            # ファイルに保存
            output_path = self._save_presentation(output_path)

            logger.info(
                "PowerPoint generation completed",
                output_path=str(output_path),
                slide_count=len(self.presentation.slides),
            )

            return output_path

        except Exception as e:
            logger.error("PowerPoint generation failed", error=str(e))
            raise PowerPointGeneratorError(f"Failed to generate PowerPoint: {e}") from e

    def _set_slide_size(self, size: SlideSize) -> None:
        """
        スライドサイズを設定します（private）.

        Args:
            size: スライドサイズ（4:3、16:9、16:10等）

        Notes:
            - 標準サポートサイズ:
              - 4:3 (Standard): 10インチ x 7.5インチ
              - 16:9 (Widescreen): 10インチ x 5.625インチ
            - カスタムサイズ: configのwidth/heightを使用（96 DPI想定で変換）
            - EMU換算: 1インチ = 914400 EMU
            - 未サポートサイズの場合は警告ログを出力してフォールバック
        """
        size_mapping = {
            SlideSize.STANDARD_4_3: (Inches(10), Inches(7.5)),
            SlideSize.WIDESCREEN_16_9: (Inches(10), Inches(5.625)),
            # 16:10サポート（将来的にSlideSize enumに追加予定）
            # SlideSize.WIDESCREEN_16_10: (Inches(10), Inches(6.25)),
        }

        if size not in size_mapping:
            # カスタムサイズの場合はconfigのwidth/heightを使用
            logger.warning(
                "Custom or unsupported slide size, using config dimensions",
                size=size.value,
                width=self.config.width,
                height=self.config.height,
            )
            # ピクセルからインチへの変換（96 DPI想定）
            width_inches = self.config.width / 96.0
            height_inches = self.config.height / 96.0
            self.presentation.slide_width = Inches(width_inches)
            self.presentation.slide_height = Inches(height_inches)
            return

        width, height = size_mapping[size]
        self.presentation.slide_width = width
        self.presentation.slide_height = height

        logger.debug(
            "Slide size set",
            size=size.value,
            width_inches=width / 914400,
            height_inches=height / 914400,
        )

    def _save_presentation(self, output_path: Path) -> Path:
        """
        Presentationをファイルに保存します（private）.

        Args:
            output_path: 出力先パス

        Returns:
            Path: 保存されたファイルの絶対パス

        Raises:
            PowerPointGeneratorError: ファイル保存に失敗した場合

        Notes:
            親ディレクトリが存在しない場合は自動的に作成されます。
        """
        try:
            # 親ディレクトリが存在しない場合は作成
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Presentationを保存
            self.presentation.save(str(output_path))

            # 絶対パスを返す
            absolute_path = output_path.resolve()

            logger.info("Presentation saved", path=str(absolute_path))

            return absolute_path

        except PermissionError as e:
            logger.error("Permission denied while saving presentation", path=str(output_path))
            raise PowerPointGeneratorError(
                f"Permission denied: Cannot save to {output_path}"
            ) from e
        except OSError as e:
            logger.error("OS error while saving presentation", path=str(output_path), error=str(e))
            raise PowerPointGeneratorError(f"Failed to save presentation: {e}") from e
        except Exception as e:
            logger.error(
                "Unexpected error while saving presentation", path=str(output_path), error=str(e)
            )
            raise PowerPointGeneratorError(f"Unexpected error during save: {e}") from e
