# コーディング規約とスタイル

## Python スタイル
- **PEP 8準拠**
- **型ヒント必須**: mypy strict mode
- **docstring**: Google形式
- **最大行長**: 100文字
- **import順序**: 標準ライブラリ → サードパーティ → ローカル

## データモデルパターン
- すべてのデータクラスはPydantic BaseModelを継承
- Fieldでバリデーションとデフォルト値を定義
- Literal型で型判別

例:
```python
from pydantic import BaseModel, Field

class TextElement(ElementDefinition):
    element_type: Literal["text"] = "text"
    content: str = Field(...)
    font: FontConfig = Field(default_factory=FontConfig)
    alignment: Alignment = Field(default=Alignment.LEFT)
```

## LLMアダプタパターン
- 抽象基底クラスでインターフェース定義
- API型とCLI型で異なる実装
- 非同期処理（async/await）必須

## エラーハンドリング
- 階層的な例外設計
- 具体的なエラー情報を提供
- ユーザーフレンドリーなメッセージ

例:
```python
class LLMError(Exception):
    """LLM関連のベース例外"""

class LLMTimeoutError(LLMError):
    """タイムアウト例外"""
```

## セキュリティ
- パストラバーサル防止（file_manager.py）
- 入力検証（RGB値: 0-255、JSON解析）
- 環境変数strictモード（未定義変数でエラー）
