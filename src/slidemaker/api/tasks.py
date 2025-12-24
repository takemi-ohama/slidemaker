"""非同期タスク管理モジュール。

このモジュールはFastAPI用の非同期タスクのライフサイクル管理を提供します。
タスク情報はS3に保存され、ステータス追跡、結果取得、エラーハンドリングを実現します。

Task Status Lifecycle:
    pending → processing → completed/failed

Storage Format:
    S3パス: tasks/{task_id}/status.json
    JSON形式: TaskStatusResponse準拠

Example:
    >>> from slidemaker.api.tasks import TaskManager
    >>> from slidemaker.api.storage import S3Storage
    >>>
    >>> storage = S3Storage(bucket_name="my-bucket")
    >>> manager = TaskManager(storage=storage)
    >>>
    >>> # タスク作成
    >>> task_id = await manager.create_task()
    >>>
    >>> # ステータス更新
    >>> await manager.update_task_status(
    ...     task_id=task_id,
    ...     status="processing",
    ...     message="Processing started",
    ...     progress=0.5
    ... )
    >>>
    >>> # 結果設定
    >>> await manager.set_task_result(
    ...     task_id=task_id,
    ...     output_url="https://s3.amazonaws.com/...",
    ...     output_filename="output.pptx",
    ...     file_size=1024000,
    ...     page_count=10
    ... )
"""

import uuid
from datetime import UTC, datetime
from typing import Any

import structlog

from slidemaker.api.schemas.responses import (
    ErrorDetail,
    TaskResult,
    TaskStatusResponse,
)

logger = structlog.get_logger(__name__)


