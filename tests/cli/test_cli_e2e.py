"""End-to-End tests for CLI commands.

このモジュールは、CLIコマンドのエンドツーエンドテストを提供します。
実際のワークフローを実行し、PowerPointファイルの生成を確認します。

Note:
    これらのテストはLLM APIを使用するため、環境変数が設定されている場合にのみ実行されます。
    環境変数が未設定の場合、テストはスキップされます。
"""

import os
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest
from typer.testing import CliRunner

from slidemaker.cli.main import app


@pytest.fixture
def runner() -> CliRunner:
    """Create a CLI test runner.

    Returns:
        CliRunner: Typer CLI test runner instance
    """
    return CliRunner()


@pytest.fixture
def temp_dir() -> Generator[Path]:
    """Create a temporary directory for tests.

    Yields:
        Path: Temporary directory path
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_markdown_file(temp_dir: Path) -> Path:
    """Create a sample Markdown file for testing.

    Args:
        temp_dir: Temporary directory

    Returns:
        Path: Sample Markdown file path
    """
    md_file = temp_dir / "test_presentation.md"
    content = """# Test Presentation

## Slide 1: Introduction
- Welcome to the test presentation
- This is an automated test

## Slide 2: Key Points
- Point 1: Testing is important
- Point 2: Automation saves time
- Point 3: Quality matters

## Slide 3: Conclusion
- Thank you for your attention
"""
    md_file.write_text(content, encoding="utf-8")
    return md_file


@pytest.fixture
def sample_pdf_file(temp_dir: Path) -> Path:
    """Create a dummy PDF file for testing.

    Note:
        これは実際のPDFファイルではなく、ダミーコンテンツです。
        実際のPDF変換テストは、PDFライブラリが利用可能な場合にのみ実行されます。

    Args:
        temp_dir: Temporary directory

    Returns:
        Path: Sample PDF file path
    """
    pdf_file = temp_dir / "test.pdf"
    pdf_file.write_text("Dummy PDF content", encoding="utf-8")
    return pdf_file


@pytest.fixture
def sample_image_file(temp_dir: Path) -> Path:
    """Create a dummy image file for testing.

    Args:
        temp_dir: Temporary directory

    Returns:
        Path: Sample image file path
    """
    img_file = temp_dir / "test.png"
    img_file.write_text("Dummy PNG content", encoding="utf-8")
    return img_file


@pytest.fixture
def config_file(temp_dir: Path) -> Path:
    """Create a test configuration file.

    Args:
        temp_dir: Temporary directory

    Returns:
        Path: Configuration file path
    """
    config_path = temp_dir / "config.yaml"
    config_content = f"""llm:
  composition:
    type: api
    provider: claude
    model: claude-3-5-sonnet-20241022
    api_key: ${{ANTHROPIC_API_KEY}}

output:
  directory: {temp_dir / "output"}
  temp_directory: {temp_dir / "tmp"}
  keep_temp: false

slide:
  default_size: "16:9"
  default_theme: "minimal"
  default_font: "Arial"

logging:
  level: INFO
  format: text
"""
    config_path.write_text(config_content, encoding="utf-8")
    return config_path


# LLM APIキーの存在確認
has_anthropic_key = os.getenv("ANTHROPIC_API_KEY") is not None
has_openai_key = os.getenv("OPENAI_API_KEY") is not None
has_google_key = os.getenv("GOOGLE_API_KEY") is not None

skip_without_llm = pytest.mark.skipif(
    not (has_anthropic_key or has_openai_key or has_google_key),
    reason="LLM API key not found in environment",
)


class TestCreateCommandE2E:
    """End-to-End tests for create command."""

    @skip_without_llm
    def test_create_command_end_to_end(
        self, runner: CliRunner, sample_markdown_file: Path, temp_dir: Path
    ) -> None:
        """Test complete create command execution with actual workflow.

        このテストは実際のLLM APIを使用してMarkdownからPowerPointを生成します。

        Note:
            E2Eテストでは、プロジェクトディレクトリ内の./outputに出力します。
            これはFileManagerのパストラバーサル防止機能により、
            一時ディレクトリへの出力が拒否されるためです。

        Args:
            runner: CLI test runner
            sample_markdown_file: Sample Markdown input file
            temp_dir: Temporary directory for output
        """
        # プロジェクトディレクトリ内のoutputディレクトリを使用
        project_output_dir = Path("output") / "test_e2e"
        project_output_dir.mkdir(parents=True, exist_ok=True)
        output_file = project_output_dir / "test_output.pptx"

        # createコマンド実行（画像生成はデフォルトでFalse）
        result = runner.invoke(
            app,
            [
                "create",
                str(sample_markdown_file),
                "--output",
                str(output_file),
            ],
        )

        # 結果確認
        assert result.exit_code == 0, f"Command failed: {result.stdout}"
        assert output_file.exists(), "Output PowerPoint file not created"
        assert output_file.stat().st_size > 0, "Output file is empty"

        # クリーンアップ
        if output_file.exists():
            output_file.unlink()

    @skip_without_llm
    def test_create_with_config_file(
        self,
        runner: CliRunner,
        sample_markdown_file: Path,
        temp_dir: Path,
    ) -> None:
        """Test create command with configuration file.

        設定ファイルを使用してcreateコマンドを実行します。

        Note:
            E2Eテストでは、プロジェクトディレクトリ内に設定ファイルと出力を作成します。

        Args:
            runner: CLI test runner
            sample_markdown_file: Sample Markdown input file
            temp_dir: Temporary directory (unused, for consistency)
        """
        # プロジェクトディレクトリ内に設定ファイルを作成
        project_output_dir = Path("output") / "test_e2e"
        project_output_dir.mkdir(parents=True, exist_ok=True)
        config_path = project_output_dir / "test_config.yaml"

        config_content = f"""llm:
  composition:
    type: api
    provider: claude
    model: claude-3-5-sonnet-20241022
    api_key: ${{ANTHROPIC_API_KEY}}

