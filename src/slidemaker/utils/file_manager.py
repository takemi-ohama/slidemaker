"""File management utilities."""

import shutil
import tempfile
from pathlib import Path
from typing import Any

from slidemaker.utils.logger import get_logger

logger = get_logger(__name__)


class FileManager:
    """Manages temporary and output files for slidemaker."""

    def __init__(
        self,
        temp_dir: str | Path | None = None,
        keep_temp: bool = False,
        output_base_dir: str | Path | None = None,
    ) -> None:
        """
        Initialize file manager.

        Args:
            temp_dir: Temporary directory path. If None, uses system temp.
            keep_temp: Whether to keep temporary files after completion.
            output_base_dir: Base directory for output files. If None, uses cwd.
                           All save_file/copy_file operations are restricted to this directory.
        """
        self.keep_temp = keep_temp
        self._temp_dir: Path | None = None
        self._output_base_dir: Path = Path(output_base_dir) if output_base_dir else Path.cwd()

        if temp_dir:
            self._temp_dir = Path(temp_dir)
            self._temp_dir.mkdir(parents=True, exist_ok=True)
        else:
            self._temp_dir = Path(tempfile.mkdtemp(prefix="slidemaker_"))

        logger.info(
            "FileManager initialized",
            temp_dir=str(self._temp_dir),
            output_base_dir=str(self._output_base_dir),
        )

    @property
    def temp_dir(self) -> Path:
        """Get temporary directory path."""
        if self._temp_dir is None:
            raise RuntimeError("FileManager not properly initialized")
        return self._temp_dir

    @property
    def output_base_dir(self) -> Path:
        """Get output base directory path."""
        return self._output_base_dir

    def _validate_output_path(self, output_path: str | Path) -> Path:
        """
        Validate and resolve output path to prevent path traversal attacks.

        Args:
            output_path: Output file path (relative to output_base_dir or absolute)

        Returns:
            Validated resolved path

        Raises:
            ValueError: If output_path attempts to escape output_base_dir
        """
        path = Path(output_path)

        # If path is not absolute, make it relative to output_base_dir
        if not path.is_absolute():
            path = self._output_base_dir / path

        # Resolve to absolute path and check if it's within output_base_dir
        try:
            resolved_path = path.resolve()
            resolved_base = self._output_base_dir.resolve()
            resolved_path.relative_to(resolved_base)
        except (ValueError, RuntimeError) as e:
            logger.error(
                "Path traversal attempt detected",
                output_path=str(output_path),
                base_dir=str(self._output_base_dir),
            )
            raise ValueError(
                f"Path '{output_path}' escapes base directory '{self._output_base_dir}'"
            ) from e

        return resolved_path

    def create_temp_file(
        self, suffix: str = "", prefix: str = "slidemaker_", content: bytes | str | None = None
    ) -> Path:
        """
        Create a temporary file.

        Args:
            suffix: File suffix/extension
            prefix: File prefix
            content: Optional content to write

        Returns:
            Path to created file
        """
        fd, path_str = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=self.temp_dir)
        path = Path(path_str)

        if content is not None:
            mode = "wb" if isinstance(content, bytes) else "w"
            with path.open(mode) as f:
                f.write(content)

        # Close the file descriptor
        import os

        os.close(fd)

        logger.debug("Created temp file", path=str(path))
        return path

    def create_temp_dir(self, prefix: str = "slidemaker_") -> Path:
        """
        Create a temporary directory.

        Args:
            prefix: Directory prefix

        Returns:
            Path to created directory
        """
        path = Path(tempfile.mkdtemp(prefix=prefix, dir=self.temp_dir))
        logger.debug("Created temp directory", path=str(path))
        return path

    def save_file(self, content: bytes | str, output_path: str | Path) -> Path:
        """
        Save content to file with path traversal protection.

        Args:
            content: Content to save
            output_path: Output file path (relative to output_base_dir or absolute)

        Returns:
            Path to saved file

        Raises:
            ValueError: If output_path attempts to escape output_base_dir
        """
        resolved_path = self._validate_output_path(output_path)
        resolved_path.parent.mkdir(parents=True, exist_ok=True)

        mode = "wb" if isinstance(content, bytes) else "w"
        with resolved_path.open(mode) as f:
            f.write(content)

        logger.info("Saved file", path=str(resolved_path))
        return resolved_path

    def copy_file(self, src: str | Path, dst: str | Path) -> Path:
        """
        Copy file from source to destination with path traversal protection.

        Args:
            src: Source file path
            dst: Destination file path (relative to output_base_dir or absolute)

        Returns:
            Path to destination file

        Raises:
            ValueError: If dst attempts to escape output_base_dir
            FileNotFoundError: If source file does not exist
        """
        src_path = Path(src)
        if not src_path.exists():
            raise FileNotFoundError(f"Source file not found: {src_path}")

        dst_path = self._validate_output_path(dst)
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, dst_path)

        logger.debug("Copied file", src=str(src_path), dst=str(dst_path))
        return dst_path

    def cleanup(self) -> None:
        """Clean up temporary files and directories."""
        if self.keep_temp:
            logger.info("Keeping temporary files", temp_dir=str(self.temp_dir))
            return

        if self._temp_dir and self._temp_dir.exists():
            try:
                shutil.rmtree(self._temp_dir)
                logger.info("Cleaned up temporary files", temp_dir=str(self._temp_dir))
            except Exception as e:
                logger.warning(
                    "Failed to clean up temporary files",
                    temp_dir=str(self._temp_dir),
                    error=str(e),
                )

    def __enter__(self) -> "FileManager":
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.cleanup()

    def __del__(self) -> None:
        """Cleanup on deletion."""
        self.cleanup()
