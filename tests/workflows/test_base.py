"""Tests for WorkflowOrchestrator base class."""

import asyncio
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from slidemaker.utils.file_manager import FileManager
from slidemaker.workflows.base import WorkflowOrchestrator
from slidemaker.workflows.exceptions import WorkflowStepError


# Concrete implementation for testing
class TestWorkflow(WorkflowOrchestrator):
    """Test implementation of WorkflowOrchestrator."""

    async def execute(self, input_data: Any, output_path: Path, **options: Any) -> Path:
        """Test execute implementation."""
        return output_path


class TestWorkflowOrchestrator:
    """Tests for WorkflowOrchestrator."""

    @pytest.fixture
    def llm_manager(self):
        """Create a mock LLM manager."""
        return MagicMock()

    @pytest.fixture
    def file_manager(self, tmp_path):
        """Create a FileManager instance."""
        return FileManager(output_base_dir=str(tmp_path))

    @pytest.fixture
    def workflow(self, llm_manager, file_manager):
        """Create a TestWorkflow instance."""
        return TestWorkflow(llm_manager, file_manager)

    def test_init(self, workflow, llm_manager, file_manager):
        """Test WorkflowOrchestrator initialization."""
        assert workflow.llm_manager == llm_manager
        assert workflow.file_manager == file_manager
        assert workflow.logger is not None

    @pytest.mark.asyncio
    async def test_execute_must_be_implemented(self):
        """Test that execute() must be implemented by subclass."""
        # WorkflowOrchestrator は抽象クラスなのでインスタンス化できない
        # （Pythonでは実際にはインスタンス化できてしまうが、execute()を呼ぶとエラー）
        with pytest.raises(TypeError):
            # 抽象クラスを直接インスタンス化しようとすると TypeError
            WorkflowOrchestrator(MagicMock(), MagicMock())  # type: ignore

    @pytest.mark.asyncio
    async def test_run_step_sync_function_success(self, workflow):
        """Test _run_step with synchronous function that succeeds."""
        def sync_func(x: int, y: int) -> int:
            return x + y

        result = await workflow._run_step("test_step", sync_func, 2, 3)
        assert result == 5

    @pytest.mark.asyncio
    async def test_run_step_async_function_success(self, workflow):
        """Test _run_step with asynchronous function that succeeds."""
        async def async_func(x: int, y: int) -> int:
            await asyncio.sleep(0.01)
            return x * y

        result = await workflow._run_step("test_step", async_func, 3, 4)
        assert result == 12

    @pytest.mark.asyncio
    async def test_run_step_with_kwargs(self, workflow):
        """Test _run_step with keyword arguments."""
        def func_with_kwargs(x: int, y: int = 10, z: int = 20) -> int:
            return x + y + z

        result = await workflow._run_step("test_step", func_with_kwargs, 5, y=15, z=25)
        assert result == 45

    @pytest.mark.asyncio
    async def test_run_step_retry_on_failure(self, workflow):
        """Test _run_step retries on failure."""
        call_count = 0

        def failing_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError(f"Attempt {call_count} failed")
            return "success"

        result = await workflow._run_step(
            "test_step",
            failing_func,
            max_retries=3,
            retry_delay=0.01,
        )

        assert result == "success"
        assert call_count == 3  # 2回失敗、3回目で成功

    @pytest.mark.asyncio
    async def test_run_step_max_retries_exceeded(self, workflow):
        """Test _run_step raises error after max retries."""
        call_count = 0

        def always_failing_func() -> None:
            nonlocal call_count
            call_count += 1
            raise ValueError(f"Attempt {call_count} failed")

        with pytest.raises(WorkflowStepError) as exc_info:
            await workflow._run_step(
                "test_step",
                always_failing_func,
                max_retries=3,
                retry_delay=0.01,
            )

        assert call_count == 3
        error = exc_info.value
        assert error.step_name == "test_step"
        assert error.attempt == 3
        assert "failed after 3 attempts" in error.message

    @pytest.mark.asyncio
    async def test_run_step_with_custom_retry_delay(self, workflow):
        """Test _run_step respects custom retry delay."""
        import time

        call_count = 0
        call_times = []

        def failing_func() -> None:
            nonlocal call_count
            call_count += 1
            call_times.append(time.time())
            if call_count < 2:
                raise ValueError("Retry me")

        start_time = time.time()
        await workflow._run_step(
            "test_step",
            failing_func,
            max_retries=2,
            retry_delay=0.1,  # 100ms
        )

        # 少なくとも retry_delay の時間が経過しているはず
        assert time.time() - start_time >= 0.1

    @pytest.mark.asyncio
    async def test_run_step_error_details_preserved(self, workflow):
        """Test that _run_step preserves error details."""
        def failing_func() -> None:
            raise ValueError("Original error message")

        with pytest.raises(WorkflowStepError) as exc_info:
            await workflow._run_step(
                "test_step",
                failing_func,
                max_retries=1,
            )

        error = exc_info.value
        assert "original_error" in error.details
        assert "Original error message" in error.details["original_error"]
        assert error.details["error_type"] == "ValueError"

    def test_validate_input_default_implementation(self, workflow):
        """Test default _validate_input does nothing."""
        # デフォルト実装は何もしない
        workflow._validate_input("any data")
        workflow._validate_input(None)
        workflow._validate_input({"key": "value"})

    def test_validate_output_path_valid(self, workflow, tmp_path):
        """Test _validate_output_path with valid path."""
        output_path = tmp_path / "output.pptx"

        # 有効なパスの場合は例外が発生しない
        workflow._validate_output_path(output_path)

    def test_validate_output_path_invalid(self, workflow):
        """Test _validate_output_path with invalid path."""
        # パストラバーサル攻撃を試みる
        invalid_path = Path("../../../etc/passwd")

        with pytest.raises(ValueError) as exc_info:
            workflow._validate_output_path(invalid_path)

        assert "Invalid output path" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_run_step_async_function_with_exception(self, workflow):
        """Test _run_step with async function that raises exception."""
        async def async_failing_func() -> None:
            await asyncio.sleep(0.01)
            raise RuntimeError("Async error")

        with pytest.raises(WorkflowStepError) as exc_info:
            await workflow._run_step(
                "async_step",
                async_failing_func,
                max_retries=2,
                retry_delay=0.01,
            )

        error = exc_info.value
        assert "RuntimeError" in error.details["error_type"]

    @pytest.mark.asyncio
    async def test_run_step_with_different_exception_types(self, workflow):
        """Test _run_step handles different exception types."""
        exceptions = [ValueError("Error 1"), TypeError("Error 2"), RuntimeError("Error 3")]
        call_count = 0

        def multi_exception_func() -> None:
            nonlocal call_count
            if call_count < len(exceptions):
                exc = exceptions[call_count]
                call_count += 1
                raise exc

        with pytest.raises(WorkflowStepError):
            await workflow._run_step(
                "test_step",
                multi_exception_func,
                max_retries=3,
                retry_delay=0.01,
            )

        assert call_count == 3

    @pytest.mark.asyncio
    async def test_run_step_return_type_preserved(self, workflow):
        """Test that _run_step preserves return type."""
        # 異なる戻り値の型をテスト
        def return_string() -> str:
            return "test"

        def return_dict() -> dict[str, int]:
            return {"count": 42}

        def return_list() -> list[int]:
            return [1, 2, 3]

        result_str = await workflow._run_step("step1", return_string)
        assert isinstance(result_str, str)
        assert result_str == "test"

        result_dict = await workflow._run_step("step2", return_dict)
        assert isinstance(result_dict, dict)
        assert result_dict == {"count": 42}

        result_list = await workflow._run_step("step3", return_list)
        assert isinstance(result_list, list)
        assert result_list == [1, 2, 3]
