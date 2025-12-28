"""
Advanced Error Handling for Historical Data Backfill.

This module provides comprehensive error handling, retry logic, and
error recovery capabilities for the backfill tool.
"""

import logging
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, TypeVar, Union
from functools import wraps
from enum import Enum
import traceback
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)
T = TypeVar("T")


class ErrorSeverity(Enum):
    """Error severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories."""

    CONNECTION = "connection"
    VALIDATION = "validation"
    PROCESSING = "processing"
    DATABASE = "database"
    API = "api"
    MEMORY = "memory"
    NETWORK = "network"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


@dataclass
class ErrorRecord:
    """Record of an error."""

    timestamp: datetime
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    details: Dict[str, Any]
    context: Dict[str, Any]
    stack_trace: Optional[str] = None
    retry_count: int = 0
    resolved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["category"] = self.category.value
        data["severity"] = self.severity.value
        return data


class ErrorRecoveryStrategy(Enum):
    """Error recovery strategies."""

    RETRY = "retry"
    SKIP = "skip"
    FALLBACK = "fallback"
    STOP = "stop"
    ALERT = "alert"


class AdvancedErrorHandler:
    """Advanced error handler with recovery strategies."""

    def __init__(self, max_error_history: int = 1000):
        self.error_history: List[ErrorRecord] = []
        self.max_error_history = max_error_history
        self.recovery_strategies: Dict[ErrorCategory, ErrorRecoveryStrategy] = {
            ErrorCategory.CONNECTION: ErrorRecoveryStrategy.RETRY,
            ErrorCategory.VALIDATION: ErrorRecoveryStrategy.SKIP,
            ErrorCategory.PROCESSING: ErrorRecoveryStrategy.FALLBACK,
            ErrorCategory.DATABASE: ErrorRecoveryStrategy.RETRY,
            ErrorCategory.API: ErrorRecoveryStrategy.RETRY,
            ErrorCategory.MEMORY: ErrorRecoveryStrategy.STOP,
            ErrorCategory.NETWORK: ErrorRecoveryStrategy.RETRY,
            ErrorCategory.TIMEOUT: ErrorRecoveryStrategy.RETRY,
            ErrorCategory.UNKNOWN: ErrorRecoveryStrategy.ALERT,
        }

    def record_error(
        self,
        category: ErrorCategory,
        severity: ErrorSeverity,
        message: str,
        details: Dict[str, Any] = None,
        context: Dict[str, Any] = None,
        exception: Optional[Exception] = None,
    ) -> ErrorRecord:
        """Record an error."""
        error_record = ErrorRecord(
            timestamp=datetime.now(),
            category=category,
            severity=severity,
            message=message,
            details=details or {},
            context=context or {},
            stack_trace=traceback.format_exc() if exception else None,
        )

        self.error_history.append(error_record)

        # Trim history if needed
        if len(self.error_history) > self.max_error_history:
            self.error_history = self.error_history[-self.max_error_history :]

        # Log based on severity
        log_message = f"[{category.value.upper()}] {message}"
        if details:
            log_message += f" | Details: {json.dumps(details, default=str)}"

        if severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
        elif severity == ErrorSeverity.HIGH:
            logger.error(log_message)
        elif severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)

        return error_record

    def get_recovery_strategy(self, error_record: ErrorRecord) -> ErrorRecoveryStrategy:
        """Get recovery strategy for an error."""
        # Check for specific patterns
        if "memory" in error_record.message.lower():
            return ErrorRecoveryStrategy.STOP

        if (
            "connection" in error_record.message.lower()
            and error_record.retry_count >= 3
        ):
            return ErrorRecoveryStrategy.ALERT

        # Use category-based strategy
        return self.recovery_strategies.get(
            error_record.category, ErrorRecoveryStrategy.ALERT
        )

    def should_retry(self, error_record: ErrorRecord, max_retries: int = 3) -> bool:
        """Determine if we should retry based on error."""
        if error_record.retry_count >= max_retries:
            return False

        strategy = self.get_recovery_strategy(error_record)
        return strategy == ErrorRecoveryStrategy.RETRY

    def get_error_summary(
        self, time_window: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """Get error summary within time window."""
        if time_window:
            cutoff = datetime.now() - time_window
            errors = [e for e in self.error_history if e.timestamp >= cutoff]
        else:
            errors = self.error_history

        # Categorize errors
        by_category = {}
        by_severity = {}

        for error in errors:
            cat = error.category.value
            sev = error.severity.value

            by_category[cat] = by_category.get(cat, 0) + 1
            by_severity[sev] = by_severity.get(sev, 0) + 1

        return {
            "total_errors": len(errors),
            "by_category": by_category,
            "by_severity": by_severity,
            "recent_errors": [e.to_dict() for e in errors[-10:]] if errors else [],
            "unresolved_errors": len([e for e in errors if not e.resolved]),
        }

    def mark_resolved(
        self, error_record: ErrorRecord, resolution_details: Dict[str, Any] = None
    ):
        """Mark an error as resolved."""
        error_record.resolved = True
        if resolution_details:
            error_record.details["resolution"] = resolution_details
        logger.info(f"Error resolved: {error_record.message}")

    def clear_old_errors(self, older_than: timedelta = timedelta(days=7)):
        """Clear errors older than specified time."""
        cutoff = datetime.now() - older_than
        self.error_history = [e for e in self.error_history if e.timestamp >= cutoff]
        logger.info(f"Cleared errors older than {older_than}")


def smart_retry(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_exceptions: tuple = (Exception,),
    giveup_exceptions: tuple = (),
    before_retry: Optional[Callable] = None,
):
    """
    Smart retry decorator with exponential backoff and jitter.

    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        jitter: Whether to add random jitter to delays
        retry_exceptions: Exceptions to retry on
        giveup_exceptions: Exceptions to not retry on
        before_retry: Callback before each retry
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            delay = initial_delay

            for attempt in range(max_retries + 1):
                try:
                    if attempt > 0 and before_retry:
                        before_retry(attempt, delay, last_exception)

                    return func(*args, **kwargs)

                except giveup_exceptions as e:
                    # These exceptions should not be retried
                    logger.error(f"Giveup exception on attempt {attempt + 1}: {e}")
                    raise

                except retry_exceptions as e:
                    last_exception = e

                    # Check if we should retry
                    if attempt >= max_retries:
                        logger.error(f"All {max_retries + 1} attempts failed")
                        raise

                    # Calculate next delay
                    if jitter:
                        # Add jitter: random value between 0.5 and 1.5 times the delay
                        import random

                        jitter_factor = 0.5 + random.random()  # 0.5 to 1.5
                        actual_delay = delay * jitter_factor
                    else:
                        actual_delay = delay

                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries + 1} failed: {e}. "
                        f"Retrying in {actual_delay:.1f}s..."
                    )

                    time.sleep(actual_delay)

                    # Update delay for next attempt
                    delay = min(delay * exponential_base, max_delay)

            # This should never be reached
            raise last_exception

        return wrapper

    return decorator


class CircuitBreaker:
    """Circuit breaker pattern for fault tolerance."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exceptions: tuple = (Exception,),
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exceptions = expected_exceptions

        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Check circuit state
            if self.state == "OPEN":
                if self._should_attempt_recovery():
                    self.state = "HALF_OPEN"
                    logger.info("Circuit breaker transitioning to HALF_OPEN")
                else:
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker is OPEN. "
                        f"Last failure: {self.last_failure_time}"
                    )

            try:
                result = func(*args, **kwargs)

                # Success - reset if in HALF_OPEN
                if self.state == "HALF_OPEN":
                    self._reset()

                return result

            except self.expected_exceptions as e:
                self._record_failure()
                raise

        return wrapper

    def _record_failure(self):
        """Record a failure."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.error(
                f"Circuit breaker OPEN: {self.failure_count} failures "
                f"(threshold: {self.failure_threshold})"
            )

    def _should_attempt_recovery(self) -> bool:
        """Check if we should attempt recovery."""
        if not self.last_failure_time:
            return True

        time_since_failure = time.time() - self.last_failure_time
        return time_since_failure >= self.recovery_timeout

    def _reset(self):
        """Reset circuit breaker."""
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"
        logger.info("Circuit breaker reset to CLOSED")

    def get_state(self) -> Dict[str, Any]:
        """Get current state."""
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
        }


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open."""

    pass


