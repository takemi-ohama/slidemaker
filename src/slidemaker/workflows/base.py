"""Workflow Orchestrator Base Class

すべてのワークフローの基底クラスを定義します。

Main Components:
    - WorkflowOrchestrator: ワークフロー実行の抽象基底クラス
"""

import asyncio
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, TypeVar

import structlog

from slidemaker.llm.manager import LLMManager
from slidemaker.utils.file_manager import FileManager
from slidemaker.workflows.exceptions import WorkflowStepError

T = TypeVar("T")


class WorkflowOrchestrator(ABC):
    """ワークフロー実行の基底クラス

    すべてのワークフロー（NewSlideWorkflow, ConversionWorkflow等）の
    共通基盤を提供します。ステップ管理、エラーハンドリング、
    リトライロジックを統一的に扱います。

    Attributes:
        llm_manager: LLMマネージャー
        file_manager: ファイルマネージャー
        logger: 構造化ロガー

    Example:
        >>> class MyWorkflow(WorkflowOrchestrator):
        ...     async def execute(self, input_data, output_path, **options):
        ...         result = await self._run_step(
        ...             "my_step",
        ...             self._my_step_function,
        ...             input_data
        ...         )
        ...         return result
    """

    def __init__(
        self,
        llm_manager: LLMManager,
        file_manager: FileManager,
    ):
        """ワークフローオーケストレーターの初期化

        Args:
            llm_manager: LLMマネージャーインスタンス
            file_manager: ファイルマネージャーインスタンス
        """
        self.llm_manager = llm_manager
        self.file_manager = file_manager
        self.logger = structlog.get_logger(self.__class__.__name__)

    @abstractmethod
    async def execute(self, input_data: Any, output_path: Path, **options) -> Path:
        """ワークフローの実行

        サブクラスで実装する必要があります。

        Args:
            input_data: 入力データ（ファイルパスまたはデータオブジェクト）
            output_path: 出力先パス
            **options: ワークフロー固有のオプション

        Returns:
            Path: 生成されたファイルのパス

        Raises:
            WorkflowError: ワークフロー実行エラー
        """
        pass

    async def _run_step(
        self,
        step_name: str,
        step_func: Callable[..., T],
        *args,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        **kwargs,
    ) -> T:
        """ステップの実行とエラーハンドリング

        指定された関数を実行し、失敗時には自動的にリトライします。
        各試行の間にはretry_delayで指定された時間待機します。

        Args:
            step_name: ステップ名（ログ用）
            step_func: 実行する関数（async関数またはsync関数）
            *args: 関数の位置引数
            max_retries: 最大リトライ回数（デフォルト: 3）
            retry_delay: リトライ間隔（秒、デフォルト: 1.0）
            **kwargs: 関数のキーワード引数

        Returns:
            T: ステップの実行結果

        Raises:
            WorkflowStepError: ステップが最大リトライ回数まで失敗した場合

        Example:
            >>> result = await self._run_step(
            ...     "parse_markdown",
            ...     self._parse_markdown,
            ...     markdown_path,
            ...     max_retries=5,
            ...     retry_delay=2.0
            ... )
        """
        self.logger.info("workflow_step_start", step=step_name)

        for attempt in range(max_retries):
            try:
                # 関数が非同期かどうかを判定して実行
                if asyncio.iscoroutinefunction(step_func):
                    result = await step_func(*args, **kwargs)
                else:
                    result = step_func(*args, **kwargs)

                self.logger.info("workflow_step_success", step=step_name)
                return result

            except Exception as e:
                self.logger.warning(
                    "workflow_step_failed",
                    step=step_name,
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    error=str(e),
                    error_type=type(e).__name__,
                )

                if attempt < max_retries - 1:
                    # まだリトライ回数が残っている場合は待機してリトライ
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    # リトライ回数を使い切った場合はエラーを発生
                    error_msg = f"Step '{step_name}' failed after {max_retries} attempts: {e}"
                    self.logger.error(
                        "workflow_step_exhausted",
                        step=step_name,
                        error=str(e),
                        error_type=type(e).__name__,
                    )
                    raise WorkflowStepError(
                        error_msg,
                        step_name=step_name,
                        attempt=max_retries,
                        details={"original_error": str(e), "error_type": type(e).__name__},
                    ) from e

    def _validate_input(self, input_data: Any) -> None:
        """入力データのバリデーション

        サブクラスでオーバーライドして、入力データの妥当性を検証します。

        Args:
            input_data: 入力データ

        Raises:
            ValueError: 入力データが不正な場合
            WorkflowValidationError: バリデーションエラー
        """
        pass  # サブクラスでオーバーライド

    def _validate_output_path(self, output_path: Path) -> None:
        """出力パスのバリデーション

        FileManagerを使用してパストラバーサル対策を含む
        出力パスの妥当性を検証します。

        Args:
            output_path: 出力先パス

        Raises:
            ValueError: 出力パスが不正な場合

        Example:
            >>> self._validate_output_path(Path("output/slides.pptx"))
        """
        try:
            # FileManagerを使用してパストラバーサル対策
            self.file_manager.validate_output_path(output_path)
            self.logger.debug("output_path_validated", path=str(output_path))
        except Exception as e:
            error_msg = f"Invalid output path: {output_path}"
            self.logger.error(
                "output_path_validation_failed",
                path=str(output_path),
                error=str(e),
            )
            raise ValueError(error_msg) from e
