# PostgreSQL客户端使用说明

## 概述

本项目使用 **psycopg2-binary** 作为PostgreSQL客户端库，采用**同步API**进行所有数据库操作。

## 技术栈详情

### 客户端库
- **库名称**: `psycopg2-binary`
- **版本**: >= 2.9.0
- **API类型**: 同步 (Synchronous)
- **Python导入**: `import psycopg2`

### 需求文件
在 `requirements.txt` 中明确指定：
```txt
psycopg2-binary>=2.9.0
```

### 代码使用示例
```python
# 正确用法（项目实际使用）
import psycopg2
from psycopg2 import Error as PostgresError

# 连接数据库
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="datalab",
    user="postgres",
    password="password"
)

# 执行查询
cursor = conn.cursor()
cursor.execute("SELECT * FROM notification_text")
```

## 重要说明

### 1. 同步 vs 异步
- **当前实现**: 仅使用同步API
- **未来扩展**: 异步操作（如`asyncpg`或`psycopg3`的异步API）是可选功能，但**未在当前故事中实现**
- **测试**: 所有测试基于同步API，无需`pytest-asyncio`

### 2. 版本一致性
- **代码**: 使用`psycopg2`（版本2）
- **文档**: 所有文档应引用`psycopg2-binary`或`psycopg2`
- **避免混淆**: 不应提及`psycopg3`、`psycopg[binary]`或异步操作，除非明确实现

### 3. 相关文件
需要保持一致的文档：
1. `requirements.txt` - 依赖声明
2. `docs/stories/*.md` - 用户故事描述
3. `docs/setup/*.md` - 设置指南
4. `docs/architecture.md` - 架构文档

## 验证方法

### 代码验证
```bash
# 检查实际导入
grep -r "import psycopg" src/ --include="*.py"

# 检查需求文件
grep psycopg requirements.txt

# 运行测试（验证同步API正常工作）
python -m pytest tests/etl/test_postgres_writer.py -v
```

### 文档验证
```bash
# 检查文档一致性
grep -r -i "psycopg[23]\|async.*postgres" docs/ --include="*.md"
```

## 更新记录

| 日期 | 变更 | 负责人 |
|------|------|--------|
| 2025-12-28 | 创建文档，澄清使用`psycopg2-binary`同步API | 系统 |
| 2025-12-28 | 更新所有相关文档确保一致性 | 系统 |

## 故障排除

### 常见问题
1. **导入错误**: 确保安装了`psycopg2-binary`而非`psycopg`或`psycopg3`
2. **异步错误**: 如果看到异步相关错误，检查是否错误引入了异步代码
3. **版本冲突**: 确保`requirements.txt`中指定了正确版本

### 安装验证
```bash
# 验证安装
python -c "import psycopg2; print(f'psycopg2 version: {psycopg2.__version__}')"

# 验证功能
python -c "
import psycopg2
print('✅ psycopg2 imported successfully')
print('✅ This confirms synchronous PostgreSQL client usage')
"
```

---

**最后更新**: 2025-12-28  
**状态**: ✅ 有效  
**适用范围**: 所有项目文档和代码
