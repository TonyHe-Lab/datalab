# Epic 2 启动计划: AI Core & Data Pipeline

## 🎯 Epic 2 目标
实现从 Snowflake 的数据同步及 AI 结构化提取，建立完整的数据处理管道。

## 📋 故事分解 (基于PRD)

### Story 2.1: Incremental ETL Script (Snowflake to Postgres)
- **目标**: 创建增量ETL脚本，从Snowflake同步数据到Postgres
- **技术栈**: Python, Snowflake Connector, psycopg, Apache Airflow/Luigi (可选)
- **关键需求**: 增量同步、错误处理、重试机制、监控

### Story 2.2: Pydantic Schema Definition (Inc. Resolution Steps)
- **目标**: 定义数据模型和验证模式
- **技术栈**: Pydantic, Python类型提示
- **关键需求**: 完整的维护日志schema、AI提取数据schema、验证规则

### Story 2.3: Azure OpenAI Integration & PII Scrubbing Logic
- **目标**: 集成Azure OpenAI进行文本分析，实现PII脱敏
- **技术栈**: Azure OpenAI SDK, regex/PII检测库
- **关键需求**: API集成、成本控制、PII检测与脱敏、错误处理

### Story 2.4: Backfill Tool for Historical Data Processing
- **目标**: 创建历史数据回填工具
- **技术栈**: Python, 批处理框架
- **关键需求**: 大规模数据处理、进度跟踪、错误恢复

## 🚀 启动步骤

### 步骤1: 环境准备 (基于Epic 1)
```bash
# 确保Epic 1环境就绪
./dev/verify_env.sh  # 验证基础环境
```

### 步骤2: 创建Epic 2工作分支
```bash
git checkout main
git pull origin main  # 确保获取Epic 1合并后的代码
git checkout -b feat/epic2-ai-core-data-pipeline
```

### 步骤3: 设置项目结构
```bash
# 创建Epic 2专用目录
mkdir -p src/etl src/models src/ai src/utils
mkdir -p tests/etl tests/models tests/ai
mkdir -p config docs/epic2
```

### 步骤4: 依赖管理
```bash
# 更新requirements.txt添加Epic 2依赖
cat >> requirements.txt << 'REQS'
# Epic 2: AI Core & Data Pipeline
snowflake-connector-python>=3.0.0
pydantic>=2.0.0
openai>=1.0.0
azure-identity>=1.0.0
pandas>=2.0.0  # 数据处理
python-dotenv>=1.0.0  # 环境变量管理
REQS
```

## 📁 建议的项目结构
```
datalab/
├── src/
│   ├── etl/              # ETL管道
│   │   ├── snowflake_loader.py
│   │   ├── postgres_writer.py
│   │   └── incremental_sync.py
│   ├── models/           # 数据模型
│   │   ├── schemas.py    # Pydantic schemas
│   │   └── entities.py   # 数据库实体
│   ├── ai/               # AI集成
│   │   ├── openai_client.py
│   │   ├── pii_scrubber.py
│   │   └── text_analyzer.py
│   └── utils/
│       ├── config.py
│       └── logging.py
├── tests/
│   ├── etl/
│   ├── models/
│   └── ai/
├── config/
│   ├── etl_config.yaml
│   └── ai_config.yaml
├── scripts/              # 工具脚本
│   ├── backfill.py
│   └── validate_etl.py
└── docs/epic2/          # Epic 2文档
    ├── architecture.md
    └── api_reference.md
```

## 🔧 技术决策

### 1. ETL框架选择
- **选项A**: 自定义Python脚本 + 调度器 (简单直接)
- **选项B**: Apache Airflow (功能强大，学习曲线陡)
- **选项C**: Prefect/Luigi (中等复杂度)
- **建议**: 从自定义脚本开始，需要时升级到Airflow

### 2. 数据验证
- 使用Pydantic进行运行时数据验证
- 创建数据质量检查脚本
- 实现数据血缘跟踪

### 3. AI集成策略
- Azure OpenAI for GPT-4/GPT-3.5
- 实现请求批处理以减少API调用
- 添加速率限制和退避重试
- PII检测: 使用正则表达式 + 预训练模型

## 📊 成功指标

### 技术指标
- ✅ ETL脚本处理1000条记录/分钟
- ✅ PII检测准确率 > 95%
- ✅ API错误率 < 1%
- ✅ 数据验证覆盖率 100%

### 业务指标
- ✅ 从Snowflake到Postgres的数据延迟 < 5分钟
- ✅ AI提取的结构化数据准确率 > 90%
- ✅ 历史数据回填完成时间 < 24小时 (100万条记录)

## 🗓️ 时间估算

| 故事 | 复杂度 | 估算时间 | 依赖 |
|------|--------|----------|------|
| 2.1 | 高 | 5-7天 | Epic 1完成 |
| 2.2 | 中 | 3-4天 | 2.1部分完成 |
| 2.3 | 高 | 5-6天 | 2.2完成 |
| 2.4 | 中 | 4-5天 | 2.1, 2.3完成 |

**总估算**: 17-22个工作日

## 🚨 风险与缓解

### 高风险
1. **Snowflake连接性能**: 测试连接池和查询优化
2. **Azure OpenAI成本控制**: 实现使用量监控和预算警报
3. **PII检测准确性**: 多阶段验证 (正则 + 模型 + 人工抽查)

### 中风险
1. **增量同步逻辑**: 实现完善的CDC机制
2. **历史数据回填性能**: 分批处理，添加进度跟踪

## 📞 下一步行动

### 立即行动 (今天)
1. 创建Epic 2分支: `feat/epic2-ai-core-data-pipeline`
2. 设置项目结构
3. 创建Story 2.1的初始故事文件

### 短期行动 (本周)
1. 实现Snowflake连接测试
2. 设计增量ETL架构
3. 创建Pydantic schema草案

### 长期规划
1. 建立CI/CD管道
2. 实现监控和告警
3. 文档和知识转移

---

**Epic 1状态**: ✅ 完成 (等待合并)  
**Epic 2状态**: 🚀 准备启动  
**生成时间**: 2025-12-27  
**负责人**: 待指定
