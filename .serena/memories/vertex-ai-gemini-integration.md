# Vertex AI Gemini統合 - 実装ガイド

## 概要

AWS Bedrock ClaudeからVertex AI Geminiへの完全移行を実施しました。処理内容に応じて最適なモデルを選定しています。

## モデル選定

### 1. Composition Generation（スライド構成生成）
- **モデル**: `gemini-2.0-flash-exp`
- **用途**: Markdown → スライド構成生成（テキスト処理のみ）
- **理由**: 高速・最新・コスト効率的
- **設定**:
  - max_tokens: 8192
  - temperature: 0.7（創造性重視）
  - location: us-central1

### 2. Image Analysis（画像分析）
- **モデル**: `gemini-1.5-pro-002`
- **用途**: PDF/画像分析、テキスト・画像要素の検出・抽出
- **理由**: 高精度Vision、画像分析に最適
- **設定**:
  - max_tokens: 8192
  - temperature: 0.3（精度重視）
  - location: us-central1

## 実装ファイル

### 1. src/slidemaker/llm/adapters/api/vertex_gemini.py（新規作成）

**主要機能**:
- Google Application Default Credentials (ADC) 認証
- OAuth2トークン自動リフレッシュ
- テキスト処理とVision（画像分析）の両方をサポート
- systemInstructionとgenerationConfigの適切な設定

**重要なポイント**:
```python
class VertexGeminiAdapter(APIAdapter):
    def __init__(self, model: str, **extra_params: Any) -> None:
        # project_idは必須パラメータ
        self.project_id = extra_params.get("project_id")
        if not self.project_id:
            raise ValueError("project_id is required for Vertex AI Gemini")
        
        # ADCで認証情報取得
        self.credentials, _ = google.auth.default()
    
    @property
    def api_base_url(self) -> str:
        # Vertex AI Gemini APIエンドポイント
        return (
            f"https://{self.location}-aiplatform.googleapis.com/v1/"
            f"projects/{self.project_id}/locations/{self.location}/"
            f"publishers/google/models/{self.model}:generateContent"
        )
```

### 2. src/slidemaker/llm/manager.py（修正）

**変更内容**:
- `provider_map`に`vertex-gemini`と`vertex`エイリアスを追加
- Vertex AI固有の初期化ロジックを追加

```python
# Vertex AI Gemini-specific initialization
if adapter_class == VertexGeminiAdapter:
    project_id = config.extra_params.get("project_id")
    if not project_id:
        raise ValueError("project_id is required for Vertex AI Gemini")
    
    location = config.extra_params.get("location", "us-central1")
    max_tokens = config.extra_params.get("max_tokens", 8192)
    temperature = config.extra_params.get("temperature", 0.7)
    
    return VertexGeminiAdapter(
        model=config.model,
        timeout=config.timeout,
        project_id=project_id,
        location=location,
        max_tokens=max_tokens,
        temperature=temperature,
    )
```

### 3. config.yaml（完全書き換え）

**変更内容**:
```yaml
llm:
  composition:
    type: api
    provider: vertex-gemini
    model: gemini-2.0-flash-exp
    extra_params:
      project_id: "${GCP_PROJECT_ID}"  # 環境変数から取得
      location: "us-central1"
      max_tokens: 8192
      temperature: 0.7
    timeout: 300

  image_generation:
    type: api
    provider: vertex-gemini
    model: gemini-1.5-pro-002
    extra_params:
      project_id: "${GCP_PROJECT_ID}"
      location: "us-central1"
      max_tokens: 8192
      temperature: 0.3  # 低temperature = 精度重視
    timeout: 300
```

## セットアップ手順

### 1. 依存関係のインストール

```bash
uv add google-auth google-auth-httplib2
```

**インストール済みライブラリ**:
- google-auth: 2.45.0
- google-auth-httplib2: 0.3.0

### 2. GCP認証の設定

**方法A: サービスアカウントキーを使用**

```bash
# サービスアカウントキーをダウンロードして環境変数に設定
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
export GCP_PROJECT_ID="your-project-id"
```

**方法B: gcloud CLIで認証**

```bash
# Application Default Credentialsを設定
gcloud auth application-default login

# プロジェクトIDを環境変数に設定
export GCP_PROJECT_ID="your-project-id"
```

