# slidemakerプロジェクト開発計画 - 開発フェーズとタスク

## 開発フェーズ概要

開発を6つのフェーズに分割し、段階的に機能を実装していきます。

```
Phase 0: プロジェクトセットアップ（1-2週間）
Phase 1: コアモデルとLLM統合（2-3週間）
Phase 2: 新規作成モード実装（3-4週間）
Phase 3: PDF/画像変換モード実装（3-4週間）
Phase 4: CLI版完成とテスト（2-3週間）
Phase 5: WebUI版開発（3-4週間）
Phase 6: デプロイとCI/CD整備（2-3週間）
```

---

## Phase 0: プロジェクトセットアップ

### 目標
プロジェクトの基盤を構築し、開発環境を整備する。

### タスクリスト

#### 0.1 リポジトリ初期化
- [ ] Gitリポジトリ作成
- [ ] .gitignore 設定
- [ ] README.md 作成
- [ ] LICENSE 追加（MIT推奨）

#### 0.2 Python環境構築
- [ ] uv インストール
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- [ ] pyproject.toml 作成（uv用）
- [ ] 依存関係定義
  - python-pptx
  - Pillow
  - pdf2image
  - pydantic
  - structlog
  - typer
  - rich
  - httpx
  - LLM SDK（openai, anthropic, google-generativeai）
- [ ] 仮想環境作成
  ```bash
  uv venv
  source .venv/bin/activate  # Linuxの場合
  ```
- [ ] 依存関係インストール
  ```bash
  uv pip install -e .
  uv pip install -e ".[dev]"
  ```
- [ ] ディレクトリ構造作成
- [ ] __init__.py 配置

#### 0.3 開発ツール設定
- [ ] Ruff設定（pyproject.toml内）
- [ ] mypy設定（pyproject.toml内）
- [ ] pytest設定（pyproject.toml内）
- [ ] pre-commit hooks設定
- [ ] VSCode設定（.vscode/）

#### 0.4 ドキュメント骨格
- [ ] docs/ ディレクトリ作成
- [ ] 基本ドキュメントファイル作成
- [ ] README に開発ガイド追加

#### 0.5 GitHub設定
- [ ] Issueテンプレート作成
- [ ] PRテンプレート作成
- [ ] Dependabot設定
- [ ] GitHub Actions基本設定

---

## Phase 1: コアモデルとLLM統合

### 目標
データモデルとLLM統合基盤を実装する。

### タスクリスト

#### 1.1 データモデル実装
- [ ] core/models/common.py
  - Position, Size, Color等の基本型
- [ ] core/models/element.py
  - ElementDefinition基底クラス
  - ImageElement
  - TextElement
  - FontConfig
- [ ] core/models/page_definition.py
  - PageDefinition
- [ ] core/models/slide_config.py
  - SlideConfig
  - BackgroundConfig
  - SlideSize列挙型
- [ ] ユニットテスト作成

#### 1.2 シリアライザ実装
- [ ] core/serializers/json_serializer.py
  - Pydanticベースのシリアライザ
- [ ] core/serializers/markdown.py
  - Markdown入出力
  - 構成定義→Markdown
  - Markdown→構成定義
- [ ] ユニットテスト作成

#### 1.3 LLM基盤実装
- [ ] llm/base.py
  - LLMAdapter抽象基底クラス
  - BaseAPIAdapter
  - BaseCLIAdapter
- [ ] llm/manager.py
  - LLMManager実装
  - アダプタファクトリー
- [ ] llm/prompts/composition.py
  - 構成定義生成プロンプトテンプレート
- [ ] llm/prompts/image_generation.py
  - 画像生成プロンプトテンプレート

#### 1.4 LLMアダプタ実装（API型）
- [ ] llm/adapters/api/claude.py
  - Anthropic SDK統合
- [ ] llm/adapters/api/gpt.py
  - OpenAI SDK統合
- [ ] llm/adapters/api/gemini.py
  - Google Generative AI SDK統合
- [ ] 統合テスト作成（モック使用）

