"""
Monitoring and Reporting Module for Historical Data Backfill.

This module provides real-time monitoring, progress tracking, and reporting
capabilities for the backfill tool.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
import json
import threading
from enum import Enum

logger = logging.getLogger(__name__)


class ReportLevel(Enum):
    """Report detail levels."""

    SUMMARY = "summary"
    DETAILED = "detailed"
    DEBUG = "debug"


@dataclass
class ProcessingMetrics:
    """Metrics for processing performance."""

    total_records: int = 0
    processed_records: int = 0
    failed_records: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    records_per_second: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    batch_size: int = 1000
    success_rate: float = 0.0

    def update_success_rate(self):
        """Update success rate based on current metrics."""
        if self.processed_records > 0:
            self.success_rate = (
                self.processed_records - self.failed_records
            ) / self.processed_records
        else:
            self.success_rate = 0.0

    def update_records_per_second(self):
        """Update records per second based on elapsed time."""
        if self.start_time and self.processed_records > 0:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            if elapsed > 0:
                self.records_per_second = self.processed_records / elapsed

    def get_elapsed_time(self) -> Optional[timedelta]:
        """Get elapsed time since start."""
        if self.start_time:
            return datetime.now() - self.start_time
        return None

    def get_estimated_time_remaining(self, total_records: int) -> Optional[timedelta]:
        """Get estimated time remaining."""
        if self.records_per_second > 0 and total_records > self.processed_records:
            seconds_remaining = (
                total_records - self.processed_records
            ) / self.records_per_second
            return timedelta(seconds=seconds_remaining)
        return None


@dataclass
class ErrorSummary:
    """Summary of errors encountered."""

    total_errors: int = 0
    error_types: Dict[str, int] = None  # type: ignore # error_type -> count
    recent_errors: List[Dict[str, Any]] = None  # type: ignore # Last N errors

    def __post_init__(self):
        if self.error_types is None:
            self.error_types = {}
        if self.recent_errors is None:
            self.recent_errors = []

    def add_error(
        self, error_type: str, error_details: Dict[str, Any], max_recent: int = 10
    ):
        """Add an error to the summary."""
        self.total_errors += 1
        self.error_types[error_type] = self.error_types.get(error_type, 0) + 1

        # Add to recent errors
        error_record = {
            "timestamp": datetime.now().isoformat(),
            "type": error_type,
            "details": error_details,
        }
        self.recent_errors.append(error_record)

        # Keep only recent errors
        if len(self.recent_errors) > max_recent:
            self.recent_errors = self.recent_errors[-max_recent:]

    def get_top_errors(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top error types."""
        sorted_errors = sorted(
            self.error_types.items(), key=lambda x: x[1], reverse=True
        )
        return [
            {"type": err_type, "count": count}
            for err_type, count in sorted_errors[:limit]
        ]


