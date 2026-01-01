#!/usr/bin/env python3
"""
灵活的Snowflake数据拉取工具
支持多种认证方式和配置选项
"""

import argparse
import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

import snowflake.connector
from snowflake.connector.errors import Error as SnowflakeError

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FlexibleSnowflakePuller:
    """灵活的Snowflake数据拉取器"""

    def __init__(
        self,
        account: str,
        user: str,
        password: Optional[str] = None,
        authenticator: str = "snowflake",
        warehouse: str = "WH_SDTB_INT_XP_DC_R",
        database: str = "SDM_PROD",
        schema: str = "public",
        role: Optional[str] = None
    ):
        """初始化连接参数"""
        self.account = account
        self.user = user
        self.password = password
        self.authenticator = authenticator
        self.warehouse = warehouse
        self.database = database
        self.schema = schema
        self.role = role
        self.connection = None

        logger.info(f"初始化Snowflake连接器: account={account}, user={user}")

    def connect(self) -> bool:
        """连接到Snowflake"""
        try:
            logger.info(f"正在连接到 Snowflake: {self.account}")

            # 构建连接参数
            conn_params = {
                "account": self.account,
                "user": self.user,
                "authenticator": self.authenticator,
                "warehouse": self.warehouse,
                "database": self.database,
                "schema": self.schema,
            }

            # 添加密码（如果提供）
            if self.password:
                conn_params["password"] = self.password

            # 添加角色（如果提供）
            if self.role:
                conn_params["role"] = self.role

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
            logger.info(f"查询成功，返回 {len(results)} 条记录")
            return results

        except SnowflakeError as e:
            logger.error(f"查询执行失败: {e}")
            raise
        except Exception as e:
            logger.error(f"查询时发生意外错误: {e}")
            raise

    def list_tables(self) -> List[str]:
        """列出所有表"""
        query = f"""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = %(schema)s
        AND table_type = 'BASE TABLE'
        ORDER BY table_name
        """

        params = {"schema": self.schema.upper()}
        results = self.execute_query(query, params)
        return [row["TABLE_NAME"] for row in results]

    def get_table_sample(self, table_name: str, limit: int = 10) -> List[Dict]:
        """获取表数据样本"""
        query = f"SELECT * FROM {table_name} LIMIT %(limit)s"
        params = {"limit": limit}
        return self.execute_query(query, params)

    def export_to_csv(self, data: List[Dict], output_path: str):
        """导出数据到CSV文件"""
        if not data:
            logger.warning("没有数据可导出")
            return

        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        # 获取所有字段名
        fieldnames = list(data[0].keys())

        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

        logger.info(f"数据已导出到: {output_path} ({len(data)} 条记录)")

    def export_to_json(self, data: List[Dict], output_path: str):
        """导出数据到JSON文件"""
        if not data:
            logger.warning("没有数据可导出")
            return

        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, indent=2, default=str)

        logger.info(f"数据已导出到: {output_path} ({len(data)} 条记录)")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()


def read_query_from_file(file_path: str) -> str:
    """从文件读取SQL查询"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        logger.error(f"读取查询文件失败: {e}")
        raise


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='灵活的Snowflake数据拉取工具')

    # 连接参数
    parser.add_argument('--account', type=str, help='Snowflake账户')
    parser.add_argument('--user', type=str, help='用户名')
    parser.add_argument('--password', type=str, help='密码（可选）')
    parser.add_argument('--authenticator', type=str, default='snowflake',
                       help='认证方式: snowflake, externalbrowser, oauth')
    parser.add_argument('--warehouse', type=str, default='WH_SDTB_INT_XP_DC_R',
                       help='仓库名称')
    parser.add_argument('--database', type=str, default='SDM_PROD',
                       help='数据库名称')
    parser.add_argument('--schema', type=str, default='public',
                       help='模式名称')
    parser.add_argument('--role', type=str, help='角色名称（可选）')

    # 查询选项
    query_group = parser.add_mutually_exclusive_group(required=True)
    query_group.add_argument('--query', type=str, help='直接SQL查询')
    query_group.add_argument('--file', type=str, help='包含SQL查询的文件路径')
    query_group.add_argument('--list-tables', action='store_true', help='列出所有表')
    query_group.add_argument('--sample', type=str, help='获取表数据样本')

    # 输出选项
    parser.add_argument('--output', type=str, help='输出文件路径')
    parser.add_argument('--format', choices=['csv', 'json'], default='csv',
                       help='输出格式')
    parser.add_argument('--limit', type=int, help='限制返回记录数')

    args = parser.parse_args()

    # 从环境变量获取缺失的参数
    account = args.account or os.getenv('SNOWFLAKE_ACCOUNT', 'yu83356')
    user = args.user or os.getenv('SNOWFLAKE_USER', 'linwei.he@siemens-healthineers.com')
    password = args.password or os.getenv('SNOWFLAKE_PASSWORD')
    authenticator = args.authenticator or os.getenv('SNOWFLAKE_AUTHENTICATOR', 'snowflake')
    warehouse = args.warehouse or os.getenv('SNOWFLAKE_WAREHOUSE', 'WH_SDTB_INT_XP_DC_R')
    database = args.database or os.getenv('SNOWFLAKE_DATABASE', 'SDM_PROD')
    schema = args.schema or os.getenv('SNOWFLAKE_SCHEMA', 'public')
    role = args.role or os.getenv('SNOWFLAKE_ROLE')

    try:
        # 创建拉取器
        puller = FlexibleSnowflakePuller(
            account=account,
            user=user,
            password=password,
            authenticator=authenticator,
            warehouse=warehouse,
            database=database,
            schema=schema,
            role=role
        )

        with puller:
            data = []

            if args.list_tables:
                # 列出所有表
                tables = puller.list_tables()
                print(f"找到 {len(tables)} 个表:")
                for table in tables:
                    print(f"  - {table}")
                return

            elif args.sample:
                # 获取表数据样本
                data = puller.get_table_sample(args.sample, args.limit or 10)

            else:
                # 执行自定义查询
                if args.file:
                    query = read_query_from_file(args.file)
                else:
                    query = args.query

                params = {"limit": args.limit} if args.limit else None
                data = puller.execute_query(query, params)

            # 输出结果
            if args.output:
                # 导出到文件
                if args.format == 'csv':
                    puller.export_to_csv(data, args.output)
                else:
                    puller.export_to_json(data, args.output)
            else:
                # 打印到控制台
                if data:
                    print(f"查询结果 ({len(data)} 条记录):")
                    for i, row in enumerate(data[:5], 1):  # 只显示前5条
                        print(f"\n记录 {i}:")
                        for key, value in row.items():
                            print(f"  {key}: {value}")

                    if len(data) > 5:
                        print(f"\n... 还有 {len(data) - 5} 条记录未显示")
                else:
                    print("查询返回空结果")

    except Exception as e:
        logger.error(f"执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()