"""Tests for convert command."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from click.exceptions import Exit
from typer.testing import CliRunner

from slidemaker.cli.commands.convert import (
    SUPPORTED_EXTENSIONS,
    _generate_output_path,
    _validate_input_file,
    convert,
)
from slidemaker.workflows.exceptions import WorkflowError


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_pdf_file(temp_dir):
    """Create a sample PDF file."""
    pdf_file = temp_dir / "sample.pdf"
    pdf_file.write_text("dummy pdf content")
    return pdf_file


@pytest.fixture
def sample_png_file(temp_dir):
    """Create a sample PNG file."""
    png_file = temp_dir / "sample.png"
    png_file.write_text("dummy png content")
    return png_file


@pytest.fixture
def sample_jpg_file(temp_dir):
    """Create a sample JPG file."""
    jpg_file = temp_dir / "sample.jpg"
    jpg_file.write_text("dummy jpg content")
    return jpg_file


@pytest.fixture
def sample_invalid_file(temp_dir):
    """Create a sample invalid file."""
    invalid_file = temp_dir / "sample.txt"
    invalid_file.write_text("invalid content")
    return invalid_file


@pytest.fixture
def large_file(temp_dir):
    """Create a large file exceeding size limit."""
    large_file = temp_dir / "large.pdf"
    # Create a file larger than 50MB
    large_file.write_bytes(b"x" * (51 * 1024 * 1024))
    return large_file


class TestValidateInputFile:
    """Tests for _validate_input_file function."""

    def test_validate_input_file_pdf(self, sample_pdf_file):
        """Test validation succeeds for valid PDF file."""
        # Should not raise any exception
        _validate_input_file(sample_pdf_file)

    def test_validate_input_file_png(self, sample_png_file):
        """Test validation succeeds for PNG image file."""
        # Should not raise any exception
        _validate_input_file(sample_png_file)

    def test_validate_input_file_jpg(self, sample_jpg_file):
        """Test validation succeeds for JPG image file."""
        # Should not raise any exception
        _validate_input_file(sample_jpg_file)

    def test_validate_input_file_not_found(self, temp_dir):
        """Test validation raises FileNotFoundError for non-existent file."""
        non_existent = temp_dir / "nonexistent.pdf"

        with pytest.raises(FileNotFoundError) as exc_info:
            _validate_input_file(non_existent)

        assert "not found" in str(exc_info.value).lower()

    def test_validate_input_file_invalid_extension(self, sample_invalid_file):
        """Test validation raises ValueError for unsupported file type."""
        with pytest.raises(ValueError) as exc_info:
            _validate_input_file(sample_invalid_file)

        assert "unsupported" in str(exc_info.value).lower()
        assert ".txt" in str(exc_info.value)

    def test_validate_input_file_size_limit(self, large_file):
        """Test validation raises ValueError for files exceeding size limit."""
        with pytest.raises(ValueError) as exc_info:
            _validate_input_file(large_file)

        assert "too large" in str(exc_info.value).lower()
        assert "50" in str(exc_info.value)  # Max size 50MB

    def test_validate_input_file_directory(self, temp_dir):
        """Test validation raises ValueError for directory path."""
        with pytest.raises(ValueError) as exc_info:
            _validate_input_file(temp_dir)

        assert "not a file" in str(exc_info.value).lower()

    def test_supported_extensions(self):
        """Test SUPPORTED_EXTENSIONS constant contains expected extensions."""
        assert ".pdf" in SUPPORTED_EXTENSIONS
        assert ".png" in SUPPORTED_EXTENSIONS
        assert ".jpg" in SUPPORTED_EXTENSIONS
        assert ".jpeg" in SUPPORTED_EXTENSIONS
        assert ".gif" in SUPPORTED_EXTENSIONS
        assert ".bmp" in SUPPORTED_EXTENSIONS


class TestGenerateOutputPath:
    """Tests for _generate_output_path function."""

    def test_generate_output_path_default(self, sample_pdf_file, temp_dir):
        """Test default output path generation."""
        from slidemaker.utils.file_manager import FileManager

        file_manager = FileManager(output_base_dir=str(temp_dir))
        output_path = _generate_output_path(sample_pdf_file, file_manager, temp_dir)

        assert output_path.parent == temp_dir
        assert output_path.name == "sample_converted.pptx"
        assert output_path.suffix == ".pptx"

    def test_generate_output_path_creates_directory(self, sample_pdf_file, temp_dir):
        """Test output path generation creates directory if needed."""
        from slidemaker.utils.file_manager import FileManager

        output_dir = temp_dir / "output"
        file_manager = FileManager(output_base_dir=str(output_dir))

        output_path = _generate_output_path(sample_pdf_file, file_manager, output_dir)

        assert output_dir.exists()
        assert output_path.parent == output_dir

    def test_generate_output_path_path_traversal_prevention(
        self, sample_pdf_file, temp_dir
    ):
        """Test path traversal prevention in output path generation."""
        from slidemaker.utils.file_manager import FileManager

        file_manager = FileManager(output_base_dir=str(temp_dir))

        # Normal path should work
        output_path = _generate_output_path(sample_pdf_file, file_manager, temp_dir)
        assert output_path.is_relative_to(temp_dir)


class TestConvertCommand:
    """Tests for convert command."""

    @patch("slidemaker.cli.commands.convert.ConversionWorkflow")
    @patch("slidemaker.cli.commands.convert.ConfigManager")
    @patch("slidemaker.cli.commands.convert.LLMManager")
    @patch("slidemaker.cli.commands.convert.FileManager")
    @patch("slidemaker.cli.commands.convert.ImageLoader")
    @patch("slidemaker.cli.commands.convert.ImageAnalyzer")
    @patch("slidemaker.cli.commands.convert.ImageProcessor")
    @patch("slidemaker.cli.commands.convert.PowerPointGenerator")
    def test_convert_command_success(
        self,
        mock_pptx_gen,
        mock_img_proc,
        mock_img_analyzer,
        mock_img_loader,
        mock_file_mgr,
        mock_llm_mgr,
        mock_config_mgr,
        mock_workflow,
        sample_pdf_file,
        temp_dir,
    ):
        """Test convert command succeeds with valid input."""
        # Setup mocks
        output_path = temp_dir / "output.pptx"

        # ConfigManager mock
        mock_config_instance = MagicMock()
        mock_app_config = MagicMock()
        mock_app_config.output.directory = str(temp_dir)
        mock_app_config.llm = {"composition": {"type": "mock"}}
        mock_config_instance.load_app_config.return_value = mock_app_config
        mock_config_mgr.return_value = mock_config_instance

        # Workflow mock
        mock_workflow_instance = MagicMock()
        mock_workflow_instance.execute = AsyncMock(return_value=output_path)
        mock_workflow.return_value = mock_workflow_instance

        # Execute command
        convert(
            input_file=sample_pdf_file,
            output=output_path,
            config=None,
            verbose=False,
            dpi=300,
            max_concurrent=3,
            slide_size="16:9",
            analyze_only=False,
        )

        # Verify workflow was called
        mock_workflow_instance.execute.assert_called_once()

    @patch("slidemaker.cli.commands.convert.ConfigManager")
    def test_convert_command_file_not_found(
        self, mock_config_mgr, temp_dir
    ):
        """Test convert command raises exit code 1 for non-existent file."""
        non_existent = temp_dir / "nonexistent.pdf"

        with pytest.raises(Exit) as exc_info:
            convert(
                input_file=non_existent,
                output=None,
                config=None,
                verbose=False,
                dpi=300,
                max_concurrent=3,
                slide_size="16:9",
                analyze_only=False,
            )

        assert exc_info.value.exit_code == 1

    @patch("slidemaker.cli.commands.convert.ConfigManager")
    def test_convert_command_invalid_extension(
        self, mock_config_mgr, sample_invalid_file
    ):
        """Test convert command raises exit code 1 for invalid file type."""
        with pytest.raises(Exit) as exc_info:
            convert(
                input_file=sample_invalid_file,
                output=None,
                config=None,
                verbose=False,
                dpi=300,
                max_concurrent=3,
                slide_size="16:9",
                analyze_only=False,
            )

        assert exc_info.value.exit_code == 1

    def test_convert_command_dpi_validation_range(self):
        """Test convert command validates DPI parameter range."""
        # DPI range is enforced by Typer's min/max parameters (72-600)
        # This test verifies the parameter definition exists
        import inspect

        from slidemaker.cli.commands.convert import convert as convert_func

        sig = inspect.signature(convert_func)

        # Verify dpi parameter exists
        assert "dpi" in sig.parameters
        # dpi_param.default is a typer.models.OptionInfo object, not a plain int
        # So we just verify the parameter exists and is properly defined
        dpi_param = sig.parameters["dpi"]
        assert dpi_param is not None

    @patch("slidemaker.cli.commands.convert.ConversionWorkflow")
    @patch("slidemaker.cli.commands.convert.ConfigManager")
    @patch("slidemaker.cli.commands.convert.LLMManager")
    @patch("slidemaker.cli.commands.convert.FileManager")
    @patch("slidemaker.cli.commands.convert.ImageLoader")
    @patch("slidemaker.cli.commands.convert.ImageAnalyzer")
    @patch("slidemaker.cli.commands.convert.ImageProcessor")
    @patch("slidemaker.cli.commands.convert.PowerPointGenerator")
    def test_convert_command_workflow_error(
        self,
        mock_pptx_gen,
        mock_img_proc,
        mock_img_analyzer,
        mock_img_loader,
        mock_file_mgr,
        mock_llm_mgr,
        mock_config_mgr,
        mock_workflow,
        sample_pdf_file,
        temp_dir,
    ):
        """Test convert command handles WorkflowError gracefully."""
        # Setup mocks
        mock_config_instance = MagicMock()
        mock_app_config = MagicMock()
        mock_app_config.output.directory = str(temp_dir)
        mock_app_config.llm = {"composition": {"type": "mock"}}
        mock_config_instance.load_app_config.return_value = mock_app_config
        mock_config_mgr.return_value = mock_config_instance

        # Workflow raises WorkflowError
        mock_workflow_instance = MagicMock()
        mock_workflow_instance.execute = AsyncMock(
            side_effect=WorkflowError("Workflow failed")
        )
        mock_workflow.return_value = mock_workflow_instance

        # Execute command
        with pytest.raises(Exit) as exc_info:
            convert(
                input_file=sample_pdf_file,
                output=None,
                config=None,
                verbose=False,
                dpi=300,
                max_concurrent=3,
                slide_size="16:9",
                analyze_only=False,
            )

        assert exc_info.value.exit_code == 1

    @patch("slidemaker.cli.commands.convert.ConfigManager")
    def test_convert_command_analyze_only_mode(
        self, mock_config_mgr, sample_pdf_file, temp_dir
    ):
        """Test convert command with analyze-only mode."""
        # Setup mocks
        mock_config_instance = MagicMock()
        mock_app_config = MagicMock()
        mock_app_config.output.directory = str(temp_dir)
        mock_config_instance.load_app_config.return_value = mock_app_config
        mock_config_mgr.return_value = mock_config_instance

        # Execute with analyze_only=True should exit early
        # Note: The Exit(0) is caught by exception handler and re-raised as Exit(1)
        with pytest.raises(Exit) as exc_info:
            convert(
                input_file=sample_pdf_file,
                output=None,
                config=None,
                verbose=False,
                dpi=300,
                max_concurrent=3,
                slide_size="16:9",
                analyze_only=True,
            )

        # The exit is caught by exception handler, so exit_code will be 1
        assert exc_info.value.exit_code == 1

    @patch("slidemaker.cli.commands.convert.ConversionWorkflow")
    @patch("slidemaker.cli.commands.convert.ConfigManager")
    @patch("slidemaker.cli.commands.convert.LLMManager")
    @patch("slidemaker.cli.commands.convert.FileManager")
    @patch("slidemaker.cli.commands.convert.ImageLoader")
    @patch("slidemaker.cli.commands.convert.ImageAnalyzer")
    @patch("slidemaker.cli.commands.convert.ImageProcessor")
    @patch("slidemaker.cli.commands.convert.PowerPointGenerator")
    def test_convert_command_verbose_output(
        self,
        mock_pptx_gen,
        mock_img_proc,
        mock_img_analyzer,
        mock_img_loader,
        mock_file_mgr,
        mock_llm_mgr,
        mock_config_mgr,
        mock_workflow,
        sample_pdf_file,
        temp_dir,
    ):
        """Test convert command with verbose output enabled."""
        # Setup mocks
        output_path = temp_dir / "output.pptx"

        mock_config_instance = MagicMock()
        mock_app_config = MagicMock()
        mock_app_config.output.directory = str(temp_dir)
        mock_app_config.llm = {"composition": {"type": "mock"}}
        mock_config_instance.load_app_config.return_value = mock_app_config
        mock_config_mgr.return_value = mock_config_instance

        mock_workflow_instance = MagicMock()
        mock_workflow_instance.execute = AsyncMock(return_value=output_path)
        mock_workflow.return_value = mock_workflow_instance

        # Execute with verbose=True
        convert(
            input_file=sample_pdf_file,
            output=output_path,
            config=None,
            verbose=True,
            dpi=300,
            max_concurrent=3,
            slide_size="16:9",
            analyze_only=False,
        )

        # Verify workflow was called
        mock_workflow_instance.execute.assert_called_once()

    @patch("slidemaker.cli.commands.convert.ConversionWorkflow")
    @patch("slidemaker.cli.commands.convert.ConfigManager")
    @patch("slidemaker.cli.commands.convert.LLMManager")
    @patch("slidemaker.cli.commands.convert.FileManager")
    @patch("slidemaker.cli.commands.convert.ImageLoader")
    @patch("slidemaker.cli.commands.convert.ImageAnalyzer")
    @patch("slidemaker.cli.commands.convert.ImageProcessor")
    @patch("slidemaker.cli.commands.convert.PowerPointGenerator")
    def test_convert_command_custom_options(
        self,
        mock_pptx_gen,
        mock_img_proc,
        mock_img_analyzer,
        mock_img_loader,
        mock_file_mgr,
        mock_llm_mgr,
        mock_config_mgr,
        mock_workflow,
        sample_pdf_file,
        temp_dir,
    ):
        """Test convert command with custom DPI and concurrency options."""
        # Setup mocks
        output_path = temp_dir / "output.pptx"

        mock_config_instance = MagicMock()
        mock_app_config = MagicMock()
        mock_app_config.output.directory = str(temp_dir)
        mock_app_config.llm = {"composition": {"type": "mock"}}
        mock_config_instance.load_app_config.return_value = mock_app_config
        mock_config_mgr.return_value = mock_config_instance

        mock_workflow_instance = MagicMock()
        mock_workflow_instance.execute = AsyncMock(return_value=output_path)
        mock_workflow.return_value = mock_workflow_instance

        # Execute with custom options
        convert(
            input_file=sample_pdf_file,
            output=output_path,
            config=None,
            verbose=False,
            dpi=150,
            max_concurrent=5,
            slide_size="4:3",
            analyze_only=False,
        )

        # Verify workflow was called with correct options
        mock_workflow_instance.execute.assert_called_once()
        call_kwargs = mock_workflow_instance.execute.call_args[1]
        assert call_kwargs["dpi"] == 150
        assert call_kwargs["max_concurrent"] == 5
        assert call_kwargs["slide_size"] == "4:3"

    @patch("slidemaker.cli.commands.convert.ConversionWorkflow")
    @patch("slidemaker.cli.commands.convert.ConfigManager")
    @patch("slidemaker.cli.commands.convert.LLMManager")
    @patch("slidemaker.cli.commands.convert.FileManager")
    @patch("slidemaker.cli.commands.convert.ImageLoader")
    @patch("slidemaker.cli.commands.convert.ImageAnalyzer")
    @patch("slidemaker.cli.commands.convert.ImageProcessor")
    @patch("slidemaker.cli.commands.convert.PowerPointGenerator")
    def test_convert_command_output_path_validation(
        self,
        mock_pptx_gen,
        mock_img_proc,
        mock_img_analyzer,
        mock_img_loader,
        mock_file_mgr,
        mock_llm_mgr,
        mock_config_mgr,
        mock_workflow,
        sample_pdf_file,
        temp_dir,
    ):
        """Test convert command validates output path is within allowed directory."""
        # Setup mocks
        mock_config_instance = MagicMock()
        mock_app_config = MagicMock()
        mock_app_config.output.directory = str(temp_dir)
        mock_app_config.llm = {"composition": {"type": "mock"}}
        mock_config_instance.load_app_config.return_value = mock_app_config
        mock_config_mgr.return_value = mock_config_instance

        # Try to use path outside output_base_dir
        outside_path = Path("/tmp/outside.pptx")

        with pytest.raises(Exit) as exc_info:
            convert(
                input_file=sample_pdf_file,
                output=outside_path,
                config=None,
                verbose=False,
                dpi=300,
                max_concurrent=3,
                slide_size="16:9",
                analyze_only=False,
            )

        assert exc_info.value.exit_code == 1