class ErrorRecoveryManager:
    """Manager for error recovery operations."""

    def __init__(self, error_handler: AdvancedErrorHandler):
        self.error_handler = error_handler
        self.recovery_actions: Dict[ErrorCategory, Callable] = {}

    def register_recovery_action(self, category: ErrorCategory, action: Callable):
        """Register a recovery action for an error category."""
        self.recovery_actions[category] = action

    def attempt_recovery(self, error_record: ErrorRecord) -> bool:
        """Attempt to recover from an error."""
        strategy = self.error_handler.get_recovery_strategy(error_record)

        logger.info(
            f"Attempting recovery for {error_record.category.value} error: "
            f"{error_record.message} (strategy: {strategy.value})"
        )

        try:
            if strategy == ErrorRecoveryStrategy.RETRY:
                return self._retry_recovery(error_record)
            elif strategy == ErrorRecoveryStrategy.SKIP:
                return self._skip_recovery(error_record)
            elif strategy == ErrorRecoveryStrategy.FALLBACK:
                return self._fallback_recovery(error_record)
            elif strategy == ErrorRecoveryStrategy.ALERT:
                return self._alert_recovery(error_record)
            elif strategy == ErrorRecoveryStrategy.STOP:
                return self._stop_recovery(error_record)
            else:
                logger.warning(f"Unknown recovery strategy: {strategy}")
                return False

        except Exception as e:
            logger.error(f"Recovery attempt failed: {e}")
            return False

    def _retry_recovery(self, error_record: ErrorRecord) -> bool:
        """Retry recovery strategy."""
        error_record.retry_count += 1

        if self.error_handler.should_retry(error_record):
            logger.info(f"Retry #{error_record.retry_count} scheduled")
            return True
        else:
            logger.warning(f"Max retries reached for error: {error_record.message}")
            return False

    def _skip_recovery(self, error_record: ErrorRecord) -> bool:
        """Skip recovery strategy."""
        logger.info(f"Skipping error: {error_record.message}")
        self.error_handler.mark_resolved(
            error_record,
            {"resolution": "skipped", "reason": "non-critical validation error"},
        )
        return True

    def _fallback_recovery(self, error_record: ErrorRecord) -> bool:
        """Fallback recovery strategy."""
        # Check if we have a registered recovery action
        action = self.recovery_actions.get(error_record.category)
        if action:
            try:
                action(error_record)
                self.error_handler.mark_resolved(
                    error_record, {"resolution": "fallback_applied"}
                )
                return True
            except Exception as e:
                logger.error(f"Fallback action failed: {e}")
                return False
        else:
            logger.warning(
                f"No fallback action registered for {error_record.category.value}"
            )
            return False

    def _alert_recovery(self, error_record: ErrorRecord) -> bool:
        """Alert recovery strategy."""
        # In a real system, this would send alerts (email, Slack, etc.)
        logger.critical(
            f"ALERT: Critical error requires attention - {error_record.message}"
        )
        # Mark as unresolved so it shows up in reports
        return False

    def _stop_recovery(self, error_record: ErrorRecord) -> bool:
        """Stop recovery strategy."""
        logger.critical(
            f"STOPPING: Critical error detected - {error_record.message}. "
            f"Processing will be halted."
        )
        # This would typically raise an exception to stop processing
        return False


def create_error_handler() -> AdvancedErrorHandler:
    """Create a configured error handler."""
    handler = AdvancedErrorHandler(max_error_history=5000)

    # Configure recovery strategies
    handler.recovery_strategies.update(
        {
            ErrorCategory.MEMORY: ErrorRecoveryStrategy.STOP,
            ErrorCategory.CONNECTION: ErrorRecoveryStrategy.RETRY,
            ErrorCategory.VALIDATION: ErrorRecoveryStrategy.SKIP,
        }
    )

    return handler
