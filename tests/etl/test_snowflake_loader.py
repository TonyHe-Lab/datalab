import pytest
from unittest.mock import Mock, patch, MagicMock
from src.utils.config import SnowflakeConfig
from src.etl.snowflake_loader import SnowflakeClient


class TestSnowflakeClient:
    """测试 Snowflake 客户端"""

    def setup_method(self):
        """测试设置"""
        self.config = SnowflakeConfig(
            account="test-account",
            user="test-user",
            password="test-password",
            authenticator="snowflake",
            warehouse="test-warehouse",
            database="test-database",
            schema="test-schema",
            role="test-role",
        )
        self.client = SnowflakeClient(self.config)

    @patch("snowflake.connector.connect")
    def test_connect_success(self, mock_connect):
        """测试成功连接"""
        # 模拟连接
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = ["3.0.0"]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # 测试连接
        result = self.client.connect()

        # 验证
        assert result is True
        assert self.client.connection is mock_conn
        mock_connect.assert_called_once()

    @patch("snowflake.connector.connect")
    def test_connect_failure(self, mock_connect):
        """测试连接失败"""
        # 模拟连接失败
        mock_connect.side_effect = Exception("Connection failed")

        # 测试连接
        result = self.client.connect()

        # 验证
        assert result is False
        assert self.client.connection is None

    def test_disconnect(self):
        """测试断开连接"""
        # 模拟连接
        mock_conn = Mock()
        self.client.connection = mock_conn

        # 测试断开连接
        self.client.disconnect()

        # 验证
        mock_conn.close.assert_called_once()
        assert self.client.connection is None

    def test_disconnect_no_connection(self):
        """测试断开连接（无连接）"""
        # 测试断开连接
        self.client.disconnect()

        # 验证没有异常
        assert self.client.connection is None

    @patch.object(SnowflakeClient, "connect")
    def test_test_connection_success(self, mock_connect):
        """测试连接测试成功"""
        # 模拟连接和游标
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = [1]
        mock_conn.cursor.return_value = mock_cursor
        self.client.connection = mock_conn

        # 测试连接测试
        result = self.client.test_connection()

        # 验证
        assert result is True
        mock_connect.assert_not_called()

    @patch.object(SnowflakeClient, "connect")
    def test_test_connection_failure(self, mock_connect):
        """测试连接测试失败"""
        # 模拟连接失败
        mock_connect.return_value = False
        self.client.connection = None

        # 测试连接测试
        result = self.client.test_connection()

        # 验证
        assert result is False
        mock_connect.assert_called_once()

    def test_context_manager(self):
        """测试上下文管理器"""
        with (
            patch.object(self.client, "connect") as mock_connect,
            patch.object(self.client, "disconnect") as mock_disconnect,
        ):
            mock_connect.return_value = True

            # 使用上下文管理器
            with self.client:
                pass

            # 验证
            mock_connect.assert_called_once()
            mock_disconnect.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
