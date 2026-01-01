#!/usr/bin/env python3
"""
测试不同的Snowflake账户格式
"""

import snowflake.connector

# 测试不同的账户格式
account_formats = [
    "yu83356",  # 仅账户名
    "yu83356.west-europe.azure",  # 带区域
    "yu83356.west-europe.azure.snowflakecomputing.com",  # 完整URL
]

test_params = {
    "user": "linwei.he@siemens-healthineers.com",
    "authenticator": "externalbrowser",
    "warehouse": "WH_SDTB_INT_XP_DC_R",
    "database": "SDM_PROD",
    "schema": "public",
}

print("🔍 测试不同的Snowflake账户格式...")

for account in account_formats:
    print(f"\n测试账户格式: {account}")

    try:
        params = test_params.copy()
        params["account"] = account

        print(f"  连接参数: {params}")

        # 尝试连接
        conn = snowflake.connector.connect(**params)
        print(f"  ✅ 连接成功!")

        # 测试查询
        cursor = conn.cursor()
        cursor.execute("SELECT CURRENT_VERSION()")
        version = cursor.fetchone()[0]
        print(f"  Snowflake版本: {version}")

        cursor.close()
        conn.close()
        break  # 如果成功，停止测试

    except Exception as e:
        print(f"  ❌ 连接失败: {e}")

print("\n" + "=" * 60)
print("如果所有格式都失败，请检查:")
print("1. 账户名称是否正确")
print("2. 是否使用正确的认证方式")
print("3. 用户是否有访问权限")
print("4. 网络连接是否正常")
print("=" * 60)