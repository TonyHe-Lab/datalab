"""
PostgreSQL Writer with Connection Pool Support.

This module extends the PostgresWriter with connection pooling capabilities
for improved performance in parallel processing scenarios.
"""

import logging
from typing import List, Dict, Optional, Any
import psycopg2
import psycopg2.extras
import psycopg2.pool
from psycopg2 import Error as PostgresError
from contextlib import contextmanager

from src.utils.config import PostgresConfig
from src.utils.batch_optimizer import BatchOptimizer, BulkInsertStrategy, TransactionManager

logger = logging.getLogger(__name__)


class PostgresWriterPool:
    """PostgreSQL writer with connection pooling."""

    def __init__(self, config: PostgresConfig, pool_size: int = 10):
        self.config = config
        self.pool_size = pool_size
        self.connection_pool: Optional[psycopg2.pool.SimpleConnectionPool] = None
        self.batch_optimizer = BatchOptimizer()

            # Build connection string
            conn_str = (
                f"host={self.config.host} "
                f"port={self.config.port} "
                f"dbname={self.config.database} "
                f"user={self.config.user} "
                f"password={self.config.password}"
            )

            # Create connection pool
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                1,  # Minimum connections
                self.pool_size,  # Maximum connections
                conn_str,
            )

            # Test the pool
            test_conn = self.connection_pool.getconn()
            self.connection_pool.putconn(test_conn)

            logger.info("PostgreSQL connection pool initialized successfully")
            return True

        except PostgresError as e:
            logger.error(f"Failed to initialize PostgreSQL connection pool: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error initializing connection pool: {e}")
            return False

    @contextmanager
    def get_connection(self):
        """Get a connection from the pool (context manager)."""
        if not self.connection_pool:
            raise RuntimeError("Connection pool not initialized")

        conn = None
        try:
            conn = self.connection_pool.getconn()
            yield conn
        finally:
            if conn:
                self.connection_pool.putconn(conn)

    def close_pool(self):
        """Close all connections in the pool."""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("PostgreSQL connection pool closed")

    def __enter__(self):
        """Context manager entry."""
        self.initialize_pool()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close_pool()

    # ========== 数据写入方法（使用连接池） ==========

    def upsert_notification_text(self, records: List[Dict]) -> int:
        """UPSERT notification text data using connection pool."""
        if not records:
            return 0

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Build UPSERT query
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
                cursor.executemany(query, records)
                conn.commit()

                processed_count = len(records)
                logger.debug(f"UPSERT完成，处理了 {processed_count} 条记录")
                return processed_count

            except PostgresError as e:
                conn.rollback()
                logger.error(f"UPSERT失败: {e}")
                raise
            finally:
                cursor.close()

    def upsert_ai_extracted_data(self, records: List[Dict]) -> int:
        """UPSERT AI extracted data using connection pool."""
        if not records:
            return 0

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Build UPSERT query
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
                cursor.executemany(query, records)
                conn.commit()

                processed_count = len(records)
                logger.debug(f"AI数据 UPSERT 完成，处理了 {processed_count} 条记录")
                return processed_count

            except PostgresError as e:
                conn.rollback()
                logger.error(f"AI数据 UPSERT 失败: {e}")
                raise
            finally:
                cursor.close()

    def upsert_semantic_embeddings(self, records: List[Dict]) -> int:
        """UPSERT semantic embeddings using connection pool."""
        if not records:
            return 0

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Build UPSERT query
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
                cursor.executemany(query, records)
                conn.commit()

                processed_count = len(records)
                logger.debug(f"嵌入数据 UPSERT 完成，处理了 {processed_count} 条记录")
                return processed_count

            except PostgresError as e:
                conn.rollback()
                logger.error(f"嵌入数据 UPSERT 失败: {e}")
                raise
            finally:
                cursor.close()

    # ========== 检查点功能（使用连接池） ==========

    def create_checkpoint(
        self,
        table_name: str,
        checkpoint_data: Dict[str, Any],
        processed_records: int,
        total_records: int = 0,
        batch_size: int = 1000,
    ):
        """Create or update checkpoint using connection pool."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

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
                conn.commit()
                logger.debug(
                    f"创建检查点: {table_name}, 已处理: {processed_records}/{total_records}"
                )
            except PostgresError as e:
                conn.rollback()
                logger.error(f"创建检查点失败: {e}")
                raise
            finally:
                cursor.close()

    def get_checkpoint(self, table_name: str) -> Optional[Dict[str, Any]]:
        """Get checkpoint data using connection pool."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

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
                cursor.execute(query, (table_name,))
                result = cursor.fetchone()

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
            finally:
                cursor.close()

    def complete_checkpoint(self, table_name: str, total_records: int):
        """Complete checkpoint using connection pool."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

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
                cursor.execute(query, (total_records, total_records, table_name))
                conn.commit()
                logger.info(f"完成检查点: {table_name}, 总记录数: {total_records}")
            except PostgresError as e:
                conn.rollback()
                logger.error(f"完成检查点失败: {e}")
                raise
            finally:
                cursor.close()

    def clear_checkpoint(self, table_name: str):
        """Clear checkpoint using connection pool."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

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
                cursor.execute(query, (table_name,))
                conn.commit()
                logger.info(f"清除检查点: {table_name}")
            except PostgresError as e:
                conn.rollback()
                logger.error(f"清除检查点失败: {e}")
                raise
            finally:
                cursor.close()

    def batch_upsert(
        self, table_name: str, records: List[Dict], batch_size: int = 1000
    ) -> int:
        """Batch UPSERT using connection pool."""
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
                    raise ValueError(f"不支持的表格: {table_name}")

                total_processed += processed
                logger.debug(
                    f"批次 {i // batch_size + 1} 完成，处理了 {processed} 条记录"
                )

            except Exception as e:
                logger.error(f"批次 {i // batch_size + 1} 处理失败: {e}")
                raise

        return total_processed
