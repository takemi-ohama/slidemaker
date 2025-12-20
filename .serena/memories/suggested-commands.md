# 開発コマンド一覧

## セットアップ
```bash
# 依存関係のインストール
uv sync
```

## テスト
```bash
# すべてのテストを実行
uv run pytest

# カバレッジ付きでテスト実行
uv run pytest --cov=slidemaker --cov-report=term-missing

# 特定のテストファイルを実行
uv run pytest tests/unit/test_models.py

# マーカーでフィルター
uv run pytest -m unit
uv run pytest -m integration
```

## リント・型チェック
```bash
# ruff（リンター）
uv run ruff check src/
uv run ruff check tests/

# ruff自動修正
uv run ruff check --fix src/

# mypy（型チェック）
uv run mypy src/
uv run mypy tests/
```

## アプリケーション実行（Phase 5以降）
```bash
# CLIヘルプ
uv run slidemaker --help

# スライド作成（未実装）
uv run slidemaker create input.md -o output.pptx

# PDF/画像変換（未実装）
uv run slidemaker convert input.pdf -o output.pptx
```

## ビルド
```bash
# パッケージビルド
uv build

# ローカルインストール
uv pip install -e .
```

## システムコマンド（Linux）
- `git`: バージョン管理
- `ls`: ファイル一覧
- `cd`: ディレクトリ移動
- `grep`: テキスト検索
- `find`: ファイル検索
