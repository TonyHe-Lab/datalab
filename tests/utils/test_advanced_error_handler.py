"""
Tests for Advanced Error Handler module.
"""

import time
from datetime import datetime, timedelta
import pytest

from src.utils.advanced_error_handler import (
    AdvancedErrorHandler,
    ErrorRecord,
    ErrorCategory,
    ErrorSeverity,
    ErrorRecoveryStrategy,
    smart_retry,
    CircuitBreaker,
    CircuitBreakerOpenError,
    ErrorRecoveryManager,
)


class TestAdvancedErrorHandler:
    """Test AdvancedErrorHandler class."""

    def test_initialization(self):
        """Test handler initialization."""
        handler = AdvancedErrorHandler(max_error_history=100)
        assert len(handler.error_history) == 0
        assert handler.max_error_history == 100
        assert len(handler.recovery_strategies) > 0

    def test_record_error(self):
        """Test recording errors."""
        handler = AdvancedErrorHandler()

        # Record an error
        error = handler.record_error(
            category=ErrorCategory.CONNECTION,
            severity=ErrorSeverity.HIGH,
            message="Database connection failed",
            details={"host": "localhost", "port": 5432},
            context={"operation": "backfill", "batch_id": 123},
        )

        assert len(handler.error_history) == 1
        assert error.category == ErrorCategory.CONNECTION
        assert error.severity == ErrorSeverity.HIGH
        assert error.message == "Database connection failed"
        assert "host" in error.details

    def test_get_recovery_strategy(self):
        """Test recovery strategy selection."""
        handler = AdvancedErrorHandler()

        # Create test error records
        connection_error = ErrorRecord(
            timestamp=datetime.now(),
            category=ErrorCategory.CONNECTION,
            severity=ErrorSeverity.MEDIUM,
            message="Connection timeout",
            details={},
            context={},
        )

        memory_error = ErrorRecord(
            timestamp=datetime.now(),
            category=ErrorCategory.MEMORY,
            severity=ErrorSeverity.CRITICAL,
            message="Out of memory",
            details={},
            context={},
        )

        # Test strategies
        assert (
            handler.get_recovery_strategy(connection_error)
            == ErrorRecoveryStrategy.RETRY
        )
        assert handler.get_recovery_strategy(memory_error) == ErrorRecoveryStrategy.STOP

    def test_should_retry(self):
        """Test retry decision logic."""
        handler = AdvancedErrorHandler()

        error = ErrorRecord(
            timestamp=datetime.now(),
            category=ErrorCategory.CONNECTION,
            severity=ErrorSeverity.MEDIUM,
            message="Test error",
            details={},
            context={},
            retry_count=0,
        )

        # Should retry for first few attempts
        assert handler.should_retry(error, max_retries=3) == True

        # After max retries, should not retry
        error.retry_count = 3
        assert handler.should_retry(error, max_retries=3) == False

    def test_get_error_summary(self):
        """Test error summary generation."""
        handler = AdvancedErrorHandler()

        # Record some errors
        for i in range(5):
            handler.record_error(
                category=ErrorCategory.CONNECTION,
                severity=ErrorSeverity.MEDIUM,
                message=f"Error {i}",
                details={},
            )

        for i in range(3):
            handler.record_error(
                category=ErrorCategory.VALIDATION,
                severity=ErrorSeverity.LOW,
                message=f"Validation error {i}",
                details={},
            )

        # Get summary
        summary = handler.get_error_summary()

        assert summary["total_errors"] == 8
        assert summary["by_category"]["connection"] == 5
        assert summary["by_category"]["validation"] == 3
        assert summary["by_severity"]["medium"] == 5
        assert summary["by_severity"]["low"] == 3
        assert len(summary["recent_errors"]) <= 10

    def test_mark_resolved(self):
        """Test marking errors as resolved."""
        handler = AdvancedErrorHandler()

        error = handler.record_error(
            category=ErrorCategory.CONNECTION,
            severity=ErrorSeverity.MEDIUM,
            message="Test error",
            details={},
        )

        assert not error.resolved

        handler.mark_resolved(error, {"fixed_by": "test", "notes": "manually resolved"})

        assert error.resolved
        assert "resolution" in error.details

    def test_clear_old_errors(self):
        """Test clearing old errors."""
        handler = AdvancedErrorHandler()

        # Record an old error
        old_error = ErrorRecord(
            timestamp=datetime.now() - timedelta(days=10),
            category=ErrorCategory.CONNECTION,
            severity=ErrorSeverity.MEDIUM,
            message="Old error",
            details={},
            context={},
        )
        handler.error_history.append(old_error)

        # Record a recent error
        recent_error = ErrorRecord(
            timestamp=datetime.now(),
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            message="Recent error",
            details={},
            context={},
        )
        handler.error_history.append(recent_error)

        # Clear errors older than 7 days
        handler.clear_old_errors(timedelta(days=7))

        assert len(handler.error_history) == 1
        assert handler.error_history[0].category == ErrorCategory.VALIDATION


