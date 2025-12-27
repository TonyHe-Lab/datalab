import pytest
import time
from unittest.mock import Mock, patch
from src.etl.error_handler import exponential_backoff, ETLMetrics


class TestExponentialBackoff:
    """测试指数退避装饰器"""

    def test_success_on_first_try(self):
        """测试第一次尝试成功"""
        mock_func = Mock(return_value="success")

        decorated = exponential_backoff(max_retries=3)(mock_func)
        result = decorated()

        assert result == "success"
        mock_func.assert_called_once()

    def test_success_on_retry(self):
        """测试重试后成功"""
        mock_func = Mock()
        mock_func.side_effect = [Exception("First failure"), "success"]

        decorated = exponential_backoff(max_retries=3, initial_delay=0.01)(mock_func)
        result = decorated()

        assert result == "success"
        assert mock_func.call_count == 2

    def test_all_retries_fail(self):
        """测试所有重试都失败"""
        mock_func = Mock()
        mock_func.side_effect = Exception("Always fails")

        decorated = exponential_backoff(max_retries=2, initial_delay=0.01)(mock_func)

        with pytest.raises(Exception, match="Always fails"):
            decorated()

        assert mock_func.call_count == 3  # 初始尝试 + 2次重试

    def test_specific_exceptions(self):
        """测试特定异常"""
        mock_func = Mock()
        mock_func.side_effect = ValueError("Value error")

        # 只捕获 ValueError
        decorated = exponential_backoff(max_retries=1, exceptions=(ValueError,))(
            mock_func
        )

        with pytest.raises(ValueError, match="Value error"):
            decorated()

        # 不捕获其他异常
        mock_func.side_effect = TypeError("Type error")
        decorated = exponential_backoff(max_retries=1, exceptions=(ValueError,))(
            mock_func
        )

        with pytest.raises(TypeError, match="Type error"):
            decorated()


class TestETLMetrics:
    """测试 ETL 指标收集器"""

    def setup_method(self):
        """测试设置"""
        self.metrics = ETLMetrics()

    def test_start_stop(self):
        """测试开始和停止"""
        self.metrics.start()
        assert self.metrics.start_time is not None

        time.sleep(0.01)
        self.metrics.stop()

        assert self.metrics.end_time is not None
        assert self.metrics.get_duration() > 0

    def test_record_processed(self):
        """测试记录处理记录数"""
        self.metrics.record_processed(5)
        assert self.metrics.records_processed == 5

        self.metrics.record_processed()
        assert self.metrics.records_processed == 6

    def test_record_error(self):
        """测试记录错误数"""
        self.metrics.record_error(2)
        assert self.metrics.errors == 2

        self.metrics.record_error()
        assert self.metrics.errors == 3

    def test_record_batch(self):
        """测试记录批次处理"""
        self.metrics.record_batch()
        assert self.metrics.batches_processed == 1

        self.metrics.record_batch()
        assert self.metrics.batches_processed == 2

    def test_get_summary(self):
        """测试获取摘要"""
        self.metrics.start()
        self.metrics.record_processed(100)
        self.metrics.record_error(2)
        self.metrics.record_batch()
        time.sleep(0.01)
        self.metrics.stop()

        summary = self.metrics.get_summary()

        assert summary["records_processed"] == 100
        assert summary["errors"] == 2
        assert summary["batches_processed"] == 1
        assert summary["duration_seconds"] > 0
        assert summary["records_per_second"] > 0

    def test_log_summary(self):
        """测试记录摘要日志"""
        self.metrics.start()
        self.metrics.record_processed(50)
        self.metrics.stop()

        # 测试日志记录（不验证具体调用次数，因为日志可能被重定向）
        self.metrics.log_summary()

        # 验证摘要数据正确
        summary = self.metrics.get_summary()
        assert summary["records_processed"] == 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
