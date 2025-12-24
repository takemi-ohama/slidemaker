"""createコマンドの実装.

MarkdownファイルからPowerPointファイルを生成するコマンドを提供します。
"""

# ruff: noqa: B008  # Typerの関数呼び出しはデフォルト引数として正常なパターン

import asyncio
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import structlog
import typer

from slidemaker.cli.config import ConfigManager
from slidemaker.cli.output import OutputFormatter
from slidemaker.llm.manager import LLMManager
from slidemaker.utils.file_manager import FileManager
from slidemaker.workflows.new_slide import NewSlideWorkflow

logger = structlog.get_logger(__name__)


def create(
    input_markdown: Path = typer.Argument(
        ...,
        help="Input Markdown file",
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
    theme: str | None = typer.Option(None, "--theme", help="Theme name"),
    generate_images: bool = typer.Option(
        False, "--generate-images", help="Generate images using LLM"
    ),
    slide_size: str = typer.Option(
        "16:9", "--slide-size", help="Slide size (16:9 or 4:3)"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Preview without generating (output JSON only)"
    ),
) -> None:
    """Create PowerPoint from Markdown file.

    Examples:
        # 基本的な使用法
        $ slidemaker create presentation.md

        # 出力パスを指定
        $ slidemaker create presentation.md -o output.pptx

        # テーマと画像生成を有効化
        $ slidemaker create presentation.md --theme corporate --generate-images

        # ドライランモード（JSON出力のみ）
        $ slidemaker create presentation.md --dry-run
    """
    asyncio.run(_create_async(
        input_markdown=input_markdown,
        output=output,
        config=config,
        verbose=verbose,
        theme=theme,
        generate_images=generate_images,
        slide_size=slide_size,
        dry_run=dry_run,
    ))


async def _create_async(
    input_markdown: Path,
    output: Path | None,
    config: Path | None,
    verbose: bool,
    theme: str | None,
    generate_images: bool,
    slide_size: str,
    dry_run: bool,
) -> None:
    """createコマンドの非同期実装.

    Args:
        input_markdown: 入力Markdownファイルパス
        output: 出力PowerPointファイルパス（Noneの場合は自動生成）
        config: 設定ファイルパス
        verbose: 詳細ログ表示
        theme: テーマ名
        generate_images: 画像生成を実行するか
        slide_size: スライドサイズ（"16:9" または "4:3"）
        dry_run: ドライランモード

    Raises:
        typer.Exit: エラー発生時
    """
    formatter = OutputFormatter(verbose=verbose)

    # ヘッダー表示
    formatter.print_header()

    try:
        # 入力ファイルのバリデーション
        _validate_input_file(input_markdown)

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
            output = _generate_output_path(input_markdown, file_manager, output_base_dir)
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

        # ドライランモードの場合はJSON出力のみ
        if dry_run:
            formatter.print_info("Dry run mode: skipping PowerPoint generation")
            # TODO: JSON出力を実装（Phase 3のCompositionParserから取得）
            formatter.print_warning("Dry run mode not fully implemented yet")
            raise typer.Exit(0)

        # LLMManagerの初期化
        llm_manager = LLMManager(
            composition_config=app_config.llm["composition"],
            image_generation_config=app_config.llm.get("image_generation"),
        )

        # NewSlideWorkflowの初期化
        workflow = NewSlideWorkflow(
            llm_manager=llm_manager,
            file_manager=file_manager,
        )

        # 進捗表示
        with formatter.create_progress() as progress:
            task = progress.add_task(
                "[cyan]Creating PowerPoint...",
                total=3,
            )

            # Step 1: Markdown解析
            progress.update(task, description="[cyan]Parsing Markdown...")
            if verbose:
                formatter.print_debug(f"Reading {input_markdown}")
            progress.advance(task)

            # Step 2: LLM構成生成
            progress.update(task, description="[cyan]Generating composition...")
            if verbose:
                formatter.print_debug("Calling LLM for composition generation")
            # ここではprogressを進めず、workflow内部で進める

            # Step 3: PowerPoint生成
            # workflowオプションの構築
            workflow_options: dict[str, Any] = {
                "generate_images": generate_images,
                "slide_size": slide_size,
            }
            if theme is not None:
                workflow_options["theme"] = theme

            # ワークフロー実行
            try:
                result_path = await workflow.execute(
                    input_data=input_markdown,
                    output_path=output,
                    **workflow_options,
                )
                progress.update(task, description="[green]✓ PowerPoint created")
                progress.advance(task)
            except Exception as e:
                progress.update(task, description="[red]✗ Failed")
                raise e

        # 成功メッセージ
        formatter.print_success(
            "PowerPoint created successfully",
            details={"file": result_path},
        )

    except typer.Exit:
        # typer.Exitは再raiseする（Exit code 0の場合もある）
        raise

    except FileNotFoundError as e:
        formatter.print_error("Input file not found", error=e)
        logger.error("file_not_found", error=str(e))
        raise typer.Exit(1) from e

    except ValueError as e:
        formatter.print_error("Validation error", error=e)
        logger.error("validation_error", error=str(e))
        raise typer.Exit(1) from e

    except Exception as e:
        formatter.print_error("Failed to create PowerPoint", error=e, show_traceback=True)
        logger.exception("create_command_failed", error=str(e))
        raise typer.Exit(1) from e


def _validate_input_file(input_markdown: Path, max_size_mb: int = 50) -> None:
    """入力ファイルのバリデーション.

    Args:
        input_markdown: 入力Markdownファイルパス
        max_size_mb: 最大ファイルサイズ（MB）

    Raises:
        FileNotFoundError: ファイルが存在しない場合
        ValueError: ファイルが無効な場合
    """
    # ファイルの存在確認（Typerがチェック済みだが念のため）
    if not input_markdown.exists():
        raise FileNotFoundError(f"Input file not found: {input_markdown}")

    if not input_markdown.is_file():
        raise ValueError(f"Not a file: {input_markdown}")

    # ファイルサイズチェック（DoS攻撃防止）
    file_size_mb = input_markdown.stat().st_size / (1024 * 1024)
    if file_size_mb > max_size_mb:
        raise ValueError(
            f"File too large: {file_size_mb:.2f}MB (max: {max_size_mb}MB)"
        )

    # 拡張子チェック
    valid_extensions = {".md", ".markdown"}
    if input_markdown.suffix.lower() not in valid_extensions:
        raise ValueError(
            f"Invalid file extension: {input_markdown.suffix}. "
            f"Allowed: {', '.join(valid_extensions)}"
        )

    # パストラバーサル対策: 絶対パスに解決
    try:
        resolved_path = input_markdown.resolve(strict=True)
        # resolved_pathが実際に存在することを確認
        if not resolved_path.is_file():
            raise ValueError(f"Path is not a file: {input_markdown}")
    except (OSError, RuntimeError) as e:
        raise ValueError(f"Invalid file path: {e}") from e


def _generate_output_path(
    input_markdown: Path,
    file_manager: FileManager,
    output_base_dir: Path,
) -> Path:
    """出力パスの安全な生成.

    入力ファイル名とタイムスタンプから、FileManagerで検証済みの
    出力パスを生成します。

    Args:
        input_markdown: 入力Markdownファイルパス
        file_manager: FileManagerインスタンス（検証用）
        output_base_dir: 出力ベースディレクトリ（FileManagerから取得）

    Returns:
        Path: 検証済みの出力PowerPointファイルパス

    Raises:
        ValueError: パス検証失敗時
    """
    # ファイル名からタイトルを取得（拡張子を除く）
    title = input_markdown.stem

    # タイムスタンプを生成
    timestamp = datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S")

    # 出力ファイル名の生成
    output_filename = f"{title}_{timestamp}.pptx"

    # FileManager経由で検証済みのパスを取得
    output_path = output_base_dir / output_filename

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
