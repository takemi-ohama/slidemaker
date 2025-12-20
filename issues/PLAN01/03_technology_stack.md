# slidemakerプロジェクト開発計画 - 技術スタック

## プログラミング言語

### Python 3.13
- **用途**: コアロジック、CLI、API、画像処理
- **選定理由**:
  - 豊富なライブラリエコシステム（PowerPoint、画像処理）
  - LLM APIの公式SDKサポート
  - AWS Lambdaサポート
  - 生産性の高さ

### TypeScript
- **用途**: WebUIフロントエンド
- **選定理由**:
  - 型安全性
  - React開発のベストプラクティス
  - モダンなツールチェーン

## コアライブラリ

### python-pptx
- **バージョン**: 最新安定版
- **用途**: PowerPointファイル生成
- **機能**:
  - スライド作成・編集
  - テキスト・画像の配置
  - スタイル適用

### Pillow (PIL)
- **バージョン**: 最新安定版
- **用途**: 画像処理
- **機能**:
  - 画像読み込み・保存
  - トリミング・リサイズ
  - 形式変換

### pdf2image
- **バージョン**: 最新安定版
- **用途**: PDF → 画像変換
- **依存**: poppler-utils
- **機能**:
  - PDFページを画像として抽出

### Pydantic v2
- **用途**: データバリデーションとシリアライゼーション
- **機能**:
  - 型安全なデータモデル
  - JSONスキーマ生成
  - バリデーション

## LLM統合

### API型統合

#### OpenAI SDK
```python
# GPT-5.2、DALL-E 3
openai >= 1.0.0
```

#### Anthropic SDK
```python
# Claude Opus
anthropic >= 0.8.0
```

#### Google Generative AI SDK
```python
# Gemini Pro
google-generativeai >= 0.3.0
```

#### カスタムAPI（Nano Banana等）
```python
# HTTPXで直接実装
httpx >= 0.25.0
```

### CLI型統合
- **実装方法**: subprocess経由で外部CLIを呼び出し
- **対応CLI**:
  - codex cli
  - gemini cli
  - claude code
  - kiro cli

## CLIフレームワーク

### Typer
- **バージョン**: 最新安定版
- **選定理由**:
  - 型ヒント活用
  - 自動ヘルプ生成
  - サブコマンド対応

### Rich
- **用途**: リッチターミナル出力
- **機能**:
  - プログレスバー
  - カラー出力
  - テーブル表示

## APIフレームワーク

### FastAPI
- **バージョン**: 最新安定版
- **選定理由**:
  - 高速（Starlette + Pydantic）
  - 自動APIドキュメント生成（OpenAPI）
  - 非同期対応
  - 型ヒント活用

### Uvicorn
- **用途**: ASGIサーバー
- **環境**: ローカル開発

### Mangum
- **用途**: FastAPI → AWS Lambda アダプタ
- **環境**: 本番環境（Lambda）

## フロントエンド

### React 18
- **用途**: UIフレームワーク
- **選定理由**:
  - 豊富なエコシステム
  - コンポーネント再利用性
  - Hooks による状態管理

### Vite
- **用途**: ビルドツール
- **選定理由**:
  - 高速な開発サーバー
  - 最適化されたプロダクションビルド
  - TypeScript完全サポート

### TanStack Query (React Query)
- **用途**: データフェッチング・キャッシング
- **機能**:
  - 非同期状態管理
  - キャッシュ管理
  - 自動リフェッチ

### Zustand
- **用途**: グローバル状態管理
- **選定理由**:
  - 軽量
  - シンプルなAPI
  - TypeScript対応

### Tailwind CSS
- **用途**: スタイリング
- **選定理由**:
  - ユーティリティファースト
  - カスタマイズ性
  - レスポンシブ対応

### Axios
- **用途**: HTTPクライアント
- **機能**:
  - リクエスト/レスポンスインターセプター
  - 自動JSONパース
  - エラーハンドリング

## AWS サービス

### Lambda
- **用途**: バックエンドAPI実行環境
- **ランタイム**: Python 3.13
- **設定**:
  - メモリ: 1024MB〜3008MB（画像処理負荷に応じて）
  - タイムアウト: 300秒（最大15分）
  - 同時実行数: 適宜調整

### API Gateway
- **用途**: REST APIエンドポイント
- **タイプ**: HTTP API（低コスト・低レイテンシ）
- **機能**:
  - CORS設定
  - スロットリング
  - ログ記録

### S3
- **用途**:
  - 生成されたPowerPointファイルの一時保存
  - アップロードされたPDF/画像の保存
  - フロントエンドホスティング（WebUI）
- **設定**:
  - ライフサイクルポリシー（一時ファイル自動削除）
  - CORS設定

### DynamoDB（オプション）
- **用途**: ジョブ状態管理（非同期処理時）
- **テーブル設計**:
  - PK: job_id
  - 属性: status, created_at, result_url, error_message

