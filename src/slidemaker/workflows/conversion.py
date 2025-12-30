"""PDF/画像からPowerPointへの変換ワークフロー."""

import asyncio
from pathlib import Path
from typing import Any

import structlog
from PIL import Image

from slidemaker.core.models.page_definition import PageDefinition
from slidemaker.image_processing.analyzer import ImageAnalyzer
from slidemaker.image_processing.loader import (
    CUSTOM_HEIGHT_PX,
    CUSTOM_WIDTH_PX,
    ImageLoader,
)
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
                temp_dir,
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
        temp_dir: Path | None = None,
    ) -> list[Image.Image]:
        """画像の読み込み（Step 1）.

        PDFの場合はページごとにPNGファイルとして保存してから読み込み、
        画像ファイルの場合はそのまま読み込みます。

        Args:
            input_path: 入力ファイルパス
            dpi: PDF変換時のDPI
            temp_dir: 一時ディレクトリ（PDFページPNG保存用、オプション）

        Returns:
            list[Image.Image]: 読み込んだ画像のリスト（正規化済み）

        Raises:
            WorkflowError: 画像読み込みエラー
        """
        try:
            # PowerPointサイズを取得（96 DPI基準のカスタムサイズ: 1835×1024 px）
            # PDFの実サイズ（1376×768 pts）を96 DPI基準で変換
            target_size = (
                self.powerpoint_generator.config.width,
                self.powerpoint_generator.config.height,
            )

            suffix = input_path.suffix.lower()

            if suffix == ".pdf":
                # PDFの場合：ページごとにPNGファイルとして保存してから読み込み
                self.logger.info(
                    "loading_pdf",
                    path=str(input_path),
                    dpi=dpi,
                    target_size=target_size,
                )

                # 一時ディレクトリの準備
                if temp_dir is None:
                    temp_dir = input_path.parent / "temp_pdf_pages"
                pdf_pages_dir = temp_dir / "pdf_pages"
                pdf_pages_dir.mkdir(parents=True, exist_ok=True)

                # PDFページをPNGファイルとして保存（PowerPoint 96 DPI基準サイズで直接変換）
                # これにより、座標変換が最小限になり、LLMが正しいサイズで要素を配置できる
                png_paths = await self.image_loader.save_pdf_pages_as_png(
                    input_path, pdf_pages_dir, dpi=dpi, target_size=target_size
                )
                self.logger.info(
                    "pdf_pages_saved_as_png",
                    page_count=len(png_paths),
                    output_dir=str(pdf_pages_dir),
                )

                # 保存したPNGファイルを個別に読み込み、正規化
                images: list[Image.Image] = []
                for png_path in png_paths:
                    self.logger.debug("loading_png_page", path=str(png_path))
                    image = await self.image_loader.load_from_image(png_path)
                    # 画像を正規化（PowerPoint 96 DPI基準サイズに合わせる）
                    # PDFから既に1835×1024 pxで変換されているため、通常はスキップされる
                    normalized_image = self.image_loader.normalize_image(
                        image, target_size=target_size
                    )
                    images.append(normalized_image)

                self.logger.info("pdf_loaded", page_count=len(images))
            else:
                # 画像ファイルの読み込み
                self.logger.info("loading_image", path=str(input_path))
                image = await self.image_loader.load_from_image(input_path)
                # 画像を正規化（PowerPoint 96 DPI基準サイズ: 1835×1024 pxに合わせる）
                normalized_image = self.image_loader.normalize_image(
                    image, target_size=target_size
                )
                images = [normalized_image]
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
        
        重複排除（Inpainting）:
        画像要素内にテキスト要素が含まれている場合、二重表示を防ぐために
        画像側のテキスト領域を背景色で塗りつぶしてから切り出します。

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
            
            # Import TextElement/ImageElement locally to avoid circular imports if any
            from slidemaker.core.models.element import ImageElement, TextElement

            for page_idx, (image, page) in enumerate(zip(images, pages, strict=True)):
                # 1. Collect text regions for masking
                text_regions = []
                for element in page.elements:
                    # Check element type string instead of isinstance to be safe
                    if getattr(element, "element_type", "") == "text":
                        # Use precise coordinates from element (already in pixels)
                        x = int(element.position.x)
                        y = int(element.position.y)
                        w = int(element.size.width)
                        h = int(element.size.height)
                        text_regions.append((x, y, w, h))
                
                self.logger.info(
                    "text_regions_collected",
                    page_idx=page_idx,
                    count=len(text_regions),
                    regions=text_regions[:5] # Log first 5 regions
                )
                
                # 2. Create masked image with auto-sampling
                # auto_sample=True: Sample color from around the text box to avoid "white box" artifacts
                masked_image = self.image_processor.mask_regions(
                    image, 
                    text_regions, 
                    fill_color=(255, 255, 255), # Fallback
                    auto_sample=True
                )

                for elem_idx, element in enumerate(page.elements):
                    if not isinstance(element, ImageElement):
                        continue

                    # 画像要素の切り出し
                    # PageDefinitionのpositionとsizeはスライドピクセル座標
                    # 画像もスライドサイズに正規化されている前提
                    img_width, img_height = masked_image.size
                    slide_width, slide_height = CUSTOM_WIDTH_PX, CUSTOM_HEIGHT_PX

                    # ゼロ除算チェック
                    if img_width == 0 or img_height == 0:
                        self.logger.warning(
                            "Invalid image size (zero dimension), skipping element",
                            page_idx=page_idx,
                            elem_idx=elem_idx,
                            image_size=(img_width, img_height),
                        )
                        continue

                    # スライドピクセル座標を画像ピクセル座標に変換 (1:1 mapping expected)
                    x_px = int(element.position.x * img_width / slide_width)
                    y_px = int(element.position.y * img_height / slide_height)
                    width_px = int(element.size.width * img_width / slide_width)
                    height_px = int(element.size.height * img_height / slide_height)

                    # 画像要素に余白（padding）を追加して広めに切り出す
                    # LLMが過小評価した座標を補正
                    # 特に下部のラベルが見切れるのを防ぐため、下方向のパディングを大きく取る
                    
                    # Horizontal: 30% padding
                    padding_ratio_x = 0.30
                    padding_x = int(width_px * padding_ratio_x)
                    
                    # Vertical: Asymmetric padding (Top 20%, Bottom 50%)
                    padding_top_ratio = 0.20
                    padding_bottom_ratio = 0.50
                    padding_top = int(height_px * padding_top_ratio)
                    padding_bottom = int(height_px * padding_bottom_ratio)

                    # 元の位置を保存（position調整用）
                    original_x_px = x_px
                    original_y_px = y_px

                    # Apply padding (clamp to image boundaries)
                    x_px = max(0, x_px - padding_x)
                    y_px = max(0, y_px - padding_top)
                    
                    # Calculate new width/height ensuring we don't exceed image bounds
                    width_px = min(img_width - x_px, width_px + 2 * padding_x)
                    height_px = min(img_height - y_px, height_px + padding_top + padding_bottom)

                    # paddingによる位置のずれを計算
                    actual_padding_x = original_x_px - x_px
                    actual_padding_y = original_y_px - y_px

                    # bboxの作成（x, y, width, height）
                    bbox = (x_px, y_px, width_px, height_px)

                    # 画像IDの生成
                    image_id = f"page{page_idx}_elem{elem_idx}"

                    # 画像の切り出しと保存
                    try:
                        # 画像の切り出し（synchronous）using masked_image
                        cropped_image = self.image_processor.crop_element(masked_image, bbox)

                        # ファイル名の生成
                        filename = f"{image_id}.png"
                        output_file_path = temp_dir / filename

                        # 画像の保存（synchronous）
                        saved_path = self.image_processor.save_image(
                            cropped_image, str(output_file_path), format="PNG"
                        )

                        # ImageElement.sourceを更新
                        element.source = str(saved_path)

                        # 切り出した画像の実サイズをスライドピクセル座標に逆変換してsizeを更新
                        from slidemaker.core.models.common import Position, Size
                        updated_width = int(width_px * slide_width / img_width)
                        updated_height = int(height_px * slide_height / img_height)
                        element.size = Size(width=updated_width, height=updated_height)

                        # paddingによる位置のずれを補正してpositionを更新
                        adjusted_x = element.position.x - int(actual_padding_x * slide_width / img_width)
                        adjusted_y = element.position.y - int(actual_padding_y * slide_height / img_height)
                        element.position = Position(x=adjusted_x, y=adjusted_y)

                        self.logger.debug(
                            "image_element_processed",
                            image_id=image_id,
                            path=str(saved_path),
                        )
                    except Exception as elem_error:
                        self.logger.warning(
                            "image_element_processing_failed",
                            image_id=image_id,
                            error=str(elem_error),
                        )
                        element.source = ""
                        continue

            # 不正なImageElementをフィルタリング (unchanged)
            # ... (rest of the method)

            for page in pages:
                valid_elements = []
                for element in page.elements:
                    # ImageElementでsourceが空または存在しない場合はスキップ
                    if isinstance(element, ImageElement) and (
                        not element.source or not Path(element.source).exists()
                    ):
                        self.logger.warning(
                            "Skipping ImageElement with invalid source",
                            source=element.source,
                        )
                        continue
                    valid_elements.append(element)
                page.elements = valid_elements

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
