基于 **Product Manager (John)** 完成的 docs/prd.md 和 **UX Designer** 提供的 docs/frontend-spec.md，我将为你生成一份最终版的 **系统架构文档 (System Architecture Document)**。

这份文档已根据你的最新决策进行了调整：**弃用 Docker 容器化部署，转为 WSL 2 原生 (Bare Metal) 部署**，并详细定义了 WSL 与 Windows 宿主机数据库之间的网络通信方案。

---

执行指令: create-doc  
目标文件: docs/architecture.md  
引用源: docs/prd.md, docs/frontend-spec.md

# ---

**医疗工单智能分析系统架构文档 (System Architecture Document)**

| Attribute        | Details                                                   |
| :--------------- | :-------------------------------------------------------- |
| **Project Name** | AI-Driven Medical Work Order Analysis System              |
| **Version**      | 2.0 (Native WSL Edition)                                  |
| **Status**       | **Approved**                                              |
| **Author**       | Architect Agent                                           |
| **Tech Stack**   | Python 3.12, React 18, PostgreSQL 18 (Host), Azure OpenAI |

## **1. 架构概览 (Executive Summary)**

本系统采用 **WSL 2 原生混合架构 (Hybrid Native Architecture)**。为了最大化单人开发效率并利用现有资源：

- **计算层 (Compute)**: 所有应用服务（后端 API、ETL Worker、前端构建）直接运行在 **WSL 2 (Ubuntu/Debian)** 子系统的用户空间中，由 **PM2** 进行进程管理。
- **数据层 (Data)**: 利用 Windows 宿主机已安装的 **PostgreSQL 18** (带 pgvector 扩展)，避免在 WSL 内重复维护数据库实例。
- **智能层 (AI)**: 桥接 **Azure OpenAI** 服务提供 NLP 能力。

这种架构消除了容器网络和卷挂载的复杂性，提供了类似于“本机开发”的流畅体验，同时保留了 Linux 开发环境的优势。

## **2. 系统上下文 (System Context)**

- **Users**:
  - **维修工程师**: 访问 Web 界面进行故障诊断。
  - **管理人员**: 访问仪表盘查看 MTBF 趋势。
- **Internal Systems (WSL 2)**:
  - **AI Ops System**: 包含 Web Server 和 ETL Process 的核心应用。
- **External Systems**:
  - **Snowflake**: 源数据仓库 (Source of Truth)。
  - **Windows Host Postgres**: 持久化存储与向量检索引擎。
  - **Azure OpenAI**: 模型推理 API (GPT-4o, Embeddings)。

## **3. 组件架构 (Component Architecture)**

### **3.1 核心服务 (Running in WSL 2)**

所有服务运行在 WSL 2 Linux 环境中，通过 venv 隔离 Python 环境。

1. **Backend Service (FastAPI)**
   - **技术栈**: Python 3.12, FastAPI, SQLAlchemy (Async), Pydantic.
   - **职责**:
     - 提供 RESTful API (/api/chat, /api/dashboard).
     - 执行混合搜索 (Hybrid Search) 逻辑。
     - 处理 RAG 上下文组装。
   - **进程管理**: PM2 (pm2 start uvicorn ...).
2. **ETL Worker (Python Script)**

   - **技术栈**: Python 3.12, Snowflake-Connector, LangChain (Optional).
   - **职责**:

     - **Sync**: 增量拉取 Snowflake 数据 1.

     - **Scrub**: 执行 PII 脱敏 (Regex/Presidio)2.

     - **Extract**: 调用 GPT-4o 提取 Json (含 Resolution Steps) 3.

     - **Vectorize**: 生成 Embedding 并写入 Postgres 4.

   - **调度**: PM2 Cron Mode 或 APScheduler.

3. **Frontend App (React)**
   - **技术栈**: React 18, Vite, Ant Design.
   - **部署**: 开发模式下 vite dev, 生产模式下构建静态文件由 Nginx 或 FastAPI StaticFiles 托管。

### **3.2 数据存储 (Windows Host)**

- **PostgreSQL 18**
  - **位置**: Windows 宿主机 (localhost on Windows).
  - **扩展**: vector (必须手动安装).
  - **监听**: 绑定至 0.0.0.0 或指定端口，允许 WSL 访问。

