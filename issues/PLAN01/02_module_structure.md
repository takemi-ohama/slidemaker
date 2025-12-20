# slidemakerプロジェクト開発計画 - モジュール構成

## プロジェクトディレクトリ構造

```
slidemaker/
├── pyproject.toml              # プロジェクト設定（Poetry）
├── README.md
├── LICENSE
├── .gitignore
├── .github/
│   └── workflows/
│       ├── ci.yml              # CI/CD設定
│       └── publish.yml         # PyPI公開
│
├── src/
│   └── slidemaker/
│       ├── __init__.py
│       ├── __version__.py
│       │
│       ├── core/               # コアドメインモジュール
│       │   ├── __init__.py
│       │   ├── models/
│       │   │   ├── __init__.py
│       │   │   ├── slide_config.py      # スライド設定モデル
│       │   │   ├── page_definition.py   # ページ定義モデル
│       │   │   ├── element.py           # 要素モデル（画像・テキスト）
│       │   │   └── common.py            # 共通型定義
│       │   │
│       │   ├── serializers/
│       │   │   ├── __init__.py
│       │   │   ├── markdown.py          # Markdown入出力
│       │   │   └── json_serializer.py   # JSON入出力
│       │   │
│       │   └── validators/
│       │       ├── __init__.py
│       │       └── definition_validator.py
│       │
│       ├── llm/                # LLM統合モジュール
│       │   ├── __init__.py
│       │   ├── manager.py              # LLMマネージャー
│       │   ├── base.py                 # 抽象基底クラス
│       │   │
│       │   ├── adapters/
│       │   │   ├── __init__.py
│       │   │   ├── api/                # API型アダプタ
│       │   │   │   ├── __init__.py
│       │   │   │   ├── base_api.py
│       │   │   │   ├── nano_banana.py
│       │   │   │   ├── gemini.py
│       │   │   │   ├── gpt.py
│       │   │   │   └── claude.py
│       │   │   │
│       │   │   └── cli/                # CLI型アダプタ
│       │   │       ├── __init__.py
│       │   │       ├── base_cli.py
│       │   │       ├── codex.py
│       │   │       ├── gemini_cli.py
│       │   │       ├── claude_code.py
│       │   │       └── kiro.py
│       │   │
│       │   └── prompts/
│       │       ├── __init__.py
│       │       ├── composition.py       # 構成定義生成プロンプト
│       │       ├── image_generation.py  # 画像生成プロンプト
│       │       └── image_processing.py  # 画像処理プロンプト
│       │
│       ├── image/              # 画像処理モジュール
│       │   ├── __init__.py
│       │   ├── loader.py               # PDF/画像読み込み
│       │   ├── extractor.py            # 要素抽出
│       │   ├── processor.py            # トリミング・加工
│       │   └── background.py           # 背景抽出
│       │
│       ├── generator/          # PowerPoint生成モジュール
│       │   ├── __init__.py
│       │   ├── pptx_generator.py       # メインジェネレーター
│       │   ├── slide_builder.py        # スライド構築
│       │   ├── element_renderer.py     # 要素レンダリング
│       │   └── style_applier.py        # スタイル適用
│       │
│       ├── workflow/           # ワークフローモジュール
│       │   ├── __init__.py
│       │   ├── orchestrator.py         # オーケストレーター
│       │   ├── new_slide.py            # 新規作成フロー
│       │   └── conversion.py           # 変換フロー
│       │
│       ├── utils/              # ユーティリティ
│       │   ├── __init__.py
│       │   ├── logger.py               # ロギング
│       │   ├── file_manager.py         # ファイル管理
│       │   └── config_loader.py        # 設定読み込み
│       │
│       ├── cli/                # CLIインターフェース
│       │   ├── __init__.py
│       │   ├── main.py                 # CLIエントリーポイント
│       │   ├── commands/
│       │   │   ├── __init__.py
│       │   │   ├── create.py           # create コマンド
│       │   │   └── convert.py          # convert コマンド
│       │   └── options.py              # 共通オプション
│       │
│       └── api/                # API（WebUI用）
│           ├── __init__.py
│           ├── app.py                  # FastAPIアプリ
│           ├── routes/
│           │   ├── __init__.py
│           │   ├── slides.py           # スライドAPI
│           │   └── jobs.py             # ジョブAPI
│           ├── schemas/
│           │   ├── __init__.py
│           │   ├── request.py          # リクエストスキーマ
│           │   └── response.py         # レスポンススキーマ
│           └── dependencies.py         # 依存性注入
│
├── webui/                      # WebUIフロントエンド
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── public/
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── components/
│       │   ├── CreateSlide.tsx
│       │   ├── ConvertSlide.tsx
│       │   ├── JobStatus.tsx
│       │   └── common/
│       ├── api/
│       │   └── client.ts               # APIクライアント
│       ├── hooks/
│       ├── types/
│       └── utils/
│
├── infrastructure/             # インフラストラクチャ（AWS CDK）
│   ├── app.py                          # CDKアプリエントリー
│   ├── cdk.json
│   ├── requirements.txt
│   └── stacks/
│       ├── __init__.py
│       ├── lambda_stack.py             # Lambda関数スタック
│       ├── api_gateway_stack.py        # API Gatewayスタック
│       └── storage_stack.py            # S3/DynamoDBスタック
│
├── tests/                      # テストコード
│   ├── __init__.py
│   ├── unit/
│   │   ├── test_models.py
│   │   ├── test_llm_adapters.py
│   │   ├── test_image_processor.py
│   │   └── test_pptx_generator.py
│   ├── integration/
│   │   ├── test_workflow.py
│   │   └── test_api.py
│   └── fixtures/
│       ├── sample_markdown.md
│       ├── sample.pdf
│       └── sample_images/
│
├── docs/                       # ドキュメント
│   ├── user_guide.md
│   ├── api_reference.md
│   ├── development.md
│   └── deployment.md
│
└── examples/                   # サンプルコード
    ├── basic_creation.py
    ├── pdf_conversion.py
    └── custom_config.yaml
```

