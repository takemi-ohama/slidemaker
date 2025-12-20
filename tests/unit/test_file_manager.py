"""Unit tests for FileManager."""

from pathlib import Path

import pytest

from slidemaker.utils import FileManager


class TestFileManager:
    """Tests for FileManager."""

    def test_initialization_default(self):
        """Test FileManager initializes with default temp directory."""
        with FileManager() as fm:
            assert fm.temp_dir.exists()
            assert "slidemaker_" in str(fm.temp_dir)

    def test_initialization_custom_temp(self, tmp_path):
        """Test FileManager with custom temp directory."""
        custom_temp = tmp_path / "custom_temp"
        with FileManager(temp_dir=custom_temp) as fm:
            assert fm.temp_dir == custom_temp
            assert fm.temp_dir.exists()

    def test_initialization_with_output_base_dir(self, tmp_path):
        """Test FileManager with custom output base directory."""
        output_base = tmp_path / "output"
        with FileManager(output_base_dir=output_base) as fm:
            assert fm.output_base_dir == output_base

    def test_create_temp_file(self):
        """Test creating temporary file."""
        with FileManager() as fm:
            temp_file = fm.create_temp_file(suffix=".txt")
            assert temp_file.exists()
            assert temp_file.suffix == ".txt"

    def test_create_temp_file_with_content(self):
        """Test creating temporary file with content."""
        with FileManager() as fm:
            content = "Hello, World!"
            temp_file = fm.create_temp_file(suffix=".txt", content=content)
            assert temp_file.read_text() == content

    def test_create_temp_file_with_binary_content(self):
        """Test creating temporary file with binary content."""
        with FileManager() as fm:
            content = b"\x00\x01\x02\x03"
            temp_file = fm.create_temp_file(suffix=".bin", content=content)
            assert temp_file.read_bytes() == content

    def test_create_temp_dir(self):
        """Test creating temporary directory."""
        with FileManager() as fm:
            temp_dir = fm.create_temp_dir(prefix="test_")
            assert temp_dir.exists()
            assert temp_dir.is_dir()
            assert "test_" in str(temp_dir)

    def test_save_file(self, tmp_path):
        """Test saving file to output directory."""
        with FileManager(output_base_dir=tmp_path) as fm:
            content = "Test content"
            output_path = fm.save_file(content, "test.txt")

            assert output_path.exists()
            assert output_path.read_text() == content
            # Verify it's within output_base_dir
            assert output_path.parent == tmp_path

    def test_save_file_with_subdirectory(self, tmp_path):
        """Test saving file to subdirectory."""
        with FileManager(output_base_dir=tmp_path) as fm:
            content = "Test content"
            output_path = fm.save_file(content, "subdir/test.txt")

            assert output_path.exists()
            assert output_path.read_text() == content
            assert output_path.parent.name == "subdir"

    def test_save_file_binary(self, tmp_path):
        """Test saving binary file."""
        with FileManager(output_base_dir=tmp_path) as fm:
            content = b"\x00\x01\x02\x03"
            output_path = fm.save_file(content, "test.bin")

            assert output_path.exists()
            assert output_path.read_bytes() == content

    def test_save_file_path_traversal_protection(self, tmp_path):
        """Test that path traversal attempts are blocked."""
        with FileManager(output_base_dir=tmp_path) as fm:
            with pytest.raises(ValueError, match="escapes base directory"):
                fm.save_file("malicious", "../../../etc/passwd")

    def test_save_file_absolute_path_outside_base(self, tmp_path):
        """Test that absolute paths outside base are blocked."""
        with FileManager(output_base_dir=tmp_path) as fm:
            with pytest.raises(ValueError, match="escapes base directory"):
                fm.save_file("malicious", "/tmp/outside.txt")

    def test_copy_file(self, tmp_path):
        """Test copying file."""
        # Create source file
        src_file = tmp_path / "source.txt"
        src_file.write_text("Source content")

        output_base = tmp_path / "output"
        output_base.mkdir()

        with FileManager(output_base_dir=output_base) as fm:
            dst_path = fm.copy_file(src_file, "copied.txt")

            assert dst_path.exists()
            assert dst_path.read_text() == "Source content"
            assert dst_path.parent == output_base

    def test_copy_file_nonexistent_source(self, tmp_path):
        """Test copying non-existent file raises FileNotFoundError."""
        with FileManager(output_base_dir=tmp_path) as fm:
            with pytest.raises(FileNotFoundError, match="Source file not found"):
                fm.copy_file("nonexistent.txt", "destination.txt")

    def test_copy_file_path_traversal_protection(self, tmp_path):
        """Test that path traversal in copy destination is blocked."""
        src_file = tmp_path / "source.txt"
        src_file.write_text("content")

        with FileManager(output_base_dir=tmp_path) as fm:
            with pytest.raises(ValueError, match="escapes base directory"):
                fm.copy_file(src_file, "../../outside.txt")

    def test_cleanup_removes_temp_files(self, tmp_path):
        """Test that cleanup removes temporary files."""
        custom_temp = tmp_path / "temp"
        fm = FileManager(temp_dir=custom_temp, keep_temp=False)
        temp_file = fm.create_temp_file()

        assert temp_file.exists()

        fm.cleanup()

        assert not custom_temp.exists()

    def test_cleanup_keeps_temp_files_when_requested(self, tmp_path):
        """Test that cleanup keeps temp files when keep_temp=True."""
        custom_temp = tmp_path / "temp"
        fm = FileManager(temp_dir=custom_temp, keep_temp=True)
        temp_file = fm.create_temp_file()

        assert temp_file.exists()

        fm.cleanup()

        assert custom_temp.exists()
        assert temp_file.exists()

    def test_context_manager_cleanup(self, tmp_path):
        """Test that context manager cleans up automatically."""
        custom_temp = tmp_path / "temp"

        with FileManager(temp_dir=custom_temp) as fm:
            temp_file = fm.create_temp_file()
            assert temp_file.exists()

        # After exiting context, temp should be cleaned up
        assert not custom_temp.exists()

    def test_validate_output_path_relative(self, tmp_path):
        """Test validating relative output path."""
        with FileManager(output_base_dir=tmp_path) as fm:
            # This should succeed
            validated = fm._validate_output_path("safe/path/file.txt")
            assert validated.is_relative_to(tmp_path)

    def test_validate_output_path_absolute_within_base(self, tmp_path):
        """Test validating absolute path within base directory."""
        with FileManager(output_base_dir=tmp_path) as fm:
            safe_path = tmp_path / "safe" / "file.txt"
            validated = fm._validate_output_path(safe_path)
            assert validated.is_relative_to(tmp_path)

    def test_output_base_dir_property(self, tmp_path):
        """Test output_base_dir property."""
        with FileManager(output_base_dir=tmp_path) as fm:
            assert fm.output_base_dir == tmp_path
