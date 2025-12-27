import logging
import sys
from typing import Optional
from datetime import datetime

from src.utils.config import load_config, validate_config
from src.etl.snowflake_loader import SnowflakeClient
from src.etl.postgres_writer import PostgresWriter
from src.etl.error_handler import exponential_backoff, ETLMetrics

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("etl.log")],
)

logger = logging.getLogger(__name__)


class IncrementalSync:
    """增量同步器"""

    def __init__(self, config=None):
        self.config = config or load_config()
        validate_config(self.config)
        self.metrics = ETLMetrics()

    @exponential_backoff(max_retries=3, initial_delay=5)
    def sync_table(
        self, table_name: str, watermark_column: str = "notification_date"
    ) -> bool:
        """同步单个表"""
        logger.info(f"开始同步表: {table_name}")

        try:
            # 连接到 Snowflake
            with SnowflakeClient(self.config.snowflake) as snowflake_client:
                if not snowflake_client.test_connection():
                    logger.error("Snowflake 连接测试失败")
                    return False

                # 连接到 PostgreSQL
                with PostgresWriter(self.config.postgres) as postgres_writer:
                    # 确保 ETL 元数据表存在
                    postgres_writer.create_etl_metadata_table()

                    # 获取最后提取时间
                    last_extraction = postgres_writer.get_last_extraction_time(
                        table_name
                    )
                    logger.info(f"最后提取时间: {last_extraction or '无'}")

                    # 获取增量数据
                    logger.info(f"从 Snowflake 获取增量数据...")
                    incremental_data = snowflake_client.get_incremental_data(
                        table_name=table_name,
                        watermark_column=watermark_column,
                        last_extraction=last_extraction,
                    )

                    if not incremental_data:
                        logger.info(f"没有新的增量数据需要同步")
                        return True

                    logger.info(f"获取到 {len(incremental_data)} 条增量记录")

                    # 批量写入 PostgreSQL
                    processed_count = postgres_writer.batch_upsert(
                        table_name=table_name,
                        records=incremental_data,
                        batch_size=self.config.etl.batch_size,
                    )

                    # 更新最后提取时间
                    if incremental_data:
                        # 获取最新的时间戳
                        latest_timestamp = max(
                            record[watermark_column]
                            for record in incremental_data
                            if record.get(watermark_column)
                        )

                        postgres_writer.update_extraction_time(
                            table_name=table_name,
                            extraction_time=latest_timestamp,
                            records_processed=processed_count,
                        )

                    self.metrics.record_processed(processed_count)
                    self.metrics.record_batch()

                    logger.info(
                        f"表 {table_name} 同步完成，处理了 {processed_count} 条记录"
                    )
                    return True

        except Exception as e:
            logger.error(f"同步表 {table_name} 失败: {e}")
            self.metrics.record_error()
            raise

    def run(self, tables: Optional[list] = None) -> bool:
        """运行同步"""
        self.metrics.start()

        try:
            # 默认同步的表
            if tables is None:
                tables = ["notification_text"]

            success_count = 0
            total_tables = len(tables)

            for table_name in tables:
                try:
                    if self.sync_table(table_name):
                        success_count += 1
                except Exception as e:
                    logger.error(f"表 {table_name} 同步失败，继续处理其他表: {e}")

            self.metrics.stop()
            self.metrics.log_summary()

            success_rate = success_count / total_tables if total_tables > 0 else 0
            logger.info(
                f"同步完成，成功率: {success_count}/{total_tables} ({success_rate:.1%})"
            )

            return success_count == total_tables

        except Exception as e:
            logger.error(f"同步运行失败: {e}")
            self.metrics.stop()
            self.metrics.log_summary()
            raise


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="增量 ETL 同步脚本")
    parser.add_argument("--tables", nargs="+", help="要同步的表名列表")
    parser.add_argument("--config", help="配置文件路径")

    args = parser.parse_args()

    try:
        sync = IncrementalSync()
        success = sync.run(args.tables)

        if success:
            logger.info("所有表同步成功")
            sys.exit(0)
        else:
            logger.error("部分表同步失败")
            sys.exit(1)

    except Exception as e:
        logger.error(f"ETL 同步失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
