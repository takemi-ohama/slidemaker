"""CLI output formatting using Rich library.

This module provides the OutputFormatter class for displaying beautiful,
colorful CLI output using the Rich library. It supports:
- Success/error messages with color coding
- Progress bars for long-running operations
- Tables for structured data display
- Application headers with version info
"""

from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeRemainingColumn
from rich.table import Table
from rich.traceback import install as install_rich_traceback

from slidemaker.__version__ import __version__

# Install rich traceback handler for better error display
install_rich_traceback(show_locals=True)


class OutputFormatter:
    """Formatter for CLI output using Rich library.

    This class provides methods for displaying formatted output in the CLI,
    including success/error messages, progress bars, and tables.

    Attributes:
        console: Rich Console instance for output
        verbose: Whether to display verbose output

    Example:
        >>> formatter = OutputFormatter(verbose=True)
        >>> formatter.print_header()
        >>> formatter.print_success("Operation completed!", {"file": "output.pptx"})
    """

    def __init__(self, verbose: bool = False) -> None:
        """Initialize the OutputFormatter.

        Args:
            verbose: If True, display verbose output including debug information
        """
        self.console = Console()
        self.verbose = verbose

    def print_header(self) -> None:
        """Print application header with version information.

        Displays a stylized header panel with the application name and version.
        """
        header_text = f"[bold blue]Slidemaker[/bold blue] v{__version__}"
        subtitle = "AI-powered PowerPoint Generator"
        self.console.print(
            Panel(
                f"{header_text}\n[dim]{subtitle}[/dim]",
                border_style="blue",
                padding=(1, 2),
            )
        )

    def print_success(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Print success message in green.

        Args:
            message: Success message to display
            details: Optional dictionary of additional details to display
                    (e.g., {"file": "output.pptx", "pages": 10})

        Example:
            >>> formatter.print_success(
            ...     "Slides created successfully!",
            ...     {"file": "/path/to/output.pptx", "pages": 5}
            ... )
        """
        self.console.print(f"[green]✓[/green] {message}")

        if details:
            for key, value in details.items():
                # Format file paths nicely
                if isinstance(value, Path):
                    value = str(value)
                self.console.print(f"  [blue]→[/blue] {key}: [bold]{value}[/bold]")

    def print_error(
        self, message: str, error: Exception | None = None, show_traceback: bool = False
    ) -> None:
        """Print error message in red.

        Args:
            message: Error message to display
            error: Optional exception object
            show_traceback: If True, display the full traceback (only in verbose mode)

        Example:
            >>> formatter.print_error("Failed to create slides", error=exc)
        """
        self.console.print(f"[red]✗ Error:[/red] {message}")

        if error:
            self.console.print(f"  [dim]{type(error).__name__}: {str(error)}[/dim]")

            if show_traceback and self.verbose:
                self.console.print_exception(show_locals=True)

    def create_progress(self, description: str = "Processing...") -> Progress:
        """Create and return a Rich Progress bar.

        Args:
            description: Description text to display with the progress bar

        Returns:
            Progress: A Rich Progress instance with spinner, text, bar, and time remaining

        Example:
            >>> progress = formatter.create_progress("Generating slides")
            >>> with progress:
            ...     task = progress.add_task(description, total=100)
            ...     for i in range(100):
            ...         progress.update(task, advance=1)
        """
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=self.console,
        )

    def print_table(
        self,
        title: str,
        headers: list[str],
        rows: list[list[str]],
        show_lines: bool = False,
    ) -> None:
        """Print data in table format.

        Args:
            title: Table title
            headers: List of column headers
            rows: List of rows, where each row is a list of cell values
            show_lines: If True, show lines between rows

        Example:
            >>> formatter.print_table(
            ...     "Slide Information",
            ...     ["Slide", "Title", "Elements"],
            ...     [
            ...         ["1", "Introduction", "3"],
            ...         ["2", "Overview", "5"],
            ...     ]
            ... )
        """
        table = Table(title=title, show_lines=show_lines)

        # Add columns
        for header in headers:
            table.add_column(header, style="cyan", no_wrap=False)

        # Add rows
        for row in rows:
            table.add_row(*row)

        self.console.print(table)

    def print_info(self, message: str) -> None:
        """Print informational message in blue.

        Args:
            message: Information message to display

        Example:
            >>> formatter.print_info("Loading configuration...")
        """
        self.console.print(f"[blue]ℹ[/blue] {message}")

    def print_warning(self, message: str) -> None:
        """Print warning message in yellow.

        Args:
            message: Warning message to display

        Example:
            >>> formatter.print_warning("No theme specified, using default")
        """
        self.console.print(f"[yellow]⚠[/yellow] {message}")

    def print_debug(self, message: str) -> None:
        """Print debug message in dim style (only in verbose mode).

        Args:
            message: Debug message to display

        Example:
            >>> formatter.print_debug("LLM API call completed in 2.3s")
        """
        if self.verbose:
            self.console.print(f"[dim]🔍 DEBUG: {message}[/dim]")

    def print_json(self, data: dict[str, Any], title: str = "Output") -> None:
        """Print data in JSON format with syntax highlighting.

        Args:
            data: Dictionary to display as JSON
            title: Optional title to display above the JSON

        Example:
            >>> formatter.print_json(
            ...     {"slides": 5, "status": "success"},
            ...     title="Generation Result"
            ... )
        """
        if title:
            self.console.print(f"\n[bold cyan]{title}[/bold cyan]")

        self.console.print_json(data=data)

    def confirm(self, message: str, default: bool = False) -> bool:
        """Prompt user for yes/no confirmation.

        Args:
            message: Confirmation message to display
            default: Default value if user just presses Enter

        Returns:
            bool: True if user confirms, False otherwise

        Example:
            >>> if formatter.confirm("Delete existing file?"):
            ...     delete_file()
        """
        default_str = "Y/n" if default else "y/N"
        self.console.print(f"[yellow]?[/yellow] {message} [{default_str}] ", end="")

        try:
            response = input().strip().lower()
            if not response:
                return default
            return response in ("y", "yes")
        except (KeyboardInterrupt, EOFError):
            self.console.print("\n[red]Cancelled[/red]")
            return False