class ProgressReporter:
    """Real-time progress reporter."""

    def __init__(self, report_interval_seconds: int = 10):
        self.report_interval = report_interval_seconds
        self.metrics = ProcessingMetrics()
        self.error_summary = ErrorSummary()
        self.last_report_time = time.time()
        self.callbacks: List[Callable[[Dict[str, Any]], None]] = []

    def start(self, total_records: int):
        """Start monitoring."""
        self.metrics.start_time = datetime.now()
        self.metrics.total_records = total_records
        logger.info(f"Progress monitoring started for {total_records} records")

    def update_processed(self, count: int = 1):
        """Update processed records count."""
        self.metrics.processed_records += count
        self._check_report()

    def update_failed(
        self,
        count: int = 1,
        error_type: str = "unknown",
        error_details: Optional[Dict[str, Any]] = None,
    ):
        """Update failed records count."""
        self.metrics.failed_records += count
        self.error_summary.add_error(error_type, error_details or {"count": count})
        self._check_report()

    def update_performance(
        self, memory_usage_mb: float = 0.0, cpu_usage_percent: float = 0.0
    ):
        """Update performance metrics."""
        self.metrics.memory_usage_mb = memory_usage_mb
        self.metrics.cpu_usage_percent = cpu_usage_percent
        self._check_report()

    def _check_report(self):
        """Check if it's time to generate a report."""
        current_time = time.time()
        if current_time - self.last_report_time >= self.report_interval:
            self.generate_report()
            self.last_report_time = current_time

    def generate_report(
        self, level: ReportLevel = ReportLevel.SUMMARY
    ) -> Dict[str, Any]:
        """Generate a progress report."""
        # Update calculated metrics
        self.metrics.update_success_rate()
        self.metrics.update_records_per_second()

        # Build report
        report = {
            "timestamp": datetime.now().isoformat(),
            "metrics": asdict(self.metrics),
            "progress_percentage": self._calculate_progress_percentage(),
            "estimated_time_remaining": self._format_estimated_time(),
            "errors": self._get_error_summary(level),
        }

        # Add detailed info if needed
        if level == ReportLevel.DETAILED:
            report["detailed_metrics"] = self._get_detailed_metrics()
        elif level == ReportLevel.DEBUG:
            report["debug_info"] = self._get_debug_info()

        # Notify callbacks
        for callback in self.callbacks:
            try:
                callback(report)
            except Exception as e:
                logger.warning(f"Callback failed: {e}")

        return report

    def _calculate_progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.metrics.total_records > 0:
            return (self.metrics.processed_records / self.metrics.total_records) * 100
        return 0.0

    def _format_estimated_time(self) -> Optional[str]:
        """Format estimated time remaining."""
        eta = self.metrics.get_estimated_time_remaining(self.metrics.total_records)
        if eta:
            # Format as HH:MM:SS
            total_seconds = int(eta.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return None

    def _get_error_summary(self, level: ReportLevel) -> Dict[str, Any]:
        """Get error summary based on report level."""
        summary = {
            "total": self.error_summary.total_errors,
            "top_types": self.error_summary.get_top_errors(3),
        }

        if level in [ReportLevel.DETAILED, ReportLevel.DEBUG]:
            summary["recent_errors"] = self.error_summary.recent_errors

        return summary

    def _get_detailed_metrics(self) -> Dict[str, Any]:
        """Get detailed metrics."""
        elapsed = self.metrics.get_elapsed_time()
        return {
            "elapsed_time": str(elapsed) if elapsed else None,
            "batch_efficiency": self._calculate_batch_efficiency(),
            "memory_trend": self._get_memory_trend(),
            "performance_trend": self._get_performance_trend(),
        }

    def _get_debug_info(self) -> Dict[str, Any]:
        """Get debug information."""
        return {
            "thread_count": threading.active_count(),
            "callbacks_registered": len(self.callbacks),
            "report_interval": self.report_interval,
            "last_report_timestamp": self.last_report_time,
        }

    def _calculate_batch_efficiency(self) -> float:
        """Calculate batch processing efficiency."""
        if self.metrics.batch_size > 0 and self.metrics.records_per_second > 0:
            # Simple efficiency metric: records per second per batch size unit
            return self.metrics.records_per_second / self.metrics.batch_size
        return 0.0

    def _get_memory_trend(self) -> str:
        """Get memory usage trend."""
        # This would normally track historical memory usage
        # For now, return a simple indicator
        if self.metrics.memory_usage_mb > 1000:  # 1GB
            return "high"
        elif self.metrics.memory_usage_mb > 500:  # 500MB
            return "medium"
        else:
            return "low"

    def _get_performance_trend(self) -> str:
        """Get performance trend."""
        # This would normally track historical performance
        # For now, return a simple indicator
        if self.metrics.records_per_second > 1000:
            return "excellent"
        elif self.metrics.records_per_second > 100:
            return "good"
        elif self.metrics.records_per_second > 10:
            return "fair"
        else:
            return "poor"

    def register_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Register a callback for report notifications."""
        self.callbacks.append(callback)

    def complete(self):
        """Mark monitoring as complete."""
        self.metrics.end_time = datetime.now()
        self.metrics.update_success_rate()
        self.metrics.update_records_per_second()

        final_report = self.generate_report(ReportLevel.DETAILED)
        logger.info("Progress monitoring completed")
        return final_report

    def fail(self, error_message: str):
        """Mark monitoring as failed."""
        self.metrics.end_time = datetime.now()
        self.error_summary.add_error("monitoring_failure", {"message": error_message})

        failure_report = self.generate_report(ReportLevel.DETAILED)
        failure_report["status"] = "failed"
        failure_report["error_message"] = error_message

        logger.error(f"Progress monitoring failed: {error_message}")
        return failure_report


class ReportGenerator:
    """Generate various types of reports."""

    @staticmethod
    def generate_summary_report(
        metrics: ProcessingMetrics, errors: ErrorSummary
    ) -> Dict[str, Any]:
        """Generate a summary report."""
        return {
            "summary": {
                "total_records": metrics.total_records,
                "processed": metrics.processed_records,
                "failed": metrics.failed_records,
                "success_rate": f"{metrics.success_rate:.2%}",
                "duration": (
                    str(metrics.get_elapsed_time()) if metrics.start_time else None
                ),
                "performance": f"{metrics.records_per_second:.1f} records/sec",
            },
            "errors": {
                "total": errors.total_errors,
                "top_types": errors.get_top_errors(5),
            },
            "recommendations": ReportGenerator._generate_recommendations(
                metrics, errors
            ),
        }

    @staticmethod
    def generate_detailed_report(
        metrics: ProcessingMetrics, errors: ErrorSummary
    ) -> Dict[str, Any]:
        """Generate a detailed report."""
        summary = ReportGenerator.generate_summary_report(metrics, errors)

        # Add detailed sections
        summary["performance_analysis"] = ReportGenerator._analyze_performance(metrics)
        summary["error_analysis"] = ReportGenerator._analyze_errors(errors)
        summary["resource_usage"] = {
            "memory_mb": metrics.memory_usage_mb,
            "cpu_percent": metrics.cpu_usage_percent,
            "batch_size": metrics.batch_size,
        }

        return summary

    @staticmethod
    def generate_export_report(
        metrics: ProcessingMetrics, errors: ErrorSummary, format: str = "json"
    ) -> str:
        """Generate a report for export."""
        report = ReportGenerator.generate_detailed_report(metrics, errors)

        if format == "json":
            return json.dumps(report, indent=2, default=str)
        elif format == "text":
            return ReportGenerator._format_text_report(report)
        else:
            raise ValueError(f"Unsupported format: {format}")

    @staticmethod
    def _generate_recommendations(
        metrics: ProcessingMetrics, errors: ErrorSummary
    ) -> List[str]:
        """Generate recommendations based on metrics and errors."""
        recommendations = []

        # Performance recommendations
        if metrics.records_per_second < 10:
            recommendations.append(
                "Consider increasing batch size for better performance"
            )
        elif metrics.records_per_second > 1000:
            recommendations.append(
                "Performance is excellent, consider processing larger datasets"
            )

        # Error recommendations
        if errors.total_errors > metrics.processed_records * 0.1:  # 10% error rate
            recommendations.append(
                "High error rate detected, review error logs and retry failed records"
            )

        if "connection_error" in errors.error_types:
            recommendations.append(
                "Connection errors detected, check database connectivity and credentials"
            )

        # Resource recommendations
        if metrics.memory_usage_mb > 1000:  # 1GB
            recommendations.append(
                "High memory usage, consider reducing batch size or optimizing memory usage"
            )

        if metrics.cpu_usage_percent > 80:
            recommendations.append("High CPU usage, consider reducing parallel workers")

        return recommendations

    @staticmethod
    def _analyze_performance(metrics: ProcessingMetrics) -> Dict[str, Any]:
        """Analyze performance metrics."""
        analysis = {
            "throughput": f"{metrics.records_per_second:.1f} records/sec",
            "efficiency": (
                "high"
                if metrics.records_per_second > 100
                else "medium" if metrics.records_per_second > 10 else "low"
            ),
            "bottleneck_analysis": ReportGenerator._identify_bottlenecks(metrics),
        }

        if metrics.start_time and metrics.end_time:
            total_time = (metrics.end_time - metrics.start_time).total_seconds()
            analysis["total_time_seconds"] = total_time
            analysis["average_throughput"] = (
                metrics.processed_records / total_time if total_time > 0 else 0
            )

        return analysis

    @staticmethod
    def _analyze_errors(errors: ErrorSummary) -> Dict[str, Any]:
        """Analyze error patterns."""
        return {
            "total_errors": errors.total_errors,
            "error_distribution": errors.error_types,
            "common_patterns": ReportGenerator._identify_error_patterns(errors),
            "suggested_fixes": ReportGenerator._suggest_error_fixes(errors),
        }

    @staticmethod
    def _identify_bottlenecks(metrics: ProcessingMetrics) -> List[str]:
        """Identify potential bottlenecks."""
        bottlenecks = []

        if metrics.records_per_second < 10:
            bottlenecks.append(
                "Low throughput - possible network or database bottleneck"
            )

        if metrics.memory_usage_mb > 1000 and metrics.records_per_second < 100:
            bottlenecks.append(
                "High memory usage with low throughput - possible memory bottleneck"
            )

        return bottlenecks

    @staticmethod
    def _identify_error_patterns(errors: ErrorSummary) -> List[Dict[str, Any]]:
        """Identify patterns in errors."""
        patterns = []

        # Look for temporal patterns
        if errors.recent_errors:
            recent_count = len(
                [
                    e
                    for e in errors.recent_errors
                    if datetime.fromisoformat(e["timestamp"])
                    > datetime.now() - timedelta(minutes=5)
                ]
            )
            if recent_count > 10:
                patterns.append(
                    {
                        "type": "temporal_cluster",
                        "description": f"{recent_count} errors in last 5 minutes",
                        "suggestion": "Check for recent system issues or rate limiting",
                    }
                )

        # Look for specific error type patterns
        for error_type, count in errors.error_types.items():
            if count > 100:
                patterns.append(
                    {
                        "type": "high_frequency",
                        "error_type": error_type,
                        "count": count,
                        "suggestion": f"Investigate root cause of {error_type} errors",
                    }
                )

        return patterns

    @staticmethod
    def _suggest_error_fixes(errors: ErrorSummary) -> List[str]:
        """Suggest fixes for common errors."""
        fixes = []

        error_mapping = {
            "connection_error": "Check database connection settings and network connectivity",
            "timeout_error": "Increase timeout settings or optimize query performance",
            "memory_error": "Reduce batch size or increase available memory",
            "validation_error": "Review data validation rules and input data quality",
            "api_error": "Check API credentials, rate limits, and endpoint availability",
        }

        for error_type in errors.error_types:
            if error_type in error_mapping:
                fixes.append(f"{error_type}: {error_mapping[error_type]}")

        return fixes

    @staticmethod
    def _format_text_report(report: Dict[str, Any]) -> str:
        """Format report as text."""
        lines = []
        lines.append("=" * 60)
        lines.append("BACKFILL PROCESSING REPORT")
        lines.append("=" * 60)
        lines.append("")

        # Summary section
        lines.append("SUMMARY")
        lines.append("-" * 40)
        summary = report["summary"]
        lines.append(f"Total Records: {summary['total_records']}")
        lines.append(f"Processed: {summary['processed']}")
        lines.append(f"Failed: {summary['failed']}")
        lines.append(f"Success Rate: {summary['success_rate']}")
        lines.append(f"Duration: {summary['duration']}")
        lines.append(f"Performance: {summary['performance']}")
        lines.append("")

        # Errors section
        lines.append("ERRORS")
        lines.append("-" * 40)
        errors = report["errors"]
        lines.append(f"Total Errors: {errors['total']}")
        for error in errors.get("top_types", []):
            lines.append(f"  {error['type']}: {error['count']}")
        lines.append("")

        # Recommendations
        lines.append("RECOMMENDATIONS")
        lines.append("-" * 40)
        for rec in report.get("recommendations", []):
            lines.append(f"• {rec}")

        return "\n".join(lines)


class AlertManager:
    """Manage alerts for critical conditions."""

    def __init__(self, alert_thresholds: Optional[Dict[str, Any]] = None):
        self.alert_thresholds = alert_thresholds or {
            "error_rate": 0.1,  # 10%
            "memory_usage_mb": 1000,  # 1GB
            "low_throughput": 10,  # records/sec
            "stalled_progress": 300,  # 5 minutes without progress
        }
        self.alerts_triggered = []
        self.last_progress_time = time.time()

    def check_metrics(
        self, metrics: ProcessingMetrics, errors: ErrorSummary
    ) -> List[Dict[str, Any]]:
        """Check metrics against alert thresholds."""
        alerts = []

        # Check error rate
        if metrics.processed_records > 0:
            error_rate = errors.total_errors / metrics.processed_records
            if error_rate > self.alert_thresholds["error_rate"]:
                alerts.append(
                    {
                        "type": "high_error_rate",
                        "severity": "high",
                        "message": f"Error rate {error_rate:.1%} exceeds threshold {self.alert_thresholds['error_rate']:.1%}",
                        "metrics": {
                            "error_rate": error_rate,
                            "threshold": self.alert_thresholds["error_rate"],
                        },
                    }
                )

        # Check memory usage
        if metrics.memory_usage_mb > self.alert_thresholds["memory_usage_mb"]:
            alerts.append(
                {
                    "type": "high_memory_usage",
                    "severity": "medium",
                    "message": f"Memory usage {metrics.memory_usage_mb:.1f}MB exceeds threshold {self.alert_thresholds['memory_usage_mb']}MB",
                    "metrics": {
                        "memory_usage_mb": metrics.memory_usage_mb,
                        "threshold": self.alert_thresholds["memory_usage_mb"],
                    },
                }
            )

        # Check throughput
        if (
            metrics.records_per_second < self.alert_thresholds["low_throughput"]
            and metrics.processed_records > 100
        ):
            alerts.append(
                {
                    "type": "low_throughput",
                    "severity": "medium",
                    "message": f"Throughput {metrics.records_per_second:.1f} records/sec below threshold {self.alert_thresholds['low_throughput']}",
                    "metrics": {
                        "records_per_second": metrics.records_per_second,
                        "threshold": self.alert_thresholds["low_throughput"],
                    },
                }
            )

        # Check for stalled progress
        current_time = time.time()
        if metrics.processed_records > 0:
            time_since_progress = current_time - self.last_progress_time
            if time_since_progress > self.alert_thresholds["stalled_progress"]:
                alerts.append(
                    {
                        "type": "stalled_progress",
                        "severity": "high",
                        "message": f"No progress for {time_since_progress:.0f} seconds",
                        "metrics": {
                            "time_since_progress": time_since_progress,
                            "threshold": self.alert_thresholds["stalled_progress"],
                        },
                    }
                )
            else:
                self.last_progress_time = current_time

        # Record alerts
        self.alerts_triggered.extend(alerts)

        return alerts

    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of all alerts triggered."""
        alert_counts = {}
        for alert in self.alerts_triggered:
            alert_type = alert["type"]
            alert_counts[alert_type] = alert_counts.get(alert_type, 0) + 1

        return {
            "total_alerts": len(self.alerts_triggered),
            "alert_counts": alert_counts,
            "recent_alerts": (
                self.alerts_triggered[-10:] if self.alerts_triggered else []
            ),
        }
