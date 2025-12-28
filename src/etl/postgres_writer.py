import logging
from typing import List, Dict, Optional, Any
import psycopg2
import psycopg2.extras
from psycopg2 import Error as PostgresError

from src.utils.config import PostgresConfig

logger = logging.getLogger(__name__)


class PostgresWriter:
    """PostgreSQL 数据写入器"""

    def __init__(self, config: PostgresConfig):
        self.config = config
        self.connection: Optional[psycopg2.extensions.connection] = None

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

            self.connection = psycopg2.connect(conn_str)
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

    # ========== 检查点功能 ==========

    def create_checkpoint(
        self,
        table_name: str,
        checkpoint_data: Dict[str, Any],
        processed_records: int,
        total_records: int = 0,
        batch_size: int = 1000,
    ):
        """创建或更新检查点"""
        query = """
        INSERT INTO etl_metadata (
            table_name, 
            sync_status, 
            checkpoint_data, 
            checkpoint_timestamp,
            processed_records,
            total_records,
            batch_size,
            updated_at
        )
        VALUES (%s, 'in_progress', %s, CURRENT_TIMESTAMP, %s, %s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT (table_name) 
        DO UPDATE SET 
            sync_status = 'in_progress',
            checkpoint_data = EXCLUDED.checkpoint_data,
            checkpoint_timestamp = EXCLUDED.checkpoint_timestamp,
            processed_records = EXCLUDED.processed_records,
            total_records = EXCLUDED.total_records,
            batch_size = EXCLUDED.batch_size,
            updated_at = CURRENT_TIMESTAMP
        """

        try:
            cursor = self.connection.cursor()
            cursor.execute(
                query,
                (
                    table_name,
                    psycopg2.extras.Json(checkpoint_data),
                    processed_records,
                    total_records,
                    batch_size,
                ),
            )
            self.connection.commit()
            cursor.close()
            logger.info(
                f"创建检查点: {table_name}, 已处理: {processed_records}/{total_records}"
            )
        except PostgresError as e:
            logger.error(f"创建检查点失败: {e}")
            raise

    def get_checkpoint(self, table_name: str) -> Optional[Dict[str, Any]]:
        """获取检查点数据"""
        query = """
        SELECT 
            checkpoint_data,
            processed_records,
            total_records,
            batch_size,
            checkpoint_timestamp
        FROM etl_metadata 
        WHERE table_name = %s AND sync_status = 'in_progress'
        """

        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (table_name,))
            result = cursor.fetchone()
            cursor.close()

            if result:
                checkpoint_data = result[0] if result[0] else {}
                return {
                    "checkpoint_data": checkpoint_data,
                    "processed_records": result[1] or 0,
                    "total_records": result[2] or 0,
                    "batch_size": result[3] or 1000,
                    "checkpoint_timestamp": result[4],
                }
            return None
        except PostgresError as e:
            logger.error(f"获取检查点失败: {e}")
            return None

    def complete_checkpoint(self, table_name: str, total_records: int):
        """完成检查点（标记为完成）"""
        query = """
        UPDATE etl_metadata 
        SET 
            sync_status = 'completed',
            processed_records = %s,
            total_records = %s,
            last_sync_timestamp = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        WHERE table_name = %s
        """

        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (total_records, total_records, table_name))
            self.connection.commit()
            cursor.close()
            logger.info(f"完成检查点: {table_name}, 总记录数: {total_records}")
        except PostgresError as e:
            logger.error(f"完成检查点失败: {e}")
            raise

    def clear_checkpoint(self, table_name: str):
        """清除检查点"""
        query = """
        UPDATE etl_metadata 
        SET 
            sync_status = 'pending',
            checkpoint_data = NULL,
            checkpoint_timestamp = NULL,
            processed_records = 0,
            updated_at = CURRENT_TIMESTAMP
        WHERE table_name = %s
        """

        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (table_name,))
            self.connection.commit()
            cursor.close()
            logger.info(f"清除检查点: {table_name}")
        except PostgresError as e:
            logger.error(f"清除检查点失败: {e}")
            raise

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
            notification_id, noti_date, noti_assigned_date,
            noti_closed_date, noti_category_id, sys_eq_id,
            noti_country_id, sys_fl_id, sys_mat_id, sys_serial_id,
            noti_trendcode_l1, noti_trendcode_l2,
            noti_trendcode_l3, notification_medium_text, notification_text
        ) VALUES (
            %(notification_id)s, %(noti_date)s, %(noti_assigned_date)s,
            %(noti_closed_date)s, %(noti_category_id)s, %(sys_eq_id)s,
            %(noti_country_id)s, %(sys_fl_id)s, %(sys_mat_id)s, %(sys_serial_id)s,
            %(noti_trendcode_l1)s, %(noti_trendcode_l2)s,
            %(noti_trendcode_l3)s, %(notification_medium_text)s, %(notification_text)s
        )
        ON CONFLICT (notification_id) 
        DO UPDATE SET
            noti_date = EXCLUDED.noti_date,
            noti_assigned_date = EXCLUDED.noti_assigned_date,
            noti_closed_date = EXCLUDED.noti_closed_date,
            noti_category_id = EXCLUDED.noti_category_id,
            sys_eq_id = EXCLUDED.sys_eq_id,
            noti_country_id = EXCLUDED.noti_country_id,
            sys_fl_id = EXCLUDED.sys_fl_id,
            sys_mat_id = EXCLUDED.sys_mat_id,
            sys_serial_id = EXCLUDED.sys_serial_id,
            noti_trendcode_l1 = EXCLUDED.noti_trendcode_l1,
            noti_trendcode_l2 = EXCLUDED.noti_trendcode_l2,
            noti_trendcode_l3 = EXCLUDED.noti_trendcode_l3,
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

    def upsert_ai_extracted_data(self, records: List[Dict]) -> int:
        """UPSERT AI提取的数据"""
        if not records:
            return 0

        if not self.connection:
            logger.error("数据库连接未建立")
            return 0

        # 构建 UPSERT 查询
        query = """
        INSERT INTO ai_extracted_data (
            notification_id, main_component_ai, primary_symptom_ai,
            root_cause_ai, summary_ai, solution_ai, keywords_ai,
            extraction_timestamp, confidence_score
        ) VALUES (
            %(notification_id)s, %(main_component_ai)s, %(primary_symptom_ai)s,
            %(root_cause_ai)s, %(summary_ai)s, %(solution_ai)s, %(keywords_ai)s,
            %(extraction_timestamp)s, %(confidence_score)s
        )
        ON CONFLICT (notification_id) 
        DO UPDATE SET
            main_component_ai = EXCLUDED.main_component_ai,
            primary_symptom_ai = EXCLUDED.primary_symptom_ai,
            root_cause_ai = EXCLUDED.root_cause_ai,
            summary_ai = EXCLUDED.summary_ai,
            solution_ai = EXCLUDED.solution_ai,
            keywords_ai = EXCLUDED.keywords_ai,
            extraction_timestamp = EXCLUDED.extraction_timestamp,
            confidence_score = EXCLUDED.confidence_score
        """

        try:
            cursor = self.connection.cursor()
            cursor.executemany(query, records)
            self.connection.commit()
            cursor.close()

            processed_count = len(records)
            logger.info(f"AI数据 UPSERT 完成，处理了 {processed_count} 条记录")
            return processed_count

        except PostgresError as e:
            logger.error(f"AI数据 UPSERT 失败: {e}")
            self.connection.rollback()
            raise

    def upsert_semantic_embeddings(self, records: List[Dict]) -> int:
        """UPSERT 语义嵌入数据"""
        if not records:
            return 0

        if not self.connection:
            logger.error("数据库连接未建立")
            return 0

        # 构建 UPSERT 查询
        query = """
        INSERT INTO semantic_embeddings (
            notification_id, embedding_vector, embedding_model,
            created_at
        ) VALUES (
            %(notification_id)s, %(embedding_vector)s, %(embedding_model)s,
            %(created_at)s
        )
        ON CONFLICT (notification_id) 
        DO UPDATE SET
            embedding_vector = EXCLUDED.embedding_vector,
            embedding_model = EXCLUDED.embedding_model,
            created_at = EXCLUDED.created_at
        """

        try:
            cursor = self.connection.cursor()
            cursor.executemany(query, records)
            self.connection.commit()
            cursor.close()

            processed_count = len(records)
            logger.info(f"嵌入数据 UPSERT 完成，处理了 {processed_count} 条记录")
            return processed_count

        except PostgresError as e:
            logger.error(f"嵌入数据 UPSERT 失败: {e}")
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
                elif table_name == "ai_extracted_data":
                    processed = self.upsert_ai_extracted_data(batch)
                elif table_name == "semantic_embeddings":
                    processed = self.upsert_semantic_embeddings(batch)
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