class TestSmartRetryDecorator:
    """Test smart_retry decorator."""

    def test_success_on_first_try(self):
        """Test function that succeeds on first try."""

        @smart_retry(max_retries=3)
        def successful_function():
            return "success"

        result = successful_function()
        assert result == "success"

    def test_success_on_retry(self):
        """Test function that succeeds after retries."""
        call_count = 0

        @smart_retry(max_retries=3, initial_delay=0.01)
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"

        result = flaky_function()
        assert result == "success"
        assert call_count == 3

    def test_all_retries_fail(self):
        """Test function that fails all retries."""

        @smart_retry(max_retries=2, initial_delay=0.01)
        def always_failing_function():
            raise RuntimeError("Always fails")

        with pytest.raises(RuntimeError):
            always_failing_function()

    def test_giveup_exceptions(self):
        """Test giveup exceptions."""
        call_count = 0

        @smart_retry(
            max_retries=3,
            initial_delay=0.01,
            retry_exceptions=(ValueError,),
            giveup_exceptions=(RuntimeError,),
        )
        def function_with_giveup():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("Giveup exception")
            return "success"

        with pytest.raises(RuntimeError):
            function_with_giveup()

        assert call_count == 1  # Should not retry for giveup exceptions


class TestCircuitBreaker:
    """Test CircuitBreaker class."""

    def test_circuit_closed_initially(self):
        """Test circuit starts in CLOSED state."""
        breaker = CircuitBreaker(failure_threshold=3)

        @breaker
        def test_function():
            return "success"

        result = test_function()
        assert result == "success"
        assert breaker.state == "CLOSED"

    def test_circuit_opens_on_failures(self):
        """Test circuit opens after threshold failures."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)

        @breaker
        def failing_function():
            raise ValueError("Failure")

        # First failure
        with pytest.raises(ValueError):
            failing_function()
        assert breaker.state == "CLOSED"

        # Second failure - should open circuit
        with pytest.raises(ValueError):
            failing_function()
        assert breaker.state == "OPEN"

    def test_circuit_blocks_when_open(self):
        """Test circuit blocks calls when open."""
        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)

        @breaker
        def test_function():
            return "success"

        # Cause circuit to open
        with pytest.raises(ValueError):

            @breaker
            def failing_function():
                raise ValueError("Failure")

            failing_function()

        assert breaker.state == "OPEN"

        # Should raise CircuitBreakerOpenError
        with pytest.raises(CircuitBreakerOpenError):
            test_function()

    def test_circuit_resets_after_timeout(self):
        """Test circuit resets after recovery timeout."""
        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)

        call_count = 0

        @breaker
        def test_function():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("First call fails")
            return "success"

        # Cause circuit to open
        with pytest.raises(ValueError):
            test_function()

        assert breaker.state == "OPEN"

        # Wait for recovery timeout
        time.sleep(0.15)

        # Should succeed now (circuit in HALF_OPEN, then CLOSED on success)
        result = test_function()
        assert result == "success"
        assert breaker.state == "CLOSED"

    def test_get_state(self):
        """Test getting circuit state."""
        breaker = CircuitBreaker(failure_threshold=3)

        state = breaker.get_state()
        assert state["state"] == "CLOSED"
        assert state["failure_count"] == 0
        assert state["failure_threshold"] == 3


class TestErrorRecoveryManager:
    """Test ErrorRecoveryManager class."""

    def test_initialization(self):
        """Test manager initialization."""
        handler = AdvancedErrorHandler()
        manager = ErrorRecoveryManager(handler)

        assert manager.error_handler == handler
        assert len(manager.recovery_actions) == 0

    def test_register_recovery_action(self):
        """Test registering recovery actions."""
        handler = AdvancedErrorHandler()
        manager = ErrorRecoveryManager(handler)

        action_called = False

        def test_action(error_record):
            nonlocal action_called
            action_called = True

        manager.register_recovery_action(ErrorCategory.CONNECTION, test_action)

        assert ErrorCategory.CONNECTION in manager.recovery_actions
        assert manager.recovery_actions[ErrorCategory.CONNECTION] == test_action

    def test_attempt_recovery_retry(self):
        """Test retry recovery strategy."""
        handler = AdvancedErrorHandler()
        manager = ErrorRecoveryManager(handler)

        error = ErrorRecord(
            timestamp=datetime.now(),
            category=ErrorCategory.CONNECTION,  # Default: RETRY
            severity=ErrorSeverity.MEDIUM,
            message="Test error",
            details={},
            context={},
            retry_count=0,
        )

        result = manager.attempt_recovery(error)
        assert result == True
        assert error.retry_count == 1

    def test_attempt_recovery_skip(self):
        """Test skip recovery strategy."""
        handler = AdvancedErrorHandler()
        manager = ErrorRecoveryManager(handler)

        error = ErrorRecord(
            timestamp=datetime.now(),
            category=ErrorCategory.VALIDATION,  # Default: SKIP
            severity=ErrorSeverity.LOW,
            message="Validation error",
            details={},
            context={},
        )

        result = manager.attempt_recovery(error)
        assert result == True
        assert error.resolved

    def test_attempt_recovery_fallback(self):
        """Test fallback recovery strategy."""
        handler = AdvancedErrorHandler()
        manager = ErrorRecoveryManager(handler)

        # Register a fallback action
        action_called = False

        def fallback_action(error_record):
            nonlocal action_called
            action_called = True

        manager.register_recovery_action(ErrorCategory.PROCESSING, fallback_action)

        error = ErrorRecord(
            timestamp=datetime.now(),
            category=ErrorCategory.PROCESSING,  # Default: FALLBACK
            severity=ErrorSeverity.MEDIUM,
            message="Processing error",
            details={},
            context={},
        )

        result = manager.attempt_recovery(error)
        assert result == True
        assert action_called
        assert error.resolved

    def test_attempt_recovery_stop(self):
        """Test stop recovery strategy."""
        handler = AdvancedErrorHandler()
        manager = ErrorRecoveryManager(handler)

        error = ErrorRecord(
            timestamp=datetime.now(),
            category=ErrorCategory.MEMORY,  # Default: STOP
            severity=ErrorSeverity.CRITICAL,
            message="Out of memory",
            details={},
            context={},
        )

        result = manager.attempt_recovery(error)
        assert result == False  # Stop strategy returns False

    def test_error_handler_integration(self):
        """Test integration with error handler."""
        handler = AdvancedErrorHandler()
        manager = ErrorRecoveryManager(handler)

        # Record an error
        error = handler.record_error(
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            message="Test error",
            details={},
        )

        # Attempt recovery
        result = manager.attempt_recovery(error)

        assert result == True
        assert error.resolved

        # Check error summary
        summary = handler.get_error_summary()
        assert summary["total_errors"] == 1
        assert summary["unresolved_errors"] == 0
