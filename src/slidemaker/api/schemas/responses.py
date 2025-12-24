"""FastAPI response schema definitions.

このモジュールはFastAPI APIエンドポイントのレスポンススキーマを定義します。
すべてのレスポンスはPydantic v2モデルとして型安全に定義されています。

Response Model Hierarchy:
    TaskResponse (base)
    └── TaskStatusResponse: タスクステータスと結果を含む拡張レスポンス

Example:
    >>> from datetime import datetime, timezone
    >>> from slidemaker.api.schemas.responses import TaskResponse, TaskStatusResponse
    >>> response = TaskResponse(
    ...     task_id="123e4567-e89b-12d3-a456-426614174000",
    ...     status="processing",
    ...     message="Task is being processed",
    ...     created_at=datetime.now(timezone.utc),
    ...     updated_at=datetime.now(timezone.utc)
    ... )
"""

from datetime import datetime, timezone  # noqa: F401 (used in docstring examples)
from typing import Any, Literal

from pydantic import BaseModel, Field


class TaskResponse(BaseModel):
    """タスク作成時の基本レスポンス

    タスク作成APIエンドポイントからのレスポンスを表します。
    タスクの基本情報（ID、ステータス、作成日時等）を含みます。

    Attributes:
        task_id: タスク識別子（UUID形式）
        status: タスクの現在のステータス
        message: ステータスに関する説明メッセージ
        created_at: タスク作成日時（UTC）
        updated_at: 最終更新日時（UTC）

    Example:
        >>> response = TaskResponse(
        ...     task_id="123e4567-e89b-12d3-a456-426614174000",
        ...     status="pending",
        ...     message="Task created successfully",
        ...     created_at=datetime.now(timezone.utc),
        ...     updated_at=datetime.now(timezone.utc)
        ... )
    """

    task_id: str = Field(
        ...,
        description="タスクID（UUID形式）",
        examples=["123e4567-e89b-12d3-a456-426614174000"]
    )
    status: Literal["pending", "processing", "completed", "failed"] = Field(
        ...,
        description="タスクステータス"
    )
    message: str = Field(
        ...,
        description="ステータスメッセージ",
        examples=["Task created successfully", "Task is being processed"]
    )
    created_at: datetime = Field(
        ...,
        description="タスク作成日時（UTC）"
    )
    updated_at: datetime = Field(
        ...,
        description="最終更新日時（UTC）"
    )

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "task_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "pending",
                "message": "Task created successfully",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }


class TaskResult(BaseModel):
    """タスク完了時の結果情報

    タスクが正常に完了した場合の結果情報を表します。
    生成されたPowerPointファイルのメタデータを含みます。

    Attributes:
        output_url: 生成されたPowerPointファイルのS3署名付きURL（有効期限7日間）
        output_filename: 出力ファイル名
        file_size: ファイルサイズ（バイト単位）
        page_count: スライド枚数

    Example:
        >>> result = TaskResult(
        ...     output_url="https://s3.amazonaws.com/bucket/file.pptx?signature=...",
        ...     output_filename="presentation.pptx",
        ...     file_size=1024000,
        ...     page_count=10
        ... )
    """

    output_url: str = Field(
        ...,
        description="生成されたPowerPointファイルのS3署名付きURL（有効期限7日間）",
        examples=["https://s3.amazonaws.com/bucket/file.pptx?signature=..."]
    )
    output_filename: str = Field(
        ...,
        description="出力ファイル名",
        examples=["presentation.pptx", "slides_20240115.pptx"]
    )
    file_size: int = Field(
        ...,
        gt=0,
        description="ファイルサイズ（バイト単位）",
        examples=[1024000]
    )
    page_count: int = Field(
        ...,
        gt=0,
        description="スライド枚数",
        examples=[10, 25]
    )

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "output_url": "https://s3.amazonaws.com/bucket/presentation.pptx?signature=...",
                "output_filename": "presentation.pptx",
                "file_size": 1024000,
                "page_count": 10
            }
        }


