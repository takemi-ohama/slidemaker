# Slidemaker - AI-Powered PowerPoint Generator

## プロジェクト概要

SlidemakerはAIを活用した次世代のPowerPoint生成ツールです。Markdownファイルから、またはPDF/画像ファイルからAIが自動的に美しいプレゼンテーションスライドを生成します。

### 主要機能

1. **新規作成モード**: Markdown → LLM → PowerPoint
   - Markdownで内容を記述
   - LLMが最適なレイアウトと構成を生成
   - 必要に応じて画像を自動生成
   - PowerPointファイルとして出力

2. **変換モード**: PDF/画像 → LLM分析 → PowerPoint
   - 既存のPDF/画像からスライドを抽出
   - LLMが要素（テキスト、画像）を分析・識別
   - 編集可能なPowerPointファイルとして再構築

### アーキテクチャ

4層アーキテクチャを採用：

```
インターフェース層（CLI / WebUI）
         ↓
アプリケーション層（ワークフロー制御）
         ↓
ドメイン層（コアロジック）
         ↓
インフラ層（LLM, ファイル, PowerPoint）
```

詳細: [issues/PLAN01/01_architecture.md](issues/PLAN01/01_architecture.md)

## 技術スタック

### バックエンド
- **言語**: Python 3.13
- **パッケージ管理**: uv (Rust製、高速)
- **LLM統合**: Claude, GPT, Gemini (API + CLI)
- **バリデーション**: Pydantic v2
- **HTTP**: httpx (非同期)
- **ロギング**: structlog
- **PowerPoint**: python-pptx
- **画像処理**: Pillow, pdf2image
- **CLI**: Typer + Rich
- **API**: FastAPI

### フロントエンド (Phase 6)
- **フレームワーク**: React 18 + TypeScript
- **ビルドツール**: Vite
- **スタイリング**: Tailwind CSS
- **Node.js**: v24.x LTS

### インフラ
- **クラウド**: AWS (Lambda, API Gateway, S3, CloudFront)
- **IaC**: AWS CDK (Python)
- **CI/CD**: GitHub Actions

詳細: [issues/PLAN01/03_technology_stack.md](issues/PLAN01/03_technology_stack.md)

## ディレクトリ構造

```
slidemaker/
├── src/slidemaker/               # メインパッケージ
│   ├── core/                     # コアドメインロジック
│   │   ├── models/               # データモデル（Pydantic）
│   │   │   ├── common.py         # 共通モデル（Position, Size, Color等）
│   │   │   ├── element.py        # 要素モデル（Text, Image）
│   │   │   ├── page_definition.py # ページ定義
│   │   │   └── slide_config.py   # スライド設定
│   │   └── serializers/          # シリアライザ
│   │       ├── json_serializer.py # JSON形式
│   │       └── markdown.py        # Markdown形式
│   ├── llm/                      # LLM統合
│   │   ├── base.py               # LLMアダプタ基底クラス
│   │   ├── manager.py            # LLMマネージャー
│   │   ├── adapters/             # LLMアダプタ実装
│   │   │   ├── api/              # API型（Claude, GPT, Gemini）
│   │   │   │   ├── base_api.py  # API基底クラス
│   │   │   │   └── claude.py    # Claude実装 ✅
│   │   │   └── cli/              # CLI型（未実装）
│   │   └── prompts/              # プロンプトテンプレート
│   │       ├── composition.py    # 構成生成
│   │       ├── image_generation.py # 画像生成
│   │       └── image_processing.py # 画像分析
│   ├── utils/                    # ユーティリティ
│   │   ├── config_loader.py      # 設定管理
│   │   ├── file_manager.py       # ファイル管理（セキュリティ強化済み）
│   │   └── logger.py             # ロガー設定
│   ├── pptx/                     # PowerPoint生成 ✅
│   │   ├── __init__.py
│   │   ├── generator.py          # PowerPointGenerator
│   │   ├── builder.py            # SlideBuilder
│   │   ├── renderers/
│   │   │   ├── text_renderer.py  # テキストレンダラー
│   │   │   └── image_renderer.py # 画像レンダラー
│   │   ├── styles/
│   │   │   └── style_applier.py  # スタイル適用
│   │   └── exceptions.py         # PowerPoint固有例外
│   ├── workflows/                # ワークフロー（Phase 3実装完了）
│   │   ├── __init__.py
│   │   ├── base.py               # WorkflowOrchestrator基底クラス
│   │   ├── new_slide.py          # NewSlideWorkflow（Markdown → PowerPoint）
│   │   ├── composition_parser.py # CompositionParser（LLM出力パース）
│   │   ├── image_coordinator.py  # ImageCoordinator（画像生成調整）
│   │   └── exceptions.py         # ワークフロー固有例外
│   ├── image_processing/         # 画像処理 ✅
│   │   ├── __init__.py
│   │   ├── loader.py             # ImageLoader（PDF/画像読み込み）
│   │   ├── analyzer.py           # ImageAnalyzer（LLM画像分析）
│   │   ├── processor.py          # ImageProcessor（画像要素抽出）
│   │   └── exceptions.py         # 画像処理固有例外
│   ├── cli/                      # CLIインターフェース（未実装）
│   └── api/                      # WebAPI（未実装）
├── tests/                        # テストスイート
├── docs/                         # ドキュメント
│   ├── getting_started.md        # スタートガイド
│   ├── phase1_summary.md         # Phase 1実装サマリー
│   ├── phase2_summary.md         # Phase 2実装サマリー
│   ├── phase3_summary.md         # Phase 3実装サマリー
│   └── phase4_summary.md         # Phase 4実装サマリー
├── examples/                     # サンプルファイル
│   ├── config.yaml.example       # 設定サンプル
│   └── sample_presentation.md    # プレゼンサンプル
├── issues/PLAN01/                # 開発計画
│   ├── 00_overview.md            # プロジェクト概要
│   ├── 01_architecture.md        # アーキテクチャ設計
│   ├── 02_module_structure.md    # モジュール構成
│   ├── 03_technology_stack.md    # 技術スタック
│   ├── 04_development_phases.md  # 開発フェーズ
│   ├── 05_deployment.md          # デプロイメント
│   └── 06_implementation_roadmap.md # Phase 2-6ロードマップ
└── pyproject.toml                # プロジェクト設定（uv対応）
```

