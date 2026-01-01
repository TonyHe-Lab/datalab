# Snowflake 生产数据拉取工具使用指南

## 📋 概述

这个工具用于从Snowflake数据仓库拉取医疗设备故障诊断与分析平台的生产数据。支持自定义SQL查询、数据导出和增量数据提取。

## 🚀 快速开始

### 1. 环境配置

确保已配置正确的Snowflake连接信息在 `config/.env` 文件中：

```bash
# Snowflake配置
SNOWFLAKE_ACCOUNT=yu83356.west-europe.azure.snowflakecomputing.com
SNOWFLAKE_USER=linwei.he@siemens-healthineers.com
SNOWFLAKE_AUTHENTICATOR=externalbrowser  # 使用浏览器认证
SNOWFLAKE_WAREHOUSE=WH_SDTB_INT_XP_DC_R
SNOWFLAKE_DATABASE=SDM_PROD
SNOWFLAKE_SCHEMA=public
```

### 2. 安装依赖

```bash
# 安装Snowflake连接器
pip install snowflake-connector-python

# 安装其他依赖
pip install pydantic pydantic-settings
```

### 3. 基本用法

#### 列出所有表
```bash
cd /home/tonyhe/TonyHe-Gitlab/datalab
python scripts/snowflake_data_puller.py --list-tables
```

#### 查看表结构
```bash
python scripts/snowflake_data_puller.py --schema maintenance_logs
```

#### 执行自定义查询
```bash
python scripts/snowflake_data_puller.py --query "SELECT * FROM maintenance_logs LIMIT 10"
```

#### 从文件执行查询
```bash
python scripts/snowflake_data_puller.py --file scripts/sample_queries/medical_device_queries.sql --limit 100
```

## 📊 常用查询示例

### 1. 故障工单数据提取

```sql
-- 最近30天的故障工单
SELECT * FROM maintenance_logs
WHERE reported_date >= DATEADD(day, -30, CURRENT_DATE())
ORDER BY reported_date DESC
LIMIT 1000;
```

### 2. 设备故障统计

```sql
-- 按设备类型统计
SELECT device_type, COUNT(*) as fault_count
FROM maintenance_logs
WHERE reported_date >= DATEADD(month, -6, CURRENT_DATE())
GROUP BY device_type
ORDER BY fault_count DESC;
```

### 3. 增量数据提取

```bash
# 提取自上次检查点以来的新数据
python scripts/snowflake_data_puller.py --incremental \
  --table maintenance_logs \
  --watermark updated_at \
  --last-extraction "2024-12-01 00:00:00"
```

## 📁 数据导出

### 导出到CSV
```bash
python scripts/snowflake_data_puller.py \
  --query "SELECT * FROM maintenance_logs LIMIT 100" \
  --output data/maintenance_logs.csv \
  --format csv
```

### 导出到JSON
```bash
python scripts/snowflake_data_puller.py \
  --query "SELECT device_type, COUNT(*) as count FROM maintenance_logs GROUP BY device_type" \
  --output reports/device_stats.json \
  --format json
```

## 🔧 高级功能

### 1. 批量数据提取

创建批量提取脚本 `extract_batch.sh`:

```bash
#!/bin/bash
# 批量提取不同时间范围的数据

START_DATE="2024-01-01"
END_DATE="2024-12-31"

python scripts/snowflake_data_puller.py \
  --query "SELECT * FROM maintenance_logs WHERE reported_date BETWEEN '$START_DATE' AND '$END_DATE'" \
  --output "data/maintenance_logs_2024.csv" \
  --format csv
```

### 2. 自动化ETL流程

创建Python脚本 `automated_etl.py`:

```python
#!/usr/bin/env python3
import subprocess
from datetime import datetime, timedelta

def run_etl():
    # 计算日期范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    # 构建查询
    query = f"""
    SELECT * FROM maintenance_logs
    WHERE reported_date BETWEEN '{start_date.strftime('%Y-%m-%d')}'
    AND '{end_date.strftime('%Y-%m-%d')}'
    """

    # 执行提取
    output_file = f"data/weekly_{end_date.strftime('%Y%m%d')}.csv"

    cmd = [
        "python", "scripts/snowflake_data_puller.py",
        "--query", query,
        "--output", output_file,
        "--format", "csv"
    ]

    subprocess.run(cmd, check=True)
    print(f"数据已提取到: {output_file}")

if __name__ == "__main__":
    run_etl()
```

### 3. 数据质量检查

