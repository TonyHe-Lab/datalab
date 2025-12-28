"""
进度跟踪器和检查点管理器。

这个模块提供了批处理进度的跟踪、检查点管理和恢复功能。
"""

import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ProgressStats:
    """进度统计信息"""

    total_records: int = 0
    processed_records: int = 0
    failed_records: int = 0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    batch_size: int = 1000
    checkpoint_interval: int = 10000

    @property
    def progress_percentage(self) -> float:
        """计算进度百分比"""
        if self.total_records == 0:
            return 0.0
        return (self.processed_records / self.total_records) * 100

    @property
    def elapsed_time(self) -> float:
        """计算已用时间（秒）"""
        if self.start_time is None:
            return 0.0
        end = self.end_time or time.time()
        return end - self.start_time

    @property
    def records_per_second(self) -> float:
        """计算每秒处理记录数"""
        elapsed = self.elapsed_time
        if elapsed == 0:
            return 0.0
        return self.processed_records / elapsed

    @property
    def estimated_time_remaining(self) -> float:
        """估计剩余时间（秒）"""
        if self.processed_records == 0 or self.total_records == 0:
            return 0.0
        records_remaining = self.total_records - self.processed_records
        return (
            records_remaining / self.records_per_second
            if self.records_per_second > 0
            else 0
        )


class ProgressTracker:
    """进度跟踪器"""

    def __init__(self, job_name: str = "backfill"):
        self.job_name = job_name
        self.stats = ProgressStats()
        self.checkpoint_data: Dict[str, Any] = {}
        self.callbacks: Dict[str, Callable] = {}
        self.last_checkpoint_time = time.time()

    def start(self, total_records: int = 0):
        """开始跟踪进度"""
        self.stats.total_records = total_records
        self.stats.start_time = time.time()
        self.stats.processed_records = 0
        self.stats.failed_records = 0
        logger.info(f"开始 {self.job_name}: 总记录数={total_records}")

    def update(
        self,
        processed: int = 1,
        failed: int = 0,
        checkpoint_data: Optional[Dict[str, Any]] = None,
        force_checkpoint: bool = False,
    ) -> bool:
        """
        更新进度

        返回: 是否创建了检查点
        """
        self.stats.processed_records += processed
        self.stats.failed_records += failed

        # 更新检查点数据
        if checkpoint_data:
            self.checkpoint_data.update(checkpoint_data)

        # 记录进度
        if self.stats.processed_records % 1000 == 0:
            self._log_progress()

        # 检查是否需要创建检查点
        should_checkpoint = (
            force_checkpoint
            or self.stats.processed_records % self.stats.checkpoint_interval == 0
            or time.time() - self.last_checkpoint_time > 300  # 5分钟
        )

        if should_checkpoint:
            self._create_checkpoint()
            self.last_checkpoint_time = time.time()
            return True

        return False

    def complete(self):
        """标记任务完成"""
        self.stats.end_time = time.time()
        self._log_completion()

    def fail(self, error_message: str):
        """标记任务失败"""
        self.stats.end_time = time.time()
        logger.error(f"{self.job_name} 失败: {error_message}")
        logger.error(f"最终统计: {self._format_stats()}")

    def get_progress_report(self) -> Dict[str, Any]:
        """获取进度报告"""
        return {
            "job_name": self.job_name,
            "stats": {
                "total_records": self.stats.total_records,
                "processed_records": self.stats.processed_records,
                "failed_records": self.stats.failed_records,
                "progress_percentage": round(self.stats.progress_percentage, 2),
                "elapsed_time": round(self.stats.elapsed_time, 2),
                "records_per_second": round(self.stats.records_per_second, 2),
                "estimated_time_remaining": round(
                    self.stats.estimated_time_remaining, 2
                ),
            },
            "checkpoint_data": self.checkpoint_data,
            "timestamp": datetime.now().isoformat(),
        }

    def register_callback(self, event: str, callback: Callable):
        """注册回调函数"""
        self.callbacks[event] = callback

    def _log_progress(self):
        """记录进度日志"""
        stats = self._format_stats()
        logger.info(f"{self.job_name} 进度: {stats}")

    def _log_completion(self):
        """记录完成日志"""
        stats = self._format_stats()
        logger.info(f"{self.job_name} 完成: {stats}")

    def _format_stats(self) -> str:
        """格式化统计信息"""
        return (
            f"已处理: {self.stats.processed_records:,}/{self.stats.total_records:,} "
            f"({self.stats.progress_percentage:.1f}%), "
            f"失败: {self.stats.failed_records:,}, "
            f"速度: {self.stats.records_per_second:.1f} 记录/秒, "
            f"已用时间: {self._format_time(self.stats.elapsed_time)}, "
            f"剩余时间: {self._format_time(self.stats.estimated_time_remaining)}"
        )

    def _format_time(self, seconds: float) -> str:
        """格式化时间"""
        if seconds < 60:
            return f"{seconds:.0f}秒"
        elif seconds < 3600:
            return f"{seconds / 60:.1f}分钟"
        else:
            return f"{seconds / 3600:.1f}小时"

    def _create_checkpoint(self):
        """创建检查点（由子类实现）"""
        if "checkpoint" in self.callbacks:
            try:
                self.callbacks["checkpoint"](self.get_progress_report())
                logger.debug(f"创建检查点: {self.job_name}")
            except Exception as e:
                logger.error(f"创建检查点回调失败: {e}")


class BatchProcessor:
    """批处理器"""

    def __init__(
        self,
        batch_size: int = 1000,
        max_workers: int = 4,
        progress_tracker: Optional[ProgressTracker] = None,
    ):
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.progress_tracker = progress_tracker or ProgressTracker("batch_processor")

    def process_batches(
        self,
        data_source,
        process_func: Callable,
        total_records: Optional[int] = None,
    ):
        """
        处理批次数据

        Args:
            data_source: 数据源（生成器或可迭代对象）
            process_func: 处理函数，接受一个批次数据并返回处理结果
            total_records: 总记录数（如果已知）
        """
        self.progress_tracker.start(total_records or 0)

        batch = []
        for record in data_source:
            batch.append(record)

            if len(batch) >= self.batch_size:
                self._process_batch(batch, process_func)
                batch = []

        # 处理最后一批
        if batch:
            self._process_batch(batch, process_func)

        self.progress_tracker.complete()

    def _process_batch(self, batch: list, process_func: Callable):
        """处理单个批次"""
        try:
            result = process_func(batch)
            self.progress_tracker.update(
                processed=len(batch),
                checkpoint_data={"last_batch_size": len(batch)},
            )
            return result
        except Exception as e:
            logger.error(f"处理批次失败: {e}")
            self.progress_tracker.update(failed=len(batch))
            raise
