# 系统架构 — 系统上下文

## 用户与外部系统

- 维修工程师：通过 Web 界面使用故障诊断与检索功能。
- 管理人员：通过仪表盘查看统计与趋势（如 MTBF）。

## 内部系统（WSL 2）

- AI Ops System：包含后端 Web 服务与 ETL 进程，运行于 WSL 2 环境中。

## 外部系统

- Snowflake：源数据仓库（Source of Truth）。
- Windows Host PostgreSQL：持久化存储与向量检索（pgvector）。
- Azure OpenAI：模型推理与 Embeddings 服务（GPT 系列）。
