#!/usr/bin/env python3
"""
Snowflake 连接测试脚本
测试与Snowflake数据仓库的连接
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config import load_config, validate_config
from src.etl.snowflake_loader import SnowflakeClient


def test_connection():
    """测试Snowflake连接"""
    print("🔍 开始测试Snowflake连接...")

    try:
        # 加载配置
        print("1. 加载配置...")
        config = load_config()

        # 验证配置
        print("2. 验证配置...")
        validate_config(config)

        print(f"   Snowflake账户: {config.snowflake.account}")
        print(f"   用户: {config.snowflake.user}")
        print(f"   数据库: {config.snowflake.database}")
        print(f"   模式: {config.snowflake.schema}")
        print(f"   仓库: {config.snowflake.warehouse}")
        print(f"   认证方式: {config.snowflake.authenticator}")

        # 创建客户端
        print("3. 创建Snowflake客户端...")
        client = SnowflakeClient(config.snowflake)

        # 测试连接
        print("4. 测试连接...")
        if client.connect():
            print("✅ Snowflake连接成功!")

            # 获取版本信息
            print("5. 获取数据库信息...")
            try:
                cursor = client.connection.cursor()

                # 测试查询
                cursor.execute("SELECT CURRENT_VERSION()")
                version = cursor.fetchone()[0]
                print(f"   Snowflake版本: {version}")

                cursor.execute("SELECT CURRENT_DATABASE(), CURRENT_SCHEMA()")
                db, schema = cursor.fetchone()
                print(f"   当前数据库: {db}")
                print(f"   当前模式: {schema}")

                cursor.execute("SELECT CURRENT_WAREHOUSE()")
                warehouse = cursor.fetchone()[0]
                print(f"   当前仓库: {warehouse}")

                cursor.execute("SELECT CURRENT_ROLE()")
                role = cursor.fetchone()[0]
                print(f"   当前角色: {role}")

                cursor.close()

                # 列出表
                print("6. 列出可用表...")
                query = f"""
                SELECT table_name, row_count, bytes
                FROM information_schema.tables
                WHERE table_schema = %(schema)s
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
                """

                params = {"schema": config.snowflake.schema.upper()}
                tables = client.execute_query(query, params)

                if tables:
                    print(f"   找到 {len(tables)} 个表:")
                    for table in tables[:10]:  # 只显示前10个
                        print(f"     - {table['TABLE_NAME']} ({table['ROW_COUNT']} 行)")

                    if len(tables) > 10:
                        print(f"     ... 还有 {len(tables) - 10} 个表未显示")
                else:
                    print("   ⚠️ 未找到表，请检查模式名称")

                # 断开连接
                client.disconnect()
                print("✅ 连接测试完成!")
                return True

            except Exception as e:
                print(f"❌ 查询执行失败: {e}")
                return False
        else:
            print("❌ Snowflake连接失败!")
            return False

    except ValueError as e:
        print(f"❌ 配置验证失败: {e}")
        print("请检查 config/.env 文件中的Snowflake配置")
        return False
    except Exception as e:
        print(f"❌ 连接测试失败: {e}")
        return False


def test_simple_query():
    """测试简单查询"""
    print("\n🔍 测试简单查询...")

    try:
        config = load_config()
        client = SnowflakeClient(config.snowflake)

        if client.connect():
            # 执行简单查询
            query = "SELECT 1 as test_value, CURRENT_TIMESTAMP() as current_time"
            results = client.execute_query(query)

            if results:
                print("✅ 查询执行成功!")
                print(f"   结果: {results[0]}")

            client.disconnect()
            return True
        else:
            print("❌ 连接失败，无法执行查询")
            return False

    except Exception as e:
        print(f"❌ 查询测试失败: {e}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("Snowflake 连接测试工具")
    print("=" * 60)

    # 测试连接
    connection_ok = test_connection()

    if connection_ok:
        # 测试查询
        query_ok = test_simple_query()

        if query_ok:
            print("\n" + "=" * 60)
            print("✅ 所有测试通过!")
            print("Snowflake连接和查询功能正常")
            print("=" * 60)
            return 0
        else:
            print("\n" + "=" * 60)
            print("⚠️ 连接成功但查询失败")
            print("请检查数据库权限和查询语法")
            print("=" * 60)
            return 1
    else:
        print("\n" + "=" * 60)
        print("❌ 连接测试失败")
        print("请检查以下内容:")
        print("1. Snowflake账户配置")
        print("2. 网络连接")
        print("3. 认证方式设置")
        print("4. 用户权限")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())