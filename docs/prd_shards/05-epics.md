```markdown
## 5. Epic List

### Epic 1: Infrastructure & Environment Setup

**Goal**: 配置 WSL 2 运行环境并打通与 Windows 宿主机的数据库连接。

- **Story 1.1**: WSL Python 3.12 & Node Environment Setup.
- **Story 1.2**: Windows Host Postgres Configuration (pg_hba.conf & Firewall).
- **Story 1.3**: Database Schema & Extension Validation (Ensure vector extension exists).

### Epic 2: AI Core & Data Pipeline

**Goal**: 实现从 Snowflake 的数据同步及 AI 结构化提取。

- **Story 2.1**: Incremental ETL Script (Snowflake to Postgres)18.
- **Story 2.2**: Pydantic Schema Definition (Inc. Resolution Steps).
- **Story 2.3**: Azure OpenAI Integration & PII Scrubbing Logic.
- **Story 2.4**: Backfill Tool for Historical Data Processing.

### Epic 3: Backend Services & Hybrid Search

**Goal**: 构建 FastAPI 服务层，提供搜索与分析 API。

- **Story 3.1**: FastAPI Skeleton & Async DB Connection.
- **Story 3.2**: Hybrid Search Implementation (SQL with RRF Logic).
- **Story 3.3**: RAG Chat Endpoint Implementation.
- **Story 3.4**: Analytics SQL Views & Endpoints (MTBF/Pareto).

### Epic 4: React Frontend & Visualization

**Goal**: 构建用户界面并完成端到端集成。

- **Story 4.1**: React App Setup with Ant Design.
- **Story 4.2**: Diagnostic Workbench UI Implementation.
- **Story 4.3**: Analytics Dashboard with Recharts.
- **Story 4.4**: Final Integration Testing (End-to-End).

---

**PRD 生成完毕。**

```