#### 1.5 LLMアダプタ実装（CLI型）
- [ ] llm/adapters/cli/base_cli.py
  - subprocess wrapper
- [ ] llm/adapters/cli/claude_code.py
- [ ] llm/adapters/cli/codex.py
- [ ] 統合テスト作成（モック使用）

#### 1.6 ユーティリティ実装
- [ ] utils/logger.py
  - structlogベースのロガー
- [ ] utils/file_manager.py
  - 一時ファイル管理
  - ファイル読み書き
- [ ] utils/config_loader.py
  - YAML設定読み込み

---

## Phase 2: 新規作成モード実装

### 目標
Markdownから新規スライドを生成する機能を実装する。

### タスクリスト

#### 2.1 PowerPoint生成基盤
- [ ] generator/pptx_generator.py
  - PowerPointGenerator実装
  - プレゼンテーション初期化
  - 保存機能
- [ ] generator/slide_builder.py
  - SlideBuilder実装
  - スライドページ作成
  - レイアウト設定
- [ ] ユニットテスト作成

#### 2.2 要素レンダリング実装
- [ ] generator/element_renderer.py
  - ImageRenderer
  - TextRenderer
  - 座標・サイズ変換
  - z-index考慮した配置
- [ ] generator/style_applier.py
  - フォントスタイル適用
  - 透過率設定
- [ ] ユニットテスト作成

#### 2.3 ワークフロー実装
- [ ] workflow/orchestrator.py
  - WorkflowOrchestrator基本実装
- [ ] workflow/new_slide.py
  - NewSlideWorkflow実装
  - Markdown → 構成定義（LLM）
  - 構成定義 → 画像生成（LLM）
  - 構成定義 + 画像 → PowerPoint
- [ ] 統合テスト作成

#### 2.4 画像生成統合
- [ ] LLM画像生成機能の実装
  - DALL-E 3統合
  - Stable Diffusion統合（オプション）
- [ ] 画像保存・管理
- [ ] 統合テスト作成

#### 2.5 エンドツーエンドテスト
- [ ] サンプルMarkdown作成
- [ ] 完全なフロー実行テスト
- [ ] 生成されたPowerPointの検証

---

## Phase 3: PDF/画像変換モード実装

### 目標
PDF/画像からスライドを再構築する機能を実装する。

### タスクリスト

#### 3.1 画像読み込み実装
- [ ] image/loader.py
  - PDFLoader（pdf2image使用）
  - ImageLoader（Pillow使用）
  - ディレクトリからの一括読み込み
- [ ] ユニットテスト作成

#### 3.2 画像分析・抽出実装
- [ ] image/extractor.py
  - LLMを使った構成分析
  - 画像・テキスト要素の識別
  - 座標・サイズの推定
- [ ] llm/prompts/image_processing.py
  - 画像分析プロンプト
- [ ] 統合テスト作成

#### 3.3 画像加工実装
- [ ] image/processor.py
  - トリミング機能
  - テキスト除去（LLM指示）
  - 画像保存
- [ ] image/background.py
  - 背景抽出
  - 前景要素除去
- [ ] ユニットテスト作成

#### 3.4 変換ワークフロー実装
- [ ] workflow/conversion.py
  - ConversionWorkflow実装
  - PDF/画像 → 画像抽出
  - 画像 → 構成分析（LLM）
  - 構成 + 画像加工 → PowerPoint
- [ ] 統合テスト作成

#### 3.5 エンドツーエンドテスト
- [ ] サンプルPDF作成
- [ ] サンプル画像セット作成
- [ ] 完全なフロー実行テスト
- [ ] 生成されたPowerPointの検証

---

## Phase 4: CLI版完成とテスト

### 目標
コマンドラインツールを完成させ、包括的なテストを実施する。

### タスクリスト

#### 4.1 CLIコマンド実装
- [ ] cli/main.py
  - Typerアプリ初期化
  - グローバルオプション
- [ ] cli/commands/create.py
  - `create`コマンド実装
  - 引数・オプション定義
  - ワークフロー呼び出し
