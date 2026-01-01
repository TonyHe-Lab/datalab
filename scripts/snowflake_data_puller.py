#!/usr/bin/env python3
"""
Snowflake 生产数据拉取工具

这个脚本用于从Snowflake数据仓库拉取生产数据。
支持自定义SQL查询、数据导出和增量数据提取。

使用方法:
    python snowflake_data_puller.py --query "SELECT * FROM table LIMIT 10"
    python snowflake_data_puller.py --file query.sql --output data.csv
    python snowflake_data_puller.py --incremental --table maintenance_logs --watermark updated_at
"""

import argparse
import csv
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config import load_config, validate_config
from src.etl.snowflake_loader import SnowflakeClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SnowflakeDataPuller:
    """Snowflake 数据拉取器"""

    def __init__(self):
        """初始化配置和客户端"""
        try:
            self.config = load_config()
            validate_config(self.config)
            self.client = SnowflakeClient(self.config.snowflake)
            logger.info("Snowflake 数据拉取器初始化成功")
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            raise

    def connect(self) -> bool:
        """连接到 Snowflake"""
        return self.client.connect()

    def disconnect(self):
        """断开连接"""
        self.client.disconnect()

    def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """执行SQL查询"""
        logger.info(f"执行查询: {query[:100]}...")
        try:
            results = self.client.execute_query(query, params)
            logger.info(f"查询成功，返回 {len(results)} 条记录")
            return results
        except Exception as e:
            logger.error(f"查询执行失败: {e}")
            raise

    def get_table_schema(self, table_name: str) -> List[Dict]:
        """获取表结构信息"""
        query = f"""
        SELECT
            column_name,
            data_type,
            is_nullable,
            column_default,
            ordinal_position
        FROM information_schema.columns
        WHERE table_name = %(table_name)s
        AND table_schema = %(schema)s
        ORDER BY ordinal_position
        """

        params = {
            "table_name": table_name.upper(),
            "schema": self.config.snowflake.schema.upper()
        }

        return self.execute_query(query, params)

    def list_tables(self) -> List[str]:
        """列出所有表"""
        query = f"""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = %(schema)s
        AND table_type = 'BASE TABLE'
        ORDER BY table_name
        """

        params = {"schema": self.config.snowflake.schema.upper()}
        results = self.execute_query(query, params)
        return [row["TABLE_NAME"] for row in results]

    def get_table_sample(self, table_name: str, limit: int = 10) -> List[Dict]:
        """获取表数据样本"""
        query = f"SELECT * FROM {table_name} LIMIT %(limit)s"
        params = {"limit": limit}
        return self.execute_query(query, params)

    def get_incremental_data(
        self,
        table_name: str,
        watermark_column: str,
        last_extraction: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """获取增量数据"""
        base_query = f"""
        SELECT *
        FROM {table_name}
        WHERE {watermark_column} > %(last_extraction)s
        ORDER BY {watermark_column} ASC
        """

        if limit:
            base_query += f" LIMIT {limit}"

        params = {"last_extraction": last_extraction or "1970-01-01 00:00:00"}

        return self.execute_query(base_query, params)

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
    parser = argparse.ArgumentParser(description='从Snowflake拉取生产数据')

    # 查询选项
    query_group = parser.add_mutually_exclusive_group(required=True)
    query_group.add_argument('--query', type=str, help='直接SQL查询')
    query_group.add_argument('--file', type=str, help='包含SQL查询的文件路径')
    query_group.add_argument('--list-tables', action='store_true', help='列出所有表')
    query_group.add_argument('--schema', type=str, help='获取表结构信息')
    query_group.add_argument('--sample', type=str, help='获取表数据样本')
    query_group.add_argument('--incremental', action='store_true', help='增量数据提取')

    # 增量数据选项
    parser.add_argument('--table', type=str, help='表名（用于增量提取）')
    parser.add_argument('--watermark', type=str, help='水位列名（用于增量提取）')
    parser.add_argument('--last-extraction', type=str, help='上次提取时间戳')

    # 输出选项
    parser.add_argument('--output', type=str, help='输出文件路径')
    parser.add_argument('--format', choices=['csv', 'json'], default='csv', help='输出格式')
    parser.add_argument('--limit', type=int, help='限制返回记录数')

    args = parser.parse_args()

    try:
        with SnowflakeDataPuller() as puller:
            data = []

            if args.list_tables:
                # 列出所有表
                tables = puller.list_tables()
                print(f"找到 {len(tables)} 个表:")
                for table in tables:
                    print(f"  - {table}")
                return

            elif args.schema:
                # 获取表结构
                schema_info = puller.get_table_schema(args.schema)
                print(f"表 '{args.schema}' 结构:")
                for col in schema_info:
                    print(f"  {col['ORDINAL_POSITION']}. {col['COLUMN_NAME']} ({col['DATA_TYPE']}) "
                          f"{'NULL' if col['IS_NULLABLE'] == 'YES' else 'NOT NULL'}")
                return

            elif args.sample:
                # 获取表数据样本
                data = puller.get_table_sample(args.sample, args.limit or 10)

            elif args.incremental:
                # 增量数据提取
                if not args.table or not args.watermark:
                    parser.error("增量提取需要 --table 和 --watermark 参数")

                data = puller.get_incremental_data(
                    table_name=args.table,
                    watermark_column=args.watermark,
                    last_extraction=args.last_extraction,
                    limit=args.limit
                )

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