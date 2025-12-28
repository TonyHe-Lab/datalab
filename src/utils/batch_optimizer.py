"""
Batch Insert Optimizer for PostgreSQL.

This module provides optimization techniques for batch database inserts,
including bulk operations, transaction management, and performance tuning.
"""

import logging
import time
from typing import List, Dict, Any
from dataclasses import dataclass
import statistics

logger = logging.getLogger(__name__)


@dataclass
class BatchOptimizerConfig:
    """Configuration for batch optimizer."""

    optimal_batch_size: int = 1000
    max_batch_size: int = 5000
    min_batch_size: int = 100
    transaction_size: int = 10000  # Commit after this many records
    enable_performance_logging: bool = True
    adaptive_batch_sizing: bool = True
    performance_sample_size: int = 10  # Number of samples for adaptive sizing


class BatchOptimizer:
    """Optimizer for batch database operations."""

    def __init__(self, config: BatchOptimizerConfig):
        self.config = config
        self.performance_history: List[float] = []  # Records per second
        self.batch_size_history: List[int] = []
        self.last_optimization_time = time.time()

    def optimize_batch_size(
        self, current_batch_size: int, performance_metrics: Dict[str, Any]
    ) -> int:
        """
        Optimize batch size based on performance metrics.

        Args:
            current_batch_size: Current batch size
            performance_metrics: Dictionary with performance metrics

        Returns:
            Optimized batch size
        """
        if not self.config.adaptive_batch_sizing:
            return current_batch_size

        # Extract performance metrics
        records_per_second = performance_metrics.get("records_per_second", 0)
        memory_usage_mb = performance_metrics.get("memory_usage_mb", 0)
        error_rate = performance_metrics.get("error_rate", 0)

        # Add to history
        self.performance_history.append(records_per_second)
        self.batch_size_history.append(current_batch_size)

        # Keep history within limits
        if len(self.performance_history) > self.config.performance_sample_size:
            self.performance_history.pop(0)
            self.batch_size_history.pop(0)

        # Only optimize if we have enough samples
        if len(self.performance_history) < 3:
            return current_batch_size

        # Calculate optimization
        new_batch_size = self._calculate_optimal_batch_size(
            current_batch_size, records_per_second, memory_usage_mb, error_rate
        )

        # Apply bounds
        new_batch_size = max(
            self.config.min_batch_size, min(new_batch_size, self.config.max_batch_size)
        )

        # Only log if batch size changed significantly
        if (
            abs(new_batch_size - current_batch_size) > current_batch_size * 0.1
        ):  # 10% change
            logger.info(
                f"Batch size optimized: {current_batch_size} -> {new_batch_size} "
                f"(performance: {records_per_second:.1f} rec/s, "
                f"memory: {memory_usage_mb:.1f}MB, error: {error_rate:.2%})"
            )

        return new_batch_size

    def _calculate_optimal_batch_size(
        self,
        current_batch_size: int,
        records_per_second: float,
        memory_usage_mb: float,
        error_rate: float,
    ) -> int:
        """Calculate optimal batch size based on metrics."""
        # Base optimization on performance trend
        if len(self.performance_history) >= 2:
            # Check if performance is improving
            recent_avg = statistics.mean(self.performance_history[-2:])
            older_avg = statistics.mean(self.performance_history[:-2])

            if recent_avg > older_avg * 1.1:  # 10% improvement
                # Increase batch size gradually
                return int(current_batch_size * 1.1)
            elif recent_avg < older_avg * 0.9:  # 10% degradation
                # Decrease batch size
                return int(current_batch_size * 0.9)

        # Adjust based on memory usage
        if memory_usage_mb > 0:
            # If memory usage is high, reduce batch size
            memory_ratio = memory_usage_mb / 100  # Assuming 100MB as reference
            if memory_ratio > 0.8:  # 80% memory usage
                return int(current_batch_size * 0.8)
            elif memory_ratio < 0.3:  # Low memory usage
                return int(current_batch_size * 1.2)

        # Adjust based on error rate
        if error_rate > 0.05:  # 5% error rate
            return int(current_batch_size * 0.9)

        # Default: small increase if performance is stable
        return int(current_batch_size * 1.05)

    def should_commit_transaction(
        self, total_records: int, last_commit_records: int
    ) -> bool:
        """
        Determine if we should commit the current transaction.

        Args:
            total_records: Total records processed in current transaction
            last_commit_records: Records processed since last commit

        Returns:
            True if we should commit
        """
        # Commit based on transaction size
        if last_commit_records >= self.config.transaction_size:
            return True

        # Commit if we've processed a significant number of records
        if (
            total_records > 0
            and last_commit_records >= self.config.optimal_batch_size * 10
        ):
            return True

        return False

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        if not self.performance_history:
            return {
                "samples": 0,
                "avg_performance": 0,
                "recommended_batch_size": self.config.optimal_batch_size,
            }

        return {
            "samples": len(self.performance_history),
            "avg_performance": statistics.mean(self.performance_history),
            "median_performance": statistics.median(self.performance_history),
            "std_performance": (
                statistics.stdev(self.performance_history)
                if len(self.performance_history) > 1
                else 0
            ),
            "current_batch_size": (
                self.batch_size_history[-1]
                if self.batch_size_history
                else self.config.optimal_batch_size
            ),
            "recommended_batch_size": self.optimize_batch_size(
                (
                    self.batch_size_history[-1]
                    if self.batch_size_history
                    else self.config.optimal_batch_size
                ),
                {
                    "records_per_second": (
                        statistics.mean(self.performance_history)
                        if self.performance_history
                        else 0
                    )
                },
            ),
        }


