"""Tests for ImageAnalyzer

ImageAnalyzerクラスの単体テストです。

Test Coverage:
    - 基本的な画像分析（テキスト、画像、混在）
    - LLMレスポンスのパース（正常系、異常系）
    - 座標・サイズの正規化
    - スタイル情報のパース（フォント、色、配置）
    - エラーハンドリング（LLMタイムアウト、JSONパースエラー、不正座標）
    - リトライロジック
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from PIL import Image

from slidemaker.core.models.common import Alignment
from slidemaker.core.models.element import ImageElement, TextElement
from slidemaker.core.models.page_definition import PageDefinition
from slidemaker.image_processing.analyzer import ImageAnalyzer
from slidemaker.image_processing.exceptions import ImageAnalysisError
from slidemaker.llm.base import LLMError, LLMTimeoutError
from slidemaker.llm.manager import LLMManager


@pytest.fixture
def mock_llm_manager() -> MagicMock:
    """LLMManagerのモック"""
    manager = MagicMock(spec=LLMManager)
    manager.composition_llm = MagicMock()
    manager.composition_llm.__class__.__name__ = "ClaudeAdapter"
    manager.analyze_image = AsyncMock()
    return manager


@pytest.fixture
def image_analyzer(mock_llm_manager: MagicMock) -> ImageAnalyzer:
    """ImageAnalyzerのフィクスチャ"""
    return ImageAnalyzer(mock_llm_manager)


@pytest.fixture
def sample_image() -> Image.Image:
    """サンプル画像を作成"""
    return Image.new("RGB", (1920, 1080), color="white")


class TestImageAnalyzerInit:
    """ImageAnalyzerの初期化テスト"""

    def test_init_success(self, mock_llm_manager: MagicMock) -> None:
        """正常な初期化"""
        analyzer = ImageAnalyzer(mock_llm_manager)
        assert analyzer.llm_manager == mock_llm_manager
        assert analyzer.max_retries == 3
        assert analyzer.slide_dimensions == (1920, 1080)
        assert analyzer.logger is not None

    def test_init_with_custom_params(self, mock_llm_manager: MagicMock) -> None:
        """カスタムパラメータでの初期化"""
        analyzer = ImageAnalyzer(
            mock_llm_manager,
            max_retries=5,
            slide_dimensions=(1280, 720),
        )
        assert analyzer.max_retries == 5
        assert analyzer.slide_dimensions == (1280, 720)


class TestAnalyzeSlideImage:
    """analyze_slide_imageメソッドのテスト"""

    @pytest.mark.asyncio
    async def test_analyze_slide_basic(
        self,
        image_analyzer: ImageAnalyzer,
        mock_llm_manager: MagicMock,
        sample_image: Image.Image,
    ) -> None:
        """基本的なスライド分析"""
        # LLMレスポンスのモック
        mock_response = {
            "page_number": 1,
            "title": "Test Slide",
            "elements": [
                {
                    "type": "text",
                    "position": {"x": 100, "y": 100},
                    "size": {"width": 500, "height": 100},
                    "content": "Hello World",
                    "style": {"font_name": "Arial", "font_size": 24},
                }
            ],
            "background": {"type": "color", "value": {"red": 255, "green": 255, "blue": 255}},
        }
        mock_llm_manager.analyze_image.return_value = mock_response

        result = await image_analyzer.analyze_slide_image(sample_image)

        assert isinstance(result, PageDefinition)
        assert result.page_number == 1
        assert result.title == "Test Slide"
        assert len(result.elements) == 1
        assert isinstance(result.elements[0], TextElement)
        assert result.elements[0].content == "Hello World"

    @pytest.mark.asyncio
    async def test_analyze_slide_text_elements(
        self,
        image_analyzer: ImageAnalyzer,
        mock_llm_manager: MagicMock,
        sample_image: Image.Image,
    ) -> None:
        """テキスト要素の検出"""
        mock_response = {
            "elements": [
                {
                    "type": "text",
                    "position": {"x": 100, "y": 100},
                    "size": {"width": 500, "height": 100},
                    "content": "Title",
                    "style": {
                        "font_name": "Arial",
                        "font_size": 36,
                        "color": {"red": 0, "green": 0, "blue": 0},
                        "bold": True,
                        "alignment": "center",
                    },
                },
                {
                    "type": "text",
                    "position": {"x": 100, "y": 300},
                    "size": {"width": 800, "height": 400},
                    "content": "Body text",
                    "style": {"font_name": "Calibri", "font_size": 18},
                },
            ],
            "background": {},
        }
        mock_llm_manager.analyze_image.return_value = mock_response

        result = await image_analyzer.analyze_slide_image(sample_image)

        assert len(result.elements) == 2
        # タイトル要素
        title = result.elements[0]
        assert isinstance(title, TextElement)
        assert title.content == "Title"
        assert title.font.size == 36
        assert title.font.bold is True
        assert title.alignment == Alignment.CENTER
        # 本文要素
        body = result.elements[1]
        assert isinstance(body, TextElement)
        assert body.content == "Body text"

    @pytest.mark.asyncio
    async def test_analyze_slide_image_elements(
        self,
        image_analyzer: ImageAnalyzer,
        mock_llm_manager: MagicMock,
        sample_image: Image.Image,
    ) -> None:
        """画像要素の検出"""
        mock_response = {
            "elements": [
                {
                    "type": "image",
                    "position": {"x": 500, "y": 200},
                    "size": {"width": 400, "height": 300},
                    "source": "image1.png",
                }
            ],
            "background": {},
        }
        mock_llm_manager.analyze_image.return_value = mock_response

        result = await image_analyzer.analyze_slide_image(sample_image)

        assert len(result.elements) == 1
        element = result.elements[0]
        assert isinstance(element, ImageElement)
        assert element.source == "image1.png"

    @pytest.mark.asyncio
    async def test_analyze_slide_mixed_elements(
        self,
        image_analyzer: ImageAnalyzer,
        mock_llm_manager: MagicMock,
        sample_image: Image.Image,
    ) -> None:
        """テキストと画像の混在検出"""
        mock_response = {
            "elements": [
                {
                    "type": "text",
                    "position": {"x": 100, "y": 50},
                    "size": {"width": 800, "height": 100},
                    "content": "Title",
                    "style": {},
                },
                {
                    "type": "image",
                    "position": {"x": 200, "y": 200},
                    "size": {"width": 400, "height": 300},
                    "source": "photo.png",
                },
                {
                    "type": "text",
                    "position": {"x": 100, "y": 600},
                    "size": {"width": 800, "height": 200},
                    "content": "Description",
                    "style": {},
                },
            ],
            "background": {},
        }
        mock_llm_manager.analyze_image.return_value = mock_response

        result = await image_analyzer.analyze_slide_image(sample_image)

        assert len(result.elements) == 3
        assert isinstance(result.elements[0], TextElement)
        assert isinstance(result.elements[1], ImageElement)
        assert isinstance(result.elements[2], TextElement)

    @pytest.mark.asyncio
    async def test_analyze_slide_empty_elements(
        self,
        image_analyzer: ImageAnalyzer,
        mock_llm_manager: MagicMock,
        sample_image: Image.Image,
    ) -> None:
        """要素なしスライドの処理"""
        mock_response = {
            "elements": [],
            "background": {"type": "color", "value": {"red": 255, "green": 255, "blue": 255}},
        }
        mock_llm_manager.analyze_image.return_value = mock_response

        result = await image_analyzer.analyze_slide_image(sample_image)

        assert len(result.elements) == 0
        assert result.background_color == "#ffffff"

    @pytest.mark.asyncio
    async def test_analyze_slide_llm_timeout_retry(
        self,
        image_analyzer: ImageAnalyzer,
        mock_llm_manager: MagicMock,
        sample_image: Image.Image,
    ) -> None:
        """LLMタイムアウト時のリトライ"""
        # 1回目: タイムアウト、2回目: 成功
        mock_llm_manager.analyze_image.side_effect = [
            LLMTimeoutError("Timeout"),
            {
                "elements": [
                    {
                        "type": "text",
                        "position": {"x": 100, "y": 100},
                        "size": {"width": 500, "height": 100},
                        "content": "Retry success",
                        "style": {},
                    }
                ],
                "background": {},
            },
        ]

        result = await image_analyzer.analyze_slide_image(sample_image)

        assert len(result.elements) == 1
        element = result.elements[0]
        assert isinstance(element, TextElement)
        assert element.content == "Retry success"
        assert mock_llm_manager.analyze_image.call_count == 2

    @pytest.mark.asyncio
    async def test_analyze_slide_llm_timeout_max_retries(
        self,
        image_analyzer: ImageAnalyzer,
        mock_llm_manager: MagicMock,
        sample_image: Image.Image,
    ) -> None:
        """LLMタイムアウト（最大リトライ超過）"""
        mock_llm_manager.analyze_image.side_effect = LLMTimeoutError("Timeout")

        with pytest.raises(ImageAnalysisError) as exc_info:
            await image_analyzer.analyze_slide_image(sample_image)

        assert "timeout after" in str(exc_info.value).lower()
        assert exc_info.value.attempt == 3
        assert mock_llm_manager.analyze_image.call_count == 3

    @pytest.mark.asyncio
    async def test_analyze_slide_llm_error_retry(
        self,
        image_analyzer: ImageAnalyzer,
        mock_llm_manager: MagicMock,
        sample_image: Image.Image,
    ) -> None:
        """LLMエラー時のリトライ"""
        # 1回目: エラー、2回目: 成功
        mock_llm_manager.analyze_image.side_effect = [
            LLMError("API error"),
            {"elements": [], "background": {}},
        ]

        result = await image_analyzer.analyze_slide_image(sample_image)

        assert isinstance(result, PageDefinition)
        assert mock_llm_manager.analyze_image.call_count == 2

    @pytest.mark.asyncio
    async def test_analyze_slide_invalid_json(
        self,
        image_analyzer: ImageAnalyzer,
        mock_llm_manager: MagicMock,
        sample_image: Image.Image,
    ) -> None:
        """無効なJSON出力時のエラー"""
        # 正しいレスポンスだが、要素データが不正
        mock_llm_manager.analyze_image.side_effect = [
            {"invalid": "response"},  # 構造が不正
            {"page_number": 1, "elements": [], "background": {}},  # 2回目成功
        ]

        result = await image_analyzer.analyze_slide_image(sample_image)

        assert isinstance(result, PageDefinition)
        # 1回目で成功（page_numberは省略可能）
        assert mock_llm_manager.analyze_image.call_count == 1


class TestCoordinateNormalization:
    """座標・サイズ正規化のテスト"""

    def test_normalize_position_same_size(self, image_analyzer: ImageAnalyzer) -> None:
        """同一サイズでの座標正規化"""
        position_data = {"x": 100, "y": 200}
        original_size = (1920, 1080)
        slide_size = (1920, 1080)

        result = image_analyzer._normalize_position(
            position_data, original_size, slide_size
        )

        assert result.x == 100
        assert result.y == 200

    def test_normalize_position_scale_up(self, image_analyzer: ImageAnalyzer) -> None:
        """拡大時の座標正規化"""
        position_data = {"x": 100, "y": 200}
        original_size = (960, 540)  # 半分のサイズ
        slide_size = (1920, 1080)

        result = image_analyzer._normalize_position(
            position_data, original_size, slide_size
        )

        assert result.x == 200  # 2倍
        assert result.y == 400  # 2倍

    def test_normalize_position_scale_down(self, image_analyzer: ImageAnalyzer) -> None:
        """縮小時の座標正規化"""
        position_data = {"x": 1000, "y": 500}
        original_size = (3840, 2160)  # 2倍のサイズ
        slide_size = (1920, 1080)

        result = image_analyzer._normalize_position(
            position_data, original_size, slide_size
        )

        assert result.x == 500  # 半分
        assert result.y == 250  # 半分

    def test_normalize_position_clamp_min(self, image_analyzer: ImageAnalyzer) -> None:
        """負の座標のクランプ（最小値）"""
        position_data = {"x": -100, "y": -200}
        original_size = (1920, 1080)
        slide_size = (1920, 1080)

        result = image_analyzer._normalize_position(
            position_data, original_size, slide_size
        )

        assert result.x == 0
        assert result.y == 0

    def test_normalize_position_clamp_max(self, image_analyzer: ImageAnalyzer) -> None:
        """大きすぎる座標のクランプ（最大値）"""
        position_data = {"x": 3000, "y": 2000}
        original_size = (1920, 1080)
        slide_size = (1920, 1080)

        result = image_analyzer._normalize_position(
            position_data, original_size, slide_size
        )

        assert result.x == 1920
        assert result.y == 1080

    def test_normalize_size_same_size(self, image_analyzer: ImageAnalyzer) -> None:
        """同一サイズでのサイズ正規化"""
        size_data = {"width": 500, "height": 300}
        original_size = (1920, 1080)
        slide_size = (1920, 1080)

        result = image_analyzer._normalize_size(size_data, original_size, slide_size)

        assert result.width == 500
        assert result.height == 300

    def test_normalize_size_scale_up(self, image_analyzer: ImageAnalyzer) -> None:
        """拡大時のサイズ正規化"""
        size_data = {"width": 200, "height": 100}
        original_size = (960, 540)
        slide_size = (1920, 1080)

        result = image_analyzer._normalize_size(size_data, original_size, slide_size)

        assert result.width == 400
        assert result.height == 200

    def test_normalize_size_clamp_min(self, image_analyzer: ImageAnalyzer) -> None:
        """0以下のサイズのクランプ"""
        size_data = {"width": 0, "height": -10}
        original_size = (1920, 1080)
        slide_size = (1920, 1080)

        result = image_analyzer._normalize_size(size_data, original_size, slide_size)

        assert result.width == 1  # 最小1
        assert result.height == 1  # 最小1


class TestStyleParsing:
    """スタイルパース機能のテスト"""

    def test_parse_font_config_full(self, image_analyzer: ImageAnalyzer) -> None:
        """完全なフォント設定のパース"""
        style_data = {
            "font_name": "Times New Roman",
            "font_size": 24,
            "color": {"red": 255, "green": 0, "blue": 0},
            "bold": True,
            "italic": True,
            "underline": True,
        }

        result = image_analyzer._parse_font_config(style_data)

        assert result.family == "Times New Roman"
        assert result.size == 24
        assert result.color.hex_value == "#ff0000"
        assert result.bold is True
        assert result.italic is True
        assert result.underline is True

    def test_parse_font_config_defaults(self, image_analyzer: ImageAnalyzer) -> None:
        """デフォルト値のフォント設定"""
        style_data: dict[str, Any] = {}

        result = image_analyzer._parse_font_config(style_data)

        assert result.family == "Arial"
        assert result.size == 18
        assert result.bold is False
        assert result.italic is False

    def test_parse_color_rgb_dict(self, image_analyzer: ImageAnalyzer) -> None:
        """RGB dict形式の色パース"""
        color_data = {"red": 255, "green": 128, "blue": 0}

        result = image_analyzer._parse_color(color_data)

        assert result.hex_value == "#ff8000"

    def test_parse_color_hex_string(self, image_analyzer: ImageAnalyzer) -> None:
        """HEX string形式の色パース"""
        color_data = "#FF8000"

        result = image_analyzer._parse_color(color_data)

        assert result.hex_value == "#FF8000"

    def test_parse_color_invalid_hex(self, image_analyzer: ImageAnalyzer) -> None:
        """不正なHEX文字列（デフォルトに戻る）"""
        color_data = "#GGGGGG"

        result = image_analyzer._parse_color(color_data)

        # デフォルト（黒）
        assert result.hex_value == "#000000"

    def test_parse_color_clamp_values(self, image_analyzer: ImageAnalyzer) -> None:
        """RGB値のクランプ（0-255）"""
        color_data = {"red": 300, "green": -50, "blue": 128}

        result = image_analyzer._parse_color(color_data)

        assert result.hex_value == "#ff0080"  # 255, 0, 128

    def test_parse_alignment_left(self, image_analyzer: ImageAnalyzer) -> None:
        """左揃えのパース"""
        assert image_analyzer._parse_alignment("left") == Alignment.LEFT
        assert image_analyzer._parse_alignment("LEFT") == Alignment.LEFT

    def test_parse_alignment_center(self, image_analyzer: ImageAnalyzer) -> None:
        """中央揃えのパース"""
        assert image_analyzer._parse_alignment("center") == Alignment.CENTER
        assert image_analyzer._parse_alignment("CENTER") == Alignment.CENTER

    def test_parse_alignment_right(self, image_analyzer: ImageAnalyzer) -> None:
        """右揃えのパース"""
        assert image_analyzer._parse_alignment("right") == Alignment.RIGHT
        assert image_analyzer._parse_alignment("RIGHT") == Alignment.RIGHT

    def test_parse_alignment_unknown(self, image_analyzer: ImageAnalyzer) -> None:
        """不明な配置（デフォルトは左揃え）"""
        assert image_analyzer._parse_alignment("unknown") == Alignment.LEFT
        assert image_analyzer._parse_alignment("") == Alignment.LEFT


class TestBackgroundParsing:
    """背景パース機能のテスト"""

    def test_parse_background_color(self, image_analyzer: ImageAnalyzer) -> None:
        """色背景のパース"""
        background_data = {"type": "color", "value": {"red": 255, "green": 255, "blue": 255}}

        bg_color, bg_image = image_analyzer._parse_background(background_data)

        assert bg_color == "#ffffff"
        assert bg_image is None

    def test_parse_background_image(self, image_analyzer: ImageAnalyzer) -> None:
        """画像背景のパース"""
        background_data = {"type": "image", "value": "background.png"}

        bg_color, bg_image = image_analyzer._parse_background(background_data)

        assert bg_color is None
        assert bg_image == "background.png"

    def test_parse_background_default(self, image_analyzer: ImageAnalyzer) -> None:
        """デフォルト背景（白）"""
        background_data: dict[str, Any] = {}

        bg_color, bg_image = image_analyzer._parse_background(background_data)

        assert bg_color == "#FFFFFF"
        assert bg_image is None


class TestImageEncoding:
    """画像エンコーディングのテスト"""

    def test_encode_image_base64_rgb(self, image_analyzer: ImageAnalyzer) -> None:
        """RGB画像のBase64エンコード"""
        image = Image.new("RGB", (100, 100), color="red")

        result = image_analyzer._encode_image_base64(image)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_encode_image_base64_rgba(self, image_analyzer: ImageAnalyzer) -> None:
        """RGBA画像のBase64エンコード（RGB変換）"""
        image = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))

        result = image_analyzer._encode_image_base64(image)

        assert isinstance(result, str)
        assert len(result) > 0
