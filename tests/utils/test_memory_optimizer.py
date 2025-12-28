"""
Tests for Memory Optimizer module.
"""

from typing import List, Dict, Generator

from src.utils.parallel_processor import MemoryOptimizer


def generate_test_data(
    num_batches: int, batch_size: int
) -> Generator[List[Dict], None, None]:
    """Generate test data."""
    for i in range(num_batches):
        batch = []
        for j in range(batch_size):
            batch.append(
                {
                    "id": i * batch_size + j,
                    "data": "x" * 100,  # 100 bytes per record
                }
            )
        yield batch


class TestMemoryOptimizer:
    """Test MemoryOptimizer class."""

    def test_stream_large_dataset_within_memory(self):
        """Test streaming large dataset within memory limits."""
        # Generate test data
        data_generator = generate_test_data(10, 100)  # 10 batches of 100 records

        # Stream with memory limit
        optimized_generator = MemoryOptimizer.stream_large_dataset(
            data_generator,
            max_memory_mb=10,  # 10MB limit
        )

        # Collect results
        batches = list(optimized_generator)

        # Verify we got all data
        total_records = sum(len(batch) for batch in batches)
        assert total_records == 10 * 100  # All records should be present

    def test_stream_large_dataset_exceeds_memory(self):
        """Test streaming when data exceeds memory limits."""
        # Generate large test data
        data_generator = generate_test_data(100, 1000)  # 100 batches of 1000 records

        # Stream with very small memory limit
        optimized_generator = MemoryOptimizer.stream_large_dataset(
            data_generator,
            max_memory_mb=1,  # 1MB limit (very small)
        )

        # Collect results
        batches = list(optimized_generator)

        # Verify we got multiple batches (due to memory constraints)
        assert len(batches) > 1

        # Verify all records are present
        total_records = sum(len(batch) for batch in batches)
        assert total_records == 100 * 1000

    def test_stream_empty_dataset(self):
        """Test streaming empty dataset."""

        def empty_generator():
            yield from []

        optimized_generator = MemoryOptimizer.stream_large_dataset(
            empty_generator(), max_memory_mb=100
        )

        batches = list(optimized_generator)
        assert len(batches) == 0

    def test_optimize_batch_size(self):
        """Test batch size optimization."""
        # Test with low memory usage
        optimized_size = MemoryOptimizer.optimize_batch_size(
            initial_batch_size=1000, memory_usage_mb=10, max_memory_mb=100
        )

        # Should increase batch size since we have plenty of memory
        # Formula: optimal = max_memory / (memory_usage / initial)
        # = 100 / (10 / 1000) = 100 / 0.01 = 10000 (capped at 10000)
        assert optimized_size == 10000

        # Test with high memory usage
        optimized_size = MemoryOptimizer.optimize_batch_size(
            initial_batch_size=1000, memory_usage_mb=90, max_memory_mb=100
        )

        # Formula: optimal = 100 / (90 / 1000) = 100 / 0.09 ≈ 1111
        assert optimized_size == 1111

        # Test with very high memory usage (exceeds limit)
        optimized_size = MemoryOptimizer.optimize_batch_size(
            initial_batch_size=1000, memory_usage_mb=200, max_memory_mb=100
        )

        # Should decrease batch size significantly
        # Formula: optimal = 100 / (200 / 1000) = 100 / 0.2 = 500
        assert optimized_size == 500

        # Test with zero memory usage
        optimized_size = MemoryOptimizer.optimize_batch_size(
            initial_batch_size=1000, memory_usage_mb=0, max_memory_mb=100
        )

        # Should return initial batch size
        assert optimized_size == 1000

    def test_optimize_batch_size_bounds(self):
        """Test batch size optimization bounds."""
        # Test minimum bound
        optimized_size = MemoryOptimizer.optimize_batch_size(
            initial_batch_size=1000,
            memory_usage_mb=1000,  # Very high memory usage
            max_memory_mb=100,
        )

        assert optimized_size >= 100  # Minimum bound

        # Test maximum bound
        optimized_size = MemoryOptimizer.optimize_batch_size(
            initial_batch_size=1000,
            memory_usage_mb=0.1,  # Very low memory usage
            max_memory_mb=100,
        )

        assert optimized_size <= 10000  # Maximum bound

    def test_stream_with_varying_batch_sizes(self):
        """Test streaming with varying batch sizes."""

        def varying_generator():
            # Yield batches of different sizes
            yield [{"id": i, "data": "x" * 100} for i in range(500)]  # 500 records
            yield [{"id": i, "data": "x" * 100} for i in range(1000)]  # 1000 records
            yield [{"id": i, "data": "x" * 100} for i in range(200)]  # 200 records
            yield [{"id": i, "data": "x" * 100} for i in range(1500)]  # 1500 records

        optimized_generator = MemoryOptimizer.stream_large_dataset(
            varying_generator(),
            max_memory_mb=5,  # 5MB limit
        )

        batches = list(optimized_generator)
        total_records = sum(len(batch) for batch in batches)
        assert total_records == 500 + 1000 + 200 + 1500

    def test_memory_estimation_accuracy(self):
        """Test memory estimation accuracy."""
        # Create a batch with known memory usage
        batch = []
        for i in range(1000):
            batch.append(
                {
                    "id": i,
                    "name": "Test Name " * 10,  # ~100 bytes
                    "description": "Test Description " * 20,  # ~300 bytes
                    "data": "x" * 600,  # 600 bytes
                }
            )
        # Total: ~1000 * 1000 bytes = ~1MB

        # Stream with memory limit just above estimated usage
        def single_batch_generator():
            yield batch

        optimized_generator = MemoryOptimizer.stream_large_dataset(
            single_batch_generator(),
            max_memory_mb=2,  # 2MB limit (above estimated 1MB)
        )

        batches = list(optimized_generator)
        # Should yield the batch as-is since it fits in memory
        assert len(batches) == 1
        assert len(batches[0]) == 1000