### CloudWatch
- **用途**: ログ・メトリクス監視
- **機能**:
  - Lambda実行ログ
  - API Gatewayアクセスログ
  - カスタムメトリクス

### Secrets Manager
- **用途**: LLM APIキーの安全な管理
- **シークレット**:
  - OpenAI API Key
  - Anthropic API Key
  - Gemini API Key

### CloudFront（オプション）
- **用途**: WebUIの配信（CDN）
- **利点**:
  - グローバル配信
  - HTTPS対応
  - キャッシング

## Infrastructure as Code

### AWS CDK (Python)
- **バージョン**: 2.x
- **選定理由**:
  - Pythonでインフラ定義
  - 型チェック
  - 再利用可能なコンストラクト

### CDK構成
```python
# requirements.txt
aws-cdk-lib >= 2.100.0
constructs >= 10.0.0
```

## 開発ツール

### パッケージ管理

#### uv
- **バージョン**: 最新安定版
- **用途**: Python依存関係管理
- **選定理由**:
  - 高速（Rust実装）
  - pip/pip-tools互換
  - 仮想環境管理
  - 依存関係解決が高速
- **機能**:
  - `uv pip install`: パッケージインストール
  - `uv venv`: 仮想環境作成
  - `uv pip compile`: 依存関係ロック
  - `uv pip sync`: ロックファイルから同期

#### npm/pnpm
- **用途**: Node.js依存関係管理
- **推奨**: pnpm（ディスク効率）

### コード品質

#### Ruff
- **用途**: Python Linter/Formatter
- **選定理由**:
  - 高速（Rust実装）
  - flake8 + Black の機能統合

#### mypy
- **用途**: Python型チェック
- **設定**: strict mode

#### ESLint
- **用途**: TypeScript/React Linter
- **プリセット**: @typescript-eslint/recommended

#### Prettier
- **用途**: TypeScript/React Formatter

### テスト

#### pytest
- **用途**: Pythonユニット・統合テスト
- **プラグイン**:
  - pytest-asyncio: 非同期テスト
  - pytest-cov: カバレッジ
  - pytest-mock: モック

#### Vitest
- **用途**: TypeScript/Reactテスト
- **選定理由**:
  - Viteとの統合
  - 高速実行

#### React Testing Library
- **用途**: Reactコンポーネントテスト

### CI/CD

#### GitHub Actions
- **用途**: 自動テスト・ビルド・デプロイ
- **ワークフロー**:
  - テスト実行（PR毎）
  - PyPI公開（タグプッシュ時）
  - AWS CDKデプロイ（main更新時）

## ロギング・モニタリング

### structlog
- **用途**: 構造化ログ
- **出力形式**: JSON
- **統合**: CloudWatch Logs

### Sentry（オプション）
- **用途**: エラートラッキング
- **環境**: 本番環境

## ドキュメント

### MkDocs
- **用途**: ドキュメントサイト生成
- **テーマ**: Material for MkDocs
- **ホスティング**: GitHub Pages

### OpenAPI/Swagger
- **用途**: API仕様
- **自動生成**: FastAPI

## バージョン管理

### Git
- **ブランチ戦略**: GitHub Flow
- **タグ**: Semantic Versioning (v1.0.0)

### Git LFS（オプション）
- **用途**: 大きなサンプルファイル管理

## セキュリティ

### Dependabot
- **用途**: 依存関係の脆弱性スキャン
- **自動PR**: 脆弱性修正

### SAST (Static Application Security Testing)
- **ツール**: Bandit（Python）、ESLint security plugin

### 環境変数管理
- **開発**: .env ファイル（.gitignore）
- **本番**: AWS Secrets Manager

## パフォーマンス最適化

### Python
- **非同期処理**: asyncio, aiohttp
- **並列処理**: concurrent.futures（CPU密集処理）
- **キャッシング**: functools.lru_cache

### フロントエンド
- **コード分割**: React.lazy, Suspense
- **バンドル最適化**: Vite rollup設定
- **画像最適化**: WebP形式

### AWS
- **Lambda最適化**:
  - 適切なメモリ設定
  - Provisioned Concurrency（必要に応じて）
- **S3最適化**:
  - Transfer Acceleration（必要に応じて）

## 開発環境

### 推奨IDE
- **VSCode**: 拡張機能充実
- **PyCharm**: Python特化

### VSCode拡張機能
- Python
- Pylance
- ESLint
- Prettier
- Tailwind CSS IntelliSense
- AWS Toolkit

### Docker（オプション）
- **用途**: 開発環境の統一
- **イメージ**: python:3.13-slim

## バージョン互換性

### Python
- **最小**: 3.13
- **推奨**: 3.13.x 最新

### Node.js
- **最小**: 20.x
- **推奨**: 24.x LTS

### ブラウザ（WebUI）
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+
