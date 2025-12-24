"""FastAPI schema definitions.

このモジュールはFastAPI APIエンドポイントのスキーマ定義をエクスポートします。
リクエスト・レスポンススキーマは型安全なPydantic v2モデルとして定義されています。

Exported Schemas:
    Request Schemas:
        - CreateSlideRequest: スライド作成リクエスト（Markdownから）
        - ConvertSlideRequest: スライド変換リクエスト（PDF/画像から）
        - SlideConfigSchema: スライド設定スキーマ
        - TaskStatusRequest: タスクステータス照会リクエスト

    Response Schemas:
        - TaskResponse: タスク作成レスポンス
        - TaskStatusResponse: タスクステータスレスポンス
        - TaskResult: タスク結果
        - ErrorDetail: エラー詳細
        - HealthCheckResponse: ヘルスチェックレスポンス

Example:
    >>> from slidemaker.api.schemas import CreateSlideRequest, TaskResponse
    >>> from datetime import datetime, timezone
    >>> request = CreateSlideRequest(
    ...     content="# My Presentation\\n\\nSlide content here",
    ...     output_filename="my_slides.pptx"
    ... )
    >>> response = TaskResponse(
    ...     task_id="123e4567-e89b-12d3-a456-426614174000",
    ...     status="pending",
    ...     message="Task created successfully",
    ...     created_at=datetime.now(timezone.utc),
    ...     updated_at=datetime.now(timezone.utc)
    ... )
"""

from slidemaker.api.schemas.requests import (
    ConvertSlideRequest,
    CreateSlideRequest,
    SlideConfigSchema,
    TaskStatusRequest,
)
from slidemaker.api.schemas.responses import (
    ErrorDetail,
    HealthCheckResponse,
    TaskResponse,
    TaskResult,
    TaskStatusResponse,
)

__all__ = [
    # Request schemas
    "ConvertSlideRequest",
    "CreateSlideRequest",
    "SlideConfigSchema",
    "TaskStatusRequest",
    # Response schemas
    "TaskResponse",
    "TaskStatusResponse",
    "TaskResult",
    "ErrorDetail",
    "HealthCheckResponse",
]