class BulkInsertStrategy:
    """Strategies for bulk database inserts."""

    @staticmethod
    def prepare_bulk_insert_query(table_name: str, columns: List[str]) -> str:
        """
        Prepare a bulk INSERT query.

        Args:
            table_name: Name of the table
            columns: List of column names

        Returns:
            SQL query string
        """
        placeholders = ", ".join(["%s"] * len(columns))
        columns_str = ", ".join(columns)

        return f"""
        INSERT INTO {table_name} ({columns_str})
        VALUES ({placeholders})
        ON CONFLICT DO NOTHING
        """

    @staticmethod
    def prepare_bulk_upsert_query(
        table_name: str, columns: List[str], conflict_column: str
    ) -> str:
        """
        Prepare a bulk UPSERT query.

        Args:
            table_name: Name of the table
            columns: List of column names
            conflict_column: Column for conflict resolution

        Returns:
            SQL query string
        """
        columns_str = ", ".join(columns)
        update_columns = ", ".join(
            [f"{col} = EXCLUDED.{col}" for col in columns if col != conflict_column]
        )

        return f"""
        INSERT INTO {table_name} ({columns_str})
        VALUES %s
        ON CONFLICT ({conflict_column}) 
        DO UPDATE SET {update_columns}
        """

    @staticmethod
    def chunk_records(records: List[Dict], chunk_size: int) -> List[List[Dict]]:
        """
        Split records into chunks.

        Args:
            records: List of records
            chunk_size: Size of each chunk

        Returns:
            List of record chunks
        """
        return [records[i : i + chunk_size] for i in range(0, len(records), chunk_size)]

    @staticmethod
    def extract_column_values(records: List[Dict], columns: List[str]) -> List[tuple]:
        """
        Extract column values from records.

        Args:
            records: List of record dictionaries
            columns: List of column names to extract

        Returns:
            List of tuples with column values
        """
        values = []
        for record in records:
            row_values = []
            for col in columns:
                row_values.append(record.get(col))
            values.append(tuple(row_values))
        return values


class TransactionManager:
    """Manage database transactions for batch operations."""

    def __init__(self, connection, autocommit: bool = False):
        self.connection = connection
        self.autocommit = autocommit
        self.transaction_count = 0
        self.records_in_transaction = 0
        self.start_time = time.time()

    def begin_transaction(self):
        """Begin a new transaction."""
        if not self.autocommit:
            self.connection.autocommit = False
        self.transaction_count += 1
        self.records_in_transaction = 0
        self.start_time = time.time()

    def commit_transaction(self):
        """Commit the current transaction."""
        if not self.autocommit:
            self.connection.commit()

        elapsed = time.time() - self.start_time
        logger.debug(
            f"Transaction {self.transaction_count} committed: "
            f"{self.records_in_transaction} records in {elapsed:.2f}s "
            f"({self.records_in_transaction / elapsed:.1f} rec/s)"
        )

        self.records_in_transaction = 0

    def rollback_transaction(self):
        """Rollback the current transaction."""
        if not self.autocommit:
            self.connection.rollback()
        logger.warning(f"Transaction {self.transaction_count} rolled back")

    def add_records(self, count: int):
        """Add records to current transaction."""
        self.records_in_transaction += count

    def should_commit(self, optimizer: BatchOptimizer) -> bool:
        """Check if we should commit based on optimizer recommendations."""
        return optimizer.should_commit_transaction(
            self.transaction_count * 10000
            + self.records_in_transaction,  # Estimate total
            self.records_in_transaction,
        )


def create_batch_optimizer(
    optimal_batch_size: int = 1000, adaptive_sizing: bool = True
) -> BatchOptimizer:
    """
    Create a batch optimizer with default configuration.

    Args:
        optimal_batch_size: Initial optimal batch size
        adaptive_sizing: Whether to use adaptive batch sizing

    Returns:
        BatchOptimizer instance
    """
    config = BatchOptimizerConfig(
        optimal_batch_size=optimal_batch_size, adaptive_batch_sizing=adaptive_sizing
    )
    return BatchOptimizer(config)
