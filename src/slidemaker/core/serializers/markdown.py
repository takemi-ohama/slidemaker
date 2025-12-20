"""Markdown serialization for slide content."""

from pathlib import Path

from slidemaker.core.models import PageDefinition, SlideConfig


class MarkdownSerializer:
    """Serializer for converting slide definitions to/from Markdown."""

    @staticmethod
    def serialize_page(page: PageDefinition) -> str:
        """Serialize a single page to Markdown."""
        lines: list[str] = []

        # Page title as H2
        if page.title:
            lines.append(f"## {page.title}")
            lines.append("")

        # Text elements as bullet points or paragraphs
        for element in page.get_text_elements():
            content = element.content.strip()
            if content:
                # Simple bullet point if content starts with dash/asterisk
                if content.startswith(("-", "*")):
                    lines.append(content)
                else:
                    lines.append(f"- {content}")

        # Image elements as markdown images
        for element in page.get_image_elements():
            alt_text = element.alt_text or f"Image {element.source}"
            lines.append(f"![{alt_text}]({element.source})")

        # Speaker notes
        if page.notes:
            lines.append("")
            lines.append("---")
            lines.append(f"Notes: {page.notes}")

        lines.append("")
        return "\n".join(lines)

    @classmethod
    def serialize_presentation(
        cls, config: SlideConfig, pages: list[PageDefinition]
    ) -> str:
        """Serialize entire presentation to Markdown."""
        lines: list[str] = []

        # Title from config
        title = config.output_filename.replace(".pptx", "").replace("_", " ").title()
        lines.append(f"# {title}")
        lines.append("")

        # Metadata comment
        lines.append(f"<!-- Slide Size: {config.size.value} -->")
        lines.append(f"<!-- Theme: {config.theme or 'default'} -->")
        lines.append("")

        # All pages
        for page in pages:
            lines.append(cls.serialize_page(page))

        return "\n".join(lines)

    @classmethod
    def save_to_file(
        cls, config: SlideConfig, pages: list[PageDefinition], file_path: str | Path
    ) -> None:
        """Save presentation to Markdown file."""
        content = cls.serialize_presentation(config, pages)
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8") as f:
            f.write(content)

    @staticmethod
    def parse_markdown(content: str) -> list[dict[str, str]]:
        """
        Parse Markdown content into basic page structure.

        This is a simplified parser. Full parsing would be handled by LLM.

        Returns:
            List of dictionaries with 'title' and 'content' for each slide.
        """
        pages: list[dict[str, str]] = []
        current_page: dict[str, str] | None = None
        current_content: list[str] = []

        for line in content.split("\n"):
            line = line.rstrip()

            # H2 headings start a new page
            if line.startswith("## "):
                if current_page is not None:
                    current_page["content"] = "\n".join(current_content).strip()
                    pages.append(current_page)

                current_page = {"title": line[3:].strip(), "content": ""}
                current_content = []

            elif current_page is not None:
                current_content.append(line)

        # Add last page
        if current_page is not None:
            current_page["content"] = "\n".join(current_content).strip()
            pages.append(current_page)

        return pages

    @classmethod
    def load_from_file(cls, file_path: str | Path) -> list[dict[str, str]]:
        """
        Load and parse Markdown file.

        Returns basic page structure that needs to be processed by LLM.
        """
        path = Path(file_path)
        with path.open("r", encoding="utf-8") as f:
            content = f.read()

        return cls.parse_markdown(content)
