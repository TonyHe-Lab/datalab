# 系统架构 — 部署与运维

## 本地开发（Development）

1. 在 Windows 上启动 PostgreSQL（确保 pgvector 已安装）。
2. 在 WSL 中：
   - cd backend
   - python3 -m venv venv && source venv/bin/activate
   - pip install -r requirements.txt
   - pm2 start ecosystem.config.js （启动后端与 ETL）
3. 前端：
   - cd frontend && npm run dev （开发）
   - 生产构建后可由 Nginx 或 FastAPI 的 StaticFiles 提供静态文件

## PM2 配置示例（ecosystem.config.js）

module.exports = {
  apps : [{
    name : "api",
    script : "uvicorn",
    args : "main:app --host 0.0.0.0 --port 8000",
    interpreter: "python3"
  }, {
    name : "etl",
    script : "scripts/etl_job.py",
    interpreter: "python3",
    cron_restart: "0 */4 * * *"
  }]
}
