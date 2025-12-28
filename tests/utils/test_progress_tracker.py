"""
进度跟踪器测试
"""

import pytest
import time
from unittest.mock import Mock
from src.utils.progress_tracker import ProgressTracker, ProgressStats, BatchProcessor


class TestProgressStats:
    """ProgressStats 测试"""

    def test_progress_percentage(self):
        """测试进度百分比计算"""
        stats = ProgressStats(total_records=100, processed_records=50)
        assert stats.progress_percentage == 50.0

        stats = ProgressStats(total_records=0, processed_records=0)
        assert stats.progress_percentage == 0.0

    def test_elapsed_time(self):
        """测试已用时间计算"""
        stats = ProgressStats()
        assert stats.elapsed_time == 0.0

        stats.start_time = time.time() - 10  # 10秒前
        stats.end_time = time.time()
        elapsed = stats.elapsed_time
        assert 9.9 <= elapsed <= 10.1

    def test_records_per_second(self):
        """测试每秒记录数计算"""
        stats = ProgressStats(total_records=100, processed_records=50)
        stats.start_time = time.time() - 10  # 10秒前
        stats.end_time = time.time()

        rps = stats.records_per_second
        assert 4.9 <= rps <= 5.1  # 50条记录 / 10秒 = 5条/秒

    def test_estimated_time_remaining(self):
        """测试剩余时间估计"""
        stats = ProgressStats(total_records=100, processed_records=50)
        stats.start_time = time.time() - 10  # 10秒前
        stats.end_time = time.time()

        remaining = stats.estimated_time_remaining
        assert 9.9 <= remaining <= 10.1  # 剩余50条，速度5条/秒，需要10秒


class TestProgressTracker:
    """ProgressTracker 测试"""

    def test_initialization(self):
        """测试初始化"""
        tracker = ProgressTracker("test_job")
        assert tracker.job_name == "test_job"
        assert tracker.stats.total_records == 0
        assert tracker.stats.processed_records == 0

    def test_start(self):
        """测试开始跟踪"""
        tracker = ProgressTracker("test_job")
        tracker.start(total_records=1000)

        assert tracker.stats.total_records == 1000
        assert tracker.stats.start_time is not None
        assert tracker.stats.processed_records == 0

    def test_update(self):
        """测试更新进度"""
        tracker = ProgressTracker("test_job")
        tracker.start(total_records=1000)

        # 更新进度
        checkpoint_created = tracker.update(processed=100, failed=5)

        assert tracker.stats.processed_records == 100
        assert tracker.stats.failed_records == 5
        assert not checkpoint_created  # 默认不会创建检查点

    def test_update_with_checkpoint(self):
        """测试带检查点的更新"""
        tracker = ProgressTracker("test_job")
        tracker.start(total_records=1000)
        tracker.stats.checkpoint_interval = 100  # 设置较小的检查点间隔

        # 第一次更新，应该创建检查点
        checkpoint_created = tracker.update(processed=100)
        assert checkpoint_created

    def test_complete(self):
        """测试完成"""
        tracker = ProgressTracker("test_job")
        tracker.start(total_records=1000)
        tracker.update(processed=1000)
        tracker.complete()

        assert tracker.stats.end_time is not None
        assert tracker.stats.processed_records == 1000

    def test_get_progress_report(self):
        """测试获取进度报告"""
        tracker = ProgressTracker("test_job")
        tracker.start(total_records=1000)
        tracker.update(processed=500)

        report = tracker.get_progress_report()

        assert report["job_name"] == "test_job"
        assert report["stats"]["total_records"] == 1000
        assert report["stats"]["processed_records"] == 500
        assert report["stats"]["progress_percentage"] == 50.0
        assert "timestamp" in report

    def test_register_callback(self):
        """测试注册回调函数"""
        tracker = ProgressTracker("test_job")
        callback = Mock()

        tracker.register_callback("test_event", callback)
        assert tracker.callbacks["test_event"] == callback


class TestBatchProcessor:
    """BatchProcessor 测试"""

    def test_initialization(self):
        """测试初始化"""
        processor = BatchProcessor(batch_size=500, max_workers=2)

        assert processor.batch_size == 500
        assert processor.max_workers == 2
        assert processor.progress_tracker is not None

    def test_process_batches(self):
        """测试批处理"""

        # 创建模拟数据源
        def mock_data_source():
            for i in range(10):
                yield {"id": i, "data": f"record_{i}"}

        # 创建模拟处理函数
        processed_records = []

        def mock_process_func(batch):
            processed_records.extend(batch)
            return len(batch)

        # 创建处理器
        processor = BatchProcessor(batch_size=3)

        # 处理数据
        processor.process_batches(
            data_source=mock_data_source(),
            process_func=mock_process_func,
            total_records=10,
        )

        # 验证结果
        assert len(processed_records) == 10
        assert processor.progress_tracker.stats.processed_records == 10

    def test_process_batches_with_error(self):
        """测试批处理错误处理"""

        # 创建模拟数据源
        def mock_data_source():
            for i in range(5):
                yield {"id": i}

        # 创建会抛出异常的处理函数
        def mock_process_func(batch):
            if len(batch) > 2:
                raise ValueError("Batch too large")
            return len(batch)

        # 创建处理器
        processor = BatchProcessor(batch_size=5)

        # 处理数据，应该抛出异常
        with pytest.raises(ValueError, match="Batch too large"):
            processor.process_batches(
                data_source=mock_data_source(),
                process_func=mock_process_func,
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
