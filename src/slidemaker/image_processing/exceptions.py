"""Image Processing Exception Classes

画像処理時の例外クラスを定義します。

Exception Hierarchy:
    ImageProcessingError (base)
    ├── ImageCropError: 画像切り出しエラー
    ├── ImageSaveError: 画像保存エラー
    └── ImageAnalysisError: 画像分析エラー
"""

from typing import Any


class ImageProcessingError(Exception):
    """画像処理関連のベース例外

    すべての画像処理固有の例外の基底クラスです。

    Attributes:
        message: エラーメッセージ
        details: 追加の詳細情報（オプション）
    """

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """ImageProcessingErrorの初期化

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


class ImageCropError(ImageProcessingError):
    """画像切り出しエラー

    画像の切り出し処理が失敗した場合に発生します。

    Attributes:
        bbox: 切り出し領域の座標 (x, y, width, height)
    """

    def __init__(
        self,
        message: str,
        bbox: tuple[int, int, int, int] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """ImageCropErrorの初期化

        Args:
            message: エラーメッセージ
            bbox: 切り出し領域の座標（オプション）
            details: 追加の詳細情報（オプション）
        """
        super().__init__(message, details)
        self.bbox = bbox

    def __str__(self) -> str:
        """エラーメッセージの文字列表現

        Returns:
            str: bbox情報を含むエラーメッセージ
        """
        parts = [self.message]
        if self.bbox is not None:
            parts.append(f"bbox={self.bbox}")
        if self.details:
            parts.append(f"details={self.details}")
        return " | ".join(parts)


class ImageSaveError(ImageProcessingError):
    """画像保存エラー

    画像の保存処理が失敗した場合に発生します。

    Attributes:
        output_path: 保存先のパス
        format: 画像形式（PNG, JPEGなど）
    """

    def __init__(
        self,
        message: str,
        output_path: str | None = None,
        format: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """ImageSaveErrorの初期化

        Args:
            message: エラーメッセージ
            output_path: 保存先のパス（オプション）
            format: 画像形式（オプション）
            details: 追加の詳細情報（オプション）
        """
        super().__init__(message, details)
        self.output_path = output_path
        self.format = format

    def __str__(self) -> str:
        """エラーメッセージの文字列表現

        Returns:
            str: 保存先パスと形式を含むエラーメッセージ
        """
        parts = [self.message]
        if self.output_path is not None:
            parts.append(f"output_path='{self.output_path}'")
        if self.format is not None:
            parts.append(f"format='{self.format}'")
        if self.details:
            parts.append(f"details={self.details}")
        return " | ".join(parts)


class ImageAnalysisError(ImageProcessingError):
    """画像分析エラー

    LLMによる画像分析が失敗した場合に発生します。

    Attributes:
        llm_provider: LLMプロバイダー名
        attempt: 試行回数
    """

    def __init__(
        self,
        message: str,
        llm_provider: str | None = None,
        attempt: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """ImageAnalysisErrorの初期化

        Args:
            message: エラーメッセージ
            llm_provider: LLMプロバイダー名(オプション)
            attempt: 試行回数(オプション)
            details: 追加の詳細情報(オプション)
        """
        super().__init__(message, details)
        self.llm_provider = llm_provider
        self.attempt = attempt

    def __str__(self) -> str:
        """エラーメッセージの文字列表現

        Returns:
            str: LLMプロバイダーと試行回数を含むエラーメッセージ
        """
        parts = [self.message]
        if self.llm_provider is not None:
            parts.append(f"llm_provider='{self.llm_provider}'")
        if self.attempt is not None:
            parts.append(f"attempt={self.attempt}")
        if self.details:
            parts.append(f"details={self.details}")
        return " | ".join(parts)