- [ ] cli/commands/convert.py
  - `convert`コマンド実装
  - 引数・オプション定義
  - ワークフロー呼び出し
- [ ] cli/options.py
  - 共通オプション定義

#### 4.2 CLI出力強化
- [ ] Rich統合
  - プログレスバー
  - ステータス表示
  - エラーメッセージ整形
- [ ] ログ出力制御
  - 詳細レベル設定（-v, -vv）

#### 4.3 設定ファイルサポート
- [ ] YAMLベース設定
- [ ] 環境変数サポート
- [ ] 優先順位制御（CLI引数 > 環境変数 > 設定ファイル）

#### 4.4 エラーハンドリング強化
- [ ] 包括的な例外処理
- [ ] ユーザーフレンドリーなエラーメッセージ
- [ ] リトライロジック（LLM呼び出し）

#### 4.5 ドキュメント作成
- [ ] README更新（使用方法）
- [ ] CLI ヘルプ改善
- [ ] examples/ にサンプル追加

#### 4.6 包括的テスト
- [ ] ユニットテストカバレッジ > 80%
- [ ] 統合テスト作成
- [ ] エンドツーエンドテスト
- [ ] 手動テスト（実際のLLM使用）

---

## Phase 5: WebUI版開発

### 目標
Webアプリケーションを開発する。

### タスクリスト

#### 5.1 フロントエンド初期化
- [ ] Viteプロジェクト作成
- [ ] TypeScript設定
- [ ] ESLint + Prettier設定
- [ ] Tailwind CSS設定
- [ ] ディレクトリ構造作成

#### 5.2 APIクライアント実装
- [ ] webui/src/api/client.ts
  - Axios設定
  - APIエンドポイント定義
  - エラーハンドリング

#### 5.3 共通コンポーネント実装
- [ ] レイアウトコンポーネント
- [ ] ボタン、入力フォーム
- [ ] ファイルアップローダー
- [ ] プログレスインジケーター
- [ ] エラー表示

#### 5.4 新規作成UI実装
- [ ] CreateSlide.tsx
  - Markdownエディタ
  - LLM設定選択
  - 送信・生成処理
  - ダウンロードボタン

#### 5.5 変換UI実装
- [ ] ConvertSlide.tsx
  - ファイルアップロード
  - LLM設定選択
  - 送信・変換処理
  - ダウンロードボタン

#### 5.6 ジョブ管理UI実装
- [ ] JobStatus.tsx
  - ジョブステータス表示
  - プログレス表示
  - エラー表示
  - ダウンロードリンク

#### 5.7 バックエンドAPI実装
- [ ] api/app.py
  - FastAPIアプリ初期化
  - CORS設定
  - エラーハンドリング
- [ ] api/routes/slides.py
  - POST /api/v1/slides/create
  - POST /api/v1/slides/convert
  - GET /api/v1/slides/{slide_id}/download
- [ ] api/routes/jobs.py
  - GET /api/v1/jobs/{job_id}
- [ ] api/schemas/
  - リクエスト・レスポンススキーマ定義

#### 5.8 非同期処理実装（オプション）
- [ ] ジョブキュー実装（Celery or AWS SQS）
- [ ] ステータス更新（DynamoDB）
- [ ] 通知機能

#### 5.9 統合テスト
- [ ] APIエンドポイントテスト
- [ ] フロントエンドコンポーネントテスト
- [ ] E2Eテスト（Playwright）

---

## Phase 6: デプロイとCI/CD整備

### 目標
本番環境へのデプロイとCI/CDパイプラインを構築する。

### タスクリスト

#### 6.1 CLI版デプロイ準備
- [ ] pyproject.toml 整備
  - メタデータ
  - エントリーポイント
  - classifiers
- [ ] PyPI用ドキュメント
- [ ] バージョン管理スクリプト

#### 6.2 CLI版 GitHub Actions
- [ ] .github/workflows/ci.yml
  - テスト実行（Python 3.13）
  - Linter実行
  - カバレッジレポート
- [ ] .github/workflows/publish.yml
  - タグトリガー
  - PyPI公開

