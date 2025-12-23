"""PDF/画像からPowerPointへの変換ワークフロー."""

import asyncio
from pathlib import Path
from typing import Any

import structlog
from PIL import Image

from slidemaker.core.models.page_definition import PageDefinition
from slidemaker.image_processing.analyzer import ImageAnalyzer
from slidemaker.image_processing.loader import ImageLoader
from slidemaker.image_processing.processor import ImageProcessor
from slidemaker.llm.manager import LLMManager
from slidemaker.pptx.generator import PowerPointGenerator
from slidemaker.utils.file_manager import FileManager
from slidemaker.workflows.base import WorkflowOrchestrator
from slidemaker.workflows.exceptions import WorkflowError, WorkflowValidationError


class ConversionWorkflow(WorkflowOrchestrator):
    """PDF/画像からPowerPointへの変換ワークフロー.

    5つのステップから構成される変換パイプライン:
    1. 画像読み込み（PDF → 画像リスト、または画像ファイル）
    2. 各画像をLLMで分析（テキスト・画像要素を検出）
    3. 検出された画像要素を切り出し・保存
    4. PageDefinitionリストを作成
    5. PowerPointファイルを生成

    Attributes:
        llm_manager: LLMマネージャー
        file_manager: ファイルマネージャー
        image_loader: 画像ローダー
        image_analyzer: 画像アナライザー
        image_processor: 画像プロセッサー
        powerpoint_generator: PowerPointジェネレーター
        logger: 構造化ロガー

    Example:
        >>> workflow = ConversionWorkflow(
        ...     llm_manager=llm_manager,
        ...     file_manager=file_manager,
        ...     image_loader=image_loader,
        ...     image_analyzer=image_analyzer,
        ...     image_processor=image_processor,
        ...     powerpoint_generator=powerpoint_generator
        ... )
        >>> result = await workflow.execute(
        ...     input_data=Path("document.pdf"),
        ...     output_path=Path("output/slides.pptx"),
        ...     dpi=300,
        ...     max_concurrent=3
        ... )
    """

    def __init__(
        self,
        llm_manager: LLMManager,
        file_manager: FileManager,
        image_loader: ImageLoader,
        image_analyzer: ImageAnalyzer,
        image_processor: ImageProcessor,
        powerpoint_generator: PowerPointGenerator,
    ) -> None:
        """ConversionWorkflowの初期化.

        Args:
            llm_manager: LLMマネージャーインスタンス
            file_manager: ファイルマネージャーインスタンス
            image_loader: ImageLoaderインスタンス
            image_analyzer: ImageAnalyzerインスタンス
            image_processor: ImageProcessorインスタンス
            powerpoint_generator: PowerPointGeneratorインスタンス
        """
        super().__init__(llm_manager=llm_manager, file_manager=file_manager)
        self.image_loader = image_loader
        self.image_analyzer = image_analyzer
        self.image_processor = image_processor
        self.powerpoint_generator = powerpoint_generator
        self.logger = structlog.get_logger(__name__)

    async def execute(
        self,
        input_data: Any,
        output_path: Path,
        **options: Any,
    ) -> Path:
        """ワークフローの実行.

        PDF/画像ファイルから最終的なPowerPointファイルまでの
        完全なパイプラインを実行します。

        Args:
            input_data: 入力ファイルパス（Path型、PDFまたは画像）
            output_path: 出力PowerPointファイルのパス
            **options: オプション
                - dpi (int): PDF変換時のDPI（デフォルト: 300）
                - max_concurrent (int): 並列分析数（デフォルト: 3）
                - slide_size (str): スライドサイズ（デフォルト: "16:9"）
                - max_retries (int): ステップの最大リトライ回数（デフォルト: 3）
                - temp_dir (Path): 一時ファイルディレクトリ
                  （デフォルト: output_path.parent / "temp"）

        Returns:
            Path: 生成されたPowerPointファイルのパス

        Raises:
            WorkflowError: ワークフロー実行エラー
            WorkflowValidationError: 入力データのバリデーションエラー
            FileNotFoundError: 入力ファイルが存在しない
            TypeError: input_dataがPath型でない場合

        Example:
            >>> result = await workflow.execute(
            ...     input_data=Path("document.pdf"),
            ...     output_path=Path("output/slides.pptx"),
            ...     dpi=300,
            ...     max_concurrent=3
            ... )
        """
        # 入力データをPathに変換・検証
        if not isinstance(input_data, Path):
            try:
                input_path = Path(input_data)
            except (TypeError, ValueError) as e:
                raise TypeError(f"input_data must be a Path or path-like string: {e}") from e
        else:
            input_path = input_data

        self.logger.info(
            "conversion_workflow_start",
            input_path=str(input_path),
            output_path=str(output_path),
            options=options,
        )

        # 入力のバリデーション
        self._validate_input(input_path)
        self._validate_output_path(output_path)

        # オプションの取得
        dpi = options.get("dpi", 300)
        max_concurrent = options.get("max_concurrent", 3)
        max_retries = options.get("max_retries", 3)
        temp_dir = options.get("temp_dir", output_path.parent / "temp")

        # 一時ディレクトリの作成
        temp_dir = Path(temp_dir)
        temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Step 1: 画像の読み込み
            images: list[Image.Image] = await self._run_step(
                "load_images",
                self._load_images,
                input_path,
                dpi,
                max_retries=max_retries,
            )

            # Step 2: 各ページの分析（PageDefinition生成）
            pages: list[PageDefinition] = await self._run_step(
                "analyze_images",
                self._analyze_images,
                images,
                max_concurrent,
                max_retries=max_retries,
            )

            # Step 3: 画像要素の抽出と保存（PageDefinitionのImageElement.sourceを更新）
            pages = await self._run_step(
                "process_images",
                self._process_images,
                images,
                pages,
                temp_dir,
                max_retries=max_retries,
            )

            # Step 4: PowerPoint生成
            result_path: Path = await self._run_step(
                "generate_powerpoint",
                self._generate_powerpoint,
                pages,
                output_path,
                max_retries=1,  # PowerPoint生成は通常リトライ不要
            )

            self.logger.info(
                "conversion_workflow_success",
                output_path=str(result_path),
                total_pages=len(pages),
            )

            return result_path

        except Exception as e:
            self.logger.error(
                "conversion_workflow_failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            # クリーンアップ: 一時ファイルの削除
            if temp_dir.exists():
                try:
                    import shutil

                    shutil.rmtree(temp_dir)
                    self.logger.debug("cleanup_temp_dir", path=str(temp_dir))
                except Exception as cleanup_error:
                    self.logger.warning(
                        "cleanup_failed",
                        error=str(cleanup_error),
                    )
            raise

    def _validate_input(self, input_data: Any) -> None:
        """入力データのバリデーション.

        入力ファイルの存在とファイル形式を検証します。

        Args:
            input_data: 入力ファイルパス（Path型）

        Raises:
            WorkflowValidationError: 入力データが不正な場合
            FileNotFoundError: ファイルが存在しない場合
        """
        if not isinstance(input_data, Path):
            raise WorkflowValidationError(
                f"Input data must be a Path, got {type(input_data).__name__}",
                details={"input_type": type(input_data).__name__},
            )

        input_path = input_data

        # ファイルの存在確認
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        if not input_path.is_file():
            raise WorkflowValidationError(
                f"Input path is not a file: {input_path}",
                details={"path": str(input_path)},
            )

        # ファイル形式のチェック
        suffix = input_path.suffix.lower()
        supported_formats = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".bmp"}
        if suffix not in supported_formats:
            raise WorkflowValidationError(
                f"Unsupported file format: {suffix}. Supported: {supported_formats}",
                details={"suffix": suffix, "supported": list(supported_formats)},
            )

        self.logger.debug(
            "input_validated",
            path=str(input_path),
            format=suffix,
        )

    async def _load_images(
        self,
        input_path: Path,
        dpi: int,
    ) -> list[Image.Image]:
        """画像の読み込み（Step 1）.

        PDFの場合はページ画像に変換、画像ファイルの場合はそのまま読み込みます。

        Args:
            input_path: 入力ファイルパス
            dpi: PDF変換時のDPI

        Returns:
            list[Image.Image]: 読み込んだ画像のリスト

        Raises:
            WorkflowError: 画像読み込みエラー
        """
        try:
            suffix = input_path.suffix.lower()

            if suffix == ".pdf":
                # PDFからページ画像に変換
                self.logger.info("loading_pdf", path=str(input_path), dpi=dpi)
                images = await self.image_loader.load_from_pdf(input_path, dpi=dpi)
                self.logger.info("pdf_loaded", page_count=len(images))
            else:
                # 画像ファイルの読み込み
                self.logger.info("loading_image", path=str(input_path))
                image = await self.image_loader.load_from_image(input_path)
                images = [image]
                self.logger.info("image_loaded")

            return images

        except Exception as e:
            error_msg = f"Failed to load images: {e}"
            self.logger.error("image_load_failed", error=str(e))
            raise WorkflowError(error_msg, details={"path": str(input_path)}) from e

    async def _analyze_images(
        self,
        images: list[Image.Image],
        max_concurrent: int,
    ) -> list[PageDefinition]:
        """画像の分析（Step 2）.

        LLMを使用して各画像のテキスト・画像要素を検出します。
        並列処理でパフォーマンスを向上させます。

        Args:
            images: 分析する画像のリスト
            max_concurrent: 最大並列数

        Returns:
            list[PageDefinition]: ページ定義のリスト

        Raises:
            WorkflowError: 分析エラー
        """
        try:
            self.logger.info(
                "analyzing_images", image_count=len(images), max_concurrent=max_concurrent
            )

            # セマフォで並列数を制限
            semaphore = asyncio.Semaphore(max_concurrent)

            async def analyze_with_semaphore(image: Image.Image, index: int) -> PageDefinition:
                async with semaphore:
                    self.logger.debug("analyzing_image", index=index)
                    result = await self.image_analyzer.analyze_slide_image(image)
                    self.logger.debug("image_analyzed", index=index)
                    return result

            # 並列分析
            page_definitions = await asyncio.gather(
                *[analyze_with_semaphore(img, i) for i, img in enumerate(images)]
            )

            self.logger.info("images_analyzed", result_count=len(page_definitions))
            return page_definitions

        except Exception as e:
            error_msg = f"Failed to analyze images: {e}"
            self.logger.error("image_analysis_failed", error=str(e))
            raise WorkflowError(error_msg, details={"image_count": len(images)}) from e

    async def _process_images(
        self,
        images: list[Image.Image],
        pages: list[PageDefinition],
        temp_dir: Path,
    ) -> list[PageDefinition]:
        """画像要素の抽出と保存（Step 3）.

        PageDefinitionから画像要素を切り出して保存し、source pathを更新します。

        Args:
            images: 元画像のリスト
            pages: ページ定義のリスト
            temp_dir: 一時ファイルディレクトリ

        Returns:
            list[PageDefinition]: 画像sourceが更新されたページ定義のリスト

        Raises:
            WorkflowError: 画像処理エラー
        """
        try:
            self.logger.info("processing_images", temp_dir=str(temp_dir), page_count=len(pages))

            for page_idx, (image, page) in enumerate(zip(images, pages, strict=True)):
                for elem_idx, element in enumerate(page.elements):
                    # ImageElement型チェック
                    from slidemaker.core.models.element import ImageElement

                    if not isinstance(element, ImageElement):
                        continue

                    # 画像要素の切り出し
                    # PageDefinitionのpositionとsizeは相対座標（%）なので、
                    # 実際のピクセル座標に変換
                    img_width, img_height = image.size
                    x_px = int(element.position.x * img_width / 100)
                    y_px = int(element.position.y * img_height / 100)
                    width_px = int(element.size.width * img_width / 100)
                    height_px = int(element.size.height * img_height / 100)

                    # bboxの作成（x, y, width, height）
                    bbox = (x_px, y_px, width_px, height_px)

                    # 画像IDの生成
                    image_id = f"page{page_idx}_elem{elem_idx}"

                    # 画像の切り出しと保存
                    try:
                        # 画像の切り出し（synchronous）
                        cropped_image = self.image_processor.crop_element(image, bbox)

                        # ファイル名の生成
                        filename = f"{image_id}.png"
                        output_file_path = temp_dir / filename

                        # 画像の保存（synchronous）
                        saved_path = self.image_processor.save_image(
                            cropped_image, str(output_file_path), format="PNG"
                        )

                        # ImageElement.sourceを更新
                        element.source = str(saved_path)

                        self.logger.debug(
                            "image_element_processed",
                            image_id=image_id,
                            path=str(saved_path),
                        )
                    except Exception as elem_error:
                        # 個別の画像要素の処理失敗は警告のみ（続行）
                        self.logger.warning(
                            "image_element_processing_failed",
                            image_id=image_id,
                            error=str(elem_error),
                        )
                        continue

            self.logger.info("images_processed", page_count=len(pages))
            return pages

        except Exception as e:
            error_msg = f"Failed to process images: {e}"
            self.logger.error("image_processing_failed", error=str(e))
            raise WorkflowError(error_msg, details={"temp_dir": str(temp_dir)}) from e

    async def _generate_powerpoint(
        self,
        pages: list[PageDefinition],
        output_path: Path,
    ) -> Path:
        """PowerPointファイルの生成（Step 4）.

        ページ定義から最終的なPowerPointファイルを生成します。

        Args:
            pages: ページ定義のリスト
            output_path: 出力先パス

        Returns:
            Path: 生成されたPowerPointファイルのパス

        Raises:
            WorkflowError: PowerPoint生成エラー
        """
        try:
            self.logger.info("generating_powerpoint", output_path=str(output_path))

            # PowerPointGeneratorで生成
            result_path = self.powerpoint_generator.generate(
                pages=pages,
                output_path=output_path,
            )

            self.logger.info("powerpoint_generated", path=str(result_path))
            return result_path

        except Exception as e:
            error_msg = f"Failed to generate PowerPoint: {e}"
            self.logger.error("powerpoint_generation_failed", error=str(e))
            raise WorkflowError(error_msg, details={"output_path": str(output_path)}) from e
