import pytest
from unittest.mock import Mock, patch, MagicMock
from src.utils.config import PostgresConfig
from src.etl.postgres_writer import PostgresWriter


class TestPostgresWriter:
    """测试 PostgreSQL 写入器"""

    def setup_method(self):
        """测试设置"""
        self.config = PostgresConfig(
            host="localhost",
            port=5432,
            user="test-user",
            password="test-password",
            database="test-db",
        )
        self.writer = PostgresWriter(self.config)

    @patch("psycopg.connect")
    def test_connect_success(self, mock_connect):
        """测试成功连接"""
        # 模拟连接
        mock_conn = Mock()
        mock_connect.return_value = mock_conn

        # 测试连接
        result = self.writer.connect()

        # 验证
        assert result is True
        assert self.writer.connection is mock_conn
        mock_connect.assert_called_once()

    @patch("psycopg.connect")
    def test_connect_failure(self, mock_connect):
        """测试连接失败"""
        # 模拟连接失败
        mock_connect.side_effect = Exception("Connection failed")

        # 测试连接
        result = self.writer.connect()

        # 验证
        assert result is False
        assert self.writer.connection is None

    def test_disconnect(self):
        """测试断开连接"""
        # 模拟连接
        mock_conn = Mock()
        self.writer.connection = mock_conn

        # 测试断开连接
        self.writer.disconnect()

        # 验证
        mock_conn.close.assert_called_once()
        assert self.writer.connection is None

    @patch.object(PostgresWriter, "connect")
    def test_create_etl_metadata_table(self, mock_connect):
        """测试创建 ETL 元数据表"""
        # 模拟连接和游标
        mock_conn = Mock()
        mock_cursor = Mock()
        # 使用简单的 cursor 模拟
        mock_conn.cursor.return_value = mock_cursor
        self.writer.connection = mock_conn

        # 测试创建表
        self.writer.create_etl_metadata_table()

        # 验证
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()

    @patch.object(PostgresWriter, "connect")
    def test_get_last_extraction_time(self, mock_connect):
        """测试获取最后提取时间"""
        # 模拟连接和游标
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = ["2024-01-01 00:00:00"]
        mock_conn.cursor.return_value = mock_cursor
        self.writer.connection = mock_conn

        # 测试获取时间
        result = self.writer.get_last_extraction_time("test_table")

        # 验证
        assert result == "2024-01-01 00:00:00"
        mock_cursor.execute.assert_called_once()

    @patch.object(PostgresWriter, "connect")
    def test_get_last_extraction_time_none(self, mock_connect):
        """测试获取最后提取时间（无记录）"""
        # 模拟连接和游标
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        mock_conn.cursor.return_value = mock_cursor
        self.writer.connection = mock_conn

        # 测试获取时间
        result = self.writer.get_last_extraction_time("test_table")

        # 验证
        assert result is None

    def test_context_manager(self):
        """测试上下文管理器"""
        with (
            patch.object(self.writer, "connect") as mock_connect,
            patch.object(self.writer, "disconnect") as mock_disconnect,
        ):
            mock_connect.return_value = True

            # 使用上下文管理器
            with self.writer:
                pass

            # 验证
            mock_connect.assert_called_once()
            mock_disconnect.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
