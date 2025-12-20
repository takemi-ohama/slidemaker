# slidemaker

AI-powered PowerPoint slide generator

## Overview

slidemakerは、LLM（大規模言語モデル）を活用してPowerPointスライドを自動生成するツールです。Markdownからの新規作成や、既存のPDF/画像からの変換に対応しています。

## Features

### 新規作成モード
- Markdownによるスライド構成定義
- LLMによる自動レイアウト設計
- LLMによる画像生成
- PowerPointファイル（.pptx）出力

### PDF/画像変換モード
- PDFまたは画像ファイル群からの変換
- LLMによる構成分析と要素分解
- 画像の自動トリミング・加工
- PowerPointファイル（.pptx）再構築

### マルチLLM対応
- **API型**: Claude Opus, GPT-5.2, Gemini, Nano Banana等
- **CLI型**: claude code, codex cli, gemini cli, kiro cli等
- 構成定義用と画像生成用を個別設定可能

## Installation

### CLI版（ユーザー向け）

```bash
pip install slidemaker
```

### 開発環境セットアップ

#### 必要要件
- Python 3.13+
- uv (Python package manager)

#### インストール手順

1. リポジトリクローン
```bash
git clone https://github.com/yourusername/slidemaker.git
cd slidemaker
```

2. uvのインストール（未インストールの場合）
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. 仮想環境作成と依存関係インストール
```bash
uv venv
source .venv/bin/activate  # Windowsの場合: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

## Usage

### CLI版

#### 新規作成
```bash
slidemaker create --input slide_plan.md --output presentation.pptx \
  --llm-config claude-opus --llm-image dalle-3
```

#### PDF/画像変換
```bash
slidemaker convert --input source.pdf --output presentation.pptx \
  --llm-config gemini-pro --llm-image stable-diffusion
```

#### 設定ファイル使用
```bash
slidemaker create --input slide_plan.md --config config.yaml
```

### 設定ファイル例（config.yaml）

```yaml
llm:
  composition:
    type: api
    provider: claude
    model: claude-opus-4-5
    api_key: ${CLAUDE_API_KEY}

  image_generation:
    type: api
    provider: dalle
    model: dall-e-3
    api_key: ${OPENAI_API_KEY}

output:
  directory: ./output
  temp_directory: ./tmp
  keep_temp: false

slide:
  default_size: "16:9"
  default_theme: "minimal"
```

## Development

### プロジェクト構造

```
slidemaker/
├── src/slidemaker/          # ソースコード
│   ├── core/               # コアドメインモジュール
│   ├── llm/                # LLM統合
│   ├── image/              # 画像処理
│   ├── generator/          # PowerPoint生成
│   ├── workflow/           # ワークフロー
│   ├── cli/                # CLIインターフェース
│   └── api/                # API（WebUI用）
├── webui/                  # WebUIフロントエンド
├── infrastructure/         # AWS CDK
├── tests/                  # テストコード
└── docs/                   # ドキュメント
```

### コマンド

```bash
# テスト実行
uv run pytest

# Linter実行
uv run ruff check src/

# 型チェック
uv run mypy src/

# フォーマット
uv run ruff format src/
```

## Architecture

システムは4層のアーキテクチャで構成されています：

1. **インターフェース層**: CLI版、WebUI版
2. **アプリケーション層**: ワークフロー制御
3. **ドメイン層**: コアビジネスロジック
4. **インフラストラクチャ層**: LLMアダプタ、ファイルシステム

詳細は[アーキテクチャドキュメント](issues/PLAN01/01_architecture.md)を参照してください。

## WebUI版

WebUI版はAWS Lambda + API Gatewayでホスティングされます（開発中）。

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) file for details

## Roadmap

- [x] Phase 0: プロジェクトセットアップ
- [ ] Phase 1: コアモデルとLLM統合
- [ ] Phase 2: 新規作成モード実装
- [ ] Phase 3: PDF/画像変換モード実装
- [ ] Phase 4: CLI版完成
- [ ] Phase 5: WebUI版開発
- [ ] Phase 6: デプロイとCI/CD整備

詳細な開発計画は[開発フェーズドキュメント](issues/PLAN01/04_development_phases.md)を参照してください。

## Support

- GitHub Issues: バグ報告や機能要望
- Documentation: [docs/](docs/) ディレクトリ

## Acknowledgments

- python-pptx - PowerPoint生成
- Anthropic Claude, OpenAI GPT, Google Gemini - LLM統合
