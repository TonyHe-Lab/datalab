```markdown
## 2. Requirements

### 2.1 Functional Requirements (FR)

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

### 2.2 Non-Functional Requirements (NFR)

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

```
