"""Composition Parser

LLMが生成したJSON構成データをPydanticモデルに変換します。

Main Components:
    - CompositionParser: 構成データのパースとバリデーション
"""

from typing import Any

import structlog
from pydantic import ValidationError

from slidemaker.core.models.common import Alignment, FitMode, Position, Size
from slidemaker.core.models.element import FontConfig, ImageElement, TextElement
from slidemaker.core.models.page_definition import PageDefinition
from slidemaker.core.models.slide_config import SlideConfig
from slidemaker.workflows.exceptions import WorkflowValidationError


class CompositionParser:
    """LLM生成の構成データをパースしてPydanticモデルに変換

    LLMが生成したJSON構成データをバリデーションし、
    SlideConfigとPageDefinitionに変換します。データの正規化、
    デフォルト値の適用、エラーハンドリングを行います。

    Example:
        >>> parser = CompositionParser()
        >>> composition = {
        ...     "slide_config": {"size": "16:9"},
        ...     "pages": [{"title": "Slide 1", "elements": []}]
        ... }
        >>> config = parser.parse_slide_config(composition["slide_config"])
        >>> pages = parser.parse_pages(composition["pages"])
    """

    def __init__(self) -> None:
        """CompositionParserの初期化"""
        self.logger = structlog.get_logger(__name__)

    def parse_slide_config(self, config_data: dict[str, Any]) -> SlideConfig:
        """SlideConfigのパース

        LLMが生成したスライド設定データをSlideConfigモデルに変換します。
        不足しているフィールドにはデフォルト値を適用します。

        Args:
            config_data: LLM生成のスライド設定データ

        Returns:
            SlideConfig: パースされたスライド設定

        Raises:
            WorkflowValidationError: バリデーションエラー

        Example:
            >>> config = parser.parse_slide_config({
            ...     "size": "16:9",
            ...     "theme": "corporate"
            ... })
        """
        try:
            # デフォルト値の設定
            normalized = self._normalize_slide_config(config_data)

            # Pydanticモデルに変換
            slide_config = SlideConfig(**normalized)

            self.logger.debug("slide_config_parsed", config=normalized)
            return slide_config

        except ValidationError as e:
            error_msg = f"Failed to parse slide config: {e}"
            self.logger.error("slide_config_parse_error", error=str(e))
            raise WorkflowValidationError(error_msg) from e

    def parse_pages(self, pages_data: list[dict[str, Any]]) -> list[PageDefinition]:
        """PageDefinitionのパース

        LLMが生成したページデータのリストをPageDefinitionモデルのリストに変換します。
        各ページの要素（テキスト、画像）を解析し、バリデーションを行います。

        Args:
            pages_data: LLM生成のページデータのリスト

        Returns:
            list[PageDefinition]: パースされたページ定義のリスト

        Raises:
            WorkflowValidationError: バリデーションエラー

        Example:
            >>> pages = parser.parse_pages([
            ...     {
            ...         "title": "Slide 1",
            ...         "elements": [
            ...             {
            ...                 "type": "text",
            ...                 "position": {"x": 100, "y": 200},
            ...                 "size": {"width": 800, "height": 100},
            ...                 "content": "Hello"
            ...             }
            ...         ]
            ...     }
            ... ])
        """
        pages = []

        for i, page_data in enumerate(pages_data):
            try:
                normalized = self._normalize_page(page_data, page_number=i + 1)
                page = PageDefinition(**normalized)
                pages.append(page)

            except ValidationError as e:
                error_msg = f"Failed to parse page {i + 1}: {e}"
                self.logger.error("page_parse_error", page_number=i + 1, error=str(e))
                raise WorkflowValidationError(error_msg) from e

        self.logger.info("pages_parsed", count=len(pages))
        return pages

    def _normalize_slide_config(self, data: dict[str, Any]) -> dict[str, Any]:
        """SlideConfigデータの正規化

        不足しているフィールドにデフォルト値を適用します。

        Args:
            data: 生データ

        Returns:
            dict: 正規化されたデータ
        """
        return {
            "size": data.get("size", "16:9"),
            "theme": data.get("theme", "default"),
        }

    def _normalize_page(
        self,
        data: dict[str, Any],
        page_number: int,
    ) -> dict[str, Any]:
        """PageDefinitionデータの正規化

        ページデータの各要素をパースし、正規化します。

        Args:
            data: 生データ
            page_number: ページ番号

        Returns:
            dict: 正規化されたデータ
        """
        # 要素のパース
        elements = []
        for elem_data in data.get("elements", []):
            element = self._parse_element(elem_data)
            if element:
                elements.append(element)

        return {
            "page_number": page_number,
            "title": data.get("title", ""),
            "background_color": data.get("background_color"),
            "background_image": data.get("background_image"),
            "elements": elements,
        }

    def _parse_element(
        self, data: dict[str, Any]
    ) -> TextElement | ImageElement | None:
        """要素のパース

        要素タイプに応じてTextElementまたはImageElementを作成します。

        Args:
            data: 要素データ

        Returns:
            TextElement | ImageElement | None: パースされた要素
                （不明なタイプの場合はNone）
        """
        element_type = data.get("type")

        if element_type == "text":
            return self._parse_text_element(data)
        elif element_type == "image":
            return self._parse_image_element(data)
        else:
            self.logger.warning("unknown_element_type", type=element_type)
            return None

    def _parse_text_element(self, data: dict[str, Any]) -> TextElement:
        """TextElementのパース

        テキスト要素のデータをTextElementモデルに変換します。
        フォント設定や配置情報を正規化して適用します。

        Args:
            data: テキスト要素データ

        Returns:
            TextElement: パースされたテキスト要素

        Raises:
            ValidationError: データが不正な場合
        """
        # Position and Size
        position = Position(
            x=int(data["position"]["x"]),
            y=int(data["position"]["y"]),
        )
        size = Size(
            width=int(data["size"]["width"]),
            height=int(data["size"]["height"]),
        )

        # FontConfig
        font_data = data.get("font", {})
        font = FontConfig(
            family=font_data.get("family", "Arial"),
            size=font_data.get("size", 18),
            color=font_data.get("color", "#000000"),
            bold=font_data.get("bold", False),
            italic=font_data.get("italic", False),
            underline=font_data.get("underline", False),
        )

        # Alignment
        alignment_str = data.get("alignment", "left")
        try:
            alignment = Alignment(alignment_str)
        except ValueError:
            self.logger.warning(
                "invalid_alignment",
                value=alignment_str,
                default="left",
            )
            alignment = Alignment.LEFT

        return TextElement(
            position=position,
            size=size,
            content=data["content"],
            font=font,
            alignment=alignment,
            z_index=data.get("z_index", 0),
        )

    def _parse_image_element(self, data: dict[str, Any]) -> ImageElement:
        """ImageElementのパース

        画像要素のデータをImageElementモデルに変換します。
        フィットモードやサイズ情報を正規化して適用します。

        Args:
            data: 画像要素データ

        Returns:
            ImageElement: パースされた画像要素

        Raises:
            ValidationError: データが不正な場合
        """
        # Position and Size
        position = Position(
            x=int(data["position"]["x"]),
            y=int(data["position"]["y"]),
        )
        size = Size(
            width=int(data["size"]["width"]),
            height=int(data["size"]["height"]),
        )

        # FitMode
        fit_mode_str = data.get("fit_mode", "contain")
        try:
            fit_mode = FitMode(fit_mode_str)
        except ValueError:
            self.logger.warning(
                "invalid_fit_mode",
                value=fit_mode_str,
                default="contain",
            )
            fit_mode = FitMode.CONTAIN

        return ImageElement(
            position=position,
            size=size,
            source=data["source"],
            fit_mode=fit_mode,
            z_index=data.get("z_index", 0),
        )
