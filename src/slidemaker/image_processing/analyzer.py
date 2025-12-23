"""Image Analyzer

LLM Vision APIを使用してスライド画像を分析し、テキスト・画像要素を検出します。

Main Components:
    - ImageAnalyzer: 画像分析とPageDefinition生成
"""

import base64
import json
from io import BytesIO
from typing import Any

import structlog
from PIL import Image
from pydantic import ValidationError

from slidemaker.core.models.common import Alignment, Color, FitMode, Position, Size
from slidemaker.core.models.element import FontConfig, ImageElement, TextElement
from slidemaker.core.models.page_definition import PageDefinition
from slidemaker.image_processing.exceptions import ImageAnalysisError
from slidemaker.llm.base import LLMError, LLMTimeoutError
from slidemaker.llm.manager import LLMManager
from slidemaker.llm.prompts.image_processing import create_image_analysis_prompt


class ImageAnalyzer:
    """LLM Vision APIによる画像分析

    スライド画像を分析し、テキスト要素・画像要素の位置とスタイル情報を抽出します。
    LLMManagerを使用してVision APIに画像とプロンプトを送信し、
    構造化されたJSON応答をPageDefinitionに変換します。

    Attributes:
        llm_manager: LLMマネージャー
        logger: 構造化ロガー
        max_retries: 最大リトライ回数
        slide_dimensions: スライドサイズ（幅、高さ）

    Example:
        >>> llm_manager = LLMManager(config)
        >>> analyzer = ImageAnalyzer(llm_manager)
        >>> image = Image.open("slide.png")
        >>> page_def = await analyzer.analyze_slide_image(image)
    """

    def __init__(
        self,
        llm_manager: LLMManager,
        max_retries: int = 3,
        slide_dimensions: tuple[int, int] = (1920, 1080),
    ) -> None:
        """ImageAnalyzerの初期化

        Args:
            llm_manager: LLMマネージャー
            max_retries: 最大リトライ回数（デフォルト: 3）
            slide_dimensions: スライドサイズ（幅、高さ）（デフォルト: (1920, 1080)）
        """
        self.llm_manager = llm_manager
        self.logger = structlog.get_logger(__name__)
        self.max_retries = max_retries
        self.slide_dimensions = slide_dimensions

    async def analyze_slide_image(self, image: Image.Image) -> PageDefinition:
        """スライド画像を分析してPageDefinitionを生成

        LLM Vision APIを使用して画像を分析し、テキスト要素・画像要素を検出します。
        リトライロジックにより、一時的なLLMエラーに対応します。

        Args:
            image: 分析対象の画像（PIL.Image）

        Returns:
            PageDefinition: テキスト・画像要素のリスト、スタイル情報

        Raises:
            ImageAnalysisError: 画像分析失敗（リトライ回数超過）
            LLMTimeoutError: LLMタイムアウト
            ValidationError: レスポンスのバリデーションエラー
        """
        self.logger.info(
            "analyzing_slide_image",
            image_size=image.size,
            slide_dimensions=self.slide_dimensions,
        )

        for attempt in range(1, self.max_retries + 1):
            try:
                # 画像をBase64エンコード
                image_base64 = self._encode_image_base64(image)

                # プロンプトの作成
                system_prompt, user_prompt = create_image_analysis_prompt(
                    width=self.slide_dimensions[0], height=self.slide_dimensions[1]
                )

                # LLMでの画像分析
                self.logger.debug(
                    "calling_llm_analyze_image",
                    attempt=attempt,
                    max_retries=self.max_retries,
                )

                llm_response = await self.llm_manager.analyze_image(
                    prompt=user_prompt,
                    system_prompt=system_prompt,
                    image_data=image_base64,
                )

                # レスポンスのパースとPageDefinition生成
                page_definition = self._parse_llm_response(
                    llm_response, image.size, self.slide_dimensions
                )

                self.logger.info(
                    "analysis_completed",
                    elements_count=len(page_definition.elements),
                    attempt=attempt,
                )
                return page_definition

            except LLMTimeoutError as e:
                self.logger.error(
                    "llm_timeout",
                    attempt=attempt,
                    max_retries=self.max_retries,
                    error=str(e),
                )
                if attempt >= self.max_retries:
                    raise ImageAnalysisError(
                        f"LLM timeout after {attempt} attempts",
                        llm_provider=self.llm_manager.composition_llm.__class__.__name__,
                        attempt=attempt,
                    ) from e
                # 次の試行へ
                continue

            except (LLMError, json.JSONDecodeError, ValidationError) as e:
                self.logger.error(
                    "analysis_error",
                    attempt=attempt,
                    max_retries=self.max_retries,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                if attempt >= self.max_retries:
                    raise ImageAnalysisError(
                        f"Image analysis failed after {attempt} attempts: {str(e)}",
                        llm_provider=self.llm_manager.composition_llm.__class__.__name__,
                        attempt=attempt,
                        details={"original_error": str(e)},
                    ) from e
                # 次の試行へ
                continue

        # 理論上ここには到達しないが、型チェックのため
        raise ImageAnalysisError(
            f"Image analysis failed after {self.max_retries} attempts",
            llm_provider=self.llm_manager.composition_llm.__class__.__name__,
            attempt=self.max_retries,
        )

    def _encode_image_base64(self, image: Image.Image) -> str:
        """画像をBase64エンコード

        PIL.ImageをBase64文字列に変換します。PNG形式で保存します。

        Args:
            image: PIL.Image

        Returns:
            str: Base64エンコードされた画像データ
        """
        buffer = BytesIO()
        # RGB形式に変換（PNGでの保存に必要）
        if image.mode != "RGB":
            image = image.convert("RGB")
        image.save(buffer, format="PNG")
        image_bytes = buffer.getvalue()
        return base64.b64encode(image_bytes).decode("utf-8")

    def _parse_llm_response(
        self,
        response: dict[str, Any],
        original_image_size: tuple[int, int],
        slide_dimensions: tuple[int, int],
    ) -> PageDefinition:
        """LLMレスポンスをパースしてPageDefinitionに変換

        LLMが返した構造化JSONデータをパースし、PageDefinitionオブジェクトを生成します。
        座標の正規化、スタイル情報の推定、要素のバリデーションを行います。

        Args:
            response: LLMからのレスポンス（構造化JSON）
            original_image_size: 元画像のサイズ（幅、高さ）
            slide_dimensions: スライドサイズ（幅、高さ）

        Returns:
            PageDefinition: パースされたページ定義

        Raises:
            ValidationError: レスポンス構造が不正
        """
        elements_data = response.get("elements", [])
        background_data = response.get("background", {})

        # ページ番号とタイトルの設定
        page_number = response.get("page_number", 1)
        title = response.get("title", "Slide")

        # 背景の設定
        background_color, background_image = self._parse_background(background_data)

        # PageDefinitionの作成
        page_definition = PageDefinition(
            page_number=page_number,
            title=title,
            elements=[],
            background_color=background_color,
            background_image=background_image,
        )

        # 各要素のパース
        for element_data in elements_data:
            element = self._parse_element(
                element_data, original_image_size, slide_dimensions
            )
            if element is not None:
                page_definition.add_element(element)

        return page_definition

    def _parse_element(
        self,
        data: dict[str, Any],
        original_image_size: tuple[int, int],
        slide_dimensions: tuple[int, int],
    ) -> TextElement | ImageElement | None:
        """要素のパース

        要素タイプに応じてTextElementまたはImageElementを作成します。
        座標を正規化し、スタイル情報を適用します。

        Args:
            data: 要素データ
            original_image_size: 元画像のサイズ
            slide_dimensions: スライドサイズ

        Returns:
            TextElement | ImageElement | None: パースされた要素
                （不明なタイプの場合はNone）
        """
        element_type = data.get("type")

        if element_type == "text":
            return self._parse_text_element(data, original_image_size, slide_dimensions)
        elif element_type == "image":
            return self._parse_image_element(
                data, original_image_size, slide_dimensions
            )
        else:
            self.logger.warning("unknown_element_type", type=element_type)
            return None

    def _parse_text_element(
        self,
        data: dict[str, Any],
        original_image_size: tuple[int, int],
        slide_dimensions: tuple[int, int],
    ) -> TextElement:
        """TextElementのパース

        LLM出力からTextElementを作成します。座標を正規化し、
        フォント・色・配置などのスタイル情報を適用します。

        Args:
            data: テキスト要素データ
            original_image_size: 元画像のサイズ
            slide_dimensions: スライドサイズ

        Returns:
            TextElement: パースされたテキスト要素
        """
        # 座標の正規化
        position = self._normalize_position(
            data.get("position", {}), original_image_size, slide_dimensions
        )
        size = self._normalize_size(
            data.get("size", {}), original_image_size, slide_dimensions
        )

        # スタイル情報のパース
        style_data = data.get("style", {})
        font_config = self._parse_font_config(style_data)
        alignment = self._parse_alignment(style_data.get("alignment", "left"))

        return TextElement(
            content=data.get("content", ""),
            position=position,
            size=size,
            font=font_config,
            alignment=alignment,
        )

    def _parse_image_element(
        self,
        data: dict[str, Any],
        original_image_size: tuple[int, int],
        slide_dimensions: tuple[int, int],
    ) -> ImageElement:
        """ImageElementのパース

        LLM出力からImageElementを作成します。座標を正規化し、
        画像パスと表示モードを設定します。

        Args:
            data: 画像要素データ
            original_image_size: 元画像のサイズ
            slide_dimensions: スライドサイズ

        Returns:
            ImageElement: パースされた画像要素
        """
        # 座標の正規化
        position = self._normalize_position(
            data.get("position", {}), original_image_size, slide_dimensions
        )
        size = self._normalize_size(
            data.get("size", {}), original_image_size, slide_dimensions
        )

        # 画像パスと表示モード
        # Note: 実際の画像パスはImageProcessorによって後で設定される
        source = data.get("image_path", data.get("source", ""))
        fit_mode = FitMode.CONTAIN  # デフォルト
        alt_text = data.get("alt_text", data.get("description", ""))

        return ImageElement(
            source=source,
            position=position,
            size=size,
            fit_mode=fit_mode,
            alt_text=alt_text,
        )

    def _normalize_position(
        self,
        position_data: dict[str, Any],
        original_image_size: tuple[int, int],
        slide_dimensions: tuple[int, int],
    ) -> Position:
        """座標の正規化

        元画像の座標をスライドサイズに正規化します。
        アスペクト比を考慮した座標変換を行います。

        Args:
            position_data: 座標データ（x, y）
            original_image_size: 元画像のサイズ
            slide_dimensions: スライドサイズ

        Returns:
            Position: 正規化された座標
        """
        x = position_data.get("x", 0)
        y = position_data.get("y", 0)

        # ゼロ除算チェック
        if original_image_size[0] == 0 or original_image_size[1] == 0:
            self.logger.warning(
                "Invalid original image size (zero dimension), returning default position (0, 0)",
                original_size=original_image_size,
            )
            return Position(x=0, y=0)

        # 元画像とスライドのスケール比を計算
        scale_x = slide_dimensions[0] / original_image_size[0]
        scale_y = slide_dimensions[1] / original_image_size[1]

        # 座標を変換
        normalized_x = int(x * scale_x)
        normalized_y = int(y * scale_y)

        # 座標のサニタイズ（0以上、スライドサイズ以下）
        normalized_x = max(0, min(normalized_x, slide_dimensions[0]))
        normalized_y = max(0, min(normalized_y, slide_dimensions[1]))

        return Position(x=normalized_x, y=normalized_y)

    def _normalize_size(
        self,
        size_data: dict[str, Any],
        original_image_size: tuple[int, int],
        slide_dimensions: tuple[int, int],
    ) -> Size:
        """サイズの正規化

        元画像のサイズをスライドサイズに正規化します。
        アスペクト比を考慮したサイズ変換を行います。

        Args:
            size_data: サイズデータ（width, height）
            original_image_size: 元画像のサイズ
            slide_dimensions: スライドサイズ

        Returns:
            Size: 正規化されたサイズ
        """
        width = size_data.get("width", 100)
        height = size_data.get("height", 50)

        # ゼロ除算チェック
        if original_image_size[0] == 0 or original_image_size[1] == 0:
            self.logger.warning(
                "Invalid original image size (zero dimension), returning default size (100, 50)",
                original_size=original_image_size,
            )
            return Size(width=100, height=50)

        # 元画像とスライドのスケール比を計算
        scale_x = slide_dimensions[0] / original_image_size[0]
        scale_y = slide_dimensions[1] / original_image_size[1]

        # サイズを変換
        normalized_width = int(width * scale_x)
        normalized_height = int(height * scale_y)

        # サイズのサニタイズ（最小1、最大スライドサイズ）
        normalized_width = max(1, min(normalized_width, slide_dimensions[0]))
        normalized_height = max(1, min(normalized_height, slide_dimensions[1]))

        return Size(width=normalized_width, height=normalized_height)

    def _parse_font_config(self, style_data: dict[str, Any]) -> FontConfig:
        """FontConfigのパース

        スタイル情報からFontConfigオブジェクトを生成します。
        フォント名、サイズ、色、太字・イタリックなどのスタイルを設定します。

        Args:
            style_data: スタイルデータ

        Returns:
            FontConfig: パースされたフォント設定
        """
        font_family = style_data.get("font_name", style_data.get("font_family", "Arial"))
        font_size = style_data.get("font_size", 18)
        color = self._parse_color(style_data.get("color", {}))
        bold = style_data.get("bold", False)
        italic = style_data.get("italic", False)
        underline = style_data.get("underline", False)

        return FontConfig(
            family=font_family,
            size=font_size,
            color=color,
            bold=bold,
            italic=italic,
            underline=underline,
        )

    def _parse_color(self, color_data: dict[str, Any] | str) -> Color:
        """Colorのパース

        色データをColorオブジェクトに変換します。
        RGB値またはHEX文字列をサポートします。

        Args:
            color_data: 色データ（RGB dict または HEX string）

        Returns:
            Color: パースされた色オブジェクト
        """
        # デフォルトは黒
        default_color = Color(hex_value="#000000")

        if isinstance(color_data, dict):
            red = color_data.get("red", 0)
            green = color_data.get("green", 0)
            blue = color_data.get("blue", 0)

            # RGB値のバリデーション（0-255）
            red = max(0, min(255, int(red)))
            green = max(0, min(255, int(green)))
            blue = max(0, min(255, int(blue)))

            return Color.from_rgb(red, green, blue)
        elif isinstance(color_data, str):
            # HEX文字列の場合（例: "#FF0000"）
            if color_data.startswith("#") and len(color_data) == 7:
                try:
                    return Color(hex_value=color_data)
                except ValueError:
                    self.logger.warning("invalid_hex_color", color=color_data)
                    return default_color
        return default_color

    def _parse_alignment(self, alignment_str: str) -> Alignment:
        """Alignmentのパース

        文字列からAlignmentオブジェクトに変換します。

        Args:
            alignment_str: 配置文字列（"left", "center", "right"）

        Returns:
            Alignment: パースされた配置
        """
        alignment_map = {
            "left": Alignment.LEFT,
            "center": Alignment.CENTER,
            "right": Alignment.RIGHT,
        }
        return alignment_map.get(alignment_str.lower(), Alignment.LEFT)

    def _parse_background(
        self, background_data: dict[str, Any]
    ) -> tuple[str | None, str | None]:
        """背景のパース

        背景データをbackground_colorとbackground_imageに変換します。

        Args:
            background_data: 背景データ

        Returns:
            tuple[str | None, str | None]: (background_color, background_image)
        """
        bg_type = background_data.get("type")

        if bg_type == "color":
            color = self._parse_color(background_data.get("value", {}))
            return color.hex_value, None
        elif bg_type == "image":
            return None, background_data.get("value", "")
        else:
            # デフォルトは白
            return "#FFFFFF", None