## 主要モジュール詳細

### 1. core モジュール

#### models
```python
# slide_config.py
@dataclass
class SlideConfig:
    size: SlideSize  # 16:9, 4:3, etc.
    width: int
    height: int
    background: Optional[BackgroundConfig]
    output_filename: str
    theme: Optional[str]

@dataclass
class BackgroundConfig:
    type: str  # 'color', 'image', 'gradient'
    value: Union[str, dict]

# page_definition.py
@dataclass
class PageDefinition:
    page_number: int
    title: Optional[str]
    elements: List[ElementDefinition]
    layout: Optional[str]
    notes: Optional[str]

# element.py
@dataclass
class ElementDefinition:
    element_type: str  # 'image', 'text'
    position: Position
    size: Size
    z_index: int
    opacity: float

@dataclass
class ImageElement(ElementDefinition):
    source: str  # ファイルパスまたはURL
    fit_mode: str  # 'fill', 'fit', 'stretch'

@dataclass
class TextElement(ElementDefinition):
    content: str
    font: FontConfig
    alignment: str

@dataclass
class FontConfig:
    family: str
    size: int
    color: str
    bold: bool
    italic: bool
```

### 2. llm モジュール

#### manager.py
```python
class LLMManager:
    def __init__(self, config: LLMConfig):
        self.composition_llm = self._create_adapter(config.composition)
        self.image_llm = self._create_adapter(config.image_generation)

    def _create_adapter(self, config: AdapterConfig) -> LLMAdapter:
        # Factory pattern for adapter creation
        pass

    async def generate_composition(self, input_data: str) -> dict:
        pass

    async def generate_image(self, prompt: str) -> bytes:
        pass
```

#### adapters/api/base_api.py
```python
class APIAdapter(LLMAdapter):
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    @abstractmethod
    async def complete(self, prompt: str, **kwargs) -> str:
        pass

    @abstractmethod
    async def generate_image(self, prompt: str, **kwargs) -> bytes:
        pass
```

### 3. generator モジュール

#### pptx_generator.py
```python
class PowerPointGenerator:
    def __init__(self, config: SlideConfig):
        self.config = config
        self.presentation = Presentation()
        self._setup_presentation()

    def generate(self, pages: List[PageDefinition], images: dict) -> str:
        for page in pages:
            slide = self._create_slide(page)
            self._render_elements(slide, page.elements, images)

        output_path = self._save()
        return output_path
```

### 4. workflow モジュール