```bash
# 检查数据完整性
python scripts/snowflake_data_puller.py \
  --query """
  SELECT
    COUNT(*) as total_records,
    COUNT(DISTINCT device_id) as unique_devices,
    MIN(reported_date) as earliest_date,
    MAX(reported_date) as latest_date,
    SUM(CASE WHEN symptom_description IS NULL THEN 1 ELSE 0 END) as missing_symptoms
  FROM maintenance_logs
  WHERE reported_date >= DATEADD(month, -3, CURRENT_DATE())
  """ \
  --output reports/data_quality.json \
  --format json
```

## 🎯 医疗设备特定查询

### 1. MTBF分析查询
```sql
-- 设备平均故障间隔时间
WITH fault_intervals AS (
    SELECT
        device_id,
        reported_date,
        LAG(reported_date) OVER (PARTITION BY device_id ORDER BY reported_date) as prev_fault_date
    FROM maintenance_logs
    WHERE status = 'CLOSED'
)
SELECT
    device_id,
    AVG(DATEDIFF(hour, prev_fault_date, reported_date)) as avg_mtbf_hours
FROM fault_intervals
WHERE prev_fault_date IS NOT NULL
GROUP BY device_id
HAVING COUNT(*) >= 3;
```

### 2. Pareto分析
```sql
-- 最常见的故障症状（80/20分析）
SELECT
    symptom_category,
    COUNT(*) as occurrence_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM maintenance_logs
WHERE reported_date >= DATEADD(year, -1, CURRENT_DATE())
GROUP BY symptom_category
ORDER BY occurrence_count DESC;
```

### 3. 预测性维护指标
```sql
-- 识别需要预防性维护的设备
SELECT
    device_id,
    device_type,
    COUNT(*) as fault_count_last_year,
    AVG(resolution_time_hours) as avg_repair_time,
    DATEDIFF(day, MAX(reported_date), CURRENT_DATE()) as days_since_last_fault
FROM maintenance_logs
WHERE reported_date >= DATEADD(year, -1, CURRENT_DATE())
GROUP BY device_id, device_type
HAVING COUNT(*) >= 3
ORDER BY fault_count_last_year DESC;
```

## 🔍 故障排除

### 1. 连接问题
```bash
# 测试连接
python -c "
from src.utils.config import load_config
from src.etl.snowflake_loader import SnowflakeClient

config = load_config()
client = SnowflakeClient(config.snowflake)
print('连接测试:', '成功' if client.connect() else '失败')
"
```

### 2. 权限问题
- 确保用户有正确的数据库访问权限
- 检查仓库（warehouse）权限
- 验证角色（role）配置

### 3. 查询性能优化
- 使用适当的LIMIT子句
- 添加日期范围过滤
- 创建物化视图用于频繁查询

## 📈 监控和日志

### 查看执行日志
```bash
# 启用详细日志
export LOG_LEVEL=DEBUG
python scripts/snowflake_data_puller.py --list-tables
```

### 监控数据提取
```bash
# 记录提取统计信息
python scripts/snowflake_data_puller.py \
  --query "SELECT COUNT(*) as record_count FROM maintenance_logs" \
  --output logs/extraction_stats_$(date +%Y%m%d_%H%M%S).json \
  --format json
```

## 🏥 医疗设备数据模型参考

### 主要数据表
1. **maintenance_logs** - 维护工单记录
   - ticket_id, device_id, device_type, symptom_description
   - reported_date, resolved_date, status, priority

2. **device_inventory** - 设备清单
   - device_id, device_type, model, serial_number
   - installation_date, warranty_expiry, facility_id

3. **spare_parts_usage** - 备件使用记录
   - usage_id, ticket_id, part_code, quantity, unit_cost

4. **technician_performance** - 技术人员绩效
   - technician_id, assigned_tickets, resolution_rate, avg_time

### 数据关系
```
maintenance_logs
    ├── device_inventory (device_id)
    ├── spare_parts_usage (ticket_id)
    └── technician_performance (technician_id)
```

## 📋 最佳实践

### 1. 安全实践
- 不要将凭据提交到版本控制
- 使用环境变量管理敏感信息
- 定期轮换访问令牌

### 2. 数据管理
- 定期清理旧数据文件
- 备份重要查询结果
- 验证数据完整性

### 3. 性能优化
- 使用增量提取减少数据量
- 在非高峰时段运行大型查询
- 监控查询执行时间

## 🆘 支持

### 常见问题
1. **认证失败**：检查authenticator设置（snowflake/externalbrowser）
2. **查询超时**：增加查询超时设置或优化查询
3. **内存不足**：减少批量大小或使用流式处理

### 获取帮助
- 查看Snowflake文档：https://docs.snowflake.com/
- 检查项目日志文件
- 联系数据库管理员

---

**最后更新**: 2026-01-01
**版本**: 1.0.0
**维护者**: 医疗设备故障诊断与分析平台团队