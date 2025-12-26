**产品需求文档 (PRD)**。

---

执行指令: doc-out  
目标文件: docs/prd.md

# ---

**AI-Driven Medical Work Order Analysis System PRD**

| Attribute        | Details                                                                  |
| :--------------- | :----------------------------------------------------------------------- |
| **Project Name** | AI 驱动的医疗工单分析系统 (AI-Driven Medical Work Order Analysis System) |
| **Version**      | 1.0                                                                      |
| **Status**       | Draft                                                                    |
| **Author**       | BMAD_METHOD Agent                                                        |
| **Date**         | 2024-05-22                                                               |

## **1. Goals and Background Context**

### **1.1 Goals**

本项目的核心目标是构建一个基于 AI 的智能化分析系统，将非结构化的医疗设备维护日志转化为高价值的结构化知识库。

- **智能化核心**: 利用 Azure OpenAI (GPT-4o) 实现多语言文本的理解与结构化提取，解决术语不统一问题。

- **五维数据提取**: 精准提取 **部件(Component)**、**故障(Fault)**、**原因(Cause)**、**总结(Summary)** 以及 **诊断与修复步骤(Resolution Steps)**，形成可检索的知识资产。

- **业务价值交付**: 提供混合搜索 (Hybrid Search) 和 RAG 智能问答辅助维修决策，并提供 MTBF (平均故障间隔时间) 等关键指标监控。

- **单人极简运维**: 基于 **WSL 2 Bare Metal** (无容器化) 和 **Python 3.12** 的架构，连接宿主机 Postgres 18，最小化运维负担。

### **1.2 Background Context**

- **当前痛点**: 医疗设备全生命周期管理 (HTM) 中，海量的维护数据沉淀在 ERP/CMMS 中，多为非结构化文本。由于语言混合（德/英/中）和书写随意，传统基于关键词的检索效率低下，无法有效辅助工程师排查疑难杂症。

- **技术机会**: 利用 LLM 的语义理解和 JSON 结构化输出能力，配合 pgvector 向量检索，可以低成本地挖掘数据价值。

- **实施约束**: 项目由单人全栈负责，必须摒弃 Kubernetes 等复杂架构，采用“模块化单体”和本地原生运行方式 。

### **1.3 Change Log**

| Version | Date       | Description                                                                                                         | Author      |
| :------ | :--------- | :------------------------------------------------------------------------------------------------------------------ | :---------- |
| 1.0     | 2024-05-22 | Initial PRD based on Technical Proposal & User Discussion. Defines Hybrid Architecture (WSL+WinDB) and React Stack. | BMAD_METHOD |

## **2. Requirements**

### **2.1 Functional Requirements (FR)**

**FR1: 增量数据摄取 (Incremental Data Ingestion)**

- 系统必须通过 Python 脚本连接 Snowflake 数据仓库。
- 必须基于 LAST_MODIFIED 时间戳和 etl_metadata 表中的水位线，仅拉取增量更新的工单 。

- 数据写入 Postgres 必须具备幂等性 (Idempotency)，使用 UPSERT 逻辑防止重复。

**FR2: 敏感数据脱敏 (PII Scrubbing)**

- 在将文本发送给 Azure OpenAI 之前，必须移除患者姓名、病历号等敏感信息，确保符合 HIPAA 合规要求。

**FR3: AI 结构化提取 (AI Structured Extraction)**

- 系统利用 GPT-4o 的 JSON Mode 从清洗后的文本中提取以下字段：
  - Component: 故障部件 (如 "X-Ray Tube")。
  - Fault: 故障现象或代码 (如 "Error 305")。
  - Root Cause: 根本原因 (如 "Filament open circuit")。
  - Resolution: **详细的诊断步骤与修复措施** (用户新增需求)。
  - Summary: 标准化的英文技术摘要。

**FR4: 混合向量存储与检索 (Hybrid Vector Storage & Search)**

- 必须将“故障+总结+修复”组合文本转换为 1536 维向量 (text-embedding-3-small)。

- 实现混合搜索算法，结合 Postgres 全文检索 (BM25) 和 向量相似度 (HNSW)，通过 RRF (倒数排名融合) 算法合并结果。

**FR5: 智能问答与看板 (RAG & Analytics)**

- 提供 RAG 接口：基于检索到的 Top 5 相似案例，生成维修建议。
- 提供统计接口：自动计算 MTBF (滚动平均) 和 Top 10 故障部件 Pareto 分布。

