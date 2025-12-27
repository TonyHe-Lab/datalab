import logging
from typing import Dict, List, Optional, Any
import snowflake.connector
from snowflake.connector.errors import Error as SnowflakeError

from src.utils.config import SnowflakeConfig

logger = logging.getLogger(__name__)


class SnowflakeClient:
    """Snowflake 客户端"""

    def __init__(self, config: SnowflakeConfig):
        self.config = config
        self.connection: Optional[snowflake.connector.SnowflakeConnection] = None

    def connect(self) -> bool:
        """连接到 Snowflake"""
        try:
            logger.info(f"正在连接到 Snowflake: {self.config.account}")

            # 构建连接参数
            conn_params = {
                "account": self.config.account,
                "user": self.config.user,
                "warehouse": self.config.warehouse,
                "database": self.config.database,
                "schema": self.config.schema,
                "authenticator": self.config.authenticator,
            }

            # 添加密码（如果提供）
            if self.config.password:
                conn_params["password"] = self.config.password

            # 添加角色（如果提供）
            if self.config.role:
                conn_params["role"] = self.config.role

            # 建立连接
            self.connection = snowflake.connector.connect(**conn_params)

            # 测试连接
            cursor = self.connection.cursor()
            cursor.execute("SELECT CURRENT_VERSION()")
            version = cursor.fetchone()[0]
            cursor.close()

            logger.info(f"Snowflake 连接成功，版本: {version}")
            return True

        except SnowflakeError as e:
            logger.error(f"Snowflake 连接失败: {e}")
            return False
        except Exception as e:
            logger.error(f"连接时发生意外错误: {e}")
            return False

    def disconnect(self):
        """断开连接"""
        if self.connection:
            try:
                self.connection.close()
                logger.info("Snowflake 连接已关闭")
            except Exception as e:
                logger.error(f"关闭连接时出错: {e}")
            finally:
                self.connection = None

    def test_connection(self) -> bool:
        """测试连接"""
        try:
            if not self.connection:
                return self.connect()

            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()[0]
            cursor.close()

            return result == 1

        except SnowflakeError as e:
            logger.error(f"连接测试失败: {e}")
            return False

    def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """执行查询并返回结果"""
        if not self.connection:
            if not self.connect():
                raise ConnectionError("无法连接到 Snowflake")

        try:
            cursor = self.connection.cursor()

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            # 获取列名
            columns = [desc[0] for desc in cursor.description]

            # 获取结果
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))

            cursor.close()
            return results

        except SnowflakeError as e:
            logger.error(f"查询执行失败: {e}")
            raise

    def get_incremental_data(
        self,
        table_name: str,
        watermark_column: str,
        last_extraction: Optional[str] = None,
    ) -> List[Dict]:
        """获取增量数据"""
        query = f"""
        SELECT * 
        FROM {table_name}
        WHERE {watermark_column} > %(last_extraction)s
        ORDER BY {watermark_column} ASC
        """

        params = {"last_extraction": last_extraction or "1970-01-01 00:00:00"}

        return self.execute_query(query, params)

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
