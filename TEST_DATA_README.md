# 测试数据部署说明

## 概述

已成功为datalab项目部署少量生产数据进行测试。这些数据模拟了真实的医疗设备工单处理流程，包含完整的业务逻辑和数据关联。

## 数据统计

| 表名 | 记录数 | 描述 |
|------|--------|------|
| `notification_text` | 16 | 工单主表，包含原始工单数据 |
| `ai_extracted_data` | 5 | AI提取的结构化数据 |
| `semantic_embeddings` | 0 | 语义嵌入表（需要AI模型生成） |
| `etl_metadata` | 2 | ETL元数据表 |

## 测试数据特征

### 1. 问题类型分布
- **Hardware** (硬件故障): 9条 (56.25%)
- **Software** (软件问题): 3条 (18.75%)
- **Configuration** (配置错误): 1条 (6.25%)
- **Network** (网络问题): 1条 (6.25%)
- **Maintenance** (维护问题): 1条 (6.25%)
- **电源模块故障**: 1条 (6.25%)

### 2. 时间分布
- 数据覆盖2025年1月到9月
- 包含不同时区的工单（UTC+8, EST, CET, JST等）

### 3. AI分析质量
- **AI提取覆盖率**: 31.25% (5/16)
- **平均置信度**: 0.900
- **最高置信度**: 0.950 (TEST003 - 网络问题)

## 新增的测试数据 (TEST系列)

### 工单数据 (`notification_text`)
| ID | 日期 | 问题类型 | 设备 | 国家 | 简要描述 |
|----|------|----------|------|------|----------|
| TEST001 | 2025-01-15 | Hardware | CT扫描仪 | CN | 图像环形伪影 |
| TEST002 | 2025-01-16 | Software | PACS系统 | US | 连接超时 |
| TEST003 | 2025-01-17 | Network | MRI设备 | DE | 网络中断 |
| TEST004 | 2025-01-18 | Configuration | 超声设备 | JP | 参数设置错误 |
| TEST005 | 2025-01-19 | Maintenance | X光机 | FR | 定期维护 |

### AI提取数据 (`ai_extracted_data`)
每个TEST工单都有对应的AI分析结果，包含：
- 关键词提取
- 主要症状识别
- 根本原因分析
- 解决方案建议
- 置信度评分 (0.85-0.95)

## 如何使用测试数据

### 1. 基本查询
```sql
-- 查看所有工单
SELECT * FROM notification_text ORDER BY noti_date DESC;

-- 查看AI分析结果
SELECT * FROM ai_extracted_data ORDER BY confidence_score_ai DESC;

-- 查看ETL状态
SELECT * FROM etl_metadata;
```

### 2. 关联查询
```sql
-- 查看完整的工单处理流程
SELECT nt.*, aed.*
FROM notification_text nt
LEFT JOIN ai_extracted_data aed ON nt.notification_id = aed.notification_id
WHERE nt.notification_id LIKE 'TEST%';
```

### 3. 统计查询
```sql
-- 按问题类型统计
SELECT noti_issue_type, COUNT(*) as count
FROM notification_text
GROUP BY noti_issue_type
ORDER BY count DESC;

-- AI分析质量统计
SELECT
    ROUND(AVG(confidence_score_ai)::numeric, 3) as avg_confidence,
    COUNT(*) as analyzed_count
FROM ai_extracted_data;
```

### 4. 使用Python脚本
```bash
# 运行演示脚本
python3 scripts/test_data_demo.py

# 运行验证脚本
PGPASSWORD=password psql -h localhost -p 5432 -U postgres -d datalab -f scripts/verify_test_data.sql
```

## 测试场景

### 1. 功能测试
- **工单查询**: 测试基本的CRUD操作
- **AI分析**: 测试AI提取数据的完整性和准确性
- **关联查询**: 测试表之间的关联关系
- **统计报表**: 测试数据聚合和统计功能

### 2. 性能测试
- **查询性能**: 测试各种查询条件的响应时间
- **并发测试**: 测试多用户同时访问的性能
- **数据量测试**: 测试大数据量下的性能表现

### 3. 集成测试
- **ETL流程**: 测试数据同步和ETL流程
- **API集成**: 测试与前端API的集成
- **AI服务集成**: 测试与AI服务的集成

## 文件说明

| 文件 | 用途 |
|------|------|
| `scripts/seed_test_data.sql` | 测试数据种子脚本 |
| `scripts/verify_test_data.sql` | 数据验证脚本 |
| `scripts/test_data_demo.py` | Python演示脚本 |
| `TEST_DATA_README.md` | 本文档 |

## 数据质量验证

所有测试数据都通过了以下验证：
- ✅ 数据完整性检查 (无缺失必填字段)
- ✅ 数据关联性检查 (无孤立记录)
- ✅ 业务逻辑验证 (符合实际业务场景)
- ✅ 数据类型验证 (符合表结构定义)

## 后续步骤

1. **扩展测试数据**: 根据需要添加更多测试场景
2. **生成语义嵌入**: 为`semantic_embeddings`表生成向量数据
3. **性能基准测试**: 建立性能基准用于后续优化
4. **自动化测试**: 将测试数据集成到CI/CD流程中

## 注意事项

1. **数据安全**: 测试数据已脱敏，不包含真实患者信息
2. **数据一致性**: 所有数据都遵循业务规则和约束
3. **可重复性**: 测试数据脚本可重复执行，具有幂等性
4. **扩展性**: 数据结构支持后续的功能扩展

---

**部署时间**: 2026-01-01
**部署状态**: ✅ 已完成
**数据质量**: ✅ 已验证
**测试覆盖**: ✅ 基础功能全覆盖