## 開発フェーズ

### Phase 1: コアモデルとLLM統合 ✅ 100%完了

**実装済み**:
- ✅ データモデル（common, element, page_definition, slide_config）
- ✅ シリアライザ（JSON, Markdown）
- ✅ ユーティリティ（logger, config_loader, file_manager）
- ✅ LLM基盤（base, manager, prompts）
- ✅ API基底アダプタ（base_api.py）
- ✅ Claudeアダプタ（claude.py）
- ✅ セキュリティ修正（パストラバーサル、RGB検証、エラーハンドリング等）

詳細: [docs/phase1_summary.md](docs/phase1_summary.md)

### Phase 2: PowerPoint生成機能 ✅ 100%完了

**実装済み**:
- ✅ PowerPointGenerator（python-pptxラッパー）
- ✅ SlideBuilder（個別スライド構築）
- ✅ TextRenderer（テキスト要素レンダリング）
- ✅ ImageRenderer（画像要素レンダリング）
- ✅ StyleApplier（スタイル適用）
- ✅ 包括的なテスト（71テスト、カバレッジ91.8%）

詳細: [docs/phase2_summary.md](docs/phase2_summary.md)

### Phase 3: 新規作成ワークフロー ✅ 100%完了

**実装済み**:
- ✅ WorkflowOrchestrator（基底クラス、リトライ機能付き）
- ✅ NewSlideWorkflow（Markdown → PowerPoint完全パイプライン）
- ✅ CompositionParser（LLM出力パース、バリデーション）
- ✅ ImageCoordinator（並列画像生成、キャッシング）
- ✅ 包括的なテスト（82テスト、カバレッジ90%以上）
- ✅ 型安全性（mypy strict mode対応）

詳細: [docs/phase3_summary.md](docs/phase3_summary.md)

### Phase 4: PDF/画像変換ワークフロー ✅ 100%完了

**実装済み**:
- ✅ ImageLoader（PDF/画像読み込み、正規化）
- ✅ ImageAnalyzer（LLM画像分析、座標正規化）
- ✅ ImageProcessor（画像要素抽出・保存）
- ✅ ConversionWorkflow（5ステップ変換パイプライン）
- ✅ 包括的なテスト（109テスト、カバレッジ88%）
- ✅ セキュリティ対策（パストラバーサル、サイズ制限、OWASP Top 10準拠）

詳細: [docs/phase4_summary.md](docs/phase4_summary.md)

### Phase 5: CLIインターフェース ⏳ 未着手

**実装予定**:
- Typerベースのコマンド
- createコマンド（Markdown → PowerPoint）
- convertコマンド（PDF/画像 → PowerPoint）
- Rich出力フォーマット

