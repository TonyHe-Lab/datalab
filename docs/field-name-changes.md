# 数据库字段名变更说明

## 变更概述

为了更好的语义表达和业务一致性，我们对数据库字段名进行了优化：

### 主要变更

1. **`maintenance_logs.last_modified` → `notification_date`**
   - **原因**: `last_modified` 语义模糊，改为 `notification_date` 更符合医疗工单业务场景
   - **影响**: 所有引用此字段的代码需要更新
   - **迁移脚本**: `db/migrate_field_names.sql`

### 字段名保持不变的说明

1. **`snowflake_id` 保持不变**
   - **原因**: 这是业务键（来自Snowflake系统的原始ID），与 `log_id`（外键）语义不同
   - `snowflake_id` = 外部系统标识符（用于数据同步）
   - `log_id` = 数据库内部关联键（用于表间关系）

2. **`log_id` 保持不变**
   - **原因**: 作为外键引用 `maintenance_logs.id`，保持现有关系模型

## 新的字段名规范

### maintenance_logs 表
| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | SERIAL PRIMARY KEY | **本地主键**，用于数据库内部关联 |
| `snowflake_id` | TEXT UNIQUE | **Snowflake原始ID**，用于数据同步和溯源 |
| `raw_text` | TEXT NOT NULL | **原始维护日志文本** |
| `notification_date` | TIMESTAMP WITH TIME ZONE | **工单通知/创建日期**，用于增量同步 |

### ai_extracted_data 表
| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | SERIAL PRIMARY KEY | AI数据主键 |
| `log_id` | INTEGER FK | **外键**，引用 `maintenance_logs.id` |
| `component` | TEXT | 故障部件 |
| `fault` | TEXT | 故障描述 |
| `cause` | TEXT | 根本原因 |
| `resolution` | JSONB | 解决步骤（结构化） |
| `summary` | TEXT | 摘要总结 |

### semantic_embeddings 表
| 字段名 | 类型 | 说明 |
|--------|------|------|
| `log_id` | INTEGER FK | **外键**，引用 `maintenance_logs.id` |
| `vector` / `vector_bytea` | vector(1536) / BYTEA | 文本向量嵌入 |

## 迁移步骤

### 1. 备份数据库
```bash
pg_dump -h localhost -U postgres datalab > datalab_backup_$(date +%Y%m%d).sql
```

### 2. 运行迁移脚本
```bash
psql -h localhost -U postgres -d datalab -f db/migrate_field_names.sql
```

### 3. 验证迁移结果
```sql
-- 检查字段名是否已更新
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'maintenance_logs' 
    AND column_name = 'notification_date';

-- 应该返回: notification_date
```

### 4. 更新应用程序代码
需要更新以下位置的字段引用：

#### Python代码
```python
# 之前
query = "SELECT * FROM maintenance_logs WHERE last_modified > %s"

# 之后
query = "SELECT * FROM maintenance_logs WHERE notification_date > %s"
```

#### Pydantic模型
```python
# 之前
class MaintenanceLog(BaseModel):
    last_modified: datetime

# 之后
class MaintenanceLog(BaseModel):
    notification_date: datetime
```

#### API响应
```json
// 之前
{
  "last_modified": "2025-12-27T10:30:00Z"
}

// 之后
{
  "notification_date": "2025-12-27T10:30:00Z"
}
```

## 影响范围

### 需要更新的文件
1. `dev/verify_db_schema.py` - ✅ 已更新
2. 所有Story文件中的数据模型描述 - ✅ 已更新
3. 架构文档 - ✅ 已更新
4. PRD文档 - ✅ 已更新
5. 未来的ETL脚本和API实现

### 不需要更新的
1. 数据库索引（自动跟随列名变更）
2. 外键约束（保持不变）
3. 表关系（保持不变）

## 业务语义说明

### notification_date 的含义
- **医疗工单场景**: 工单创建或通知日期
- **ETL同步**: 用于增量数据提取的时间戳
- **业务分析**: 工单时间趋势分析的基础

### 为什么不是 noti_date
我们使用完整的 `notification_date` 而不是缩写 `noti_date`，因为：
1. 更清晰的语义表达
2. 符合数据库命名规范（使用完整单词）
3. 避免歧义（noti可能被误解为其他含义）

## 回滚方案

如果需要回滚到旧的字段名：

```sql
-- 回滚脚本
ALTER TABLE maintenance_logs RENAME COLUMN notification_date TO last_modified;
```

## 问题排查

### 常见问题
1. **Q**: 迁移后应用程序报错 "column last_modified does not exist"
   **A**: 更新应用程序代码中的字段引用

2. **Q**: 迁移脚本执行失败
   **A**: 检查数据库连接和权限，确保有ALTER TABLE权限

3. **Q**: 数据丢失风险
   **A**: 迁移只更改列名，不更改数据。但仍建议先备份

### 技术支持
如有问题，请参考：
1. 数据库schema: `db/init_schema.sql`
2. 验证脚本: `dev/verify_db_schema.py`
3. 数据模型文档: `docs/prd_shards/10-data-model.md`

---

**变更生效日期**: 2025-12-27  
**负责人**: 数据库架构团队  
**状态**: ✅ 已实施