#### orchestrator.py
```python
class WorkflowOrchestrator:
    def __init__(self, llm_manager: LLMManager):
        self.llm_manager = llm_manager
        self.workflows = {
            'create': NewSlideWorkflow(llm_manager),
            'convert': ConversionWorkflow(llm_manager)
        }

    async def execute(self, mode: str, input_data: Any, config: dict) -> str:
        workflow = self.workflows[mode]
        return await workflow.run(input_data, config)
```

## データモデル仕様

### 構成定義JSON形式
```json
{
  "slide_config": {
    "size": "16:9",
    "width": 1920,
    "height": 1080,
    "background": {
      "type": "color",
      "value": "#FFFFFF"
    },
    "output_filename": "presentation.pptx"
  },
  "pages": [
    {
      "page_number": 1,
      "title": "タイトルページ",
      "elements": [
        {
          "element_type": "text",
          "position": {"x": 100, "y": 200},
          "size": {"width": 800, "height": 100},
          "z_index": 1,
          "opacity": 1.0,
          "content": "プレゼンテーションタイトル",
          "font": {
            "family": "Arial",
            "size": 44,
            "color": "#000000",
            "bold": true,
            "italic": false
          }
        },
        {
          "element_type": "image",
          "position": {"x": 500, "y": 400},
          "size": {"width": 400, "height": 300},
          "z_index": 0,
          "opacity": 1.0,
          "source": "images/slide1_image1.png",
          "fit_mode": "fit"
        }
      ]
    }
  ]
}
```

## 依存関係管理

### パッケージマネージャー: uv
プロジェクトの依存関係管理には**uv**を使用します。uvは高速で信頼性の高いPythonパッケージマネージャーです。

#### pyproject.toml（uv用）
```toml
[project]
name = "slidemaker"
version = "1.0.0"
description = "AI-powered PowerPoint slide generator"
authors = [
    {name = "Your Name", email = "email@example.com"}
]
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.13"
keywords = ["powerpoint", "slides", "ai", "llm", "automation"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.13",
    "Topic :: Office/Business",
]

dependencies = [
    "python-pptx>=0.6.21",
    "Pillow>=10.0.0",
    "pdf2image>=1.16.0",
    "pydantic>=2.0.0",
    "structlog>=23.1.0",
    "typer>=0.9.0",
    "rich>=13.0.0",
    "httpx>=0.25.0",
    "openai>=1.0.0",
    "anthropic>=0.8.0",
    "google-generativeai>=0.3.0",
    "PyYAML>=6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.11.0",
    "mypy>=1.5.0",
    "ruff>=0.1.0",
]
api = [
    "fastapi>=0.104.0",
    "uvicorn>=0.24.0",
    "mangum>=0.17.0",
]
infra = [
    "aws-cdk-lib>=2.100.0",
    "boto3>=1.28.0",
]

[project.scripts]
slidemaker = "slidemaker.cli.main:app"

[project.urls]
Homepage = "https://github.com/yourusername/slidemaker"
Repository = "https://github.com/yourusername/slidemaker"
Documentation = "https://slidemaker.readthedocs.io"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 100
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]

[tool.mypy]
python_version = "3.13"
strict = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
```

## 依存ライブラリ

### Python（コア）
- **python-pptx**: PowerPoint生成
- **Pillow**: 画像処理
- **pdf2image**: PDF変換
- **pydantic**: データバリデーション
- **structlog**: ロギング

### Python（LLM API）
- **openai**: GPT API
- **anthropic**: Claude API
- **google-generativeai**: Gemini API
- **httpx**: 非同期HTTPクライアント

### Python（CLI）
- **typer**: CLIフレームワーク
- **rich**: リッチターミナル出力

### Python（API）
- **fastapi**: APIフレームワーク
- **uvicorn**: ASGIサーバー
- **mangum**: Lambda用アダプタ

### Python（インフラ）
- **aws-cdk-lib**: AWS CDK
- **boto3**: AWS SDK

### TypeScript（WebUI）
- **react**: UIフレームワーク
- **vite**: ビルドツール
- **axios**: HTTPクライアント
- **react-query**: データフェッチング
- **tailwindcss**: スタイリング
- **zustand**: 状態管理

## 設定ファイル形式

### config.yaml例
```yaml
llm:
  composition:
    type: api  # or 'cli'
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

logging:
  level: INFO
  format: json
```
