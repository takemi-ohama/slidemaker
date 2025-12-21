"""Workflow Exception Classes

ワークフロー実行時の例外クラスを定義します。

Exception Hierarchy:
    WorkflowError (base)
    ├── WorkflowStepError: ステップ実行エラー
    ├── WorkflowTimeoutError: タイムアウトエラー
    └── WorkflowValidationError: バリデーションエラー
"""

from typing import Any


class WorkflowError(Exception):
    """ワークフロー関連のベース例外

    すべてのワークフロー固有の例外の基底クラスです。

    Attributes:
        message: エラーメッセージ
        details: 追加の詳細情報（オプション）
    """

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """WorkflowErrorの初期化

        Args:
            message: エラーメッセージ
            details: 追加の詳細情報（デフォルト: None）
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        """エラーメッセージの文字列表現

        Returns:
            str: エラーメッセージ（詳細情報を含む）
        """
        if self.details:
            return f"{self.message} (details: {self.details})"
        return self.message


class WorkflowStepError(WorkflowError):
    """ワークフローステップ実行エラー

    ワークフローの特定のステップが失敗した場合に発生します。

    Attributes:
        step_name: 失敗したステップ名
        attempt: 試行回数
    """

    def __init__(
        self,
        message: str,
        step_name: str | None = None,
        attempt: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """WorkflowStepErrorの初期化

        Args:
            message: エラーメッセージ
            step_name: 失敗したステップ名（オプション）
            attempt: 試行回数（オプション）
            details: 追加の詳細情報（オプション）
        """
        super().__init__(message, details)
        self.step_name = step_name
        self.attempt = attempt

    def __str__(self) -> str:
        """エラーメッセージの文字列表現

        Returns:
            str: ステップ情報を含むエラーメッセージ
        """
        parts = [self.message]
        if self.step_name:
            parts.append(f"step='{self.step_name}'")
        if self.attempt is not None:
            parts.append(f"attempt={self.attempt}")
        if self.details:
            parts.append(f"details={self.details}")
        return " | ".join(parts)


class WorkflowTimeoutError(WorkflowError):
    """ワークフロータイムアウトエラー

    ワークフローまたはステップの実行がタイムアウトした場合に発生します。

    Attributes:
        timeout_seconds: タイムアウト時間（秒）
    """

    def __init__(
        self,
        message: str,
        timeout_seconds: float | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """WorkflowTimeoutErrorの初期化

        Args:
            message: エラーメッセージ
            timeout_seconds: タイムアウト時間（秒、オプション）
            details: 追加の詳細情報（オプション）
        """
        super().__init__(message, details)
        self.timeout_seconds = timeout_seconds

    def __str__(self) -> str:
        """エラーメッセージの文字列表現

        Returns:
            str: タイムアウト時間を含むエラーメッセージ
        """
        parts = [self.message]
        if self.timeout_seconds is not None:
            parts.append(f"timeout={self.timeout_seconds}s")
        if self.details:
            parts.append(f"details={self.details}")
        return " | ".join(parts)


class WorkflowValidationError(WorkflowError):
    """ワークフロー入力バリデーションエラー

    ワークフローの入力データまたはLLM出力のバリデーションが失敗した場合に発生します。

    Attributes:
        validation_errors: バリデーションエラーのリスト
    """

    def __init__(
        self,
        message: str,
        validation_errors: list[str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """WorkflowValidationErrorの初期化

        Args:
            message: エラーメッセージ
            validation_errors: バリデーションエラーのリスト（オプション）
            details: 追加の詳細情報（オプション）
        """
        super().__init__(message, details)
        self.validation_errors = validation_errors or []

    def __str__(self) -> str:
        """エラーメッセージの文字列表現

        Returns:
            str: バリデーションエラーを含むエラーメッセージ
        """
        parts = [self.message]
        if self.validation_errors:
            errors_str = ", ".join(self.validation_errors)
            parts.append(f"errors=[{errors_str}]")
        if self.details:
            parts.append(f"details={self.details}")
        return " | ".join(parts)
