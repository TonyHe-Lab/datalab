"""
Tests for Monitoring and Reporter module.
"""

import time
from datetime import datetime, timedelta
from src.utils.monitoring_reporter import (
    ProcessingMetrics,
    ErrorSummary,
    ProgressReporter,
    ReportGenerator,
    AlertManager,
    ReportLevel,
)


class TestProcessingMetrics:
    """Test ProcessingMetrics class."""

    def test_initialization(self):
        """Test metrics initialization."""
        metrics = ProcessingMetrics()
        assert metrics.total_records == 0
        assert metrics.processed_records == 0
        assert metrics.failed_records == 0
        assert metrics.start_time is None
        assert metrics.end_time is None

    def test_update_success_rate(self):
        """Test success rate calculation."""
        metrics = ProcessingMetrics()
        metrics.processed_records = 100
        metrics.failed_records = 10

        metrics.update_success_rate()
        assert metrics.success_rate == 0.9  # (100-10)/100 = 0.9

    def test_update_records_per_second(self):
        """Test records per second calculation."""
        metrics = ProcessingMetrics()
        metrics.start_time = datetime.now() - timedelta(seconds=10)
        metrics.processed_records = 100

        metrics.update_records_per_second()
        # Allow small floating point differences
        assert abs(metrics.records_per_second - 10.0) < 0.1  # 100/10 = 10 ± 0.1

    def test_get_elapsed_time(self):
        """Test elapsed time calculation."""
        metrics = ProcessingMetrics()
        metrics.start_time = datetime.now() - timedelta(seconds=30)

        elapsed = metrics.get_elapsed_time()
        assert elapsed is not None
        assert elapsed.total_seconds() >= 30

    def test_get_estimated_time_remaining(self):
        """Test estimated time remaining calculation."""
        metrics = ProcessingMetrics()
        metrics.start_time = datetime.now() - timedelta(seconds=10)
        metrics.processed_records = 100
        metrics.records_per_second = 10.0

        eta = metrics.get_estimated_time_remaining(200)
        assert eta is not None
        # Should be about 10 seconds remaining (100 records at 10 rec/s)
        assert 9 <= eta.total_seconds() <= 11


class TestErrorSummary:
    """Test ErrorSummary class."""

    def test_initialization(self):
        """Test error summary initialization."""
        errors = ErrorSummary()
        assert errors.total_errors == 0
        assert errors.error_types == {}
        assert errors.recent_errors == []

    def test_add_error(self):
        """Test adding errors."""
        errors = ErrorSummary()

        # Add first error
        errors.add_error("connection_error", {"message": "Connection failed"})
        assert errors.total_errors == 1
        assert errors.error_types["connection_error"] == 1
        assert len(errors.recent_errors) == 1

        # Add second error of same type
        errors.add_error("connection_error", {"message": "Timeout"})
        assert errors.total_errors == 2
        assert errors.error_types["connection_error"] == 2
        assert len(errors.recent_errors) == 2

        # Add different error type
        errors.add_error("validation_error", {"field": "name", "issue": "missing"})
        assert errors.total_errors == 3
        assert errors.error_types["validation_error"] == 1
        assert len(errors.recent_errors) == 3

    def test_get_top_errors(self):
        """Test getting top errors."""
        errors = ErrorSummary()

        # Add multiple errors
        for _ in range(5):
            errors.add_error("type_a", {})
        for _ in range(3):
            errors.add_error("type_b", {})
        errors.add_error("type_c", {})

        top_errors = errors.get_top_errors(2)
        assert len(top_errors) == 2
        assert top_errors[0]["type"] == "type_a"
        assert top_errors[0]["count"] == 5
        assert top_errors[1]["type"] == "type_b"
        assert top_errors[1]["count"] == 3


class TestProgressReporter:
    """Test ProgressReporter class."""

    def test_initialization(self):
        """Test reporter initialization."""
        reporter = ProgressReporter()
        assert reporter.report_interval == 10
        assert reporter.metrics.total_records == 0
        assert len(reporter.callbacks) == 0

    def test_start(self):
        """Test starting monitoring."""
        reporter = ProgressReporter()
        reporter.start(1000)

        assert reporter.metrics.total_records == 1000
        assert reporter.metrics.start_time is not None

    def test_update_processed(self):
        """Test updating processed records."""
        reporter = ProgressReporter(report_interval_seconds=1)
        reporter.start(100)

        # Update processed records
        reporter.update_processed(10)
        assert reporter.metrics.processed_records == 10

        # Wait and update again
        time.sleep(1.1)  # Wait longer than report interval
        reporter.update_processed(5)
        assert reporter.metrics.processed_records == 15

    def test_update_failed(self):
        """Test updating failed records."""
        reporter = ProgressReporter()
        reporter.start(100)

        # Update failed records
        reporter.update_failed(3, "connection_error", {"host": "localhost"})

        assert reporter.metrics.failed_records == 3
        assert reporter.error_summary.total_errors == 1
        assert "connection_error" in reporter.error_summary.error_types

    def test_generate_report(self):
        """Test report generation."""
        reporter = ProgressReporter()
        reporter.start(1000)
        reporter.update_processed(250)
        reporter.update_failed(10, "test_error")

        # Generate summary report
        report = reporter.generate_report(ReportLevel.SUMMARY)

        assert "timestamp" in report
        assert "metrics" in report
        assert "progress_percentage" in report
        assert report["progress_percentage"] == 25.0  # 250/1000 = 25%

        # Check metrics
        metrics = report["metrics"]
        assert metrics["total_records"] == 1000
        assert metrics["processed_records"] == 250
        assert metrics["failed_records"] == 10

    def test_complete(self):
        """Test completing monitoring."""
        reporter = ProgressReporter()
        reporter.start(100)
        reporter.update_processed(100)

        final_report = reporter.complete()

        assert reporter.metrics.end_time is not None
        assert "metrics" in final_report
        assert final_report["metrics"]["success_rate"] == 1.0  # No failures

    def test_register_callback(self):
        """Test callback registration."""
        reporter = ProgressReporter()

        callback_called = False
        callback_data = None

        def test_callback(data):
            nonlocal callback_called, callback_data
            callback_called = True
            callback_data = data

        reporter.register_callback(test_callback)
        reporter.start(100)

        # Generate report should trigger callback
        report = reporter.generate_report()

        assert callback_called
        assert callback_data == report