output:
  directory: {project_output_dir.absolute()}
  temp_directory: {project_output_dir.absolute() / "tmp"}
  keep_temp: false

slide:
  default_size: "16:9"
  default_theme: "minimal"
  default_font: "Arial"

logging:
  level: INFO
  format: text
"""
        config_path.write_text(config_content, encoding="utf-8")

        # createコマンド実行（設定ファイル指定、画像生成はデフォルトでFalse）
        result = runner.invoke(
            app,
            [
                "create",
                str(sample_markdown_file),
                "--config",
                str(config_path),
            ],
        )

        # 結果確認
        assert result.exit_code == 0, f"Command failed: {result.stdout}"

        # 出力ディレクトリ内にPowerPointファイルが生成されたことを確認
        pptx_files = list(project_output_dir.glob("*.pptx"))
        assert len(pptx_files) > 0, "No PowerPoint file created"
        assert pptx_files[0].stat().st_size > 0, "Output file is empty"

        # クリーンアップ
        for pptx_file in pptx_files:
            pptx_file.unlink()
        config_path.unlink()

    def test_create_command_error_handling(
        self, runner: CliRunner, temp_dir: Path
    ) -> None:
        """Test create command error handling with non-existent file.

        存在しないファイルを指定した場合のエラーハンドリングをテストします。

        Args:
            runner: CLI test runner
            temp_dir: Temporary directory
        """
        non_existent = temp_dir / "nonexistent.md"

        # createコマンド実行（存在しないファイル）
        result = runner.invoke(
            app,
            [
                "create",
                str(non_existent),
            ],
        )

        # エラーで終了することを確認
        assert result.exit_code != 0, "Command should fail with non-existent file"
        # エラーメッセージはstderrに出力される
        error_output = result.stderr if result.stderr else result.stdout
        assert (
            "does not exist" in error_output.lower()
            or "not found" in error_output.lower()
        ), f"Error message not found. stderr: {result.stderr}, stdout: {result.stdout}"


class TestConvertCommandE2E:
    """End-to-End tests for convert command."""

    @pytest.mark.skip(reason="ConversionWorkflow not yet implemented (Phase 4)")
    def test_convert_command_end_to_end_pdf(
        self, runner: CliRunner, sample_pdf_file: Path, temp_dir: Path
    ) -> None:
        """Test complete convert command execution with PDF input.

        Note:
            このテストはPhase 4のConversionWorkflow実装後に有効化されます。

        Args:
            runner: CLI test runner
            sample_pdf_file: Sample PDF input file
            temp_dir: Temporary directory for output
        """
        output_file = temp_dir / "converted.pptx"

        # convertコマンド実行
        result = runner.invoke(
            app,
            [
                "convert",
                str(sample_pdf_file),
                "--output",
                str(output_file),
            ],
        )

        # 結果確認
        assert result.exit_code == 0, f"Command failed: {result.stdout}"
        assert output_file.exists(), "Output PowerPoint file not created"
        assert output_file.stat().st_size > 0, "Output file is empty"

    @pytest.mark.skip(reason="ConversionWorkflow not yet implemented (Phase 4)")
    def test_convert_command_end_to_end_image(
        self, runner: CliRunner, sample_image_file: Path, temp_dir: Path
    ) -> None:
        """Test complete convert command execution with image input.

        Note:
            このテストはPhase 4のConversionWorkflow実装後に有効化されます。

        Args:
            runner: CLI test runner
            sample_image_file: Sample image input file
            temp_dir: Temporary directory for output
        """
        output_file = temp_dir / "converted.pptx"

        # convertコマンド実行
        result = runner.invoke(
            app,
            [
                "convert",
                str(sample_image_file),
                "--output",
                str(output_file),
            ],
        )

        # 結果確認
        assert result.exit_code == 0, f"Command failed: {result.stdout}"
        assert output_file.exists(), "Output PowerPoint file not created"
        assert output_file.stat().st_size > 0, "Output file is empty"

    def test_convert_command_error_handling(
        self, runner: CliRunner, temp_dir: Path
    ) -> None:
        """Test convert command error handling with invalid file.

        不正なファイル形式を指定した場合のエラーハンドリングをテストします。

        Args:
            runner: CLI test runner
            temp_dir: Temporary directory
        """
        # 不正な拡張子のファイル
        invalid_file = temp_dir / "test.txt"
        invalid_file.write_text("Invalid content", encoding="utf-8")

        # convertコマンド実行
        result = runner.invoke(
            app,
            [
                "convert",
                str(invalid_file),
            ],
        )

        # エラーで終了することを確認
        assert result.exit_code != 0, "Command should fail with invalid file type"


class TestVersionCommand:
    """Tests for version command."""

    def test_version_command(self, runner: CliRunner) -> None:
        """Test version command execution.

        バージョン情報が正しく表示されることを確認します。

        Args:
            runner: CLI test runner
        """
        result = runner.invoke(app, ["version"])

        # 正常終了
        assert result.exit_code == 0

        # バージョン情報が含まれる
        assert "slidemaker version" in result.stdout.lower()


class TestHelpCommands:
    """Tests for help messages."""

    def test_help_command(self, runner: CliRunner) -> None:
        """Test main help message display.

        メインのヘルプメッセージが表示されることを確認します。

        Args:
            runner: CLI test runner
        """
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "slidemaker" in result.stdout.lower()
        assert "AI-powered PowerPoint generator" in result.stdout
        assert "create" in result.stdout
        assert "convert" in result.stdout
        assert "version" in result.stdout

    def test_create_help_command(self, runner: CliRunner) -> None:
        """Test create command help message.

        createコマンドのヘルプメッセージが表示されることを確認します。

        Args:
            runner: CLI test runner
        """
        result = runner.invoke(app, ["create", "--help"])

        assert result.exit_code == 0
        assert "create" in result.stdout.lower()
        assert "markdown" in result.stdout.lower()
        # オプションの確認
        assert "--output" in result.stdout
        assert "--config" in result.stdout
        assert "--theme" in result.stdout
        assert "--slide-size" in result.stdout

    def test_convert_help_command(self, runner: CliRunner) -> None:
        """Test convert command help message.

        convertコマンドのヘルプメッセージが表示されることを確認します。

        Args:
            runner: CLI test runner
        """
        result = runner.invoke(app, ["convert", "--help"])

        assert result.exit_code == 0
        assert "convert" in result.stdout.lower()
        # オプションの確認
        assert "--output" in result.stdout
        assert "--config" in result.stdout
        assert "--dpi" in result.stdout
        assert "--max-concurrent" in result.stdout


class TestCLIIntegration:
    """Integration tests for CLI commands."""

    def test_invalid_command(self, runner: CliRunner) -> None:
        """Test CLI behavior with invalid command.

        無効なコマンドを指定した場合のエラー表示を確認します。

        Args:
            runner: CLI test runner
        """
        result = runner.invoke(app, ["invalid-command"])

        # エラーで終了
        assert result.exit_code != 0

    def test_no_args_shows_help(self, runner: CliRunner) -> None:
        """Test that running with no args shows help message.

        引数なしで実行した場合にヘルプが表示されることを確認します。

        Args:
            runner: CLI test runner
        """
        result = runner.invoke(app, [])

        # no_args_is_help=Trueのため、helpが表示される
        assert "slidemaker" in result.stdout.lower() or "usage" in result.stdout.lower()

    @skip_without_llm
    def test_create_with_minimal_options(
        self, runner: CliRunner, sample_markdown_file: Path, temp_dir: Path
    ) -> None:
        """Test create command with minimal required options.

        最小限のオプションでcreateコマンドを実行します。

        Note:
            E2Eテストでは、プロジェクトディレクトリ内の./outputに出力します。

        Args:
            runner: CLI test runner
            sample_markdown_file: Sample Markdown input file
            temp_dir: Temporary directory (unused, for consistency)
        """
        # プロジェクトディレクトリ内のoutputディレクトリを使用
        project_output_dir = Path("output") / "test_e2e"
        project_output_dir.mkdir(parents=True, exist_ok=True)
        output_file = project_output_dir / "minimal_test_output.pptx"

        # 最小限のオプション（入力ファイルのみ、画像生成はデフォルトでFalse）
        result = runner.invoke(
            app,
            [
                "create",
                str(sample_markdown_file),
                "--output",
                str(output_file),
            ],
        )

        # 正常終了することを確認
        assert result.exit_code == 0, f"Command failed: {result.stdout}\nStderr: {result.stderr}"

        # クリーンアップ
        if output_file.exists():
            output_file.unlink()

    def test_create_with_invalid_slide_size(
        self, runner: CliRunner, sample_markdown_file: Path
    ) -> None:
        """Test create command with invalid slide size option.

        不正なスライドサイズを指定した場合のエラーを確認します。

        Args:
            runner: CLI test runner
            sample_markdown_file: Sample Markdown input file
        """
        result = runner.invoke(
            app,
            [
                "create",
                str(sample_markdown_file),
                "--slide-size",
                "invalid-size",
            ],
        )

        # エラーで終了（Typerがオプション検証を行う）
        assert result.exit_code != 0
