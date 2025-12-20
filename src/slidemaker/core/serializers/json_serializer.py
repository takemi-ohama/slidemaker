"""JSON serialization for slide definitions."""

import json
from pathlib import Path
from typing import Any

from slidemaker.core.models import PageDefinition, SlideConfig


class JSONSerializer:
    """Serializer for converting slide definitions to/from JSON."""

    @staticmethod
    def serialize_config(config: SlideConfig) -> dict[str, Any]:
        """Serialize SlideConfig to dictionary."""
        return config.model_dump(mode="json")

    @staticmethod
    def deserialize_config(data: dict[str, Any]) -> SlideConfig:
        """Deserialize dictionary to SlideConfig."""
        return SlideConfig.model_validate(data)

    @staticmethod
    def serialize_page(page: PageDefinition) -> dict[str, Any]:
        """Serialize PageDefinition to dictionary."""
        return page.model_dump(mode="json")

    @staticmethod
    def deserialize_page(data: dict[str, Any]) -> PageDefinition:
        """Deserialize dictionary to PageDefinition."""
        return PageDefinition.model_validate(data)

    @classmethod
    def serialize_presentation(
        cls, config: SlideConfig, pages: list[PageDefinition]
    ) -> dict[str, Any]:
        """Serialize entire presentation to dictionary."""
        return {
            "slide_config": cls.serialize_config(config),
            "pages": [cls.serialize_page(page) for page in pages],
        }

    @classmethod
    def deserialize_presentation(
        cls, data: dict[str, Any]
    ) -> tuple[SlideConfig, list[PageDefinition]]:
        """Deserialize presentation from dictionary."""
        config = cls.deserialize_config(data["slide_config"])
        pages = [cls.deserialize_page(page_data) for page_data in data["pages"]]
        return config, pages

    @classmethod
    def save_to_file(
        cls, config: SlideConfig, pages: list[PageDefinition], file_path: str | Path
    ) -> None:
        """Save presentation to JSON file."""
        data = cls.serialize_presentation(config, pages)
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load_from_file(cls, file_path: str | Path) -> tuple[SlideConfig, list[PageDefinition]]:
        """
        Load presentation from JSON file.

        Args:
            file_path: Path to JSON file

        Returns:
            Tuple of (SlideConfig, list of PageDefinition)

        Raises:
            FileNotFoundError: If file does not exist
            ValueError: If file contains invalid JSON or schema
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Presentation file not found: {path}")

        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Invalid JSON format in {path}: {e.msg} at line {e.lineno}, column {e.colno}"
            ) from e
        except Exception as e:
            raise ValueError(f"Failed to read file {path}: {e}") from e

        if not isinstance(data, dict):
            raise ValueError(f"Invalid presentation format in {path}: expected object, got {type(data).__name__}")

        if "slide_config" not in data:
            raise ValueError(f"Invalid presentation format in {path}: missing 'slide_config' field")

        if "pages" not in data:
            raise ValueError(f"Invalid presentation format in {path}: missing 'pages' field")

        try:
            return cls.deserialize_presentation(data)
        except Exception as e:
            raise ValueError(f"Invalid presentation schema in {path}: {e}") from e
