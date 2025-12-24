"""convert command for CLI.

PDF/画像ファイルからPowerPointファイルを生成します。
"""

import asyncio
from pathlib import Path
from typing import Any

import typer

from slidemaker.cli.config import ConfigManager
from slidemaker.cli.output import OutputFormatter
from slidemaker.core.models.common import SlideSize
from slidemaker.core.models.slide_config import SlideConfig
from slidemaker.image_processing import ImageAnalyzer, ImageLoader, ImageProcessor
from slidemaker.llm.manager import LLMManager
from slidemaker.pptx.generator import PowerPointGenerator
from slidemaker.utils.file_manager import FileManager
from slidemaker.utils.logger import get_logger
from slidemaker.workflows.conversion import ConversionWorkflow

logger = get_logger(__name__)

# サポートされるファイル拡張子
SUPPORTED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".bmp"}


def convert(
    input_file: Path = typer.Argument(
        ...,
        help="Input PDF or image file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    output: Path | None = typer.Option(
        None, "--output", "-o", help="Output PowerPoint file path"
    ),
    config: Path | None = typer.Option(
        None, "--config", "-c", help="Config file path"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    dpi: int = typer.Option(300, "--dpi", help="PDF resolution (DPI)", min=72, max=600),
    max_concurrent: int = typer.Option(
        3, "--max-concurrent", help="Maximum concurrent analysis", min=1, max=10
    ),
    slide_size: str = typer.Option(
        "16:9", "--slide-size", help="Slide size (16:9 or 4:3)"
    ),
    analyze_only: bool = typer.Option(
        False, "--analyze-only", help="Analyze without converting (output JSON only)"
    ),
) -> None:
    """Convert PDF/image to PowerPoint file.

    Examples:
        # 基本的な使用法
        $ slidemaker convert document.pdf

        # 出力パスを指定
        $ slidemaker convert document.pdf -o output.pptx

        # DPIと並列数を指定
        $ slidemaker convert document.pdf --dpi 300 --max-concurrent 5

        # 分析のみモード（JSON出力）
        $ slidemaker convert document.pdf --analyze-only
    """
    asyncio.run(
        _convert_async(
            input_file=input_file,
            output=output,
            config=config,
            verbose=verbose,
            dpi=dpi,
            max_concurrent=max_concurrent,
            slide_size=slide_size,
            analyze_only=analyze_only,
        )
    )


async def _convert_async(
    input_file: Path,
    output: Path | None,
    config: Path | None,
    verbose: bool,
    dpi: int,
    max_concurrent: int,
    slide_size: str,
    analyze_only: bool,
) -> None:
    """convertコマンドの非同期実装.

    Args:
        input_file: 入力PDF/画像ファイルパス
        output: 出力PowerPointファイルパス（Noneの場合は自動生成）
        config: 設定ファイルパス
        verbose: 詳細ログ表示
        dpi: PDF解像度
        max_concurrent: 最大並列分析数
        slide_size: スライドサイズ（"16:9" または "4:3"）
        analyze_only: 分析のみモード

    Raises:
        typer.Exit: エラー発生時
    """
    formatter = OutputFormatter(verbose=verbose)

    # ヘッダー表示
    formatter.print_header()

    try:
        # 入力ファイルのバリデーション
        _validate_input_file(input_file)

        # 設定読み込み
        config_manager = ConfigManager(strict_env=False)
        app_config = config_manager.load_app_config(config_path=config)

        if verbose:
            formatter.print_debug("Configuration loaded successfully")

        # FileManagerの初期化（出力パス決定前に必要）
        output_base_dir = Path(app_config.output.directory)
        file_manager = FileManager(
            output_base_dir=output_base_dir,
        )

        # 出力パスの決定
        if output is None:
            output = _generate_output_path(input_file, file_manager, output_base_dir)
        else:
            # ユーザー指定パスの場合も検証
            try:
                output.resolve().relative_to(output_base_dir.resolve())
            except ValueError as e:
                raise ValueError(
                    f"Output path outside allowed directory: {output}"
                ) from e

        if verbose:
            formatter.print_info(f"Output path: {output}")

        # 分析のみモードの場合はJSON出力のみ
        if analyze_only:
            formatter.print_info("Analyze-only mode: skipping PowerPoint generation")
            formatter.print_warning("Analyze-only mode not fully implemented yet")
            raise typer.Exit(0)

        # LLMManagerとFileManagerの初期化
        # composition_configは必須なので、デフォルト設定を使用
        composition_config = app_config.llm.get("composition")
        if composition_config is None:
            raise ValueError("LLM composition config is required")

        llm_manager = LLMManager(
            composition_config=composition_config,
            image_generation_config=app_config.llm.get("image_generation"),
        )

        # Image処理コンポーネントの初期化
        image_loader = ImageLoader(file_manager=file_manager)
        image_analyzer = ImageAnalyzer(llm_manager=llm_manager)
        image_processor = ImageProcessor(file_manager=file_manager)

        # SlideConfigの作成
        slide_size_enum = (
            SlideSize.WIDESCREEN_16_9 if slide_size == "16:9" else SlideSize.STANDARD_4_3
        )
        slide_config = SlideConfig(size=slide_size_enum)
        powerpoint_generator = PowerPointGenerator(config=slide_config)

        # ConversionWorkflowの初期化
        workflow = ConversionWorkflow(
            llm_manager=llm_manager,
            file_manager=file_manager,
            image_loader=image_loader,
            image_analyzer=image_analyzer,
            image_processor=image_processor,
            powerpoint_generator=powerpoint_generator,
        )

        # 進捗表示
        with formatter.create_progress() as progress:
            task = progress.add_task(
                "[cyan]Converting to PowerPoint...",
                total=4,
            )

            # Step 1: 画像読み込み
            progress.update(task, description="[cyan]Loading images...")
            if verbose:
                formatter.print_debug(f"Reading {input_file}")
            progress.advance(task)

            # Step 2: 画像分析
            progress.update(task, description="[cyan]Analyzing images...")
            if verbose:
                formatter.print_debug("Analyzing images with LLM")

            # Step 3: 画像処理
            # Step 4: PowerPoint生成
            # workflowオプションの構築
            workflow_options: dict[str, Any] = {
                "dpi": dpi,
                "max_concurrent": max_concurrent,
                "slide_size": slide_size,
            }

            # ワークフロー実行
            try:
                result_path = await workflow.execute(
                    input_data=input_file,
                    output_path=output,
                    **workflow_options,
                )
                progress.update(task, completed=4, description="[green]✓ PowerPoint created")
            except Exception as e:
                progress.update(task, description="[red]✗ Failed")
                raise e

        # 成功メッセージ
        formatter.print_success(
            "PowerPoint created successfully",
            details={"file": result_path},
        )

    except FileNotFoundError as e:
        formatter.print_error("Input file not found", error=e)
        logger.error("file_not_found", error=str(e))
        raise typer.Exit(1) from e

    except ValueError as e:
        formatter.print_error("Validation error", error=e)
        logger.error("validation_error", error=str(e))
        raise typer.Exit(1) from e

    except Exception as e:
        formatter.print_error(
            "Failed to convert to PowerPoint", error=e, show_traceback=True
        )
        logger.exception("convert_command_failed", error=str(e))
        raise typer.Exit(1) from e


def _validate_input_file(file_path: Path, max_size_mb: int = 50) -> None:
    """入力ファイルのバリデーション.

    Args:
        file_path: 入力ファイルパス
        max_size_mb: 最大ファイルサイズ（MB）

    Raises:
        FileNotFoundError: ファイルが存在しない
        ValueError: ファイル形式が無効
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")

    if not file_path.is_file():
        raise ValueError(f"Input path is not a file: {file_path}")

    # ファイルサイズチェック（DoS攻撃防止）
    file_size_mb = file_path.stat().st_size / (1024 * 1024)
    if file_size_mb > max_size_mb:
        raise ValueError(
            f"File too large: {file_size_mb:.2f}MB (max: {max_size_mb}MB)"
        )

    # 拡張子のチェック
    ext = file_path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise ValueError(
            f"Unsupported file type: {ext}. Supported: {supported}"
        )


def _generate_output_path(
    input_file: Path,
    file_manager: FileManager,
    output_base_dir: Path,
) -> Path:
    """出力ファイルパスの安全な生成.

    Args:
        input_file: 入力ファイルパス
        file_manager: FileManagerインスタンス（検証用）
        output_base_dir: 出力ベースディレクトリ（FileManagerから取得）

    Returns:
        Path: 検証済みの出力パス

    Raises:
        ValueError: パス検証失敗時
    """
    # ファイル名: <input_name>_converted.pptx
    output_name = f"{input_file.stem}_converted.pptx"

    # FileManager経由で検証済みのパスを取得
    output_path = output_base_dir / output_name

    # パストラバーサル対策: output_base_dir内に含まれることを確認
    try:
        output_path.resolve().relative_to(output_base_dir.resolve())
    except ValueError as e:
        raise ValueError(
            f"Output path outside allowed directory: {output_path}"
        ) from e

    # 出力ディレクトリの作成
    output_base_dir.mkdir(parents=True, exist_ok=True)

    return output_path