推定工数: 1-2週

### Phase 6: WebUIとデプロイメント ⏳ 未着手

**実装予定**:
- FastAPI バックエンドAPI
- React + TypeScript フロントエンド
- AWS CDKインフラ定義
- CI/CDパイプライン

推定工数: 4-6週

詳細: [issues/PLAN01/06_implementation_roadmap.md](issues/PLAN01/06_implementation_roadmap.md)

## セキュリティ対策

Phase 1実装時にQAエージェントによる包括的なセキュリティレビューを実施し、以下の脆弱性を修正:

### Critical: パストラバーサル脆弱性
- **場所**: `file_manager.py`
- **修正**: `output_base_dir`による制限、`_validate_output_path()`での検証
- **影響**: ../../../etc/passwdのような攻撃を防止

### High: 入力検証不足
- **RGB値検証**: 0-255範囲チェック追加
- **JSON解析**: 包括的なエラーハンドリングとバリデーション
- **環境変数**: strictモード追加（未定義変数でエラー）

すべての修正は [docs/phase1_summary.md#セキュリティ修正](docs/phase1_summary.md#セキュリティ修正) に詳細記載。

## 設定ファイル

### config.yaml の例

```yaml
llm:
  composition:
    type: "api"
    provider: "claude"
    model: "claude-3-5-sonnet-20241022"
    api_key: "${ANTHROPIC_API_KEY}"
    timeout: 300

  image_generation:
    type: "api"
    provider: "gemini"
    model: "gemini-2.0-flash-exp"
    api_key: "${GOOGLE_API_KEY}"

output:
  directory: "./output"
  filename_template: "{title}_{timestamp}.pptx"

slide_defaults:
  size: "16:9"
  font: "Arial"
  font_size: 18

logging:
  level: "INFO"
  format: "json"
```

サンプル: [examples/config.yaml.example](examples/config.yaml.example)

## 重要な実装パターン

### 1. データモデル（Pydantic）

```python
from pydantic import BaseModel, Field

class TextElement(ElementDefinition):
    element_type: Literal["text"] = "text"
    content: str = Field(...)
    font: FontConfig = Field(default_factory=FontConfig)
    alignment: Alignment = Field(default=Alignment.LEFT)
```

- すべてのデータクラスはPydantic BaseModelを継承
- Fieldでバリデーションとデフォルト値を定義
- Literal型で型判別

### 2. LLMアダプタパターン

```python
class LLMAdapter(ABC):
    @abstractmethod
    async def generate_text(self, prompt: str, ...) -> str:
        pass

    @abstractmethod
    async def generate_structured(self, prompt: str, ...) -> dict:
        pass
```

- 抽象基底クラスでインターフェース定義
- API型とCLI型で異なる実装
- 非同期処理（async/await）

### 3. エラーハンドリング

```python
class LLMError(Exception):
    """LLM関連のベース例外"""

class LLMTimeoutError(LLMError):
    """タイムアウト例外"""

class LLMRateLimitError(LLMError):
    """レート制限例外"""
```

- 階層的な例外設計
- 具体的なエラー情報を提供
- ユーザーフレンドリーなメッセージ

## 開発環境セットアップ

### 必要な環境
- Python 3.13+
- uv (パッケージマネージャー)
- Node.js 24.x (WebUI開発時)

### インストール

```bash
# uvのインストール
curl -LsSf https://astral.sh/uv/install.sh | sh

# プロジェクトのクローン
git clone <repository-url>
cd slidemaker

# 依存関係のインストール
uv sync

# テストの実行
uv run pytest

# リンターの実行
uv run ruff check src/
uv run mypy src/
```

詳細: [docs/getting_started.md](docs/getting_started.md)

## テスト戦略

### 目標カバレッジ
- ユニットテスト: 80%以上
- 統合テスト: 主要ワークフロー100%
- E2Eテスト: 主要ユースケース100%

### テスト構成

```
tests/
├── core/                    # コアモデルのテスト
│   ├── test_models.py
│   └── test_serializers.py
├── llm/                     # LLM統合のテスト
│   ├── test_manager.py
│   └── adapters/
│       ├── test_api_adapters.py
│       └── test_cli_adapters.py
├── utils/                   # ユーティリティのテスト
│   ├── test_config_loader.py
│   ├── test_file_manager.py
│   └── test_logger.py
├── integration/             # 統合テスト
│   ├── test_llm_integration.py
│   └── test_serialization_roundtrip.py
└── e2e/                     # エンドツーエンドテスト
    ├── test_create_workflow.py
    └── test_convert_workflow.py
```

## CI/CD

### GitHub Actions ワークフロー

1. **ci.yml**: プルリクエスト時
   - ruff（リンター）
   - mypy（型チェック）
   - pytest（テスト実行）
   - カバレッジレポート

2. **publish.yml**: リリース時
   - ビルド
   - PyPIへの公開

3. **deploy-api.yml**: main mergeまたはタグ時
   - AWS Lambda デプロイ

4. **deploy-frontend.yml**: main merge時
   - S3 + CloudFrontデプロイ

## 環境変数

### 開発環境

```bash
# LLM APIキー
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
export GOOGLE_API_KEY="..."

# AWS認証情報（デプロイ時）
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_DEFAULT_REGION="us-east-1"

# ロギング
export LOG_LEVEL="DEBUG"
export LOG_FORMAT="console"  # または "json"
```

### 本番環境

- AWS Secrets Managerで管理
- Lambda環境変数として注入
- strictモード有効（未定義変数でエラー）

## コーディング規約

### Python
- PEP 8準拠
- 型ヒント必須（mypy strict mode）
- docstring（Google形式）
- 最大行長: 100文字
- import順序: 標準ライブラリ → サードパーティ → ローカル

### TypeScript
- ESLint + Prettier
- strictモード有効
- 関数型プログラミングスタイル推奨
- Props型定義必須

## 参考リンク

### 開発計画
- [プロジェクト概要](issues/PLAN01/00_overview.md)
- [アーキテクチャ設計](issues/PLAN01/01_architecture.md)
- [モジュール構成](issues/PLAN01/02_module_structure.md)
- [技術スタック](issues/PLAN01/03_technology_stack.md)
- [開発フェーズ](issues/PLAN01/04_development_phases.md)
- [デプロイメント](issues/PLAN01/05_deployment.md)
- [実装ロードマップ](issues/PLAN01/06_implementation_roadmap.md)

### 実装サマリー
- [Phase 1実装サマリー](docs/phase1_summary.md)
- [Phase 2実装サマリー](docs/phase2_summary.md)
- [Phase 3実装サマリー](docs/phase3_summary.md)

### サンプル
- [設定ファイルサンプル](examples/config.yaml.example)
- [プレゼンテーションサンプル](examples/sample_presentation.md)

### 外部ドキュメント
- [python-pptx Documentation](https://python-pptx.readthedocs.io/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)

## 次のステップ

### 短期（Phase 5）
1. Typerベースのコマンドラインインターフェース
2. createコマンド（Markdown → PowerPoint）
3. convertコマンド（PDF/画像 → PowerPoint）
4. Rich出力フォーマット
5. エンドツーエンドテスト

### 長期（Phase 6）
1. FastAPI バックエンドAPIの実装
2. React + TypeScript フロントエンドの実装
3. AWS CDKインフラ定義
4. CI/CDパイプラインの構築
5. PyPIへの公開

## トラブルシューティング

### よくある問題

**Q: uv sync が失敗する**
```bash
# uvを最新版に更新
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Q: python-pptxでフォントが正しく表示されない**
- システムにフォントがインストールされているか確認
- フォント名を正確に指定（"Arial", "MS Gothic"等）

**Q: LLM APIがタイムアウトする**
- timeoutパラメータを増やす（デフォルト300秒）
- ネットワーク接続を確認
- APIキーが有効か確認

**Q: ファイル保存時にパーミッションエラー**
- output_base_dirの書き込み権限を確認
- パストラバーサル防止機能により正しいディレクトリ内かチェック

**Q: PDF変換が失敗する**
- poppler-utilsがインストールされているか確認
  - Ubuntu/Debian: `apt-get install poppler-utils`
  - macOS: `brew install poppler`
- PDFページ数が制限（100ページ）を超えていないか確認
- PDFファイルが破損していないか確認

**Q: 画像分析が不正確**
- LLM APIキーが有効か確認
- 画像の解像度が十分か確認（推奨: 1920x1080以上）
- 複雑なレイアウトの場合は手動修正が必要な場合あり（Phase 5で対応予定）

## ライセンス

このプロジェクトのライセンスについては [LICENSE](LICENSE) を参照してください。

---

**最終更新**: 2025-12-21
**バージョン**: 0.4.0 (Phase 4: 100%完了)
**メンテナー**: Claude Code + Project Team
@CLAUDE.ndf.md
