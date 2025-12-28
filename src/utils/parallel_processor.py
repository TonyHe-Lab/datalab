"""
Parallel Processing Module for Historical Data Backfill.

This module provides parallel processing capabilities for handling large datasets
efficiently using multiprocessing and threading.
"""

import logging
import concurrent.futures
import multiprocessing
import threading
import queue
from typing import List, Dict, Any, Callable, Optional, Generator, Tuple
from dataclasses import dataclass
import time

logger = logging.getLogger(__name__)


@dataclass
class ParallelConfig:
    """Configuration for parallel processing."""

    max_workers: int = 4
    use_multiprocessing: bool = True  # Use multiprocessing instead of threading
    chunk_size: int = 1000
    timeout_seconds: int = 300
    max_retries: int = 3
    retry_delay: float = 1.0


class ParallelProcessor:
    """Parallel processor for handling large datasets."""

    def __init__(self, config: ParallelConfig):
        self.config = config
        self.executor = None
        self.results_queue = queue.Queue()
        self.error_queue = queue.Queue()
        self.progress_lock = threading.Lock()
        self.processed_count = 0
        self.error_count = 0

    def __enter__(self):
        """Context manager entry."""
        self._initialize_executor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()

    def _initialize_executor(self):
        """Initialize the executor based on configuration."""
        if self.config.use_multiprocessing:
            # Use ProcessPoolExecutor for CPU-bound tasks
            self.executor = concurrent.futures.ProcessPoolExecutor(
                max_workers=self.config.max_workers
            )
            logger.info(
                f"Initialized ProcessPoolExecutor with {self.config.max_workers} workers"
            )
        else:
            # Use ThreadPoolExecutor for I/O-bound tasks
            self.executor = concurrent.futures.ThreadPoolExecutor(
                max_workers=self.config.max_workers
            )
            logger.info(
                f"Initialized ThreadPoolExecutor with {self.config.max_workers} workers"
            )

    def shutdown(self):
        """Shutdown the executor."""
        if self.executor:
            self.executor.shutdown(wait=True)
            logger.info("Executor shutdown completed")

    def process_batches_parallel(
        self,
        data_source: Generator[List[Dict], None, None],
        process_func: Callable[[List[Dict]], Tuple[int, int]],
        total_records: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Process batches in parallel.

        Args:
            data_source: Generator yielding batches of data
            process_func: Function to process a batch, returns (success_count, error_count)
            total_records: Total number of records (for progress tracking)

        Returns:
            Dictionary with processing statistics
        """
        if not self.executor:
            self._initialize_executor()

        start_time = time.time()
        futures = []
        batch_index = 0

        try:
            # Submit batches to executor
            for batch in data_source:
                if not batch:
                    continue

                future = self.executor.submit(
                    self._process_batch_with_retry, batch, process_func, batch_index
                )
                futures.append(future)
                batch_index += 1

                # Limit number of pending futures to control memory usage
                if len(futures) >= self.config.max_workers * 2:
                    self._collect_results(futures)

            # Collect remaining results
            if futures:
                self._collect_results(futures)

        except Exception as e:
            logger.error(f"Error during parallel processing: {e}")
            raise

        finally:
            # Calculate statistics
            elapsed_time = time.time() - start_time
            records_per_second = (
                self.processed_count / elapsed_time if elapsed_time > 0 else 0
            )

            return {
                "total_batches": batch_index,
                "processed_records": self.processed_count,
                "error_records": self.error_count,
                "elapsed_time": elapsed_time,
                "records_per_second": records_per_second,
                "success_rate": (
                    (self.processed_count - self.error_count) / self.processed_count
                    if self.processed_count > 0
                    else 0
                ),
            }

    def _process_batch_with_retry(
        self,
        batch: List[Dict],
        process_func: Callable[[List[Dict]], Tuple[int, int]],
        batch_index: int,
    ) -> Tuple[int, int, int]:
        """
        Process a batch with retry logic.

        Args:
            batch: Batch of records to process
            process_func: Function to process the batch
            batch_index: Index of the batch

        Returns:
            Tuple of (batch_index, success_count, error_count)
        """
        retry_count = 0

        while retry_count <= self.config.max_retries:
            try:
                success_count, error_count = process_func(batch)

                # Update progress
                with self.progress_lock:
                    self.processed_count += success_count + error_count
                    self.error_count += error_count

                logger.debug(
                    f"Batch {batch_index} processed: {success_count} success, "
                    f"{error_count} errors (retry {retry_count})"
                )

                return batch_index, success_count, error_count

            except Exception as e:
                retry_count += 1

                if retry_count <= self.config.max_retries:
                    logger.warning(
                        f"Batch {batch_index} failed (attempt {retry_count}/{self.config.max_retries}): {e}"
                    )
                    time.sleep(
                        self.config.retry_delay * (2 ** (retry_count - 1))
                    )  # Exponential backoff
                else:
                    logger.error(
                        f"Batch {batch_index} failed after {self.config.max_retries} retries: {e}"
                    )

                    # Mark all records in batch as errors
                    with self.progress_lock:
                        self.processed_count += len(batch)
                        self.error_count += len(batch)

                    return batch_index, 0, len(batch)

        return batch_index, 0, len(batch)  # Should never reach here

    def _collect_results(self, futures: List[concurrent.futures.Future]):
        """Collect results from completed futures."""
        completed, _ = concurrent.futures.wait(
            futures,
            timeout=self.config.timeout_seconds,
            return_when=concurrent.futures.FIRST_COMPLETED,
        )

        for future in completed:
            try:
                batch_index, success_count, error_count = future.result(timeout=10)
                logger.debug(
                    f"Batch {batch_index} completed: {success_count} success, {error_count} errors"
                )
            except concurrent.futures.TimeoutError:
                logger.warning("Future result timeout")
            except Exception as e:
                logger.error(f"Error getting future result: {e}")

        # Remove completed futures
        for future in completed:
            futures.remove(future)


class ConnectionPool:
    """Database connection pool for efficient connection reuse."""

    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self.connections = queue.Queue(maxsize=max_connections)
        self.connection_count = 0
        self.lock = threading.Lock()

    def get_connection(self, create_func: Callable) -> Any:
        """
        Get a connection from the pool or create a new one.

        Args:
            create_func: Function to create a new connection

        Returns:
            Database connection
        """
        try:
            # Try to get connection from pool without blocking
            return self.connections.get_nowait()
        except queue.Empty:
            with self.lock:
                if self.connection_count < self.max_connections:
                    # Create new connection
                    connection = create_func()
                    self.connection_count += 1
                    logger.debug(
                        f"Created new connection, total: {self.connection_count}"
                    )
                    return connection
                else:
                    # Wait for connection to become available
                    logger.debug("Waiting for available connection...")
                    return self.connections.get()

    def return_connection(self, connection: Any):
        """Return connection to pool."""
        try:
            self.connections.put_nowait(connection)
        except queue.Full:
            # Pool is full, close the connection
            self._close_connection(connection)
            with self.lock:
                self.connection_count -= 1

    def _close_connection(self, connection: Any):
        """Close a connection."""
        try:
            if hasattr(connection, "close"):
                connection.close()
        except Exception as e:
            logger.warning(f"Error closing connection: {e}")

    def close_all(self):
        """Close all connections in the pool."""
        while not self.connections.empty():
            try:
                connection = self.connections.get_nowait()
                self._close_connection(connection)
            except queue.Empty:
                break

        with self.lock:
            self.connection_count = 0
        logger.info("All connections closed")


class MemoryOptimizer:
    """Memory optimization utilities for large dataset processing."""

    @staticmethod
    def stream_large_dataset(
        data_source: Generator[List[Dict], None, None], max_memory_mb: int = 100
    ) -> Generator[List[Dict], None, None]:
        """
        Stream large dataset with memory constraints.

        Args:
            data_source: Original data source generator
            max_memory_mb: Maximum memory usage in MB

        Yields:
            Batches of data within memory limits
        """
        current_batch = []
        estimated_memory = 0

        for batch in data_source:
            # Estimate memory usage of batch (rough estimate: 1KB per record)
            batch_memory = len(batch) * 1024 / (1024 * 1024)  # Convert to MB

            if estimated_memory + batch_memory > max_memory_mb and current_batch:
                # Yield current batch if adding new batch would exceed memory limit
                yield current_batch
                current_batch = batch
                estimated_memory = batch_memory
            else:
                # Add to current batch
                current_batch.extend(batch)
                estimated_memory += batch_memory

        # Yield any remaining records
        if current_batch:
            yield current_batch

    @staticmethod
    def optimize_batch_size(
        initial_batch_size: int, memory_usage_mb: float, max_memory_mb: int = 100
    ) -> int:
        """
        Dynamically adjust batch size based on memory usage.

        Args:
            initial_batch_size: Initial batch size
            memory_usage_mb: Current memory usage in MB
            max_memory_mb: Maximum allowed memory usage in MB

        Returns:
            Optimized batch size
        """
        if memory_usage_mb <= 0:
            return initial_batch_size

        # Calculate memory per record
        memory_per_record = memory_usage_mb / initial_batch_size

        # Calculate optimal batch size
        optimal_batch_size = int(max_memory_mb / memory_per_record)

        # Apply bounds
        optimal_batch_size = max(100, min(optimal_batch_size, 10000))

        logger.debug(
            f"Memory optimization: {memory_usage_mb:.2f}MB used, "
            f"{memory_per_record:.4f}MB/record, "
            f"batch size adjusted from {initial_batch_size} to {optimal_batch_size}"
        )

        return optimal_batch_size


def create_parallel_config(
    cpu_count: Optional[int] = None,
    use_multiprocessing: bool = True,
    chunk_size: int = 1000,
) -> ParallelConfig:
    """
    Create parallel configuration based on system resources.

    Args:
        cpu_count: Number of CPU cores to use (default: system CPU count - 1)
        use_multiprocessing: Whether to use multiprocessing
        chunk_size: Size of data chunks

    Returns:
        ParallelConfig instance
    """
    if cpu_count is None:
        cpu_count = multiprocessing.cpu_count()
        # Leave one core for system
        cpu_count = max(1, cpu_count - 1)

    return ParallelConfig(
        max_workers=cpu_count,
        use_multiprocessing=use_multiprocessing,
        chunk_size=chunk_size,
    )
