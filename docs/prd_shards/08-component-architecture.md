# 系统架构 — 组件架构

## 运行在 WSL 2 的核心服务

### Backend Service (FastAPI)
- 技术栈：Python 3.12, FastAPI, SQLAlchemy (Async), Pydantic
- 职责：提供 RESTful API（/api/chat, /api/dashboard）、执行混合搜索（Hybrid Search）、组装 RAG 上下文
- 进程管理：PM2（例如用 pm2 启动 uvicorn）

### ETL Worker
- 技术栈：Python 3.12, Snowflake-Connector, 可选 LangChain
- 职责：增量拉取 Snowflake 数据、PII 脱敏、调用模型提取结构化 JSON、生成 Embedding 并写入 Postgres
- 调度：PM2 Cron Mode 或 APScheduler

### Frontend App (React)
- 技术栈：React 18, Vite, Ant Design
- 开发：vite dev；生产：构建静态文件并由 Nginx 或 FastAPI StaticFiles 托管

## 数据存储（Windows Host）

- PostgreSQL 18（Host）：安装 pgvector 扩展，监听可被 WSL 访问的地址/端口
