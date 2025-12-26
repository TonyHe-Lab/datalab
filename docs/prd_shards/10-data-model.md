# 系统架构 — 数据模型

## 主要表结构（概要）

1. maintenance_logs（原始数据快照）
- id (PK), snowflake_id (Unique), raw_text, last_modified

2. ai_extracted_data（结构化知识）
- log_id (FK), component, fault, cause, resolution_steps (Text/JSON), summary

3. semantic_embeddings（向量索引）
- log_id (FK), vector (例如 1536 维), 可配合 HNSW 索引使用

设计要点：保留原始快照以便可审计，结构化表用于快速查询与展示，向量表用于语义检索。
