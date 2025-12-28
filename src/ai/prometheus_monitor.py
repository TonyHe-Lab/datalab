"""Prometheus metrics exporter for AI cost monitoring.

This module provides Prometheus metrics for tracking Azure OpenAI usage
and costs. It can be integrated with Prometheus server for production
monitoring.

Usage:
    monitor = PrometheusMonitor()
    monitor.record_cost(10.5, "chat")
    monitor.record_tokens(1500, "prompt")

    # Expose metrics on HTTP endpoint
    # from prometheus_client import start_http_server
    # start_http_server(8000)
"""

from typing import Optional
import logging

try:
    from prometheus_client import Counter, Gauge, Histogram

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

    # Create dummy classes for when Prometheus is not available
    class DummyMetric:
        def __init__(self, *args, **kwargs):
            pass

        def labels(self, **kwargs):
            return self

        def inc(self, amount=1):
            pass

        def set(self, value):
            pass

        def observe(self, value):
            pass

    Counter = Gauge = Histogram = DummyMetric

logger = logging.getLogger(__name__)


class PrometheusMonitor:
    """Prometheus metrics monitor for AI costs and usage."""

    def __init__(self, namespace: str = "ai"):
        self.namespace = namespace

        if not PROMETHEUS_AVAILABLE:
            logger.warning("Prometheus client not available. Using dummy metrics.")

        # Cost metrics
        self.cost_total = Counter(
            f"{namespace}_cost_total", "Total cost in USD", ["operation_type"]
        )

        self.cost_current = Gauge(
            f"{namespace}_cost_current", "Current cost in USD", ["operation_type"]
        )

        # Token metrics
        self.tokens_total = Counter(
            f"{namespace}_tokens_total", "Total tokens processed", ["token_type"]
        )

        self.tokens_current = Gauge(
            f"{namespace}_tokens_current", "Current tokens in request", ["token_type"]
        )

        # Request metrics
        self.requests_total = Counter(
            f"{namespace}_requests_total",
            "Total requests made",
            ["operation_type", "status"],
        )

        self.request_duration = Histogram(
            f"{namespace}_request_duration_seconds",
            "Request duration in seconds",
            ["operation_type"],
        )

        # Error metrics
        self.errors_total = Counter(
            f"{namespace}_errors_total",
            "Total errors encountered",
            ["error_type", "operation_type"],
        )

        # Rate limit metrics
        self.rate_limit_hits = Counter(
            f"{namespace}_rate_limit_hits_total",
            "Total rate limit hits",
            ["operation_type"],
        )

    def record_cost(self, cost: float, operation_type: str = "unknown"):
        """Record cost for an operation."""
        self.cost_total.labels(operation_type=operation_type).inc(cost)
        self.cost_current.labels(operation_type=operation_type).set(cost)
        logger.debug(f"Recorded cost: {cost} USD for {operation_type}")

    def record_tokens(self, tokens: int, token_type: str):
        """Record token usage."""
        self.tokens_total.labels(token_type=token_type).inc(tokens)
        self.tokens_current.labels(token_type=token_type).set(tokens)

    def record_request(
        self,
        operation_type: str,
        status: str = "success",
        duration: Optional[float] = None,
    ):
        """Record a request."""
        self.requests_total.labels(operation_type=operation_type, status=status).inc()

        if duration is not None:
            self.request_duration.labels(operation_type=operation_type).observe(
                duration
            )

    def record_error(self, error_type: str, operation_type: str = "unknown"):
        """Record an error."""
        self.errors_total.labels(
            error_type=error_type, operation_type=operation_type
        ).inc()
        logger.warning(f"Recorded error: {error_type} for {operation_type}")

    def record_rate_limit(self, operation_type: str = "unknown"):
        """Record a rate limit hit."""
        self.rate_limit_hits.labels(operation_type=operation_type).inc()
        logger.warning(f"Rate limit hit for {operation_type}")

    def get_metrics_summary(self) -> dict:
        """Get summary of current metrics (for testing/logging)."""
        return {
            "prometheus_available": PROMETHEUS_AVAILABLE,
            "namespace": self.namespace,
            "metrics": [
                "cost_total",
                "cost_current",
                "tokens_total",
                "tokens_current",
                "requests_total",
                "request_duration",
                "errors_total",
                "rate_limit_hits",
            ],
        }

    def start_http_server(self, port: int = 8000, addr: str = ""):
        """Start HTTP server to expose Prometheus metrics.

        Args:
            port: Port to listen on (default: 8000)
            addr: Address to bind to (default: all interfaces)
        """
        if not PROMETHEUS_AVAILABLE:
            logger.warning("Prometheus client not available. Cannot start HTTP server.")
            return

        try:
            from prometheus_client import start_http_server

            start_http_server(port, addr)
            logger.info(f"Prometheus metrics server started on port {port}")
        except Exception as e:
            logger.error(f"Failed to start Prometheus HTTP server: {e}")

    def get_alertmanager_rules(self) -> dict:
        """Generate Alertmanager alert rules for AI cost monitoring.

        Returns:
            dict: Alertmanager rules in YAML-compatible format
        """
        return {
            "groups": [
                {
                    "name": "ai_cost_alerts",
                    "rules": [
                        {
                            "alert": "HighAICost",
                            "expr": f'{self.namespace}_cost_current{{operation_type=~"chat|embedding"}} > 10',
                            "for": "5m",
                            "labels": {"severity": "warning", "team": "ai-ops"},
                            "annotations": {
                                "summary": "High AI cost detected",
                                "description": "AI cost for {{ $labels.operation_type }} is {{ $value }} USD (threshold: 10 USD)",
                            },
                        },
                        {
                            "alert": "RateLimitHit",
                            "expr": f"rate({self.namespace}_rate_limit_hits_total[5m]) > 0",
                            "for": "1m",
                            "labels": {"severity": "warning", "team": "ai-ops"},
                            "annotations": {
                                "summary": "Rate limit hit detected",
                                "description": "Rate limit hit for {{ $labels.operation_type }}",
                            },
                        },
                        {
                            "alert": "HighErrorRate",
                            "expr": f"rate({self.namespace}_errors_total[5m]) / rate({self.namespace}_requests_total[5m]) > 0.1",
                            "for": "5m",
                            "labels": {"severity": "critical", "team": "ai-ops"},
                            "annotations": {
                                "summary": "High error rate detected",
                                "description": "Error rate is {{ $value }} (threshold: 0.1)",
                            },
                        },
                    ],
                }
            ]
        }


# Global monitor instance for easy access
_default_monitor: Optional[PrometheusMonitor] = None


def get_monitor() -> PrometheusMonitor:
    """Get or create the default Prometheus monitor."""
    global _default_monitor
    if _default_monitor is None:
        _default_monitor = PrometheusMonitor()
    return _default_monitor


def record_cost(cost: float, operation_type: str = "unknown"):
    """Record cost using the default monitor."""
    get_monitor().record_cost(cost, operation_type)


def record_tokens(tokens: int, token_type: str):
    """Record tokens using the default monitor."""
    get_monitor().record_tokens(tokens, token_type)


def record_request(
    operation_type: str, status: str = "success", duration: Optional[float] = None
):
    """Record request using the default monitor."""
    get_monitor().record_request(operation_type, status, duration)


def record_error(error_type: str, operation_type: str = "unknown"):
    """Record error using the default monitor."""
    get_monitor().record_error(error_type, operation_type)


def record_rate_limit(operation_type: str = "unknown"):
    """Record rate limit using the default monitor."""
    get_monitor().record_rate_limit(operation_type)
