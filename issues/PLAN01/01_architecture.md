# slidemakerプロジェクト開発計画 - アーキテクチャ設計

## システムアーキテクチャ

### レイヤー構成

```mermaid
graph TB
    subgraph interface["インターフェース層"]
        CLI["CLI版<br/>(typer等)"]
        WebUI["WebUI版<br/>(React+TS)"]
    end

    subgraph application["アプリケーション層"]
        workflow["ワークフロー制御<br/>モード選択（新規作成/PDF変換）<br/>パイプライン処理"]
    end

    subgraph domain["ドメイン層（コア層）"]
        config["構成定義モジュール<br/>- スライド設定管理<br/>- ページ定義管理<br/>- Markdown入出力"]
        pptx["PowerPoint生成モジュール<br/>- ドキュメント作成<br/>- 要素配置（画像・テキスト）<br/>- スタイル適用"]
        image["画像処理モジュール<br/>- PDF/画像読み込み<br/>- トリミング・加工<br/>- 背景抽出"]
    end

    subgraph infrastructure["インフラストラクチャ層"]
        llm["LLMアダプタモジュール<br/>- API型アダプタ（Nano Banana, Gemini, GPT-5.2, Claude）<br/>- CLI型アダプタ（codex, gemini cli, claude code, kiro）"]
        fs["ファイルシステムモジュール<br/>- 入出力管理<br/>- 一時ファイル管理"]
    end

    CLI --> workflow
    WebUI --> workflow
    workflow --> config
    workflow --> pptx
    workflow --> image
    config --> llm
    pptx --> llm
    image --> llm
    config --> fs
    pptx --> fs
    image --> fs
```

## 主要コンポーネント

### 1. ワークフローエンジン
- **責務**: 処理フローの制御と各モジュールの協調
- **主要クラス**:
  - `WorkflowOrchestrator`: 全体フロー制御
  - `NewSlideWorkflow`: 新規作成モードフロー
  - `ConversionWorkflow`: PDF/画像変換モードフロー

### 2. LLMマネージャー
- **責務**: LLM呼び出しの抽象化と統一インターフェース
- **主要クラス**:
  - `LLMManager`: LLM管理とルーティング
  - `LLMAdapter`: 抽象基底クラス
  - `APIAdapter`: API型LLMアダプタ
  - `CLIAdapter`: CLI型LLMアダプタ
- **設計パターン**: Strategy Pattern

### 3. 構成定義マネージャー
- **責務**: スライド設定とページ定義の管理
- **主要クラス**:
  - `SlideConfiguration`: スライド設定
  - `PageDefinition`: ページ定義
  - `ElementDefinition`: 要素定義（画像・テキスト）
  - `MarkdownSerializer`: Markdown入出力

### 4. PowerPointジェネレーター
- **責務**: PowerPointドキュメントの生成
- **主要クラス**:
  - `PowerPointGenerator`: メインジェネレーター
  - `SlideBuilder`: スライドページ構築
  - `ElementRenderer`: 要素レンダリング（画像・テキスト）
- **利用ライブラリ**: python-pptx

### 5. 画像プロセッサー
- **責務**: 画像の読み込み、加工、抽出
- **主要クラス**:
  - `ImageLoader`: PDF/画像読み込み
  - `ImageExtractor`: 要素抽出
  - `ImageProcessor`: トリミング・加工
- **利用ライブラリ**: Pillow, pdf2image

## データフロー

### 新規作成モード

```mermaid
graph LR
    A[Markdown入力] --> B[LLM<br/>構成定義]
    B --> C[構成定義JSON]
    C --> D[LLM<br/>画像生成]
    D --> E[画像ファイル群]
    C --> F[PowerPoint<br/>ジェネレーター]
    E --> F
    F --> G[.pptxファイル]
```

### PDF/画像変換モード

```mermaid
graph TB
    A[PDF/画像] --> B[画像抽出]
    B --> C[LLM<br/>構成分析]
    C --> D[構成定義JSON]
    D --> E[LLM<br/>画像加工指示]
    E --> F[画像プロセッサー]
    F --> G[加工済み画像]
    D --> H[PowerPoint<br/>ジェネレーター]
    G --> H
    H --> I[.pptxファイル]
```

## インターフェース設計

### CLI版インターフェース
```bash
# 新規作成
slidemaker create --input slide_plan.md --output presentation.pptx \
  --llm-config claude-opus --llm-image dalle-3

# PDF変換
slidemaker convert --input source.pdf --output presentation.pptx \
  --llm-config gemini-pro --llm-image stable-diffusion

# 設定ファイル使用
slidemaker create --input slide_plan.md --config config.yaml
```

### WebUI版インターフェース
- **フロントエンド**: React + TypeScript (SPA)
- **バックエンド**: AWS Lambda (Python 3.13)
- **API**: REST API via API Gateway
- **認証**: 将来的にCognito統合検討

### REST API設計
```
POST /api/v1/slides/create
  - Request: { markdown, llm_config, options }
  - Response: { job_id, status }

POST /api/v1/slides/convert
  - Request: { file_upload, llm_config, options }
  - Response: { job_id, status }

GET /api/v1/jobs/{job_id}
  - Response: { status, progress, result_url }

GET /api/v1/slides/{slide_id}/download
  - Response: .pptx file
```

## 非機能要件

### パフォーマンス
- LLM呼び出しの並列化（可能な場合）
- 画像処理の効率化
- 大量スライド対応（バッチ処理）

### スケーラビリティ
- WebUI版: Lambda並列実行による自動スケール
- 長時間処理: 非同期ジョブキュー（SQS検討）

### セキュリティ
- API認証・認可
- ファイルアップロードのバリデーション
- LLM API キーの安全な管理（環境変数、AWS Secrets Manager）

### 可観測性
- ログ: structlog使用
- メトリクス: CloudWatch連携（WebUI版）
- トレーシング: 処理時間計測

## 拡張性

### プラグイン機構
- カスタムLLMアダプタの追加
- カスタムテンプレートの追加
- カスタムエクスポート形式（PDF、画像等）

### 将来的な拡張
- Google Slides対応
- Keynote対応
- テンプレートライブラリ
- スライドプレビュー機能
