"""Tests for workflow exceptions."""

import pytest

from slidemaker.workflows.exceptions import (
    WorkflowError,
    WorkflowStepError,
    WorkflowTimeoutError,
    WorkflowValidationError,
)


class TestWorkflowError:
    """Tests for WorkflowError base exception."""

    def test_init_with_message_only(self):
        """Test initialization with message only."""
        error = WorkflowError("Test error")
        assert error.message == "Test error"
        assert error.details == {}

    def test_init_with_details(self):
        """Test initialization with details."""
        details = {"key": "value", "count": 42}
        error = WorkflowError("Test error", details=details)
        assert error.message == "Test error"
        assert error.details == details

    def test_str_without_details(self):
        """Test string representation without details."""
        error = WorkflowError("Test error")
        assert str(error) == "Test error"

    def test_str_with_details(self):
        """Test string representation with details."""
        details = {"key": "value"}
        error = WorkflowError("Test error", details=details)
        assert str(error) == "Test error (details: {'key': 'value'})"

    def test_inheritance(self):
        """Test that WorkflowError inherits from Exception."""
        error = WorkflowError("Test error")
        assert isinstance(error, Exception)


class TestWorkflowStepError:
    """Tests for WorkflowStepError."""

    def test_init_minimal(self):
        """Test initialization with minimal arguments."""
        error = WorkflowStepError("Step failed")
        assert error.message == "Step failed"
        assert error.step_name is None
        assert error.attempt is None
        assert error.details == {}

    def test_init_with_step_info(self):
        """Test initialization with step information."""
        error = WorkflowStepError(
            "Step failed",
            step_name="parse_markdown",
            attempt=3,
            details={"error_type": "ValueError"},
        )
        assert error.message == "Step failed"
        assert error.step_name == "parse_markdown"
        assert error.attempt == 3
        assert error.details == {"error_type": "ValueError"}

    def test_str_minimal(self):
        """Test string representation with minimal info."""
        error = WorkflowStepError("Step failed")
        assert str(error) == "Step failed"

    def test_str_with_step_name(self):
        """Test string representation with step name."""
        error = WorkflowStepError("Step failed", step_name="parse_markdown")
        assert str(error) == "Step failed | step='parse_markdown'"

    def test_str_with_attempt(self):
        """Test string representation with attempt number."""
        error = WorkflowStepError("Step failed", attempt=3)
        assert str(error) == "Step failed | attempt=3"

    def test_str_complete(self):
        """Test string representation with all information."""
        error = WorkflowStepError(
            "Step failed",
            step_name="parse_markdown",
            attempt=3,
            details={"error_type": "ValueError"},
        )
        result = str(error)
        assert "Step failed" in result
        assert "step='parse_markdown'" in result
        assert "attempt=3" in result
        assert "details=" in result

    def test_inheritance(self):
        """Test that WorkflowStepError inherits from WorkflowError."""
        error = WorkflowStepError("Step failed")
        assert isinstance(error, WorkflowError)
        assert isinstance(error, Exception)


class TestWorkflowTimeoutError:
    """Tests for WorkflowTimeoutError."""

    def test_init_minimal(self):
        """Test initialization with minimal arguments."""
        error = WorkflowTimeoutError("Operation timed out")
        assert error.message == "Operation timed out"
        assert error.timeout_seconds is None
        assert error.details == {}

    def test_init_with_timeout(self):
        """Test initialization with timeout value."""
        error = WorkflowTimeoutError(
            "Operation timed out",
            timeout_seconds=30.5,
            details={"step": "llm_call"},
        )
        assert error.message == "Operation timed out"
        assert error.timeout_seconds == 30.5
        assert error.details == {"step": "llm_call"}

    def test_str_minimal(self):
        """Test string representation without timeout."""
        error = WorkflowTimeoutError("Operation timed out")
        assert str(error) == "Operation timed out"

    def test_str_with_timeout(self):
        """Test string representation with timeout."""
        error = WorkflowTimeoutError("Operation timed out", timeout_seconds=30.0)
        assert str(error) == "Operation timed out | timeout=30.0s"

    def test_str_complete(self):
        """Test string representation with all information."""
        error = WorkflowTimeoutError(
            "Operation timed out",
            timeout_seconds=30.0,
            details={"step": "llm_call"},
        )
        result = str(error)
        assert "Operation timed out" in result
        assert "timeout=30.0s" in result
        assert "details=" in result

    def test_inheritance(self):
        """Test that WorkflowTimeoutError inherits from WorkflowError."""
        error = WorkflowTimeoutError("Operation timed out")
        assert isinstance(error, WorkflowError)
        assert isinstance(error, Exception)


class TestWorkflowValidationError:
    """Tests for WorkflowValidationError."""

    def test_init_minimal(self):
        """Test initialization with minimal arguments."""
        error = WorkflowValidationError("Validation failed")
        assert error.message == "Validation failed"
        assert error.validation_errors == []
        assert error.details == {}

    def test_init_with_errors(self):
        """Test initialization with validation errors."""
        validation_errors = ["Field 'name' is required", "Field 'age' must be positive"]
        error = WorkflowValidationError(
            "Validation failed",
            validation_errors=validation_errors,
            details={"field_count": 2},
        )
        assert error.message == "Validation failed"
        assert error.validation_errors == validation_errors
        assert error.details == {"field_count": 2}

    def test_str_minimal(self):
        """Test string representation without errors."""
        error = WorkflowValidationError("Validation failed")
        assert str(error) == "Validation failed"

    def test_str_with_errors(self):
        """Test string representation with validation errors."""
        validation_errors = ["Error 1", "Error 2"]
        error = WorkflowValidationError("Validation failed", validation_errors=validation_errors)
        result = str(error)
        assert "Validation failed" in result
        assert "errors=[Error 1, Error 2]" in result

    def test_str_complete(self):
        """Test string representation with all information."""
        validation_errors = ["Error 1"]
        error = WorkflowValidationError(
            "Validation failed",
            validation_errors=validation_errors,
            details={"field": "name"},
        )
        result = str(error)
        assert "Validation failed" in result
        assert "errors=[Error 1]" in result
        assert "details=" in result

    def test_inheritance(self):
        """Test that WorkflowValidationError inherits from WorkflowError."""
        error = WorkflowValidationError("Validation failed")
        assert isinstance(error, WorkflowError)
        assert isinstance(error, Exception)
