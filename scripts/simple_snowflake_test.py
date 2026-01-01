#!/usr/bin/env python3
"""
简单的Snowflake连接测试
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 手动设置环境变量（如果.env文件有问题）
os.environ.update({
    "SNOWFLAKE_ACCOUNT": "yu83356.west-europe.azure.snowflakecomputing.com",
    "SNOWFLAKE_USER": "linwei.he@siemens-healthineers.com",
    "SNOWFLAKE_AUTHENTICATOR": "externalbrowser",
    "SNOWFLAKE_WAREHOUSE": "WH_SDTB_INT_XP_DC_R",
    "SNOWFLAKE_DATABASE": "SDM_PROD",
    "SNOWFLAKE_SCHEMA": "public",
    # SNOWFLAKE_ROLE 是可选的，可以留空
})

try:
    import snowflake.connector
    print("✅ Snowflake连接器已安装")

    # 测试直接连接
    print("\n🔍 测试直接Snowflake连接...")

    conn_params = {
        "account": os.environ["SNOWFLAKE_ACCOUNT"],
        "user": os.environ["SNOWFLAKE_USER"],
        "authenticator": os.environ["SNOWFLAKE_AUTHENTICATOR"],
        "warehouse": os.environ["SNOWFLAKE_WAREHOUSE"],
        "database": os.environ["SNOWFLAKE_DATABASE"],
        "schema": os.environ["SNOWFLAKE_SCHEMA"],
    }

    print(f"连接参数:")
    for key, value in conn_params.items():
        print(f"  {key}: {value}")

    try:
        # 尝试连接
        conn = snowflake.connector.connect(**conn_params)
        print("✅ Snowflake连接成功!")

        # 执行简单查询
        cursor = conn.cursor()
        cursor.execute("SELECT CURRENT_VERSION()")
        version = cursor.fetchone()[0]
        print(f"  Snowflake版本: {version}")

        cursor.execute("SELECT CURRENT_DATABASE(), CURRENT_SCHEMA()")
        db, schema = cursor.fetchone()
        print(f"  当前数据库: {db}")
        print(f"  当前模式: {schema}")

        # 列出表
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s
            AND table_type = 'BASE TABLE'
            LIMIT 5
        """, (os.environ["SNOWFLAKE_SCHEMA"].upper(),))

        tables = cursor.fetchall()
        if tables:
            print(f"  找到 {len(tables)} 个表 (前5个):")
            for table in tables:
                print(f"    - {table[0]}")
        else:
            print("  ⚠️ 未找到表")

        cursor.close()
        conn.close()
        print("✅ 测试完成!")

    except Exception as e:
        print(f"❌ 连接失败: {e}")
        print("\n故障排除建议:")
        print("1. 检查网络连接")
        print("2. 验证账户信息")
        print("3. 确认用户权限")
        print("4. 尝试使用密码认证")

except ImportError as e:
    print(f"❌ 缺少依赖: {e}")
    print("请安装: pip install snowflake-connector-python")
except Exception as e:
    print(f"❌ 测试失败: {e}")