class ErrorDetail(BaseModel):
    """エラー詳細情報

    タスクが失敗した場合のエラー詳細を表します。
    標準化されたエラーコードとメッセージを含みます。

    Standard Error Codes:
        - VALIDATION_ERROR: 入力データバリデーションエラー
        - LLM_ERROR: LLM API呼び出しエラー
        - STORAGE_ERROR: ストレージ（S3等）アクセスエラー
        - TIMEOUT_ERROR: タイムアウトエラー
        - INTERNAL_ERROR: 内部エラー

    Attributes:
        error_code: 標準化されたエラーコード
        error_message: ユーザーフレンドリーなエラーメッセージ
        details: 追加の詳細情報（オプション）

    Example:
        >>> error = ErrorDetail(
        ...     error_code="VALIDATION_ERROR",
        ...     error_message="Invalid input format",
        ...     details={"field": "markdown_content", "issue": "Empty content"}
        ... )
    """

    error_code: str = Field(
        ...,
        description="エラーコード",
        examples=["VALIDATION_ERROR", "LLM_ERROR", "STORAGE_ERROR"]
    )
    error_message: str = Field(
        ...,
        description="エラーメッセージ",
        examples=["Invalid input format", "LLM API call failed"]
    )
    details: dict[str, Any] | None = Field(
        default=None,
        description="追加の詳細情報（オプション）"
    )

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "error_code": "VALIDATION_ERROR",
                "error_message": "Invalid input format",
                "details": {
                    "field": "markdown_content",
                    "issue": "Empty content"
                }
            }
        }


class TaskStatusResponse(TaskResponse):
    """タスクステータス取得時の拡張レスポンス

    TaskResponseを継承し、タスクの結果やエラー情報を追加します。
    ステータス照会APIエンドポイントからのレスポンスを表します。

    Attributes:
        result: タスク結果（status="completed"の場合のみ）
        error: エラー詳細（status="failed"の場合のみ）
        progress: 進捗率（status="processing"の場合のみ、0.0-1.0）

    Status-specific fields:
        - pending: result=None, error=None, progress=None
        - processing: result=None, error=None, progress=0.0-1.0
        - completed: result=TaskResult, error=None, progress=None
        - failed: result=None, error=ErrorDetail, progress=None

    Example:
        >>> # 完了時のレスポンス
        >>> response = TaskStatusResponse(
        ...     task_id="123e4567-e89b-12d3-a456-426614174000",
        ...     status="completed",
        ...     message="Task completed successfully",
        ...     created_at=datetime.now(timezone.utc),
        ...     updated_at=datetime.now(timezone.utc),
        ...     result=TaskResult(
        ...         output_url="https://...",
        ...         output_filename="output.pptx",
        ...         file_size=1024000,
        ...         page_count=10
        ...     )
        ... )
    """

    result: TaskResult | None = Field(
        default=None,
        description="タスク結果（status='completed'の場合のみ）"
    )
    error: ErrorDetail | None = Field(
        default=None,
        description="エラー詳細（status='failed'の場合のみ）"
    )
    progress: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="進捗率（status='processing'の場合のみ、0.0-1.0）"
    )

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "task_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "completed",
                "message": "Task completed successfully",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:35:00Z",
                "result": {
                    "output_url": "https://s3.amazonaws.com/bucket/presentation.pptx?signature=...",
                    "output_filename": "presentation.pptx",
                    "file_size": 1024000,
                    "page_count": 10
                },
                "error": None,
                "progress": None
            }
        }


class HealthCheckResponse(BaseModel):
    """ヘルスチェックエンドポイントのレスポンス

    サービスの健全性チェック結果を表します。
    全体のステータスと各コンポーネントの状態を含みます。

    Status Values:
        - ok: すべてのコンポーネントが正常
        - degraded: 一部のコンポーネントに問題あり（サービスは継続）
        - down: サービス停止中

    Attributes:
        status: サービス全体のステータス
        version: アプリケーションバージョン
        timestamp: ヘルスチェック実行日時（UTC）
        checks: 各種チェック結果

    Example:
        >>> response = HealthCheckResponse(
        ...     status="ok",
        ...     version="0.1.0",
        ...     timestamp=datetime.now(timezone.utc),
        ...     checks={
        ...         "llm_available": True,
        ...         "storage_available": True
        ...     }
        ... )
    """

    status: Literal["ok", "degraded", "down"] = Field(
        ...,
        description="サービス全体のステータス"
    )
    version: str = Field(
        ...,
        description="アプリケーションバージョン",
        examples=["0.1.0", "1.2.3"]
    )
    timestamp: datetime = Field(
        ...,
        description="ヘルスチェック実行日時（UTC）"
    )
    checks: dict[str, bool] = Field(
        ...,
        description="各種チェック結果"
    )

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "status": "ok",
                "version": "0.1.0",
                "timestamp": "2024-01-15T10:30:00Z",
                "checks": {
                    "llm_available": True,
                    "storage_available": True
                }
            }
        }
