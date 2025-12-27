# 增量 ETL 脚本 (Snowflake 到 PostgreSQL)

## 概述

这个增量 ETL 脚本实现了从 Snowflake 数据仓库到 PostgreSQL 数据库的数据同步功能。它支持增量数据提取、幂等数据加载、错误恢复和性能监控。

## 功能特性

- ✅ **多认证方式**: 支持密码认证和浏览器 SSO 认证
- ✅ **增量同步**: 基于时间戳的水位线跟踪
- ✅ **幂等加载**: UPSERT 逻辑防止重复记录
- ✅ **错误处理**: 指数退避重试机制
- ✅ **性能监控**: 详细的指标收集和日志记录
- ✅ **配置管理**: 通过环境变量灵活配置
- ✅ **批量处理**: 支持大规模数据的高效处理
- ✅ **全面测试**: 单元测试和集成测试覆盖

## 项目结构

```
src/
├── etl/
│   ├── snowflake_loader.py    # Snowflake 客户端
│   ├── postgres_writer.py     # PostgreSQL 写入器
│   ├── error_handler.py       # 错误处理和指标收集
│   └── incremental_sync.py    # 增量同步主逻辑
├── utils/
│   └── config.py              # 配置加载和验证
└── scripts/
    └── run_etl.py            # 命令行入口点

tests/
├── etl/                       # 单元测试
│   ├── test_snowflake_loader.py
│   ├── test_postgres_writer.py
│   ├── test_error_handler.py
│   └── test_incremental_sync.py
└── integration/               # 集成测试
    └── test_etl_pipeline.py
```

## 快速开始

### 1. 环境设置

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 到 `.env` 并填写您的配置：

```bash
cp .env.example .env
# 编辑 .env 文件，填写您的 Snowflake 和 PostgreSQL 连接信息
```

### 3. 运行 ETL 同步

```bash
# 运行完整的 ETL 同步
python scripts/run_etl.py

# 同步特定表格
python scripts/run_etl.py --tables notification_text

# 查看帮助信息
python scripts/run_etl.py --help
```

## 配置说明

### Snowflake 配置

```env
# 必填字段
SNOWFLAKE_ACCOUNT=your-account.snowflakecomputing.com
SNOWFLAKE_USER=your-username
SNOWFLAKE_WAREHOUSE=your-warehouse
SNOWFLAKE_DATABASE=your-database
SNOWFLAKE_SCHEMA=your-schema

# 认证方式（选择一种）
# 方式1: 密码认证
SNOWFLAKE_PASSWORD=your-password
SNOWFLAKE_AUTHENTICATOR=snowflake

# 方式2: 浏览器 SSO 认证
# SNOWFLAKE_AUTHENTICATOR=externalbrowser
# 不需要密码

# 可选字段
SNOWFLAKE_ROLE=your-role
```

### PostgreSQL 配置

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password
POSTGRES_DB=datalab
```

### ETL 配置

```env
ETL_BATCH_SIZE=1000
ETL_MAX_RETRIES=3
ETL_RETRY_DELAY=5
ETL_WATERMARK_TABLE=etl_metadata
```

## 工作原理

### 增量同步流程

1. **连接 Snowflake**: 使用配置的认证方式连接到 Snowflake
2. **获取水位线**: 从 PostgreSQL 的 `etl_metadata` 表读取最后成功提取时间
3. **增量提取**: 查询 Snowflake 中上次提取时间之后的新记录
4. **批量写入**: 使用 UPSERT 逻辑将数据写入 PostgreSQL
5. **更新水位线**: 更新 `etl_metadata` 表中的最后提取时间
6. **记录指标**: 收集处理记录数、处理时间等性能指标

### 错误恢复机制

- **指数退避重试**: 网络故障时自动重试，重试间隔指数增长
- **事务管理**: 数据库操作使用事务确保数据一致性
- **错误隔离**: 单个表格同步失败不影响其他表格
- **详细日志**: 结构化日志便于问题排查

## 测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/etl/test_snowflake_loader.py -v

# 运行集成测试
pytest tests/integration/ -v
```

## 开发指南

### 添加新表格支持

1. 在 `src/etl/postgres_writer.py` 中添加新的 UPSERT 方法
2. 在 `batch_upsert` 方法中添加对新表格的支持
3. 更新测试以确保新功能正常工作

### 扩展功能

- **监控集成**: 集成 Prometheus 或 Datadog 进行监控
- **警报机制**: 添加错误警报和性能警报
- **调度系统**: 集成 Apache Airflow 或 cron 进行定期调度
- **数据验证**: 添加数据质量检查和验证规则

## 故障排除

### 常见问题

1. **连接失败**: 检查网络连接和防火墙设置
2. **认证错误**: 验证认证方式和凭据是否正确
3. **权限不足**: 确保数据库用户有足够的权限
4. **内存不足**: 调整批处理大小减少内存使用

### 日志查看

```bash
# 查看 ETL 日志
cat etl.log

# 实时查看日志
tail -f etl.log
```

## 许可证

本项目遵循 MIT 许可证。
