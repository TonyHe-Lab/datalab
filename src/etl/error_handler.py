import logging
import time
from typing import Callable, TypeVar, Optional
from functools import wraps

T = TypeVar("T")

logger = logging.getLogger(__name__)


def exponential_backoff(
    max_retries: int = 3,
    initial_delay: int = 1,
    max_delay: int = 60,
    exceptions: tuple = (Exception,),
):
    """指数退避装饰器"""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    if attempt > 0:
                        logger.warning(
                            f"重试 {attempt}/{max_retries}，等待 {delay} 秒..."
                        )
                        time.sleep(delay)

                    return func(*args, **kwargs)

                except exceptions as e:
                    last_exception = e
                    logger.error(f"尝试 {attempt + 1}/{max_retries + 1} 失败: {e}")

                    if attempt < max_retries:
                        delay = min(delay * 2, max_delay)
                    else:
                        logger.error(f"所有 {max_retries + 1} 次尝试均失败")
                        raise

            raise last_exception

        return wrapper

    return decorator


class ETLMetrics:
    """ETL 指标收集器"""

    def __init__(self):
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.records_processed = 0
        self.errors = 0
        self.batches_processed = 0

    def start(self):
        """开始计时"""
        self.start_time = time.time()
        logger.info("ETL 处理开始")

    def stop(self):
        """停止计时"""
        self.end_time = time.time()

    def record_processed(self, count: int = 1):
        """记录处理记录数"""
        self.records_processed += count

    def record_error(self, count: int = 1):
        """记录错误数"""
        self.errors += count

    def record_batch(self):
        """记录批次处理"""
        self.batches_processed += 1

    def get_duration(self) -> float:
        """获取处理时长（秒）"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        elif self.start_time:
            return time.time() - self.start_time
        return 0.0

    def get_summary(self) -> dict:
        """获取摘要"""
        duration = self.get_duration()
        return {
            "records_processed": self.records_processed,
            "errors": self.errors,
            "batches_processed": self.batches_processed,
            "duration_seconds": round(duration, 2),
            "records_per_second": round(self.records_processed / duration, 2)
            if duration > 0
            else 0,
            "start_time": self.start_time,
            "end_time": self.end_time,
        }

    def log_summary(self):
        """记录摘要日志"""
        summary = self.get_summary()
        logger.info("ETL 处理完成，摘要:")
        for key, value in summary.items():
            if key not in ["start_time", "end_time"]:
                logger.info(f"  {key}: {value}")
