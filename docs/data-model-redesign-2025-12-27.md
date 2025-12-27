# 数据模型重大变更说明 (2025-12-27)

## 概述

为了更好的业务语义表达和系统可维护性，我们对数据库schema进行了全面的重新设计。新的数据模型采用业务导向的命名规范，统一使用`notification_id`作为主键和外键，并添加了完整的业务字段。

## 变更摘要

### 表名变更
| 旧表名 | 新表名 | 说明 |
|--------|--------|------|
| `maintenance_logs` | `notification_text` | 更符合业务语义，明确存储通知工单文本 |
| `ai_extracted_data` | `ai_extracted_data` | 表名不变，但字段结构完全改变 |
| `semantic_embeddings` | `semantic_embeddings` | 表名不变，但字段结构完全改变 |

### 主键和外键统一
- **旧模型**: 使用`id`（整数自增）作为主键，`log_id`作为外键
- **新模型**: 统一使用`notification_id`（文本，来自Snowflake）作为主键和外键

### 新增业务字段
新的`notification_text`表包含了完整的业务上下文：
- 设备信息（编号、序列号、物料号）
- 地点信息（国家、场地）
- 时间信息（通知、分配、关闭日期）
- 分类信息（类别、趋势代码）
- 文本内容（短文本、长文本）

## 详细变更

### 1. notification_text 表（原 maintenance_logs）

**字段映射**:
| 旧字段 | 新字段 | 说明 |
|--------|--------|------|
| `id` | ❌ 删除 | 不再使用自增ID |
| `external_id` | `notification_id` (PK) | 业务主键，来自Snowflake |
| `raw_text` | `notification_text` | 重命名为业务术语 |
| `notification_date` | `notification_date` | 保持不变 |
| ❌ 新增 | `notification_assigned_date` | 工单分配日期 |
| ❌ 新增 | `notification_closed_date` | 工单关闭日期 |
| ❌ 新增 | `noti_category_id` | 工单类别编号 |
| ❌ 新增 | `sys_eq_id` | 设备编号 |
| ❌ 新增 | `noti_country_id` | 工单国家简称 |
| ❌ 新增 | `sys_fl_id` | 设备场地编号 |
| ❌ 新增 | `sys_mat_id` | 设备物料号 |
| ❌ 新增 | `sys_serial_id` | 设备序列号 |
| ❌ 新增 | `notification_trendcode_l1/l2/l3` | 工单趋势代码 |
| ❌ 新增 | `notification_medium_text` | 工单保修短文本 |

### 2. ai_extracted_data 表

**字段映射**:
| 旧字段 | 新字段 | 说明 |
|--------|--------|------|
| `log_id` | `notification_id` | 改为引用notification_text.notification_id |
| `component` | `component_ai` | 添加_ai后缀明确来源 |
| `fault` | `fault_ai` | 添加_ai后缀明确来源 |
| `cause` | `cause_ai` | 添加_ai后缀明确来源 |
| `resolution` | `resolution_ai` | 添加_ai后缀明确来源 |
| `summary` | `summary` | 保持不变 |
| ❌ 新增 | `modules_ai` | 子故障模块 |
| ❌ 新增 | `process_ai` | 故障流程 |
| ❌ 新增 | `confidence_score` | AI提取置信度 |
| ❌ 新增 | `model_version` | AI模型版本 |
| ❌ 新增 | `extracted_at` | AI提取时间 |

### 3. semantic_embeddings 表

**字段映射**:
| 旧字段 | 新字段 | 说明 |
|--------|--------|------|
| `log_id` | `notification_id` | 改为引用notification_text.notification_id |
| `vector` / `vector_bytea` | `vector` / `vector_bytea` | 保持不变 |
| ❌ 新增 | `source_text_ai` | 用于生成向量的原始文本 |
| ❌ 新增 | `created_at` | 向量创建时间 |

## 设计原则

### 1. 业务导向命名
- 所有字段名使用业务术语而非技术术语
- 表名明确表达业务含义（notification_text而非maintenance_logs）
- 字段名完整描述业务含义

### 2. 统一关联键
- 三张表统一使用`notification_id`作为关联键
- 避免整数ID和业务ID的转换
- 简化数据关系模型

### 3. 完整业务上下文
- 包含设备、地点、时间等完整维度
- 支持多维度的业务分析
- 为AI分析提供丰富上下文

### 4. AI质量跟踪
- 记录AI提取的置信度
- 跟踪使用的模型版本
- 便于质量监控和模型迭代

## 迁移指南

### 自动迁移
运行迁移脚本：
```bash
psql -h localhost -U postgres -d datalab -f db/migrate_to_new_schema.sql
```

### 手动迁移步骤
1. **备份数据库**
   ```bash
   pg_dump -h localhost -U postgres datalab > datalab_backup_$(date +%Y%m%d).sql
   ```

2. **创建新表结构**
   ```bash
   psql -h localhost -U postgres -d datalab -f db/init_schema.sql
   ```

3. **迁移数据**
   - 根据业务规则映射旧数据到新结构
   - 特别注意`notification_id`的生成规则

4. **验证迁移**
   ```bash
   python dev/verify_db_schema.py
   ```

5. **更新应用程序**
   - 更新所有SQL查询
   - 更新ORM模型定义
   - 更新API接口

## 影响范围

### 需要更新的组件
1. **ETL脚本** (Story 2.1)
   - 数据提取逻辑
   - 数据插入逻辑
   - 增量同步逻辑

2. **Pydantic模型** (Story 2.2)
   - 所有数据模型定义
   - 验证规则
   - 序列化/反序列化逻辑

3. **AI集成** (Story 2.3)
   - 数据预处理
   - 结果存储
   - 质量跟踪

4. **后端API** (未来Epic 3)
   - 所有数据访问层
   - API响应格式
   - 查询参数

### 不需要更新的
1. **Snowflake连接** - 数据源不变
2. **PostgreSQL连接** - 数据库不变
3. **基础架构** - 部署方式不变

## 回滚方案

如果遇到问题，可以回滚到旧schema：

1. **恢复备份**
   ```bash
   psql -h localhost -U postgres -d datalab -f datalab_backup_YYYYMMDD.sql
   ```

2. **恢复旧代码**
   - 恢复旧的`db/init_schema.sql`
   - 恢复旧的应用程序代码

## 测试策略

### 单元测试
- 测试新的数据模型定义
- 测试数据迁移逻辑
- 测试外键约束

### 集成测试
- 测试ETL管道端到端
- 测试AI提取流程
- 测试搜索功能

### 性能测试
- 测试新索引性能
- 测试查询性能
- 测试迁移过程性能

## 时间线

- **2025-12-27**: 设计新数据模型
- **2025-12-27**: 实施数据库变更
- **2025-12-28**: 更新应用程序代码
- **2025-12-29**: 全面测试
- **2025-12-30**: 生产环境部署

## 负责人

- **数据库设计**: 架构团队
- **迁移实施**: 开发团队  
- **测试验证**: QA团队
- **文档更新**: 技术文档团队

---

**状态**: ✅ 设计完成  
**下一步**: 实施迁移和更新应用程序代码
