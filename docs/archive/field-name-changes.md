# 数据库字段命名规范

## 规范概述

为了更好的语义表达和代码一致性，我们制定了统一的字段命名规范：

### 命名规范原则

1. **工单相关字段**: 使用 `noti_` 前缀（notification的缩写）
2. **系统/设备相关字段**: 使用 `sys_` 前缀（system的缩写）
3. **主键字段**: 保持完整名称，如 `notification_id`
4. **时间戳字段**: 使用 `_at` 后缀，如 `created_at`, `updated_at`

## 字段命名规范

### notification_text 表（通知工单主表）
| 字段名 | 类型 | 说明 |
|--------|------|------|
| `notification_id` | TEXT PRIMARY KEY | **主键**，来自Snowflake系统的唯一工单号 |
| `noti_date` | TIMESTAMP WITH TIME ZONE NOT NULL | **工单通知/创建日期**，用于增量同步 |
| `noti_assigned_date` | TIMESTAMP WITH TIME ZONE | **工单分配日期** |
| `noti_closed_date` | TIMESTAMP WITH TIME ZONE | **工单关闭日期** |
| `noti_category_id` | TEXT | **工单类别编号** |
| `noti_country_id` | TEXT | **工单国家简称** |
| `noti_trendcode_l1` | TEXT | **工单趋势代码级别1** |
| `noti_trendcode_l2` | TEXT | **工单趋势代码级别2** |
| `noti_trendcode_l3` | TEXT | **工单趋势代码级别3** |
| `noti_issue_type` | TEXT | **工单问题类型**（如：硬件故障、软件问题等） |
| `noti_medium_text` | TEXT | **工单保修短文本** |
| `noti_text` | TEXT NOT NULL | **工单维修日志长文本**（AI分析的主要文本） |
| `sys_eq_id` | TEXT | **设备编号** |
| `sys_fl_id` | TEXT | **设备场地编号** |
| `sys_mat_id` | TEXT | **设备物料号** |
| `sys_serial_id` | TEXT | **设备序列号** |
| `created_at` | TIMESTAMP WITH TIME ZONE DEFAULT now() | **创建时间** |
| `updated_at` | TIMESTAMP WITH TIME ZONE DEFAULT now() | **更新时间** |

### ai_extracted_data 表（AI提取数据表）
| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | SERIAL PRIMARY KEY | AI数据主键 |
| `notification_id` | TEXT FK | **外键**，引用 `notification_text.notification_id` |
| `keywords_ai` | TEXT | **关键词提取** |
| `primary_symptom_ai` | TEXT | **主要症状** |
| `root_cause_ai` | TEXT | **根本原因** |
| `summary_ai` | TEXT | **摘要总结** |
| `solution_ai` | TEXT | **解决方案** |
| `solution_type_ai` | TEXT | **解决方案类型** |
| `components_ai` | TEXT | **相关部件** |
| `processes_ai` | TEXT | **相关流程** |
| `main_component_ai` | TEXT | **主要部件** |
| `main_process_ai` | TEXT | **主要流程** |
| `confidence_score_ai` | DECIMAL(5,4) | **置信度分数** |
| `extracted_at` | TIMESTAMP WITH TIME ZONE | **提取时间** |
| `model_version` | TEXT | **模型版本** |

### semantic_embeddings 表（向量索引表）
| 字段名 | 类型 | 说明 |
|--------|------|------|
| `notification_id` | TEXT FK | **外键**，引用 `notification_text.notification_id` |
| `source_text_ai` | TEXT | **源文本** |
| `vector` | vector(1536) | **文本向量嵌入**（1536维） |
| `created_at` | TIMESTAMP WITH TIME ZONE DEFAULT now() | **创建时间** |

### etl_metadata 表（ETL元数据表）
| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | SERIAL PRIMARY KEY | 元数据主键 |
| `table_name` | TEXT NOT NULL | **表名** |
| `last_sync_timestamp` | TIMESTAMP WITH TIME ZONE | **最后同步时间戳** |
| `rows_processed` | INTEGER | **处理行数** |
| `sync_status` | TEXT | **同步状态** |
| `error_message` | TEXT | **错误信息** |
| `created_at` | TIMESTAMP WITH TIME ZONE DEFAULT now() | **创建时间** |
| `updated_at` | TIMESTAMP WITH TIME ZONE DEFAULT now() | **更新时间** |


## 实施状态

### 已完成的更新
1. ✅ 数据库Schema (`db/init_schema.sql`)
2. ✅ Pydantic模型 (`src/models/schemas.py`)
3. ✅ SQLAlchemy实体 (`src/models/entities.py`)
4. ✅ 数据转换工具 (`src/models/transformations/`)
5. ✅ 测试文件 (`tests/models/`)
6. ✅ 架构文档 (`docs/architecture.md`)
7. ✅ PRD文档 (`docs/prd_shards/10-data-model.md`)
8. ✅ User Story文件 (`docs/stories/`)
9. ✅ 数据模型重设计文档 (`docs/data-model-redesign-2025-12-27.md`)

### 命名规范优势
1. **一致性**: 统一的命名前缀提高代码可读性
2. **语义清晰**: `noti_`前缀明确表示工单相关字段，`sys_`前缀明确表示系统/设备相关字段
3. **易于维护**: 规范的命名减少歧义和错误
4. **扩展性**: 为未来新增字段提供清晰的命名指导

## 使用示例

### SQL查询
```sql
-- 查询特定设备的工单
SELECT notification_id, noti_date, noti_text, noti_issue_type
FROM notification_text
WHERE sys_eq_id = 'EQ-001'
ORDER BY noti_date DESC;
```

### Python代码
```python
# Pydantic模型
from src.models.schemas import MaintenanceLogCreate

log = MaintenanceLogCreate(
    notification_id="NOTIF-2025-001",
    noti_date="2025-12-28T10:00:00Z",
    noti_text="设备出现硬件故障...",
    noti_issue_type="硬件故障",
    sys_eq_id="EQ-001"
)
```

### API响应
```json
{
  "notification_id": "NOTIF-2025-001",
  "noti_date": "2025-12-28T10:00:00Z",
  "noti_text": "设备出现硬件故障...",
  "noti_issue_type": "硬件故障",
  "sys_eq_id": "EQ-001",
  "created_at": "2025-12-28T10:00:00Z"
}
```

## 技术支持
如有问题，请参考：
1. 数据库schema: `db/init_schema.sql`
2. 验证脚本: `dev/verify_db_schema.py`
3. 数据模型文档: `docs/prd_shards/10-data-model.md`

---

**规范生效日期**: 2025-12-28  
**负责人**: 数据库架构团队  
**状态**: ✅ 已实施并测试通过
