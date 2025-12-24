"""Tests for create command."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import typer

from slidemaker.cli.commands.create import (
    _generate_output_path,
    _validate_input_file,
    create,
)


class TestValidateInputFile:
    """Tests for _validate_input_file function."""

    def test_validate_input_file_success(self, tmp_path):
        """Test validation with a valid Markdown file."""
        # 正常なMarkdownファイルを作成
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test Markdown\n\nThis is a test.")

        # 例外が発生しないことを確認
        _validate_input_file(md_file)

    def test_validate_input_file_not_found(self, tmp_path):
        """Test validation fails when file does not exist."""
        # 存在しないファイル
        non_existent = tmp_path / "nonexistent.md"

        with pytest.raises(FileNotFoundError) as exc_info:
            _validate_input_file(non_existent)

        assert "not found" in str(exc_info.value).lower()
        assert str(non_existent) in str(exc_info.value)

    def test_validate_input_file_invalid_extension(self, tmp_path):
        """Test validation fails with invalid file extension."""
        # 不正な拡張子のファイル
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("This is a text file")

        with pytest.raises(ValueError) as exc_info:
            _validate_input_file(txt_file)

        assert "invalid file extension" in str(exc_info.value).lower()
        assert ".txt" in str(exc_info.value)

    def test_validate_input_file_size_limit(self, tmp_path):
        """Test validation fails when file exceeds size limit."""
        # サイズ制限を超えるファイルを作成（51MB相当のダミーデータ）
        large_file = tmp_path / "large.md"
        large_content = "# Large File\n\n" + ("x" * 1024 * 1024 * 51)  # 51MB
        large_file.write_text(large_content)

        with pytest.raises(ValueError) as exc_info:
            _validate_input_file(large_file, max_size_mb=50)

        assert "too large" in str(exc_info.value).lower()
        assert "50mb" in str(exc_info.value).lower()

    def test_validate_input_file_directory(self, tmp_path):
        """Test validation fails when path is a directory."""
        # ディレクトリを渡す
        with pytest.raises(ValueError) as exc_info:
            _validate_input_file(tmp_path)

        assert "not a file" in str(exc_info.value).lower()

    def test_validate_input_file_markdown_extension(self, tmp_path):
        """Test validation succeeds with .markdown extension."""
        # .markdown拡張子のファイル
        md_file = tmp_path / "test.markdown"
        md_file.write_text("# Test Markdown\n\nContent")

        # 例外が発生しないことを確認
        _validate_input_file(md_file)

    def test_validate_input_file_path_traversal_attack(self, tmp_path):
        """Test validation handles path traversal attempts safely."""
        # パストラバーサル対策のテスト
        # 実際の攻撃シナリオではなく、resolve()が正常に動作することを確認
        md_file = tmp_path / "subdir" / ".." / "test.md"
        md_file.parent.mkdir(parents=True, exist_ok=True)
        md_file.write_text("# Test")

        # 例外が発生しないことを確認
        _validate_input_file(md_file)


class TestGenerateOutputPath:
    """Tests for _generate_output_path function."""

    def test_generate_output_path_default(self, tmp_path):
        """Test output path generation with default settings."""
        from slidemaker.utils.file_manager import FileManager

        # テスト用の入力ファイル
        input_file = tmp_path / "presentation.md"
        input_file.write_text("# Test")

        # FileManager作成
        output_base_dir = tmp_path / "output"
        file_manager = FileManager(output_base_dir=str(output_base_dir))

        # 出力パス生成
        output_path = _generate_output_path(input_file, file_manager, output_base_dir)

        # 検証
        assert output_path.parent == output_base_dir
        assert output_path.name.startswith("presentation_")
        assert output_path.suffix == ".pptx"
        assert output_base_dir.exists()

    def test_generate_output_path_timestamp_format(self, tmp_path):
        """Test output path includes properly formatted timestamp."""
        from slidemaker.utils.file_manager import FileManager

        input_file = tmp_path / "test.md"
        input_file.write_text("# Test")

        output_base_dir = tmp_path / "output"
        file_manager = FileManager(output_base_dir=str(output_base_dir))

        with patch("slidemaker.cli.commands.create.datetime") as mock_datetime:
            # タイムスタンプを固定
            mock_datetime.now.return_value.strftime.return_value = "20250101_120000"

            output_path = _generate_output_path(input_file, file_manager, output_base_dir)

            # タイムスタンプが含まれることを確認
            assert "20250101_120000" in output_path.name
            assert output_path.name == "test_20250101_120000.pptx"

    def test_generate_output_path_path_traversal(self, tmp_path):
        """Test output path generation prevents path traversal."""
        from slidemaker.utils.file_manager import FileManager

        # パストラバーサルを試みる入力（ファイル名に..を含む）
        input_file = tmp_path / "..malicious.md"
        input_file.write_text("# Test")

        output_base_dir = tmp_path / "output"
        file_manager = FileManager(output_base_dir=str(output_base_dir))

        # 出力パスは安全に生成されるべき
        output_path = _generate_output_path(input_file, file_manager, output_base_dir)

        # output_base_dir内に含まれることを確認
        assert output_path.resolve().is_relative_to(output_base_dir.resolve())


class TestCreateCommand:
    """Tests for create command."""

    @pytest.fixture
    def mock_llm_manager(self):
        """Create a mock LLM manager."""
        manager = MagicMock()
        manager.generate_structured = AsyncMock(
            return_value={
                "slide_config": {"size": "16:9", "theme": "default"},
                "pages": [
                    {
                        "title": "Test Slide",
                        "elements": [
                            {
                                "type": "text",
                                "position": {"x": 100, "y": 100},
                                "size": {"width": 800, "height": 50},
                                "content": "Test content",
                            }
                        ],
                    }
                ],
            }
        )
        return manager

    @pytest.fixture
    def sample_markdown(self, tmp_path):
        """Create a sample Markdown file."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test Presentation\n\nThis is a test.")
        return md_file

    @pytest.fixture
    def mock_workflow(self):
        """Create a mock NewSlideWorkflow."""
        workflow = MagicMock()
        workflow.execute = AsyncMock(return_value=Path("output.pptx"))
        return workflow

    def test_create_command_success(self, tmp_path, sample_markdown, mock_workflow):
        """Test successful execution of create command."""
        output_dir = tmp_path / "output"
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / "test.pptx"

        with patch("slidemaker.cli.commands.create.ConfigManager") as mock_config_cls, \
             patch("slidemaker.cli.commands.create.LLMManager") as mock_llm_cls, \
             patch("slidemaker.cli.commands.create.FileManager") as mock_file_mgr_cls, \
             patch("slidemaker.cli.commands.create.NewSlideWorkflow") as mock_workflow_cls:

            # ConfigManagerのモック
            mock_config = MagicMock()
            mock_config.load_app_config.return_value.output.directory = str(output_dir)
            mock_config.load_app_config.return_value.llm = {
                "composition": {"type": "api", "provider": "claude"}
            }
            mock_config_cls.return_value = mock_config

            # LLMManagerのモック
            mock_llm = MagicMock()
            mock_llm_cls.return_value = mock_llm

            # FileManagerのモック
            mock_file_mgr = MagicMock()
            mock_file_mgr_cls.return_value = mock_file_mgr

            # NewSlideWorkflowのモック
            mock_workflow.execute.return_value = output_file
            mock_workflow_cls.return_value = mock_workflow

            # createコマンド実行
            try:
                create(
                    input_markdown=sample_markdown,
                    output=None,
                    config=None,
                    verbose=False,
                    theme=None,
                    generate_images=False,
                    slide_size="16:9",
                    dry_run=False,
                )
            except typer.Exit as e:
                # Exit code 0以外の場合は失敗
                assert e.exit_code == 0, f"Command failed with exit code {e.exit_code}"

            # 必要なメソッドが呼ばれたことを確認
            mock_config.load_app_config.assert_called_once()
            mock_workflow_cls.assert_called_once()
            mock_workflow.execute.assert_called_once()

    def test_create_command_with_output_specified(
        self, tmp_path, sample_markdown, mock_workflow
    ):
        """Test create command with user-specified output path."""
        output_dir = tmp_path / "output"
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / "custom_output.pptx"

        with patch("slidemaker.cli.commands.create.ConfigManager") as mock_config_cls, \
             patch("slidemaker.cli.commands.create.LLMManager") as mock_llm_cls, \
             patch("slidemaker.cli.commands.create.FileManager") as mock_file_mgr_cls, \
             patch("slidemaker.cli.commands.create.NewSlideWorkflow") as mock_workflow_cls:

            # ConfigManagerのモック
            mock_config = MagicMock()
            mock_config.load_app_config.return_value.output.directory = str(output_dir)
            mock_config.load_app_config.return_value.llm = {
                "composition": {"type": "api", "provider": "claude"}
            }
            mock_config_cls.return_value = mock_config

            # LLMManagerのモック
            mock_llm_cls.return_value = MagicMock()

            # FileManagerのモック
            mock_file_mgr_cls.return_value = MagicMock()

            # NewSlideWorkflowのモック
            mock_workflow.execute.return_value = output_file
            mock_workflow_cls.return_value = mock_workflow

            # createコマンド実行（出力パス指定）
            try:
                create(
                    input_markdown=sample_markdown,
                    output=output_file,
                    config=None,
                    verbose=False,
                    theme=None,
                    generate_images=False,
                    slide_size="16:9",
                    dry_run=False,
                )
            except typer.Exit as e:
                assert e.exit_code == 0, f"Command failed with exit code {e.exit_code}"

            # execute呼び出しで指定されたoutput_pathを確認
            call_kwargs = mock_workflow.execute.call_args.kwargs
            assert call_kwargs["output_path"] == output_file

    def test_create_command_config_error(self, tmp_path, sample_markdown):
        """Test create command handles configuration errors."""
        with patch("slidemaker.cli.commands.create.ConfigManager") as mock_config_cls:
            # ConfigManagerが例外を投げる
            mock_config_cls.side_effect = Exception("Config file not found")

            with pytest.raises(typer.Exit) as exc_info:
                create(
                    input_markdown=sample_markdown,
                    output=None,
                    config=None,
                    verbose=False,
                    theme=None,
                    generate_images=False,
                    slide_size="16:9",
                    dry_run=False,
                )

            # Exit code 1で終了することを確認
            assert exc_info.value.exit_code == 1

    def test_create_command_workflow_error(self, tmp_path, sample_markdown, mock_workflow):
        """Test create command handles workflow errors."""
        output_dir = tmp_path / "output"
        output_dir.mkdir(exist_ok=True)

        with patch("slidemaker.cli.commands.create.ConfigManager") as mock_config_cls, \
             patch("slidemaker.cli.commands.create.LLMManager") as mock_llm_cls, \
             patch("slidemaker.cli.commands.create.FileManager") as mock_file_mgr_cls, \
             patch("slidemaker.cli.commands.create.NewSlideWorkflow") as mock_workflow_cls:

            # ConfigManagerのモック
            mock_config = MagicMock()
            mock_config.load_app_config.return_value.output.directory = str(output_dir)
            mock_config.load_app_config.return_value.llm = {
                "composition": {"type": "api", "provider": "claude"}
            }
            mock_config_cls.return_value = mock_config

            # LLMManagerのモック
            mock_llm_cls.return_value = MagicMock()

            # FileManagerのモック
            mock_file_mgr_cls.return_value = MagicMock()

            # NewSlideWorkflowが例外を投げる
            mock_workflow.execute.side_effect = RuntimeError("Workflow failed")
            mock_workflow_cls.return_value = mock_workflow

            with pytest.raises(typer.Exit) as exc_info:
                create(
                    input_markdown=sample_markdown,
                    output=None,
                    config=None,
                    verbose=False,
                    theme=None,
                    generate_images=False,
                    slide_size="16:9",
                    dry_run=False,
                )

            # Exit code 1で終了することを確認
            assert exc_info.value.exit_code == 1

    def test_create_command_dry_run(self, tmp_path, sample_markdown):
        """Test create command with dry run mode."""
        output_dir = tmp_path / "output"
        output_dir.mkdir(exist_ok=True)

        with patch("slidemaker.cli.commands.create.ConfigManager") as mock_config_cls, \
             patch("slidemaker.cli.commands.create.FileManager") as mock_file_mgr_cls:

            # ConfigManagerのモック
            mock_config = MagicMock()
            mock_config.load_app_config.return_value.output.directory = str(output_dir)
            mock_config.load_app_config.return_value.llm = {
                "composition": {"type": "api", "provider": "claude"}
            }
            mock_config_cls.return_value = mock_config

            # FileManagerのモック
            mock_file_mgr_cls.return_value = MagicMock()

            # ドライランモード実行（typer.Exit(0)が投げられることを期待）
            # Exit code 0は正常終了なので、例外として扱わない
            # 代わりに正常に完了するか、例外が投げられた場合はコード0であることを確認
            try:
                create(
                    input_markdown=sample_markdown,
                    output=None,
                    config=None,
                    verbose=False,
                    theme=None,
                    generate_images=False,
                    slide_size="16:9",
                    dry_run=True,
                )
                # 例外が投げられない場合も正常
                pass
            except typer.Exit as e:
                # Exit code 0で終了することを確認
                assert e.exit_code == 0

    def test_create_command_with_options(self, tmp_path, sample_markdown, mock_workflow):
        """Test create command with various options (theme, generate_images, slide_size)."""
        output_dir = tmp_path / "output"
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / "test.pptx"

        with patch("slidemaker.cli.commands.create.ConfigManager") as mock_config_cls, \
             patch("slidemaker.cli.commands.create.LLMManager") as mock_llm_cls, \
             patch("slidemaker.cli.commands.create.FileManager") as mock_file_mgr_cls, \
             patch("slidemaker.cli.commands.create.NewSlideWorkflow") as mock_workflow_cls:

            # ConfigManagerのモック
            mock_config = MagicMock()
            mock_config.load_app_config.return_value.output.directory = str(output_dir)
            mock_config.load_app_config.return_value.llm = {
                "composition": {"type": "api", "provider": "claude"},
                "image_generation": {"type": "api", "provider": "gemini"},
            }
            mock_config_cls.return_value = mock_config

            # LLMManagerのモック
            mock_llm_cls.return_value = MagicMock()

            # FileManagerのモック
            mock_file_mgr_cls.return_value = MagicMock()

            # NewSlideWorkflowのモック
            mock_workflow.execute.return_value = output_file
            mock_workflow_cls.return_value = mock_workflow

            # createコマンド実行（オプション指定）
            try:
                create(
                    input_markdown=sample_markdown,
                    output=None,
                    config=None,
                    verbose=False,
                    theme="corporate",
                    generate_images=True,
                    slide_size="4:3",
                    dry_run=False,
                )
            except typer.Exit as e:
                assert e.exit_code == 0, f"Command failed with exit code {e.exit_code}"

            # execute呼び出しでオプションが渡されたことを確認
            call_kwargs = mock_workflow.execute.call_args.kwargs
            assert call_kwargs["generate_images"] is True
            assert call_kwargs["slide_size"] == "4:3"
            assert call_kwargs["theme"] == "corporate"

    def test_create_command_verbose_output(self, tmp_path, sample_markdown, mock_workflow):
        """Test create command with verbose mode."""
        output_dir = tmp_path / "output"
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / "test.pptx"

        with patch("slidemaker.cli.commands.create.ConfigManager") as mock_config_cls, \
             patch("slidemaker.cli.commands.create.LLMManager") as mock_llm_cls, \
             patch("slidemaker.cli.commands.create.FileManager") as mock_file_mgr_cls, \
             patch("slidemaker.cli.commands.create.NewSlideWorkflow") as mock_workflow_cls:

            # ConfigManagerのモック
            mock_config = MagicMock()
            mock_config.load_app_config.return_value.output.directory = str(output_dir)
            mock_config.load_app_config.return_value.llm = {
                "composition": {"type": "api", "provider": "claude"}
            }
            mock_config_cls.return_value = mock_config

            # LLMManagerのモック
            mock_llm_cls.return_value = MagicMock()

            # FileManagerのモック
            mock_file_mgr_cls.return_value = MagicMock()

            # NewSlideWorkflowのモック
            mock_workflow.execute.return_value = output_file
            mock_workflow_cls.return_value = mock_workflow

            # verboseモード実行
            try:
                create(
                    input_markdown=sample_markdown,
                    output=None,
                    config=None,
                    verbose=True,
                    theme=None,
                    generate_images=False,
                    slide_size="16:9",
                    dry_run=False,
                )
            except typer.Exit as e:
                assert e.exit_code == 0, f"Command failed with exit code {e.exit_code}"

            # 正常に完了したことを確認
            mock_workflow.execute.assert_called_once()

    def test_create_command_file_not_found(self, tmp_path):
        """Test create command with non-existent input file."""
        non_existent = tmp_path / "nonexistent.md"

        # Typerが存在しないファイルを拒否するため、直接_validate_input_fileをテスト
        with pytest.raises(FileNotFoundError):
            _validate_input_file(non_existent)

    def test_create_command_output_path_traversal(self, tmp_path, sample_markdown):
        """Test create command rejects output path outside allowed directory."""
        output_dir = tmp_path / "output"
        output_dir.mkdir(exist_ok=True)
        # パストラバーサルを試みる出力パス
        malicious_output = Path("/etc/passwd")

        with patch("slidemaker.cli.commands.create.ConfigManager") as mock_config_cls, \
             patch("slidemaker.cli.commands.create.FileManager") as mock_file_mgr_cls:

            # ConfigManagerのモック
            mock_config = MagicMock()
            mock_config.load_app_config.return_value.output.directory = str(output_dir)
            mock_config.load_app_config.return_value.llm = {
                "composition": {"type": "api", "provider": "claude"}
            }
            mock_config_cls.return_value = mock_config

            # FileManagerのモック
            mock_file_mgr_cls.return_value = MagicMock()

            # パストラバーサルを試みる
            with pytest.raises(typer.Exit) as exc_info:
                create(
                    input_markdown=sample_markdown,
                    output=malicious_output,
                    config=None,
                    verbose=False,
                    theme=None,
                    generate_images=False,
                    slide_size="16:9",
                    dry_run=False,
                )

            # Exit code 1で終了することを確認
            assert exc_info.value.exit_code == 1
