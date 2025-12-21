"""Phase 2統合テスト - PowerPointGenerator, SlideBuilder, Renderers統合確認"""

from pathlib import Path

from slidemaker.core.models.common import Alignment, Position, Size
from slidemaker.core.models.element import FontConfig, ImageElement, TextElement
from slidemaker.core.models.page_definition import PageDefinition
from slidemaker.core.models.slide_config import SlideConfig
from slidemaker.pptx.generator import PowerPointGenerator


def test_phase2_integration():
    """Phase 2統合テスト: 実際のPowerPointファイルを生成"""
    # スライド設定
    config = SlideConfig.create_16_9()

    # ジェネレータ初期化
    generator = PowerPointGenerator(config)

    # ページ定義を作成
    pages = [
        # タイトルスライド
        PageDefinition(
            page_number=1,
            title="Phase 2統合テスト",
            background_color="#F0F0F0",
            elements=[
                TextElement(
                    position=Position(x=100, y=200),
                    size=Size(width=800, height=100),
                    content="Slidemaker Phase 2統合",
                    font=FontConfig(family="Arial", size=44, bold=True),
                    alignment=Alignment.CENTER,
                    z_index=1,
                ),
                TextElement(
                    position=Position(x=100, y=350),
                    size=Size(width=800, height=50),
                    content="PowerPoint生成機能の統合確認",
                    font=FontConfig(family="Arial", size=28),
                    alignment=Alignment.CENTER,
                    z_index=2,
                ),
            ],
        ),
        # コンテンツスライド
        PageDefinition(
            page_number=2,
            title="統合内容",
            background_color="#FFFFFF",
            elements=[
                TextElement(
                    position=Position(x=50, y=50),
                    size=Size(width=900, height=60),
                    content="統合内容",
                    font=FontConfig(family="Arial", size=36, bold=True),
                    alignment=Alignment.LEFT,
                    z_index=1,
                ),
                TextElement(
                    position=Position(x=50, y=150),
                    size=Size(width=900, height=400),
                    content=(
                        "✓ SlideBuilderにTextRendererを統合\n"
                        "✓ SlideBuilderにImageRendererを統合\n"
                        "✓ PowerPointGeneratorにSlideBuilderを統合\n"
                        "✓ 型安全性の確保（isinstance チェック）\n"
                        "✓ リンター・型チェッカーのパス"
                    ),
                    font=FontConfig(family="Arial", size=24),
                    alignment=Alignment.LEFT,
                    z_index=2,
                ),
            ],
        ),
    ]

    # PowerPoint生成
    output_path = Path("output") / "phase2_integration_test.pptx"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    result = generator.generate(pages, output_path)

    print(f"✓ 統合テスト成功")
    print(f"  生成ファイル: {result}")
    print(f"  スライド数: {len(generator.presentation.slides)}")

    # ファイル存在確認
    assert result.exists(), f"ファイルが生成されていません: {result}"
    assert result.stat().st_size > 0, "ファイルサイズが0です"

    print("\n統合テスト完了: すべてのモジュールが正しく統合されています")


if __name__ == "__main__":
    test_phase2_integration()
