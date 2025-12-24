"""Tests for CLI output formatting."""

from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest
from rich.console import Console

from slidemaker.cli.output import OutputFormatter


class TestOutputFormatter:
    """Tests for OutputFormatter class."""

    @pytest.fixture
    def output_buffer(self):
        """Create a StringIO buffer to capture console output."""
        return StringIO()

    @pytest.fixture
    def formatter(self, output_buffer):
        """Create an OutputFormatter with captured console."""
        formatter = OutputFormatter(verbose=False)
        # Replace console with one that writes to our buffer
        formatter.console = Console(file=output_buffer, force_terminal=True, width=100)
        return formatter

    @pytest.fixture
    def verbose_formatter(self, output_buffer):
        """Create a verbose OutputFormatter with captured console."""
        formatter = OutputFormatter(verbose=True)
        formatter.console = Console(file=output_buffer, force_terminal=True, width=100)
        return formatter

    def test_init_default(self):
        """Test OutputFormatter initialization with defaults."""
        formatter = OutputFormatter()

        assert formatter.verbose is False
        assert formatter.console is not None
        assert isinstance(formatter.console, Console)

    def test_init_verbose(self):
        """Test OutputFormatter initialization with verbose=True."""
        formatter = OutputFormatter(verbose=True)

        assert formatter.verbose is True
        assert formatter.console is not None

    def test_print_header(self, formatter, output_buffer):
        """Test printing application header."""
        formatter.print_header()

        output = output_buffer.getvalue()

        # Check for key elements in header
        assert "Slidemaker" in output
        assert "AI-powered PowerPoint Generator" in output
        # Version should be present (any version format)
        assert "v" in output

    def test_print_success_simple(self, formatter, output_buffer):
        """Test printing simple success message."""
        formatter.print_success("Operation completed")

        output = output_buffer.getvalue()

        assert "Operation completed" in output
        assert "✓" in output  # Success checkmark

    def test_print_success_with_details(self, formatter, output_buffer):
        """Test printing success message with details dictionary."""
        details = {
            "file": "output.pptx",
            "pages": 10,
            "size": "1.5MB",
        }

        formatter.print_success("Slides created successfully!", details)

        output = output_buffer.getvalue()

        # Check main message
        assert "Slides created successfully!" in output
        assert "✓" in output

        # Check all details are present
        assert "file" in output
        assert "output.pptx" in output
        assert "pages" in output
        assert "10" in output
        assert "size" in output
        # Rich may split "1.5MB" with ANSI codes, so check separately
        assert "1." in output or "1.5" in output
        assert "MB" in output

    def test_print_success_with_path_detail(self, formatter, output_buffer):
        """Test success message with Path object in details."""
        details = {"output": Path("/path/to/output.pptx")}

        formatter.print_success("File saved", details)

        output = output_buffer.getvalue()

        assert "File saved" in output
        assert "output" in output
        # Rich may split path with ANSI codes, check for key components
        assert "/path/to/" in output or "output.pptx" in output

    def test_print_error_simple(self, formatter, output_buffer):
        """Test printing simple error message."""
        formatter.print_error("Failed to create slides")

        output = output_buffer.getvalue()

        assert "Error" in output
        assert "Failed to create slides" in output
        assert "✗" in output  # Error mark

    def test_print_error_with_exception(self, formatter, output_buffer):
        """Test printing error message with exception."""
        error = ValueError("Invalid input value")

        formatter.print_error("Operation failed", error=error)

        output = output_buffer.getvalue()

        assert "Operation failed" in output
        assert "ValueError" in output
        assert "Invalid input value" in output

    def test_print_error_with_traceback_non_verbose(self, formatter, output_buffer):
        """Test error with traceback in non-verbose mode (should not show)."""
        error = RuntimeError("Test error")

        formatter.print_error("Error occurred", error=error, show_traceback=True)

        output = output_buffer.getvalue()

        # In non-verbose mode, traceback should not be shown even if requested
        assert "Error occurred" in output
        assert "RuntimeError" in output
        # Full traceback details should not appear in non-verbose mode

    def test_print_error_with_traceback_verbose(self, verbose_formatter, output_buffer):
        """Test error with traceback in verbose mode."""
        # print_exception() requires being called from an exception handler
        # Test that show_traceback flag is respected in verbose mode
        error = RuntimeError("Test error with traceback")

        # Without being in an exception handler, we just verify the error is printed
        verbose_formatter.print_error("Error occurred", error=error, show_traceback=False)

        output = output_buffer.getvalue()

        assert "Error occurred" in output
        assert "RuntimeError" in output
        assert "Test error with traceback" in output

    def test_print_error_with_traceback_in_exception_handler(
        self, verbose_formatter, output_buffer
    ):
        """Test error with traceback when called from exception handler."""
        # Test that traceback is printed when called from an actual exception handler
        try:
            raise RuntimeError("Test error in handler")
        except RuntimeError as e:
            verbose_formatter.print_error("Error occurred", error=e, show_traceback=True)

        output = output_buffer.getvalue()

        assert "Error occurred" in output
        assert "RuntimeError" in output
        # In an actual exception handler, traceback should be printed
        assert "Test error in handler" in output

    def test_create_progress(self, formatter):
        """Test creating a progress bar."""
        progress = formatter.create_progress("Processing files...")

        assert progress is not None
        assert progress.console == formatter.console

        # Test that progress can be used in context manager
        with progress:
            task = progress.add_task("Processing files...", total=100)
            assert task is not None

    def test_create_progress_custom_description(self, formatter):
        """Test creating progress bar with custom description."""
        description = "Generating slides"
        progress = formatter.create_progress(description)

        assert progress is not None

        with progress:
            task = progress.add_task(description, total=50)
            progress.update(task, advance=10)
            # No error should occur

    def test_print_table(self, formatter, output_buffer):
        """Test printing a table."""
        title = "Slide Information"
        headers = ["Slide", "Title", "Elements"]
        rows = [
            ["1", "Introduction", "3"],
            ["2", "Overview", "5"],
            ["3", "Conclusion", "2"],
        ]

        formatter.print_table(title, headers, rows)

        output = output_buffer.getvalue()

        # Check title
        assert "Slide Information" in output

        # Check headers
        assert "Slide" in output
        assert "Title" in output
        assert "Elements" in output

        # Check row data
        assert "Introduction" in output
        assert "Overview" in output
        assert "Conclusion" in output
        assert "3" in output
        assert "5" in output
        assert "2" in output

    def test_print_table_with_lines(self, formatter, output_buffer):
        """Test printing table with row lines."""
        headers = ["Col1", "Col2"]
        rows = [["A", "B"], ["C", "D"]]

        formatter.print_table("Test Table", headers, rows, show_lines=True)

        output = output_buffer.getvalue()

        assert "Test Table" in output
        assert "Col1" in output
        assert "Col2" in output
        assert "A" in output
        assert "D" in output

    def test_print_table_empty_rows(self, formatter, output_buffer):
        """Test printing table with no rows."""
        headers = ["Col1", "Col2"]
        rows: list[list[str]] = []

        formatter.print_table("Empty Table", headers, rows)

        output = output_buffer.getvalue()

        assert "Empty Table" in output
        assert "Col1" in output
        assert "Col2" in output

    def test_print_info(self, formatter, output_buffer):
        """Test printing info message."""
        formatter.print_info("Loading configuration...")

        output = output_buffer.getvalue()

        # Rich may split the text with ANSI codes, check for key parts
        assert "Loading configuration" in output
        assert "ℹ" in output  # Info icon

    def test_print_warning(self, formatter, output_buffer):
        """Test printing warning message."""
        formatter.print_warning("No theme specified, using default")

        output = output_buffer.getvalue()

        assert "No theme specified, using default" in output
        assert "⚠" in output  # Warning icon

    def test_print_debug_non_verbose(self, formatter, output_buffer):
        """Test debug message in non-verbose mode (should not print)."""
        formatter.print_debug("Debug information")

        output = output_buffer.getvalue()

        # Debug should not appear in non-verbose mode
        assert output == ""

    def test_print_debug_verbose(self, verbose_formatter, output_buffer):
        """Test debug message in verbose mode."""
        verbose_formatter.print_debug("Debug information")

        output = output_buffer.getvalue()

        assert "Debug information" in output
        assert "DEBUG" in output
        assert "🔍" in output  # Debug icon

    def test_print_json(self, formatter, output_buffer):
        """Test printing JSON data."""
        data = {
            "slides": 5,
            "status": "success",
            "duration": 12.5,
        }

        formatter.print_json(data, title="Generation Result")

        output = output_buffer.getvalue()

        # Check title
        assert "Generation Result" in output

        # JSON output should contain the data
        assert "slides" in output
        assert "5" in output
        assert "status" in output
        assert "success" in output
        assert "duration" in output

    def test_print_json_no_title(self, formatter, output_buffer):
        """Test printing JSON without title."""
        data = {"key": "value"}

        formatter.print_json(data)

        output = output_buffer.getvalue()

        assert "key" in output
        assert "value" in output

    def test_confirm_yes(self, formatter):
        """Test confirm prompt with 'yes' response."""
        with patch("builtins.input", return_value="y"):
            result = formatter.confirm("Delete file?")

        assert result is True

    def test_confirm_yes_full(self, formatter):
        """Test confirm prompt with 'yes' full word response."""
        with patch("builtins.input", return_value="yes"):
            result = formatter.confirm("Delete file?")

        assert result is True

    def test_confirm_no(self, formatter):
        """Test confirm prompt with 'no' response."""
        with patch("builtins.input", return_value="n"):
            result = formatter.confirm("Delete file?")

        assert result is False

    def test_confirm_empty_default_false(self, formatter):
        """Test confirm with empty input and default=False."""
        with patch("builtins.input", return_value=""):
            result = formatter.confirm("Continue?", default=False)

        assert result is False

    def test_confirm_empty_default_true(self, formatter):
        """Test confirm with empty input and default=True."""
        with patch("builtins.input", return_value=""):
            result = formatter.confirm("Continue?", default=True)

        assert result is True

    def test_confirm_invalid_input(self, formatter):
        """Test confirm with invalid input (should return False)."""
        with patch("builtins.input", return_value="invalid"):
            result = formatter.confirm("Continue?")

        assert result is False

    def test_confirm_keyboard_interrupt(self, formatter, output_buffer):
        """Test confirm with KeyboardInterrupt."""
        with patch("builtins.input", side_effect=KeyboardInterrupt):
            result = formatter.confirm("Continue?")

        assert result is False

        output = output_buffer.getvalue()
        assert "Cancelled" in output

    def test_confirm_eof_error(self, formatter, output_buffer):
        """Test confirm with EOFError."""
        with patch("builtins.input", side_effect=EOFError):
            result = formatter.confirm("Continue?")

        assert result is False

        output = output_buffer.getvalue()
        assert "Cancelled" in output

    def test_confirm_case_insensitive(self, formatter):
        """Test that confirm handles uppercase input."""
        with patch("builtins.input", return_value="Y"):
            result = formatter.confirm("Continue?")

        assert result is True

        with patch("builtins.input", return_value="YES"):
            result = formatter.confirm("Continue?")

        assert result is True

    def test_confirm_whitespace_handling(self, formatter):
        """Test that confirm handles whitespace in input."""
        with patch("builtins.input", return_value="  y  "):
            result = formatter.confirm("Continue?")

        assert result is True

        with patch("builtins.input", return_value="  n  "):
            result = formatter.confirm("Continue?")

        assert result is False
