"""Slidemaker Workflows

このパッケージは、Markdown/PDF/画像からPowerPointファイルを生成する
ワークフローを提供します。

Main Components:
    - WorkflowOrchestrator: ワークフロー実行の基底クラス
    - NewSlideWorkflow: Markdown → PowerPoint ワークフロー
    - ConversionWorkflow: PDF/画像 → PowerPoint ワークフロー（Phase 4）
    - CompositionParser: LLM出力のパースとバリデーション
    - ImageCoordinator: 画像生成の調整と管理

Example:
    >>> from slidemaker.workflows import NewSlideWorkflow
    >>> from slidemaker.llm.manager import LLMManager
    >>> from slidemaker.utils.file_manager import FileManager
    >>>
    >>> llm_manager = LLMManager(config)
    >>> file_manager = FileManager(output_base_dir="./output")
    >>> workflow = NewSlideWorkflow(llm_manager, file_manager)
    >>>
    >>> result = await workflow.execute(
    ...     markdown_path="input.md",
    ...     output_path="output.pptx"
    ... )
"""

from slidemaker.workflows.base import WorkflowOrchestrator
from slidemaker.workflows.exceptions import (
    WorkflowError,
    WorkflowStepError,
    WorkflowTimeoutError,
    WorkflowValidationError,
)

__all__ = [
    "WorkflowOrchestrator",
    "WorkflowError",
    "WorkflowStepError",
    "WorkflowTimeoutError",
    "WorkflowValidationError",
]
