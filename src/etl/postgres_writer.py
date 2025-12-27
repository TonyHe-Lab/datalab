import logging
from typing import List, Dict, Optional, Any
import psycopg
from psycopg.errors import Error as PostgresError

from src.utils.config import PostgresConfig

logger = logging.getLogger(__name__)


class PostgresWriter:
    """PostgreSQL 数据写入器"""

    def __init__(self, config: PostgresConfig):
        self.config = config
        self.connection: Optional[psycopg.Connection] = None

    def connect(self) -> bool:
        """连接到 PostgreSQL"""
        try:
            logger.info(f"正在连接到 PostgreSQL: {self.config.host}:{self.config.port}")

            # 构建连接字符串
            conn_str = (
                f"host={self.config.host} "
                f"port={self.config.port} "
                f"dbname={self.config.database} "
                f"user={self.config.user} "
                f"password={self.config.password}"
            )

            self.connection = psycopg.connect(conn_str)
            logger.info("PostgreSQL 连接成功")
            return True

        except PostgresError as e:
            logger.error(f"PostgreSQL 连接失败: {e}")
            return False
        except Exception as e:
            logger.error(f"连接时发生意外错误: {e}")
            return False

    def disconnect(self):
        """断开连接"""
        if self.connection:
            try:
                self.connection.close()
                logger.info("PostgreSQL 连接已关闭")
            except Exception as e:
                logger.error(f"关闭连接时出错: {e}")
            finally:
                self.connection = None

    def create_etl_metadata_table(self):
        """创建 ETL 元数据表"""
        query = """
        CREATE TABLE IF NOT EXISTS etl_metadata (
            table_name VARCHAR(255) PRIMARY KEY,
            last_successful_extraction TIMESTAMP,
            records_processed INTEGER DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """

        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            self.connection.commit()
            cursor.close()
            logger.info("ETL 元数据表创建/验证完成")
        except PostgresError as e:
            logger.error(f"创建 ETL 元数据表失败: {e}")
            raise

    def get_last_extraction_time(self, table_name: str) -> Optional[str]:
        """获取最后提取时间"""
        query = """
        SELECT last_successful_extraction 
        FROM etl_metadata 
        WHERE table_name = %s
        """

        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (table_name,))
            result = cursor.fetchone()
            cursor.close()
            return result[0] if result else None
        except PostgresError as e:
            logger.error(f"获取最后提取时间失败: {e}")
            return None

    def update_extraction_time(
        self, table_name: str, extraction_time: str, records_processed: int
    ):
        """更新提取时间"""
        query = """
        INSERT INTO etl_metadata (table_name, last_successful_extraction, records_processed)
        VALUES (%s, %s, %s)
        ON CONFLICT (table_name) 
        DO UPDATE SET 
            last_successful_extraction = EXCLUDED.last_successful_extraction,
            records_processed = EXCLUDED.records_processed,
            last_updated = CURRENT_TIMESTAMP
        """

        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (table_name, extraction_time, records_processed))
            self.connection.commit()
            cursor.close()
            logger.info(
                f"更新 {table_name} 的提取时间: {extraction_time}, 处理记录数: {records_processed}"
            )
        except PostgresError as e:
            logger.error(f"更新提取时间失败: {e}")
            raise

    def upsert_notification_text(self, records: List[Dict]) -> int:
        """UPSERT 通知文本数据"""
        if not records:
            return 0

        # 构建 UPSERT 查询
        query = """
        INSERT INTO notification_text (
            notification_id, notification_date, notification_assigned_date,
            notification_closed_date, noti_category_id, sys_eq_id,
            noti_country_id, sys_fl_id, sys_mat_id, sys_serial_id,
            notification_trendcode_l1, notification_trendcode_l2,
            notification_trendcode_l3, notification_medium_text, notification_text
        ) VALUES (
            %(notification_id)s, %(notification_date)s, %(notification_assigned_date)s,
            %(notification_closed_date)s, %(noti_category_id)s, %(sys_eq_id)s,
            %(noti_country_id)s, %(sys_fl_id)s, %(sys_mat_id)s, %(sys_serial_id)s,
            %(notification_trendcode_l1)s, %(notification_trendcode_l2)s,
            %(notification_trendcode_l3)s, %(notification_medium_text)s, %(notification_text)s
        )
        ON CONFLICT (notification_id) 
        DO UPDATE SET
            notification_date = EXCLUDED.notification_date,
            notification_assigned_date = EXCLUDED.notification_assigned_date,
            notification_closed_date = EXCLUDED.notification_closed_date,
            noti_category_id = EXCLUDED.noti_category_id,
            sys_eq_id = EXCLUDED.sys_eq_id,
            noti_country_id = EXCLUDED.noti_country_id,
            sys_fl_id = EXCLUDED.sys_fl_id,
            sys_mat_id = EXCLUDED.sys_mat_id,
            sys_serial_id = EXCLUDED.sys_serial_id,
            notification_trendcode_l1 = EXCLUDED.notification_trendcode_l1,
            notification_trendcode_l2 = EXCLUDED.notification_trendcode_l2,
            notification_trendcode_l3 = EXCLUDED.notification_trendcode_l3,
            notification_medium_text = EXCLUDED.notification_medium_text,
            notification_text = EXCLUDED.notification_text
        """

        try:
            cursor = self.connection.cursor()
            cursor.executemany(query, records)
            self.connection.commit()
            cursor.close()

            processed_count = len(records)
            logger.info(f"UPSERT 完成，处理了 {processed_count} 条记录")
            return processed_count

        except PostgresError as e:
            logger.error(f"UPSERT 失败: {e}")
            self.connection.rollback()
            raise

    def batch_upsert(
        self, table_name: str, records: List[Dict], batch_size: int = 1000
    ) -> int:
        """批量 UPSERT"""
        total_processed = 0

        for i in range(0, len(records), batch_size):
            batch = records[i : i + batch_size]

            try:
                if table_name == "notification_text":
                    processed = self.upsert_notification_text(batch)
                else:
                    # 可以扩展支持其他表
                    raise ValueError(f"不支持的表格: {table_name}")

                total_processed += processed
                logger.info(
                    f"批次 {i // batch_size + 1} 完成，处理了 {processed} 条记录"
                )

            except Exception as e:
                logger.error(f"批次 {i // batch_size + 1} 处理失败: {e}")
                raise

        return total_processed

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