## **4. 关键技术实现 (Key Technical Implementations)**

### **4.1 WSL 与 Windows Host 网络通信 (Critical)**

这是本架构最大的风险点，需严格配置。

1. Host IP 获取:  
   WSL 2 每次重启 IP 会变。应用程序需动态获取宿主机 IP。

   - _方法 A (推荐)_: 解析 /etc/resolv.conf 中的 nameserver。
   - _方法 B_: 使用 $(hostname).local (依赖 mDNS)。
   - _代码实现 (config.py)_:  
     Python  
     import os  
     def get_host_ip():  
      with open('/etc/resolv.conf') as f:  
      for line in f:  
      if 'nameserver' in line:  
      return line.split()[1]  
      return 'localhost'

     DB_HOST = os.getenv('POSTGRES_HOST', get_host_ip())

2. Postgres 配置 (pg_hba.conf on Windows):  
   必须允许来自 WSL 子网的连接。  
   Plaintext

   # Allow WSL 2 Subnet (Example range, adjust as needed)

   host all all 172.0.0.0/8 scram-sha-256

3. Windows Firewall:  
   必须添加入站规则，允许端口 5432 接收来自 WSL IP 的 TCP 连接。

### **4.2 混合搜索算法 (Hybrid Search)**

利用 Postgres 的 SQL 能力实现 RRF 融合 5。

- **SQL Logic**:  
  SQL  
  WITH semantic AS (  
   SELECT log_id, 1/(60 + RANK() OVER (ORDER BY vector <=> :query_vec)) as score  
   FROM semantic_embeddings ORDER BY vector <=> :query_vec LIMIT 20  
  ),  
  keyword AS (  
   SELECT log_id, 1/(60 + RANK() OVER (ORDER BY ts_rank(to_tsvector('english', raw_text), plainto_tsquery(:query_text)) DESC)) as score  
   FROM maintenance_logs WHERE to_tsvector('english', raw_text) @@ plainto_tsquery(:query_text) LIMIT 20  
  )  
  SELECT COALESCE(s.log_id, k.log_id) as id, (COALESCE(s.score, 0) + COALESCE(k.score, 0)) as final_score  
  FROM semantic s FULL OUTER JOIN keyword k ON s.log_id = k.log_id  
  ORDER BY final_score DESC LIMIT 10;

## **5. 数据模型 (Data Model)**

1. **maintenance_logs**: 原始数据快照。
   - id (PK), snowflake_id (Unique), raw_text, last_modified.
2. **ai_extracted_data**: 结构化知识。
   - log_id (FK), component, fault, cause, resolution_steps (Text/JSON), summary.
3. **semantic_embeddings**: 向量索引。
   - log_id (FK), vector (1536 dim, HNSW Index).

## **6. 部署与运维 (Deployment & Ops)**

### **6.1 本地开发 (Development)**

1. **Windows**: 启动 Postgres。
2. **WSL**:
   - cd backend && python3 -m venv venv && source venv/bin/activate
   - pip install -r requirements.txt
   - pm2 start ecosystem.config.js (启动后端和 ETL)。
   - cd frontend && npm run dev.

### **6.2 进程守护 (PM2 Configuration)**

在项目根目录创建 ecosystem.config.js:

JavaScript

module.exports = {  
 apps : [{
 name : "api",
 script : "uvicorn",
 args : "main:app --host 0.0.0.0 --port 8000",
 interpreter: "python3" // 指向 venv 中的 python
 }, {
 name : "etl",
 script : "scripts/etl_job.py",
 interpreter: "python3",
 cron_restart: "0 */4 * * *" // 每 4 小时运行一次
 }]  
}

## **7. 安全考量 (Security Constraints)**

- **Secrets**: API Keys 和 DB 密码 **严禁** 硬编码，必须通过 .env 加载。
- **PII Compliance**: ETL 脚本必须包含 scrub_pii(text) 函数，并在调用 OpenAI 前执行。
- **Network**: FastAPI 默认监听 0.0.0.0 在 WSL 中是安全的（只对宿主机暴露），但需注意不要通过 Windows 端口转发将其暴露到公网。

---

