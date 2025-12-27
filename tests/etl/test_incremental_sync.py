import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from src.etl.incremental_sync import IncrementalSync
from src.utils.config import Config, SnowflakeConfig, PostgresConfig, ETLConfig


class TestIncrementalSync:
    """测试增量同步器"""

    def setup_method(self):
        """测试设置"""
        self.config = Config(
            snowflake=SnowflakeConfig(
                account="test-account",
                user="test-user",
                password="test-password",
                authenticator="snowflake",
                warehouse="test-warehouse",
                database="test-database",
                schema="test-schema",
                role=None,
            ),
            postgres=PostgresConfig(
                host="localhost",
                port=5432,
                user="test-user",
                password="test-password",
                database="test-db",
            ),
            etl=ETLConfig(
                batch_size=1000,
                max_retries=3,
                retry_delay=5,
                watermark_table="etl_metadata",
            ),
        )
        self.sync = IncrementalSync(self.config)

    @patch("src.etl.incremental_sync.SnowflakeClient")
    @patch("src.etl.incremental_sync.PostgresWriter")
    def test_sync_table_success(self, mock_postgres_writer, mock_snowflake_client):
        """测试成功同步表"""
        # 模拟 Snowflake 客户端
        mock_sf_client = Mock()
        mock_sf_client.test_connection.return_value = True
        mock_sf_client.get_incremental_data.return_value = [
            {
                "notification_id": 1,
                "notification_date": "2024-01-01 00:00:00",
                "notification_text": "Test notification",
            }
        ]
        mock_snowflake_client.return_value.__enter__.return_value = mock_sf_client

        # 模拟 PostgreSQL 写入器
        mock_pg_writer = Mock()
        mock_pg_writer.get_last_extraction_time.return_value = None
        mock_pg_writer.batch_upsert.return_value = 1
        mock_postgres_writer.return_value.__enter__.return_value = mock_pg_writer

        # 测试同步
        result = self.sync.sync_table("notification_text")

        # 验证
        assert result is True
        mock_sf_client.test_connection.assert_called_once()
        mock_pg_writer.create_etl_metadata_table.assert_called_once()
        mock_pg_writer.get_last_extraction_time.assert_called_once_with(
            "notification_text"
        )
        mock_sf_client.get_incremental_data.assert_called_once()
        mock_pg_writer.batch_upsert.assert_called_once()

    @patch("src.etl.incremental_sync.SnowflakeClient")
    @patch("src.etl.incremental_sync.PostgresWriter")
    def test_sync_table_no_new_data(self, mock_postgres_writer, mock_snowflake_client):
        """测试同步表（无新数据）"""
        # 模拟 Snowflake 客户端
        mock_sf_client = Mock()
        mock_sf_client.test_connection.return_value = True
        mock_sf_client.get_incremental_data.return_value = []
        mock_snowflake_client.return_value.__enter__.return_value = mock_sf_client

        # 模拟 PostgreSQL 写入器
        mock_pg_writer = Mock()
        mock_pg_writer.get_last_extraction_time.return_value = "2024-01-01 00:00:00"
        mock_postgres_writer.return_value.__enter__.return_value = mock_pg_writer

        # 测试同步
        result = self.sync.sync_table("notification_text")

        # 验证
        assert result is True
        mock_pg_writer.batch_upsert.assert_not_called()

    @patch("src.etl.incremental_sync.SnowflakeClient")
    @patch("src.etl.incremental_sync.PostgresWriter")
    def test_sync_table_connection_failure(
        self, mock_postgres_writer, mock_snowflake_client
    ):
        """测试同步表（连接失败）"""
        # 模拟 Snowflake 客户端连接失败
        mock_sf_client = Mock()
        mock_sf_client.test_connection.return_value = False
        mock_snowflake_client.return_value.__enter__.return_value = mock_sf_client

        # 模拟 PostgreSQL 写入器
        mock_pg_writer = Mock()
        mock_postgres_writer.return_value.__enter__.return_value = mock_pg_writer

        # 测试同步
        result = self.sync.sync_table("notification_text")

        # 验证
        assert result is False

    @patch.object(IncrementalSync, "sync_table")
    def test_run_success(self, mock_sync_table):
        """测试运行成功"""
        # 模拟同步表成功
        mock_sync_table.return_value = True

        # 测试运行
        result = self.sync.run(["notification_text"])

        # 验证
        assert result is True
        mock_sync_table.assert_called_once_with("notification_text")

    @patch.object(IncrementalSync, "sync_table")
    def test_run_partial_failure(self, mock_sync_table):
        """测试运行部分失败"""
        # 模拟同步表部分成功
        mock_sync_table.side_effect = [True, False]

        # 测试运行
        result = self.sync.run(["table1", "table2"])

        # 验证
        assert result is False
        assert mock_sync_table.call_count == 2

    def test_metrics_collection(self):
        """测试指标收集"""
        # 开始指标收集
        self.sync.metrics.start()

        # 记录一些指标
        self.sync.metrics.record_processed(10)
        self.sync.metrics.record_error(1)
        self.sync.metrics.record_batch()

        # 停止指标收集
        self.sync.metrics.stop()

        # 获取摘要
        summary = self.sync.metrics.get_summary()

        # 验证
        assert summary["records_processed"] == 10
        assert summary["errors"] == 1
        assert summary["batches_processed"] == 1
        # 持续时间可能为0，因为测试运行太快
        assert summary["duration_seconds"] >= 0