class TaskManager:
    """非同期タスクのライフサイクル管理クラス。

    タスクの作成、ステータス更新、結果取得を管理します。
    タスク情報はS3にJSON形式で永続化されます。

    Attributes:
        storage: S3Storage インスタンス（ファイル操作担当）

    Task Data Structure:
        {
            "task_id": "uuid",
            "status": "pending|processing|completed|failed",
            "message": "...",
            "created_at": "ISO 8601",
            "updated_at": "ISO 8601",
            "result": {...},  // 完了時のみ
            "error": {...},   // 失敗時のみ
            "progress": 0.5   // 処理中のみ
        }

    Example:
        >>> storage = S3Storage(bucket_name="my-bucket")
        >>> manager = TaskManager(storage=storage)
        >>> task_id = await manager.create_task()
        >>> await manager.update_task_status(task_id, "processing", "Started")
    """

    def __init__(self, storage: Any) -> None:
        """TaskManagerを初期化します。

        Args:
            storage: S3Storage インスタンス。以下のインターフェースを持つ必要があります:
                - async def upload_json(self, key: str, data: dict) -> None
                - async def download_json(self, key: str) -> dict

        Example:
            >>> from slidemaker.api.storage import S3Storage
            >>> storage = S3Storage(bucket_name="my-bucket")
            >>> manager = TaskManager(storage=storage)
        """
        self.storage = storage
        self._logger = logger.bind(component="TaskManager")

    def _get_task_key(self, task_id: str) -> str:
        """タスクIDからS3キーを生成します。

        Args:
            task_id: タスク識別子（UUID形式）

        Returns:
            S3オブジェクトキー（例: "tasks/123e4567-.../status.json"）

        Example:
            >>> manager._get_task_key("123e4567-e89b-12d3-a456-426614174000")
            'tasks/123e4567-e89b-12d3-a456-426614174000/status.json'
        """
        return f"tasks/{task_id}/status.json"

    def _datetime_to_iso(self, dt: datetime) -> str:
        """datetimeをISO 8601形式の文字列に変換します。

        Args:
            dt: 変換対象のdatetime（タイムゾーン付き推奨）

        Returns:
            ISO 8601形式の文字列（例: "2024-01-15T10:30:00Z"）

        Example:
            >>> from datetime import UTC, datetime
            >>> dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)
            >>> manager._datetime_to_iso(dt)
            '2024-01-15T10:30:00+00:00'
        """
        return dt.isoformat()

    def _iso_to_datetime(self, iso_str: str) -> datetime:
        """ISO 8601形式の文字列をdatetimeに変換します。

        Args:
            iso_str: ISO 8601形式の文字列

        Returns:
            タイムゾーン付きdatetime（UTC）

        Example:
            >>> iso_str = "2024-01-15T10:30:00Z"
            >>> dt = manager._iso_to_datetime(iso_str)
            >>> dt.tzinfo
            datetime.UTC
        """
        # Python 3.11+ではdatetime.fromisoformat()が"Z"をサポート
        # 互換性のため"Z"を"+00:00"に変換
        if iso_str.endswith("Z"):
            iso_str = iso_str[:-1] + "+00:00"
        return datetime.fromisoformat(iso_str)

    async def create_task(self) -> str:
        """新しいタスクを作成します。

        タスクIDを生成し、初期ステータス（pending）でS3に保存します。

        Returns:
            生成されたタスクID（UUID v4形式）

        Raises:
            Exception: S3への保存に失敗した場合

        Example:
            >>> task_id = await manager.create_task()
            >>> print(task_id)
            '123e4567-e89b-12d3-a456-426614174000'
        """
        task_id = str(uuid.uuid4())
        now = datetime.now(UTC)

        task_data = {
            "task_id": task_id,
            "status": "pending",
            "message": "Task created",
            "created_at": self._datetime_to_iso(now),
            "updated_at": self._datetime_to_iso(now),
        }

        self._logger.info(
            "Creating new task",
            task_id=task_id,
        )

        try:
            await self.storage.upload_json(
                key=self._get_task_key(task_id),
                data=task_data,
            )
            self._logger.info(
                "Task created successfully",
                task_id=task_id,
            )
            return task_id
        except Exception as e:
            self._logger.error(
                "Failed to create task",
                task_id=task_id,
                error=str(e),
            )
            raise

    async def get_task_status(self, task_id: str) -> TaskStatusResponse:
        """タスクステータスを取得します。

        S3からタスク情報を読み込み、TaskStatusResponseに変換します。

        Args:
            task_id: タスク識別子

        Returns:
            タスクステータス情報

        Raises:
            ValueError: タスクが存在しない場合
            Exception: S3からの読み込みに失敗した場合

        Example:
            >>> status = await manager.get_task_status(task_id)
            >>> print(status.status)
            'completed'
            >>> print(status.result.output_filename)
            'presentation.pptx'
        """
        self._logger.debug(
            "Retrieving task status",
            task_id=task_id,
        )

        try:
            task_data = await self.storage.download_json(
                key=self._get_task_key(task_id)
            )
        except Exception as e:
            self._logger.error(
                "Failed to retrieve task status",
                task_id=task_id,
                error=str(e),
            )
            raise ValueError(f"Task not found: {task_id}") from e

        # ISO文字列をdatetimeに変換
        task_data["created_at"] = self._iso_to_datetime(task_data["created_at"])
        task_data["updated_at"] = self._iso_to_datetime(task_data["updated_at"])

        # resultフィールドが存在する場合はTaskResultに変換
        if "result" in task_data and task_data["result"] is not None:
            task_data["result"] = TaskResult(**task_data["result"])

        # errorフィールドが存在する場合はErrorDetailに変換
        if "error" in task_data and task_data["error"] is not None:
            task_data["error"] = ErrorDetail(**task_data["error"])

        return TaskStatusResponse(**task_data)

    async def update_task_status(
        self,
        task_id: str,
        status: str,
        message: str,
        progress: float | None = None,
    ) -> None:
        """タスクステータスを更新します。

        既存のタスクデータを読み込み、ステータス、メッセージ、進捗率を更新してS3に保存します。

        Args:
            task_id: タスク識別子
            status: 新しいステータス（"pending", "processing", "completed", "failed"）
            message: ステータスメッセージ
            progress: 進捗率（0.0-1.0、processingステータス時のみ）

        Raises:
            ValueError: タスクが存在しない場合
            Exception: S3操作に失敗した場合

        Example:
            >>> await manager.update_task_status(
            ...     task_id=task_id,
            ...     status="processing",
            ...     message="Generating slides",
            ...     progress=0.5
            ... )
        """
        self._logger.info(
            "Updating task status",
            task_id=task_id,
            status=status,
            progress=progress,
        )

        try:
            # 既存データを取得
            task_data = await self.storage.download_json(
                key=self._get_task_key(task_id)
            )
        except Exception as e:
            self._logger.error(
                "Failed to retrieve task for update",
                task_id=task_id,
                error=str(e),
            )
            raise ValueError(f"Task not found: {task_id}") from e

        # ステータス更新
        task_data["status"] = status
        task_data["message"] = message
        task_data["updated_at"] = self._datetime_to_iso(datetime.now(UTC))

        # 進捗率を更新（processingステータス時のみ）
        if progress is not None:
            task_data["progress"] = progress
        elif "progress" in task_data:
            # progressがNoneの場合は削除（completedやfailedステータス）
            del task_data["progress"]

        try:
            await self.storage.upload_json(
                key=self._get_task_key(task_id),
                data=task_data,
            )
            self._logger.info(
                "Task status updated successfully",
                task_id=task_id,
                status=status,
            )
        except Exception as e:
            self._logger.error(
                "Failed to update task status",
                task_id=task_id,
                error=str(e),
            )
            raise

    async def set_task_result(
        self,
        task_id: str,
        output_url: str,
        output_filename: str,
        file_size: int,
        page_count: int,
    ) -> None:
        """タスク完了時の結果を設定します。

        statusを"completed"に更新し、resultフィールドを追加します。

        Args:
            task_id: タスク識別子
            output_url: 生成されたPowerPointファイルのS3署名付きURL
            output_filename: 出力ファイル名
            file_size: ファイルサイズ（バイト単位）
            page_count: スライド枚数

        Raises:
            ValueError: タスクが存在しない場合
            Exception: S3操作に失敗した場合

        Example:
            >>> await manager.set_task_result(
            ...     task_id=task_id,
            ...     output_url="https://s3.amazonaws.com/bucket/file.pptx?signature=...",
            ...     output_filename="presentation.pptx",
            ...     file_size=1024000,
            ...     page_count=10
            ... )
        """
        self._logger.info(
            "Setting task result",
            task_id=task_id,
            output_filename=output_filename,
            file_size=file_size,
            page_count=page_count,
        )

        try:
            # 既存データを取得
            task_data = await self.storage.download_json(
                key=self._get_task_key(task_id)
            )
        except Exception as e:
            self._logger.error(
                "Failed to retrieve task for result",
                task_id=task_id,
                error=str(e),
            )
            raise ValueError(f"Task not found: {task_id}") from e

        # 結果を設定
        task_data["status"] = "completed"
        task_data["message"] = "Task completed successfully"
        task_data["updated_at"] = self._datetime_to_iso(datetime.now(UTC))
        task_data["result"] = {
            "output_url": output_url,
            "output_filename": output_filename,
            "file_size": file_size,
            "page_count": page_count,
        }

        # 不要なフィールドを削除
        task_data.pop("progress", None)
        task_data.pop("error", None)

        try:
            await self.storage.upload_json(
                key=self._get_task_key(task_id),
                data=task_data,
            )
            self._logger.info(
                "Task result set successfully",
                task_id=task_id,
            )
        except Exception as e:
            self._logger.error(
                "Failed to set task result",
                task_id=task_id,
                error=str(e),
            )
            raise

    async def set_task_error(
        self,
        task_id: str,
        error_code: str,
        error_message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """タスク失敗時のエラーを設定します。

        statusを"failed"に更新し、errorフィールドを追加します。

        Standard Error Codes:
            - VALIDATION_ERROR: 入力データバリデーションエラー
            - LLM_ERROR: LLM API呼び出しエラー
            - STORAGE_ERROR: ストレージ（S3等）アクセスエラー
            - TIMEOUT_ERROR: タイムアウトエラー
            - INTERNAL_ERROR: 内部エラー

        Args:
            task_id: タスク識別子
            error_code: エラーコード
            error_message: エラーメッセージ
            details: 追加の詳細情報（オプション）

        Raises:
            ValueError: タスクが存在しない場合
            Exception: S3操作に失敗した場合

        Example:
            >>> await manager.set_task_error(
            ...     task_id=task_id,
            ...     error_code="VALIDATION_ERROR",
            ...     error_message="Invalid markdown content",
            ...     details={"field": "markdown_content", "issue": "Empty content"}
            ... )
        """
        self._logger.error(
            "Setting task error",
            task_id=task_id,
            error_code=error_code,
            error_message=error_message,
        )

        try:
            # 既存データを取得
            task_data = await self.storage.download_json(
                key=self._get_task_key(task_id)
            )
        except Exception as e:
            self._logger.error(
                "Failed to retrieve task for error",
                task_id=task_id,
                error=str(e),
            )
            raise ValueError(f"Task not found: {task_id}") from e

        # エラーを設定
        task_data["status"] = "failed"
        task_data["message"] = error_message
        task_data["updated_at"] = self._datetime_to_iso(datetime.now(UTC))
        task_data["error"] = {
            "error_code": error_code,
            "error_message": error_message,
        }
        if details is not None:
            task_data["error"]["details"] = details

        # 不要なフィールドを削除
        task_data.pop("progress", None)
        task_data.pop("result", None)

        try:
            await self.storage.upload_json(
                key=self._get_task_key(task_id),
                data=task_data,
            )
            self._logger.error(
                "Task error set successfully",
                task_id=task_id,
                error_code=error_code,
            )
        except Exception as e:
            self._logger.error(
                "Failed to set task error",
                task_id=task_id,
                error=str(e),
            )
            raise