#### 6.3 AWS CDK実装
- [ ] infrastructure/app.py
  - CDKアプリエントリーポイント
- [ ] infrastructure/stacks/lambda_stack.py
  - Lambda関数定義
  - レイヤー定義
  - 環境変数設定
- [ ] infrastructure/stacks/api_gateway_stack.py
  - HTTP API定義
  - ルート設定
  - CORS設定
- [ ] infrastructure/stacks/storage_stack.py
  - S3バケット作成
  - DynamoDBテーブル作成（オプション）
  - ライフサイクルポリシー

#### 6.4 Secrets設定
- [ ] AWS Secrets Manager
  - LLM APIキー登録
- [ ] Lambda環境変数設定
  - Secret参照

#### 6.5 フロントエンドビルド
- [ ] Viteプロダクションビルド
- [ ] S3デプロイ設定
- [ ] CloudFront設定（オプション）

#### 6.6 WebUI版 GitHub Actions
- [ ] .github/workflows/deploy-webui.yml
  - フロントエンドビルド
  - S3アップロード
  - キャッシュ無効化

#### 6.7 CDKデプロイパイプライン
- [ ] .github/workflows/deploy-cdk.yml
  - CDK synth
  - CDK deploy（ステージング）
  - 承認ステップ
  - CDK deploy（本番）

#### 6.8 モニタリング設定
- [ ] CloudWatchアラーム
  - Lambda エラー率
  - API Gateway 5xxエラー
- [ ] ログ保持期間設定
- [ ] メトリクスダッシュボード作成

#### 6.9 本番デプロイ
- [ ] ステージング環境デプロイ
- [ ] 動作確認
- [ ] 本番環境デプロイ
- [ ] ドメイン設定（オプション）

#### 6.10 ドキュメント最終化
- [ ] デプロイガイド作成
- [ ] トラブルシューティングガイド
- [ ] API仕様書最終化
- [ ] ユーザーガイド最終化

---

## マイルストーン

### M1: プロトタイプ完成（Phase 0-2完了）
- コアモデルとLLM統合完了
- 新規作成モードの基本機能動作
- CLI版での基本的な新規スライド生成が可能

### M2: フル機能CLI版完成（Phase 3-4完了）
- PDF/画像変換モード実装完了
- 包括的なテスト完了
- PyPIへの公開準備完了

### M3: WebUI版ベータ（Phase 5完了）
- WebUIフロントエンド完成
- バックエンドAPI完成
- ローカルでの動作確認完了

### M4: 本番リリース（Phase 6完了）
- AWS環境への完全デプロイ
- CI/CDパイプライン構築完了
- ドキュメント完備
- 一般公開

---

## リスクと対策

### リスク1: LLM API制約
- **リスク**: レート制限、コスト、可用性
- **対策**:
  - 複数LLMサポートでフォールバック
  - リトライロジック実装
  - レート制限エラーの適切なハンドリング

### リスク2: PowerPoint生成の複雑性
- **リスク**: python-pptxの制約、フォーマット問題
- **対策**:
  - 初期段階で基本機能の検証
  - 段階的な機能追加
  - 代替ライブラリの調査

### リスク3: 画像処理の精度
- **リスク**: LLMによる画像分析・加工の不正確さ
- **対策**:
  - プロンプトエンジニアリングの継続改善
  - ユーザーによる手動調整機能の提供
  - 複数LLMでの結果比較

### リスク4: AWS Lambda制約
- **リスク**: メモリ不足、タイムアウト
- **対策**:
  - 適切なメモリ設定（3008MB推奨）
  - 非同期処理への移行（必要に応じて）
  - ストリーミング処理の検討

### リスク5: 開発期間の遅延
- **リスク**: 見積もりオーバー
- **対策**:
  - MVPに集中（オプション機能は後回し）
  - 定期的な進捗確認
  - 並行開発可能な部分の特定

---

## 次のアクション

1. Phase 0のタスクから着手
2. 2週間ごとのスプリント計画
3. 週次進捗レビュー
4. 継続的なドキュメント更新
