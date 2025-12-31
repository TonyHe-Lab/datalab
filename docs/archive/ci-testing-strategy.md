# CI测试策略文档

## 概述

本文档描述了在CI环境中如何可靠地运行Snowflake和PostgreSQL测试的策略。

## 测试策略

### 1. Snowflake连接器测试策略

#### 模拟（Mocking）策略
- **单元测试**: 使用`unittest.mock`完全模拟Snowflake连接器
- **集成测试**: 使用模拟数据验证ETL流程
- **CI环境**: 不实际连接Snowflake，完全依赖模拟

#### 示例代码
```python
# tests/etl/test_snowflake_loader.py
@patch("snowflake.connector.connect")
def test_connect_success(self, mock_connect):
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_cursor.fetchone.return_value = ["3.0.0"]
    mock_conn.cursor.return_value = mock_cursor
    mock_connect.return_value = mock_conn
```

### 2. PostgreSQL测试策略

#### 临时数据库服务
- **CI服务**: 使用GitHub Actions的PostgreSQL服务
- **数据库**: `postgres:13` 镜像
- **配置**: 自动创建测试数据库 `datalab_test`
- **清理**: 每次运行后自动清理

#### 配置示例
```yaml
# .github/workflows/ci-python.yml
services:
  postgres:
    image: postgres:13
    env:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: datalab_test
    ports:
      - 5432:5432
```

### 3. ETL干运行（Dry-run）测试

#### 目的
- 验证ETL配置和基本功能
- 不实际连接外部服务
- 快速验证CI设置

#### 实现
- **脚本**: `scripts/etl_dry_run.py`
- **策略**: 完全模拟Snowflake和PostgreSQL连接
- **验证点**: 配置加载、连接测试、同步流程

### 4. 测试分类

#### 单元测试（无需外部服务）
```bash
# 运行单元测试
pytest tests/etl/test_snowflake_loader.py -v
pytest tests/etl/test_postgres_writer.py -v
pytest tests/etl/test_error_handler.py -v
```

#### 集成测试（需要PostgreSQL服务）
```bash
# 运行集成测试（需要PostgreSQL服务）
pytest tests/integration/ -v
```

#### 冒烟测试（CI验证）
```bash
# 运行ETL干运行测试
python scripts/etl_dry_run.py
```

## CI工作流

### 工作流步骤
1. **设置环境**: Python 3.12 + 依赖安装
2. **启动服务**: PostgreSQL临时数据库
3. **运行测试**: 
   - 单元测试（模拟Snowflake）
   - 集成测试（真实PostgreSQL）
   - ETL干运行测试
4. **生成报告**: 测试结果和覆盖率

### 配置文件
```yaml
# .github/workflows/ci-python.yml
name: CI - Python
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres: # PostgreSQL服务配置
        image: postgres:13
        env: ...
    steps:
      - name: Run tests
        run: pytest -q
      - name: Run ETL dry-run test
        run: python scripts/etl_dry_run.py
```

## 验证方法

### 1. 本地验证
```bash
# 启动本地PostgreSQL（可选）
docker run -d --name test-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 postgres:13

# 运行测试
python scripts/etl_dry_run.py
pytest tests/ -v
```

### 2. CI验证
- 每次推送或PR自动运行CI
- 验证所有测试通过
- 验证ETL干运行测试通过

### 3. 手动验证
```bash
# 检查测试覆盖率
pytest --cov=src tests/

# 运行特定测试类别
pytest tests/etl/ -k "test_connect"
```

## 故障排除

### 常见问题

#### 1. Snowflake连接失败
**症状**: 测试尝试实际连接Snowflake
**解决**: 确保测试正确模拟`snowflake.connector.connect`

#### 2. PostgreSQL连接失败
**症状**: 无法连接到CI的PostgreSQL服务
**解决**: 
- 检查服务配置
- 验证端口映射
- 检查数据库名称和凭据

#### 3. 测试数据不一致
**症状**: 测试数据与当前schema不匹配
**解决**: 更新测试数据以匹配`notification_text`表结构

### 调试步骤
1. 检查CI日志中的错误信息
2. 本地运行失败测试
3. 验证环境变量配置
4. 检查模拟数据的一致性

## 更新记录

| 日期 | 变更 | 负责人 |
|------|------|--------|
| 2025-12-28 | 创建文档，定义CI测试策略 | 系统 |
| 2025-12-28 | 添加ETL干运行测试脚本 | 系统 |
| 2025-12-28 | 更新CI工作流配置 | 系统 |

---

**最后更新**: 2025-12-28  
**状态**: ✅ 有效  
**适用范围**: 所有CI测试和本地开发测试