### 3. Vertex AI APIの有効化

GCPコンソールで以下のAPIを有効化する必要があります：

1. **Vertex AI API**
   - https://console.cloud.google.com/apis/library/aiplatform.googleapis.com

2. **必要な権限**:
   - `aiplatform.endpoints.predict`
   - `aiplatform.models.predict`

### 4. テスト実行

```bash
# 環境変数の確認
echo "GCP_PROJECT_ID: ${GCP_PROJECT_ID}"
echo "GOOGLE_APPLICATION_CREDENTIALS: ${GOOGLE_APPLICATION_CREDENTIALS}"

# PDF変換テスト
uv run slidemaker convert samples/MDX_Strategic_Engine_2026.pdf \
  -o output/MDX_Strategic_Engine_2026_vertex.pptx

# キャプチャ生成（LibreOffice + pdf2image）
uv run python -c "
from pptx import Presentation
import subprocess
from pdf2image import convert_from_path

# PPTX → PDF
prs = Presentation('output/MDX_Strategic_Engine_2026_vertex.pptx')
subprocess.run(['libreoffice', '--headless', '--convert-to', 'pdf', 
                '--outdir', 'output', 
                'output/MDX_Strategic_Engine_2026_vertex.pptx'])

# PDF → PNG (最初のページのみ)
images = convert_from_path('output/MDX_Strategic_Engine_2026_vertex.pdf', 
                           first_page=1, last_page=1)
images[0].save('output/vertex_capture.png', 'PNG')
print('Capture saved to output/vertex_capture.png')
"
```

## トラブルシューティング

### エラー: "project_id is required for Vertex AI Gemini"

**原因**: config.yamlの`${GCP_PROJECT_ID}`が解決されていない

**解決方法**:
```bash
export GCP_PROJECT_ID="your-actual-project-id"
```

### エラー: "Could not automatically determine credentials"

**原因**: ADC認証情報が設定されていない

**解決方法**:
```bash
# 方法1: gcloud CLI
gcloud auth application-default login

# 方法2: サービスアカウントキー
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
```

### エラー: "Permission denied for Vertex AI API"

**原因**: サービスアカウントまたはユーザーに適切な権限がない

**解決方法**:
1. GCPコンソールで Vertex AI API を有効化
2. IAMで適切なロール（Vertex AI User）を付与

### エラー: "Model not found: gemini-2.0-flash-exp"

**原因**: リージョンでモデルが利用できない

**解決方法**:
- `location`を`us-central1`に変更（Gemini 2.0は限定リージョンのみ）
- または`gemini-1.5-pro`などの安定版モデルを使用

## パフォーマンス比較

### 期待される改善点

1. **画像分析精度**:
   - Gemini 1.5 Pro のVision能力は Claude 3 Sonnetと同等以上
   - フォントサイズ推定の精度向上が期待される
   - 画像境界検出の精度向上が期待される

2. **処理速度**:
   - Gemini 2.0 Flash Exp は非常に高速
   - テキスト処理タスクで大幅な高速化が期待される

3. **コスト**:
   - Gemini 2.0 Flash は Claude 3 Sonnet より安価
   - ただしGemini 1.5 Pro はやや高価

### ベンチマーク（実施予定）

以下の指標で比較テストを実施予定:

1. **精度**:
   - フォントサイズ推定の正確性
   - word_wrap判定の正確性
   - 画像境界検出の正確性

2. **速度**:
   - PDFページあたりの処理時間
   - 全体の変換時間

3. **品質**:
   - テキストの可読性
   - 画像の配置精度
   - レイアウトの再現性

## 次のステップ

1. ✅ Vertex AI Gemini アダプタ実装完了
2. ✅ config.yaml の更新完了
3. ✅ 依存関係のインストール完了
4. ⏳ GCP認証の設定（要ユーザー対応）
5. ⏳ テスト実行と検証
6. ⏳ パフォーマンス比較

## 参考リンク

- [Vertex AI Gemini API Documentation](https://cloud.google.com/vertex-ai/docs/generative-ai/model-reference/gemini)
- [Google Cloud Authentication](https://cloud.google.com/docs/authentication/getting-started)
- [Gemini Models Overview](https://ai.google.dev/models/gemini)
