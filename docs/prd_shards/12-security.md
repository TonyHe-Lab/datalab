# 系统架构 — 安全考量

- Secrets：API Keys 与 DB 凭证不得硬编码，应通过 `.env` 或系统级密钥管理加载。
- PII 合规：ETL 必须实现 `scrub_pii(text)`，在调用 OpenAI 前清洗敏感信息。
- 网络：FastAPI 在 WSL 中监听 `0.0.0.0` 是对宿主机可用，但必须谨慎避免将端口公开至公网。
- DB 安全：在 `pg_hba.conf` 中仅允许可信子网，启用 scram-sha-256 等安全认证机制。
