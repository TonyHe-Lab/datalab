"""
Historical Data Processor for backfilling medical work orders.

This module handles extraction of historical data from Snowflake,
processing in batches, and integration with the AI pipeline.
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Generator, Tuple, Any
from dataclasses import dataclass
import json

from src.etl.snowflake_loader import SnowflakeClient
from src.etl.postgres_writer import PostgresWriter
from src.utils.config import SnowflakeConfig, PostgresConfig
from src.utils.progress_tracker import ProgressTracker, BatchProcessor
from src.utils.parallel_processor import (
    ParallelProcessor,
    ParallelConfig,
    ConnectionPool,
    MemoryOptimizer,
)
from src.ai.cost_tracker import CostTracker
from src.ai.openai_client import AzureOpenAIClient
from src.ai.text_analyzer import analyze_text
from src.ai.embedding_pipeline import EmbeddingPipeline, EmbeddingCache
from src.ai.pii_scrubber import redact_pii

logger = logging.getLogger(__name__)


@dataclass
class BackfillConfig:
    """Configuration for historical data backfill."""

    start_date: Optional[date] = None
    end_date: Optional[date] = None
    batch_size: int = 1000
    max_records: Optional[int] = None
    enable_ai_processing: bool = True
    enable_embeddings: bool = True
    dry_run: bool = False
    # Parallel processing configuration
    enable_parallel_processing: bool = True
    max_workers: int = 4
    use_multiprocessing: bool = True
    connection_pool_size: int = 10
    max_memory_mb: int = 100


class HistoricalProcessor:
    """Processor for historical data extraction and processing."""

    def __init__(
        self,
        snowflake_config: SnowflakeConfig,
        postgres_config: PostgresConfig,
        backfill_config: BackfillConfig,
    ):
        self.snowflake_config = snowflake_config
        self.postgres_config = postgres_config
        self.backfill_config = backfill_config

        self.snowflake_client: Optional[SnowflakeClient] = None
        self.postgres_writer: Optional[PostgresWriter] = None
        self.cost_tracker: Optional[CostTracker] = None
        self.openai_client: Optional[AzureOpenAIClient] = None
        self.embedding_pipeline: Optional[EmbeddingPipeline] = None

        self.total_records = 0
        self.processed_records = 0
        self.failed_records = 0
        self.checkpoint_data: Dict[str, Any] = {}

    def initialize(self) -> bool:
        """Initialize all components."""
        try:
            # Initialize Snowflake client
            self.snowflake_client = SnowflakeClient(self.snowflake_config)
            if not self.snowflake_client.connect():
                logger.error("Failed to connect to Snowflake")
                return False

            # Initialize PostgreSQL writer
            self.postgres_writer = PostgresWriter(self.postgres_config)
            if not self.postgres_writer.connect():
                logger.error("Failed to connect to PostgreSQL")
                return False

            # Initialize cost tracker
            self.cost_tracker = CostTracker()

            # Initialize AI components if enabled
            if self.backfill_config.enable_ai_processing:
                try:
                    from src.utils.config import load_config

                    config = load_config()

                    # Initialize Azure OpenAI client
                    self.openai_client = AzureOpenAIClient(
                        endpoint=config.get("azure_openai", {}).get("endpoint"),
                        api_key=config.get("azure_openai", {}).get("api_key"),
                        api_version=config.get("azure_openai", {}).get("api_version"),
                        chat_deployment=config.get("azure_openai", {}).get(
                            "chat_deployment"
                        ),
                        embed_deployment=config.get("azure_openai", {}).get(
                            "embed_deployment"
                        ),
                    )

                    # Initialize embedding pipeline if enabled
                    if self.backfill_config.enable_embeddings:
                        self.embedding_pipeline = EmbeddingPipeline(
                            client=self.openai_client,
                            embed_deployment=config.get("azure_openai", {}).get(
                                "embed_deployment"
                            ),
                            writer=self.postgres_writer,
                        )

                    logger.info("AI components initialized successfully")
                except Exception as ai_error:
                    logger.warning(f"Failed to initialize AI components: {ai_error}")
                    logger.warning("Continuing without AI processing")
                    self.backfill_config.enable_ai_processing = False
                    self.backfill_config.enable_embeddings = False

            logger.info("Historical processor initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize historical processor: {e}")
            return False

    def build_historical_query(self) -> str:
        """Build Snowflake query for historical data extraction."""
        base_query = """
        SELECT 
            notification_id,
            notification_text,
            created_at,
            equipment_id,
            facility_id,
            priority_level,
            status,
            assigned_technician,
            resolution_time,
            category
        FROM notification_text
        WHERE 1=1
        """

        # Add date range filtering if specified
        if self.backfill_config.start_date:
            base_query += f" AND created_at >= '{self.backfill_config.start_date}'"

        if self.backfill_config.end_date:
            base_query += f" AND created_at <= '{self.backfill_config.end_date}'"

        # Order by created_at for consistent processing
        base_query += " ORDER BY created_at ASC"

        # Add limit if specified
        if self.backfill_config.max_records:
            base_query += f" LIMIT {self.backfill_config.max_records}"

        return base_query

    def extract_historical_data(self) -> Generator[List[Dict], None, None]:
        """Extract historical data from Snowflake in batches."""
        if not self.snowflake_client:
            raise RuntimeError("Snowflake client not initialized")

        query = self.build_historical_query()
        logger.info(f"Executing historical query: {query[:200]}...")

        try:
            # Use streaming cursor for large result sets
            cursor = self.snowflake_client.connection.cursor()
            cursor.execute(query)

            batch = []
            record_count = 0

            while True:
                row = cursor.fetchone()
                if row is None:
                    break

                # Convert row to dictionary
                record = {
                    "notification_id": row[0],
                    "notification_text": row[1],
                    "created_at": row[2],
                    "equipment_id": row[3],
                    "facility_id": row[4],
                    "priority_level": row[5],
                    "status": row[6],
                    "assigned_technician": row[7],
                    "resolution_time": row[8],
                    "category": row[9],
                }

                batch.append(record)
                record_count += 1

                # Yield batch when size is reached
                if len(batch) >= self.backfill_config.batch_size:
                    logger.debug(f"Yielding batch of {len(batch)} records")
                    yield batch
                    batch = []

            # Yield any remaining records
            if batch:
                logger.debug(f"Yielding final batch of {len(batch)} records")
                yield batch

            self.total_records = record_count
            logger.info(f"Total records to process: {record_count}")

            cursor.close()

        except Exception as e:
            logger.error(f"Error extracting historical data: {e}")
            raise

    def validate_record(self, record: Dict) -> Tuple[bool, Optional[str]]:
        """Validate a single record."""
        try:
            # Check required fields
            required_fields = ["notification_id", "notification_text", "created_at"]
            for field in required_fields:
                if not record.get(field):
                    return False, f"Missing required field: {field}"

            # Validate notification_id format
            notification_id = str(record["notification_id"])
            if not notification_id.strip():
                return False, "Empty notification_id"

            # Validate created_at is a valid date
            created_at = record["created_at"]
            if not isinstance(created_at, (datetime, date)):
                return False, f"Invalid created_at type: {type(created_at)}"

            # Validate notification_text length
            notification_text = str(record["notification_text"])
            if len(notification_text.strip()) < 10:
                return (
                    False,
                    f"Notification text too short: {len(notification_text)} chars",
                )

            return True, None

        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def process_batch(self, batch: List[Dict]) -> Tuple[int, int]:
        """Process a batch of records."""
        if not self.postgres_writer:
            raise RuntimeError("PostgreSQL writer not initialized")

        valid_records = []
        batch_errors = []

        # Validate each record
        for record in batch:
            is_valid, error_msg = self.validate_record(record)
            if is_valid:
                valid_records.append(record)
            else:
                batch_errors.append(
                    {
                        "notification_id": record.get("notification_id"),
                        "error": error_msg,
                    }
                )
                self.failed_records += 1

        if not valid_records:
            logger.warning(f"Batch had no valid records. Errors: {batch_errors}")
            return 0, len(batch_errors)

        try:
            # Write to PostgreSQL
            success_count = self.postgres_writer.write_notification_text_batch(
                valid_records
            )

            # Update processed records count
            self.processed_records += success_count

            # Log batch processing results
            logger.info(
                f"Batch processed: {success_count} successful, "
                f"{len(batch_errors)} failed, "
                f"total processed: {self.processed_records}/{self.total_records}"
            )

            # Log errors if any
            if batch_errors:
                for error in batch_errors[:5]:  # Log first 5 errors
                    logger.warning(f"Record error: {error}")
                if len(batch_errors) > 5:
                    logger.warning(f"... and {len(batch_errors) - 5} more errors")

            return success_count, len(batch_errors)

        except Exception as e:
            logger.error(f"Error processing batch: {e}")
            self.failed_records += len(valid_records)
            return 0, len(valid_records)

    def create_checkpoint(self) -> Dict[str, Any]:
        """Create checkpoint data for resuming."""
        checkpoint = {
            "total_records": self.total_records,
            "processed_records": self.processed_records,
            "failed_records": self.failed_records,
            "last_processed_date": datetime.now().isoformat(),
            "config": {
                "start_date": self.backfill_config.start_date.isoformat()
                if self.backfill_config.start_date
                else None,
                "end_date": self.backfill_config.end_date.isoformat()
                if self.backfill_config.end_date
                else None,
                "batch_size": self.backfill_config.batch_size,
                "max_records": self.backfill_config.max_records,
            },
        }

        # Store checkpoint in instance
        self.checkpoint_data = checkpoint

        return checkpoint

    def save_checkpoint(self, checkpoint_file: str = "backfill_checkpoint.json"):
        """Save checkpoint to file."""
        checkpoint = self.create_checkpoint()

        try:
            with open(checkpoint_file, "w") as f:
                json.dump(checkpoint, f, indent=2)
            logger.info(f"Checkpoint saved to {checkpoint_file}")
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")

    def load_checkpoint(
        self, checkpoint_file: str = "backfill_checkpoint.json"
    ) -> bool:
        """Load checkpoint from file."""
        try:
            with open(checkpoint_file, "r") as f:
                checkpoint = json.load(f)

            # Restore state
            self.total_records = checkpoint.get("total_records", 0)
            self.processed_records = checkpoint.get("processed_records", 0)
            self.failed_records = checkpoint.get("failed_records", 0)

            logger.info(
                f"Checkpoint loaded: processed {self.processed_records}/"
                f"{self.total_records} records, {self.failed_records} failed"
            )
            return True

        except FileNotFoundError:
            logger.info("No checkpoint file found, starting fresh")
            return False
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return False

    # ========== 进度跟踪和检查点功能 ==========

    def create_database_checkpoint(self, checkpoint_data: Dict[str, Any]):
        """在数据库中创建检查点"""
        if not self.postgres_writer:
            raise RuntimeError("PostgreSQL writer not initialized")

        try:
            self.postgres_writer.create_checkpoint(
                table_name="notification_text_backfill",
                checkpoint_data=checkpoint_data,
                processed_records=self.processed_records,
                total_records=self.total_records,
                batch_size=self.backfill_config.batch_size,
            )
            logger.debug(f"数据库检查点创建成功: {checkpoint_data}")
        except Exception as e:
            logger.error(f"创建数据库检查点失败: {e}")

    def load_database_checkpoint(self) -> Optional[Dict[str, Any]]:
        """从数据库加载检查点"""
        if not self.postgres_writer:
            raise RuntimeError("PostgreSQL writer not initialized")

        try:
            checkpoint = self.postgres_writer.get_checkpoint(
                "notification_text_backfill"
            )
            if checkpoint:
                self.processed_records = checkpoint["processed_records"]
                self.total_records = checkpoint["total_records"]
                self.backfill_config.batch_size = checkpoint["batch_size"]
                logger.info(
                    f"从数据库加载检查点: 已处理 {self.processed_records}/"
                    f"{self.total_records} 记录"
                )
                return checkpoint["checkpoint_data"]
            return None
        except Exception as e:
            logger.error(f"加载数据库检查点失败: {e}")
            return None

    def complete_database_checkpoint(self):
        """完成数据库检查点"""
        if not self.postgres_writer:
            raise RuntimeError("PostgreSQL writer not initialized")

        try:
            self.postgres_writer.complete_checkpoint(
                "notification_text_backfill", self.total_records
            )
            logger.info("数据库检查点标记为完成")
        except Exception as e:
            logger.error(f"完成数据库检查点失败: {e}")

    def clear_database_checkpoint(self):
        """清除数据库检查点"""
        if not self.postgres_writer:
            raise RuntimeError("PostgreSQL writer not initialized")

        try:
            self.postgres_writer.clear_checkpoint("notification_text_backfill")
            logger.info("数据库检查点已清除")
        except Exception as e:
            logger.error(f"清除数据库检查点失败: {e}")

    def process_with_progress_tracking(self, resume: bool = False):
        """使用进度跟踪处理历史数据"""
        # 初始化进度跟踪器
        progress_tracker = ProgressTracker("historical_backfill")

        # 注册检查点回调
        progress_tracker.register_callback(
            "checkpoint",
            lambda report: self.create_database_checkpoint(report["checkpoint_data"]),
        )

        # 如果需要恢复，加载检查点
        if resume:
            checkpoint_data = self.load_database_checkpoint()
            if checkpoint_data:
                progress_tracker.checkpoint_data = checkpoint_data
                logger.info(f"从检查点恢复: {checkpoint_data}")
            else:
                logger.info("未找到检查点，开始新任务")

        # 初始化批处理器
        batch_processor = BatchProcessor(
            batch_size=self.backfill_config.batch_size,
            progress_tracker=progress_tracker,
        )

        try:
            # 开始处理
            progress_tracker.start(self.total_records)

            # 提取和处理数据
            data_generator = self.extract_historical_data()
            batch_processor.process_batches(
                data_source=data_generator,
                process_func=self._process_batch_with_ai,
                total_records=self.total_records,
            )

            # 标记完成
            self.complete_database_checkpoint()
            progress_tracker.complete()

        except Exception as e:
            logger.error(f"处理失败: {e}")
            progress_tracker.fail(str(e))
            raise

    def _process_batch_with_ai(self, batch: List[Dict]) -> bool:
        """使用AI处理批次数据"""
        if not self.postgres_writer:
            return False

        try:
            # 1. 写入原始通知文本（如果有数据）
            if batch and not self.backfill_config.dry_run:
                self.postgres_writer.upsert_notification_text(batch)

            # 2. AI处理（如果启用）
            if self.backfill_config.enable_ai_processing and self.openai_client:
                ai_results = self._process_batch_with_ai_extraction(batch)

                # 写入AI提取的数据
                if ai_results and not self.backfill_config.dry_run:
                    self.postgres_writer.upsert_ai_extracted_data(ai_results)

            # 3. 嵌入生成（如果启用）
            if self.backfill_config.enable_embeddings and self.embedding_pipeline:
                embeddings = self._process_batch_with_embeddings(batch)

                # 写入嵌入数据
                if embeddings and not self.backfill_config.dry_run:
                    self.postgres_writer.upsert_semantic_embeddings(embeddings)

            # 4. 更新检查点数据
            if batch:
                last_record = batch[-1]
                self.checkpoint_data = {
                    "last_notification_id": last_record.get("notification_id"),
                    "last_created_at": last_record.get("created_at"),
                    "batch_size": len(batch),
                    "processed_records": self.processed_records + len(batch),
                    "failed_records": self.failed_records,
                }

            # 5. 更新统计信息
            self.processed_records += len(batch)

            logger.info(f"成功处理批次: {len(batch)} 条记录")
            return True

        except Exception as e:
            logger.error(f"处理批次失败: {e}")
            self.failed_records += len(batch)
            return False

    def _process_batch_with_ai_extraction(self, batch: List[Dict]) -> List[Dict]:
        """使用AI提取批次数据的结构化信息"""
        if not self.openai_client:
            return []

        ai_results = []

        for record in batch:
            notification_id = record.get("notification_id")
            text = record.get("notification_text", "")

            if not notification_id:
                logger.warning("记录缺少notification_id，跳过AI处理")
                continue

            try:
                # 调用AI分析
                result = analyze_text(
                    notification_id=notification_id,
                    text=text,
                    client=self.openai_client,
                )

                if result.get("success"):
                    ai_data = result.get("data", {})
                    ai_results.append(ai_data)

                    # 记录成本（暂时注释，需要扩展CostTracker）
                    # if self.cost_tracker:
                    #     self.cost_tracker.record_ai_call(
                    #         model="gpt-4",
                    #         tokens_used=result.get("tokens_used", 0),
                    #         cost_usd=result.get("cost_usd", 0)
                    #     )
                else:
                    logger.warning(
                        f"AI处理失败 {notification_id}: {result.get('error')}"
                    )
                    self.failed_records += 1

            except Exception as e:
                logger.error(f"AI处理异常 {notification_id}: {e}")
                self.failed_records += 1

        logger.info(f"AI提取完成: {len(ai_results)}/{len(batch)} 成功")

        # 质量验证
        if ai_results:
            quality_report = self._validate_ai_quality(ai_results)
            logger.info(f"AI质量报告: {quality_report}")

        return ai_results

    def _validate_ai_quality(self, ai_results: List[Dict]) -> Dict[str, Any]:
        """验证AI输出质量"""
        total = len(ai_results)
        if total == 0:
            return {"total": 0, "valid": 0, "invalid": 0, "quality_score": 0.0}

        valid_count = 0
        quality_scores = []

        for result in ai_results:
            # 检查必填字段
            required_fields = ["main_component_ai", "primary_symptom_ai", "summary_ai"]
            has_required = all(result.get(field) for field in required_fields)

            # 检查字段长度
            summary = result.get("summary_ai", "")
            has_valid_summary = len(summary) >= 10 and len(summary) <= 500

            # 检查关键词
            keywords = result.get("keywords_ai", [])
            has_keywords = isinstance(keywords, list) and len(keywords) > 0

            # 计算质量分数
            score = 0.0
            if has_required:
                score += 0.4
            if has_valid_summary:
                score += 0.3
            if has_keywords:
                score += 0.3

            quality_scores.append(score)

            if score >= 0.7:  # 质量阈值
                valid_count += 1

        avg_quality = (
            sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        )

        return {
            "total": total,
            "valid": valid_count,
            "invalid": total - valid_count,
            "quality_score": round(avg_quality, 3),
            "quality_distribution": {
                "excellent": len([s for s in quality_scores if s >= 0.9]),
                "good": len([s for s in quality_scores if 0.7 <= s < 0.9]),
                "fair": len([s for s in quality_scores if 0.5 <= s < 0.7]),
                "poor": len([s for s in quality_scores if s < 0.5]),
            },
        }

    def _process_batch_with_embeddings(self, batch: List[Dict]) -> List[Dict]:
        """为批次数据生成嵌入"""
        if not self.embedding_pipeline:
            return []

        embeddings = []

        # 准备文本列表
        texts = []
        records_for_embedding = []

        for record in batch:
            notification_id = record.get("notification_id")
            text = record.get("notification_text", "")

            if text:
                texts.append(text)
                records_for_embedding.append(record)

        if not texts:
            return []

        try:
            # 批量生成嵌入
            vectors = self.embedding_pipeline.batch_generate(texts)

            # 构建嵌入记录
            for i, (record, vector) in enumerate(zip(records_for_embedding, vectors)):
                embedding_record = {
                    "notification_id": record.get("notification_id"),
                    "embedding_vector": vector,
                    "embedding_model": self.embedding_pipeline.embed_deployment,
                    "created_at": datetime.now(),
                }
                embeddings.append(embedding_record)

                # 记录成本（暂时注释，需要扩展CostTracker）
                # if self.cost_tracker:
                #     self.cost_tracker.record_embedding_call(
                #         model=self.embedding_pipeline.embed_deployment,
                #         tokens_used=len(texts[i].split()) * 1.3,  # 估算
                #         cost_usd=0.0001  # 估算成本
                #     )

            logger.info(f"嵌入生成完成: {len(embeddings)} 条记录")
            return embeddings

        except Exception as e:
            logger.error(f"嵌入生成失败: {e}")
            return []

    def cleanup(self):
        """Clean up resources."""
        if self.snowflake_client:
            self.snowflake_client.disconnect()

        if self.postgres_writer:
            self.postgres_writer.disconnect()

        logger.info("Historical processor cleanup completed")

    # ========== 并行处理方法 ==========

    def process_with_parallel_tracking(self, resume: bool = False):
        """使用并行处理和进度跟踪处理历史数据"""
        if not self.backfill_config.enable_parallel_processing:
            logger.info("并行处理已禁用，使用串行处理")
            return self.process_with_progress_tracking(resume)

        # 初始化进度跟踪器
        progress_tracker = ProgressTracker("historical_backfill_parallel")

        # 注册检查点回调
        progress_tracker.register_callback(
            "checkpoint",
            lambda report: self.create_database_checkpoint(report["checkpoint_data"]),
        )

        # 如果需要恢复，加载检查点
        if resume:
            checkpoint_data = self.load_database_checkpoint()
            if checkpoint_data:
                progress_tracker.checkpoint_data = checkpoint_data
                logger.info(f"从检查点恢复: {checkpoint_data}")
            else:
                logger.info("未找到检查点，开始新任务")

        try:
            # 开始处理
            progress_tracker.start(self.total_records)

            # 创建并行处理器配置
            parallel_config = ParallelConfig(
                max_workers=self.backfill_config.max_workers,
                use_multiprocessing=self.backfill_config.use_multiprocessing,
                chunk_size=self.backfill_config.batch_size,
                timeout_seconds=300,
                max_retries=3,
                retry_delay=1.0,
            )

            # 使用并行处理器
            with ParallelProcessor(parallel_config) as processor:
                # 提取数据（使用内存优化）
                data_generator = self.extract_historical_data()
                optimized_generator = MemoryOptimizer.stream_large_dataset(
                    data_generator, max_memory_mb=self.backfill_config.max_memory_mb
                )

                # 并行处理批次
                stats = processor.process_batches_parallel(
                    data_source=optimized_generator,
                    process_func=self._process_batch_for_parallel,
                    total_records=self.total_records,
                )

                # 记录统计信息
                logger.info(f"并行处理完成: {stats}")

            # 标记完成
            self.complete_database_checkpoint()
            progress_tracker.complete()

        except Exception as e:
            logger.error(f"并行处理失败: {e}")
            progress_tracker.fail(str(e))
            raise

    def _process_batch_for_parallel(self, batch: List[Dict]) -> Tuple[int, int]:
        """
        为并行处理准备的批次处理方法。

        返回:
            Tuple[成功记录数, 失败记录数]
        """
        try:
            success_count = 0
            error_count = 0

            # 处理批次（重用现有的AI处理方法）
            if batch and not self.backfill_config.dry_run:
                # 写入原始通知文本
                try:
                    self.postgres_writer.upsert_notification_text(batch)
                    success_count += len(batch)
                except Exception as e:
                    logger.error(f"写入通知文本失败: {e}")
                    error_count += len(batch)

                # AI处理（如果启用）
                if self.backfill_config.enable_ai_processing and self.openai_client:
                    try:
                        ai_results = self._process_batch_with_ai_extraction(batch)
                        if ai_results:
                            self.postgres_writer.upsert_ai_extracted_data(ai_results)
                            success_count += len(ai_results)
                    except Exception as e:
                        logger.error(f"AI处理失败: {e}")
                        error_count += len(batch)

                # 嵌入生成（如果启用）
                if self.backfill_config.enable_embeddings and self.embedding_pipeline:
                    try:
                        embeddings = self._process_batch_with_embeddings(batch)
                        if embeddings:
                            self.postgres_writer.upsert_semantic_embeddings(embeddings)
                            success_count += len(embeddings)
                    except Exception as e:
                        logger.error(f"嵌入生成失败: {e}")
                        error_count += len(batch)

            return success_count, error_count

        except Exception as e:
            logger.error(f"批次处理失败: {e}")
            return 0, len(batch) if batch else 0

    def optimize_database_writes(self):
        """优化数据库写入性能"""
        if not self.postgres_writer:
            return

        logger.info("优化数据库写入性能...")

        # 这里可以添加数据库写入优化逻辑，例如：
        # 1. 批量插入优化
        # 2. 索引管理
        # 3. 连接池优化
        # 4. 事务批处理

        # 示例：调整批量插入大小
        optimal_batch_size = MemoryOptimizer.optimize_batch_size(
            initial_batch_size=self.backfill_config.batch_size,
            memory_usage_mb=50,  # 假设当前内存使用
            max_memory_mb=self.backfill_config.max_memory_mb,
        )

        if optimal_batch_size != self.backfill_config.batch_size:
            logger.info(
                f"优化批量大小: {self.backfill_config.batch_size} -> {optimal_batch_size}"
            )
            self.backfill_config.batch_size = optimal_batch_size

        logger.info("数据库写入优化完成")