### **2.2 Non-Functional Requirements (NFR)**

**NFR1: 运行环境约束 (WSL Native)**

- 系统后端和 ETL 脚本必须直接运行在 WSL 2 (Ubuntu/Debian) 环境中。
- **Python 版本必须为 3.12**。
- 进程管理应使用 PM2 或 Systemd，确保服务在 WSL 启动时自动运行。

**NFR2: 外部数据库集成 (External DB Integration)**

- 系统必须连接运行在 Windows 宿主机的 **PostgreSQL 18**。
- 必须确保宿主机 Postgres 已手动安装并启用了 pgvector 扩展。

- 网络配置必须允许 WSL 子网访问宿主机 5432 端口。

**NFR3: 性能与资源 (Performance)**

- 单次 ETL 批处理限制为 5000 条记录，防止内存溢出。

- 向量索引查询响应时间应在毫秒级 (依赖 HNSW 索引)。

## **3. UI Design Goals**

### **3.1 UX Vision**

- **工程师导向**: 界面采用高密度信息展示，风格简洁专业 (Ant Design)。
- **分离视图**: 明确区分“诊断工作台 (一线维修)”和“管理仪表盘 (宏观分析)”。

### **3.2 Core Screens**

1. **智能诊断工作台 (Diagnostic Workbench)**
   - 提供类似 Chat 的自然语言输入框。
   - 左侧/底部展示 AI 生成的建议 (Markdown 渲染)。
   - 右侧展示 "Reference Cases" (佐证)，列出相似的历史工单详情。
2. **趋势监控仪表盘 (Analytics Dashboard)**
   - **MTBF 趋势图**: 使用折线图展示设备可靠性变化。
   - **故障 Pareto 图**: 使用条形图展示高频故障原因。
   - 支持按“时间范围”和“设备型号”筛选。

### **3.3 Technology Stack (Frontend)**

- **Framework**: React (Vite) Single Page Application.
- **Component Library**: **Ant Design** (for efficiency).
- **Charting Library**: **Recharts** (for visualization).

## **4. Technical Constraints & Assumptions**

### **4.1 Technology Stack**

- **Frontend**: React + Ant Design + Recharts (Monorepo /frontend).
- **Backend**: Python 3.12 + FastAPI (Monorepo /backend).
- **ETL**: Python 3.12 Scripts + Snowflake Connector.
- **Database**: PostgreSQL 18 (Windows Host) + pgvector extension.
- **AI**: Azure OpenAI (GPT-4o, text-embedding-3-small).

### **4.2 Code Organization**

- **Repository**: Monorepo structure.
- **Process Manager**: PM2 (running inside WSL).

## **5. Epic List**

### **Epic 1: Infrastructure & Environment Setup**

**Goal**: 配置 WSL 2 运行环境并打通与 Windows 宿主机的数据库连接。

- **Story 1.1**: WSL Python 3.12 & Node Environment Setup.
- **Story 1.2**: Windows Host Postgres Configuration (pg_hba.conf & Firewall).
- **Story 1.3**: Database Schema & Extension Validation (Ensure vector extension exists).

### **Epic 2: AI Core & Data Pipeline**

**Goal**: 实现从 Snowflake 的数据同步及 AI 结构化提取。

- **Story 2.1**: Incremental ETL Script (Snowflake to Postgres)18.

- **Story 2.2**: Pydantic Schema Definition (Inc. Resolution Steps).
- **Story 2.3**: Azure OpenAI Integration & PII Scrubbing Logic.

- **Story 2.4**: Backfill Tool for Historical Data Processing.

### **Epic 3: Backend Services & Hybrid Search**

**Goal**: 构建 FastAPI 服务层，提供搜索与分析 API。

- **Story 3.1**: FastAPI Skeleton & Async DB Connection.
- **Story 3.2**: Hybrid Search Implementation (SQL with RRF Logic).

- **Story 3.3**: RAG Chat Endpoint Implementation.
- **Story 3.4**: Analytics SQL Views & Endpoints (MTBF/Pareto).

### **Epic 4: React Frontend & Visualization**

**Goal**: 构建用户界面并完成端到端集成。

- **Story 4.1**: React App Setup with Ant Design.
- **Story 4.2**: Diagnostic Workbench UI Implementation.
- **Story 4.3**: Analytics Dashboard with Recharts.
- **Story 4.4**: Final Integration Testing (End-to-End).

---

**PRD 生成完毕。**
