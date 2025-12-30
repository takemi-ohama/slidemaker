# Slidemaker - AI-Powered PowerPoint Generator (Gemini Edition)

## プロジェクト概要
Slidemakerは、AIを活用してMarkdown、PDF、または画像からPowerPointプレゼンテーションを自動生成するツールです。

**このプロジェクトは常に日本語で応対してください**

### 主要機能
1. **新規作成モード**: Markdown → LLM分析 → PowerPoint生成
2. **変換モード**: PDF/画像 → LLM要素抽出 → PowerPoint再構築

## 技術スタック
- **言語**: Python 3.13
- **パッケージ管理**: uv
- **LLM統合**: Gemini (Google AI SDK), Claude (Anthropic/Bedrock), GPT
- **主なライブラリ**: Pydantic v2, python-pptx, Pillow, pdf2image, Typer, Rich, FastAPI
- **MCP統合**:
  - Office-PowerPoint-MCP-Server v2.0.6
  - Serena (https://github.com/oraios/serena)

## 開発コマンド

### セットアップ & 依存関係
```bash
# 依存関係のインストール
uv sync
```

### テスト実行
```bash
# 全テスト実行
uv run pytest

# 特定のテスト実行
uv run pytest tests/unit/
uv run pytest tests/integration/
uv run pytest tests/workflows/

# カバレッジ測定
uv run pytest --cov=src/slidemaker
```

### リンター & 型チェック
```bash
# Ruff (リンター・フォーマッタ)
uv run ruff check src/
uv run ruff format src/

# Mypy (型チェック)
uv run mypy src/
```

### CLI実行
```bash
# ヘルプ表示
uv run python -m slidemaker.cli.main --help

# スライド作成例
uv run python -m slidemaker.cli.main create examples/sample_presentation.md -o output/test.pptx
```

## ディレクトリ構造の要約
- `src/slidemaker/`: ソースコード
    - `api/`: Web API (FastAPI)
    - `cli/`: コマンドラインインターフェース (Typer)
    - `core/`: データモデル (Pydantic) とシリアライザ
    - `generator/`: スライド生成ロジック
    - `image_processing/`: PDF/画像解析
    - `llm/`: LLMアダプター (Gemini, Claude, GPT)
    - `pptx/`: PowerPoint生成 (python-pptx)
    - `workflow/`: 生成・変換ワークフローのオーケストレーション
- `tests/`: テストコード
- `docs/`: 各フェーズの実装サマリー
- `issues/`: 開発計画と設計ドキュメント

## コーディング規約
- **Python**: PEP 8準拠、型ヒント必須 (mypy strict mode対応)。
- **非同期**: LLM呼び出しやファイル操作には `async/await` を使用。
- **エラーハンドリング**: `src/slidemaker/*/exceptions.py` で定義された独自の例外クラスを使用。
- **セキュリティ**: `file_manager.py` を通じたパスバリデーションを徹底し、パストラバーサルを防止する。
- **ドキュメント**: Googleスタイルのdocstring。

## Gemini固有の設定
- **対話ルール**: ツール実行前の動作報告（例: "I will..." で始まる思考プロセス）を含め、すべての応答を日本語で行うこと。
- **LLMアダプター**: Geminiを利用する場合は以下の設定が推奨されます：
  - プロバイダー: `gemini`
  - モデル: `gemini-1.5-pro` または `gemini-1.5-flash`
  - 画像解析には `gemini-1.5-flash` の高速性を活用。

## メンテナンス情報
**最終更新**: 2025-12-26
**バージョン**: 0.5.0 (Phase 5完了)
**メンテナー**: Gemini CLI
