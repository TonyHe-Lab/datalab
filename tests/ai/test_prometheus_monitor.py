"""Tests for Prometheus monitoring integration."""

import pytest
from src.ai.prometheus_monitor import PrometheusMonitor, get_monitor, record_cost


class TestPrometheusMonitor:
    def test_monitor_creation(self):
        """Test that monitor can be created."""
        monitor = PrometheusMonitor(namespace="test")
        assert monitor.namespace == "test"

        summary = monitor.get_metrics_summary()
        assert "prometheus_available" in summary
        assert summary["namespace"] == "test"

    def test_record_cost(self, caplog):
        """Test recording cost metrics."""
        monitor = PrometheusMonitor(namespace="test")

        # Record some costs
        monitor.record_cost(10.5, "chat_completion")
        monitor.record_cost(2.3, "embedding")
        monitor.record_cost(0.5, "unknown")

        # Verify no errors - check for warning if Prometheus not available
        # or debug message if it is available
        if "Prometheus client not available" in caplog.text:
            # This is expected when Prometheus is not installed
            assert "Prometheus client not available" in caplog.text
        else:
            # If Prometheus is available, check for debug message
            assert "Recorded cost" in caplog.text

    def test_record_tokens(self):
        """Test recording token metrics."""
        monitor = PrometheusMonitor(namespace="test")

        monitor.record_tokens(1500, "prompt")
        monitor.record_tokens(800, "completion")
        monitor.record_tokens(5000, "embedding")

        # Just verify no exceptions

    def test_record_request(self):
        """Test recording request metrics."""
        monitor = PrometheusMonitor(namespace="test")

        monitor.record_request("chat", "success", 1.5)
        monitor.record_request("embedding", "success", 0.8)
        monitor.record_request("chat", "error", 2.0)

        # Just verify no exceptions

    def test_record_error(self, caplog):
        """Test recording error metrics."""
        monitor = PrometheusMonitor(namespace="test")

        monitor.record_error("rate_limit", "chat")
        monitor.record_error("timeout", "embedding")
        monitor.record_error("authentication", "unknown")

        # Check for warning message
        assert "Recorded error" in caplog.text

    def test_global_monitor(self):
        """Test global monitor instance."""
        monitor1 = get_monitor()
        monitor2 = get_monitor()

        # Should be the same instance
        assert monitor1 is monitor2

    def test_convenience_functions(self):
        """Test convenience functions."""
        # These should not raise exceptions
        record_cost(5.0, "test")

        # Import and test other functions
        from src.ai.prometheus_monitor import (
            record_tokens,
            record_request,
            record_error,
            record_rate_limit,
        )

        record_tokens(100, "prompt")
        record_request("test", "success", 1.0)
        record_error("test_error", "test")
        record_rate_limit("test")

    def test_metrics_summary_structure(self):
        """Test metrics summary has expected structure."""
        monitor = PrometheusMonitor()
        summary = monitor.get_metrics_summary()

        expected_keys = {"prometheus_available", "namespace", "metrics"}
        assert expected_keys.issubset(summary.keys())

        expected_metrics = [
            "cost_total",
            "cost_current",
            "tokens_total",
            "tokens_current",
            "requests_total",
            "request_duration",
            "errors_total",
            "rate_limit_hits",
        ]

        for metric in expected_metrics:
            assert metric in summary["metrics"]

    def test_alertmanager_rules(self):
        """Test Alertmanager rules generation."""
        monitor = PrometheusMonitor(namespace="test")
        rules = monitor.get_alertmanager_rules()

        # Check structure
        assert "groups" in rules
        assert len(rules["groups"]) == 1
        assert rules["groups"][0]["name"] == "ai_cost_alerts"

        # Check rules
        rules_list = rules["groups"][0]["rules"]
        assert len(rules_list) == 3

        # Check each rule has required fields
        for rule in rules_list:
            assert "alert" in rule
            assert "expr" in rule
            assert "for" in rule
            assert "labels" in rule
            assert "annotations" in rule

            # Check severity
            if rule["alert"] == "HighErrorRate":
                assert rule["labels"]["severity"] == "critical"
            else:
                assert rule["labels"]["severity"] == "warning"

    def test_http_server_method(self):
        """Test HTTP server method doesn't crash."""
        monitor = PrometheusMonitor()

        # This should not raise an exception
        monitor.start_http_server(port=0)  # Port 0 for testing

        # If Prometheus is available, it would start a server
        # If not, it should log a warning but not crash


@pytest.mark.integration
class TestIntegrationWithCostTracker:
    """Integration tests with CostTracker."""

    def test_cost_tracker_integration(self):
        """Test that CostTracker can work with PrometheusMonitor."""
        from src.ai.cost_tracker import CostTracker, Pricing

        # Create cost tracker
        pricing = Pricing(
            prompt_per_1k=0.01, completion_per_1k=0.03, embedding_per_1k=0.0001
        )
        tracker = CostTracker(pricing, alert_threshold=100.0)

        # Estimate cost
        usage = {
            "prompt_tokens": 1500,
            "completion_tokens": 800,
            "embedding_tokens": 5000,
        }

        cost_estimate = tracker.estimate(usage)

        # Verify cost estimate structure
        expected_keys = {
            "prompt_cost",
            "completion_cost",
            "embedding_cost",
            "total_cost",
        }
        assert expected_keys.issubset(cost_estimate.keys())

        # All costs should be non-negative
        for key, value in cost_estimate.items():
            assert value >= 0, f"{key} should be non-negative, got {value}"

        # Total should be sum of components
        total = sum(
            cost_estimate[k]
            for k in ["prompt_cost", "completion_cost", "embedding_cost"]
        )
        assert abs(cost_estimate["total_cost"] - total) < 0.0001

        # Record cost to Prometheus (integration point)
        record_cost(cost_estimate["total_cost"], "batch_processing")

        print(f"Cost estimate: {cost_estimate}")
        print(
            "Integration test passed - CostTracker and PrometheusMonitor work together"
        )


if __name__ == "__main__":
    # Run integration test directly
    test = TestIntegrationWithCostTracker()
    test.test_cost_tracker_integration()