class TestReportGenerator:
    """Test ReportGenerator class."""

    def test_generate_summary_report(self):
        """Test summary report generation."""
        metrics = ProcessingMetrics()
        metrics.total_records = 1000
        metrics.processed_records = 750
        metrics.failed_records = 25
        metrics.start_time = datetime.now() - timedelta(minutes=5)
        metrics.update_success_rate()
        metrics.update_records_per_second()

        errors = ErrorSummary()
        errors.add_error("connection_error", {})
        errors.add_error("validation_error", {})

        report = ReportGenerator.generate_summary_report(metrics, errors)

        assert "summary" in report
        assert "errors" in report
        assert "recommendations" in report

        summary = report["summary"]
        assert summary["total_records"] == 1000
        assert summary["processed"] == 750
        assert summary["failed"] == 25

    def test_generate_detailed_report(self):
        """Test detailed report generation."""
        metrics = ProcessingMetrics()
        metrics.total_records = 500
        metrics.processed_records = 400
        metrics.failed_records = 20
        metrics.memory_usage_mb = 250.5
        metrics.cpu_usage_percent = 45.2

        errors = ErrorSummary()
        for _ in range(5):
            errors.add_error("test_error", {})

        report = ReportGenerator.generate_detailed_report(metrics, errors)

        # Check additional sections in detailed report
        assert "performance_analysis" in report
        assert "error_analysis" in report
        assert "resource_usage" in report

        resource_usage = report["resource_usage"]
        assert resource_usage["memory_mb"] == 250.5
        assert resource_usage["cpu_percent"] == 45.2

    def test_generate_export_report_json(self):
        """Test JSON export report."""
        metrics = ProcessingMetrics()
        metrics.total_records = 100
        metrics.processed_records = 100

        errors = ErrorSummary()

        json_report = ReportGenerator.generate_export_report(metrics, errors, "json")

        # Should be valid JSON
        import json

        parsed = json.loads(json_report)
        assert "summary" in parsed

    def test_generate_export_report_text(self):
        """Test text export report."""
        metrics = ProcessingMetrics()
        metrics.total_records = 200
        metrics.processed_records = 150
        metrics.failed_records = 10

        errors = ErrorSummary()
        errors.add_error("test_error", {})

        text_report = ReportGenerator.generate_export_report(metrics, errors, "text")

        # Should contain expected sections
        assert "BACKFILL PROCESSING REPORT" in text_report
        assert "SUMMARY" in text_report
        assert "ERRORS" in text_report
        assert "RECOMMENDATIONS" in text_report


class TestAlertManager:
    """Test AlertManager class."""

    def test_initialization(self):
        """Test alert manager initialization."""
        manager = AlertManager()
        assert manager.alert_thresholds["error_rate"] == 0.1
        assert manager.alert_thresholds["memory_usage_mb"] == 1000
        assert len(manager.alerts_triggered) == 0

    def test_check_metrics_no_alerts(self):
        """Test metrics check with no alerts."""
        manager = AlertManager()

        metrics = ProcessingMetrics()
        metrics.processed_records = 100
        metrics.records_per_second = 50
        metrics.memory_usage_mb = 500

        errors = ErrorSummary()
        errors.total_errors = 5  # 5% error rate

        alerts = manager.check_metrics(metrics, errors)
        assert len(alerts) == 0

    def test_check_metrics_high_error_rate(self):
        """Test alert for high error rate."""
        manager = AlertManager()

        metrics = ProcessingMetrics()
        metrics.processed_records = 100

        errors = ErrorSummary()
        errors.total_errors = 20  # 20% error rate (above 10% threshold)

        alerts = manager.check_metrics(metrics, errors)
        assert len(alerts) == 1
        assert alerts[0]["type"] == "high_error_rate"

    def test_check_metrics_high_memory_usage(self):
        """Test alert for high memory usage."""
        manager = AlertManager()

        metrics = ProcessingMetrics()
        metrics.processed_records = 100
        metrics.memory_usage_mb = 1500  # Above 1000MB threshold

        errors = ErrorSummary()

        alerts = manager.check_metrics(metrics, errors)
        assert len(alerts) == 1
        assert alerts[0]["type"] == "high_memory_usage"

    def test_check_metrics_low_throughput(self):
        """Test alert for low throughput."""
        manager = AlertManager()

        metrics = ProcessingMetrics()
        metrics.processed_records = 200  # Enough records to trigger
        metrics.records_per_second = 5  # Below 10 records/sec threshold

        errors = ErrorSummary()

        alerts = manager.check_metrics(metrics, errors)
        assert len(alerts) == 1
        assert alerts[0]["type"] == "low_throughput"

    def test_get_alert_summary(self):
        """Test alert summary generation."""
        manager = AlertManager()

        # Trigger some alerts
        metrics = ProcessingMetrics()
        metrics.processed_records = 100
        metrics.memory_usage_mb = 1200

        errors = ErrorSummary()
        errors.total_errors = 15

        manager.check_metrics(metrics, errors)

        summary = manager.get_alert_summary()
        assert summary["total_alerts"] > 0
        assert "alert_counts" in summary
        assert "recent_alerts" in summary
