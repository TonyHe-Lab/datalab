# 系统架构 — 数据模型

## 主要表结构（概要）

1. notification_text（通知工单主表）
- notification_id (PK), notification_date, notification_assigned_date, notification_closed_date
- noti_category_id, sys_eq_id, noti_country_id, sys_fl_id, sys_mat_id, sys_serial_id
- notification_trendcode_l1, notification_trendcode_l2, notification_trendcode_l3
- **notification_issue_type** (新增：问题类型分类，如硬件故障、软件问题等)
- notification_medium_text, notification_text
- created_at, updated_at

2. ai_extracted_data（结构化知识）
- id (PK), notification_id (FK), keywords_ai, primary_symptom_ai, root_cause_ai
- summary_ai, solution_ai, solution_type_ai, components_ai, processes_ai
- main_component_ai, main_process_ai, confidence_score_ai, extracted_at, model_version

3. semantic_embeddings（向量索引）
- notification_id (FK), source_text_ai, vector (1536维), created_at

4. etl_metadata（ETL元数据）
- id (PK), table_name, last_sync_timestamp, rows_processed
- sync_status, error_message, created_at, updated_at

设计要点：保留原始快照以便可审计，结构化表用于快速查询与展示，向量表用于语义检索，新增问题类型字段支持精细化分类分析。
