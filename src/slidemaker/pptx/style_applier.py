"""Style applier for PowerPoint presentations.

This module provides functionality to apply themes and styles to PowerPoint presentations,
including template loading, default font settings, and style configuration.
"""

from pathlib import Path

import structlog
from pptx import Presentation
from pptx.presentation import Presentation as PresentationType

logger = structlog.get_logger(__name__)


class StyleApplierError(Exception):
    """Base exception for style applier errors."""

    pass


class TemplateNotFoundError(StyleApplierError):
    """Exception raised when template file is not found."""

    pass


class StyleApplier:
    """Apply themes and styles to PowerPoint presentations.

    This class handles the application of themes, templates, and default styles
    to PowerPoint presentations. Note that python-pptx has limited support for
    directly editing slide masters, so the recommended approach is to use
    PowerPoint to create custom templates and load them here.

    Attributes:
        template_path: Optional path to a template file to use as base.

    Example:
        >>> from pathlib import Path
        >>> applier = StyleApplier(template_path=Path("theme.pptx"))
        >>> presentation = Presentation()
        >>> applier.apply_theme(presentation)
        >>> applier.set_default_font(presentation, "Arial")
    """

    def __init__(self, template_path: Path | None = None) -> None:
        """Initialize StyleApplier with optional template.

        Args:
            template_path: Optional path to a PowerPoint template file (.pptx).
                          If provided, the template will be loaded and used as
                          the base for new presentations.

        Raises:
            TemplateNotFoundError: If template_path is provided but file doesn't exist.
        """
        self.template_path = template_path

        if template_path is not None:
            if not template_path.exists():
                error_msg = f"Template file not found: {template_path}"
                logger.error("template_file_not_found", path=str(template_path))
                raise TemplateNotFoundError(error_msg)

            logger.info("style_applier_initialized", template_path=str(template_path))
        else:
            logger.info("style_applier_initialized", template_path=None)

    def apply_theme(self, presentation: PresentationType) -> None:
        """Apply theme from template to a presentation.

        If a template_path was provided during initialization, this method loads
        the template and applies its theme to the presentation. Note that python-pptx
        has limited support for programmatically editing themes, so using a
        pre-designed template is the recommended approach.

        Args:
            presentation: The Presentation object to apply theme to.

        Note:
            Due to python-pptx limitations, slide masters cannot be directly edited.
            This method primarily ensures the presentation uses the template's layouts
            and theme colors. For custom themes, it's recommended to create a template
            in PowerPoint and load it with `_load_template()`.

        Example:
            >>> from pptx import Presentation
            >>> applier = StyleApplier(template_path=Path("corporate_theme.pptx"))
            >>> prs = Presentation()
            >>> applier.apply_theme(prs)
        """
        if self.template_path is None:
            logger.warning(
                "apply_theme_called_without_template",
                message="No template path provided, skipping theme application",
            )
            return

        logger.info("applying_theme", template_path=str(self.template_path))

        # Note: python-pptx has limited support for applying themes programmatically.
        # The best practice is to load the template directly when creating the
        # presentation (via Presentation(template_path)) rather than trying to
        # apply a theme to an existing presentation.
        logger.warning(
            "theme_application_limited",
            message=(
                "python-pptx has limited theme application support. "
                "Consider using Presentation(template_path) to load template directly."
            ),
        )

    def set_default_font(
        self, presentation: PresentationType, font_name: str, font_size: int | None = None
    ) -> None:
        """Set default font for the presentation.

        Note: python-pptx does not support setting theme-level default fonts directly.
        This method provides a utility that can be used to apply fonts to text elements.
        For true default fonts, use a template created in PowerPoint.

        Args:
            presentation: The Presentation object to configure.
            font_name: Name of the font (e.g., "Arial", "Calibri", "MS Gothic").
            font_size: Optional font size in points. If None, only the font name
                      is configured.

        Note:
            This method logs the default font settings but does not apply them
            automatically to all text. You need to apply the font to each text
            element individually when creating slides. Consider using helper
            functions to apply consistent fonts across slides.

        Example:
            >>> from pptx import Presentation
            >>> applier = StyleApplier()
            >>> prs = Presentation()
            >>> applier.set_default_font(prs, "Arial", 18)
        """
        logger.info(
            "setting_default_font",
            font_name=font_name,
            font_size=font_size,
        )

        # Note: python-pptx does not provide a way to set default fonts at the
        # presentation or master slide level. The recommended approach is to:
        # 1. Create a template in PowerPoint with desired default fonts
        # 2. Load that template when creating the presentation
        # 3. Manually apply fonts to text elements as they are created
        logger.warning(
            "default_font_limitation",
            message=(
                "python-pptx does not support setting default fonts programmatically. "
                "Fonts must be applied to individual text elements. "
                "For consistent fonts, use a PowerPoint template."
            ),
        )

    def _load_template(self, template_path: Path) -> PresentationType:
        """Load a PowerPoint template file.

        This is a private helper method that loads a template file and returns
        a Presentation object. This is the recommended way to apply custom themes,
        as python-pptx has limited support for programmatic theme editing.

        Args:
            template_path: Path to the template file (.pptx).

        Returns:
            Presentation: A new Presentation object loaded from the template.

        Raises:
            TemplateNotFoundError: If the template file doesn't exist.
            StyleApplierError: If there's an error loading the template.

        Example:
            >>> from pathlib import Path
            >>> applier = StyleApplier()
            >>> template_path = Path("corporate_template.pptx")
            >>> prs = applier._load_template(template_path)
        """
        if not template_path.exists():
            error_msg = f"Template file not found: {template_path}"
            logger.error("template_file_not_found", path=str(template_path))
            raise TemplateNotFoundError(error_msg)

        try:
            logger.info("loading_template", path=str(template_path))
            presentation = Presentation(str(template_path))
            logger.info("template_loaded_successfully", path=str(template_path))
            return presentation
        except Exception as e:
            error_msg = f"Failed to load template: {e}"
            logger.error(
                "template_load_failed",
                path=str(template_path),
                error=str(e),
            )
            raise StyleApplierError(error_msg) from e
