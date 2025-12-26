# 系统架构 — 关键技术实现

## 1) WSL 与 Windows Host 网络通信（关键风险点）

概述：WSL2 重启后宿主 IP 会变化，应用需动态解析宿主机地址以访问 Windows 上的 Postgres。

- 推荐方法：从 `/etc/resolv.conf` 解析 `nameserver` 以获取宿主 IP。
- 可选方法：依赖 mDNS 使用 `$(hostname).local`（不稳定）。

示例（config.py）：

import os
def get_host_ip():
    with open('/etc/resolv.conf') as f:
        for line in f:
            if 'nameserver' in line:
                return line.split()[1]
    return 'localhost'

DB_HOST = os.getenv('POSTGRES_HOST', get_host_ip())

注意：Windows 上需在 `pg_hba.conf` 中允许 WSL 子网连接，并在防火墙中开通 5432 入站规则。

## 2) 混合搜索（Hybrid Search）

思路：融合基于向量的语义检索与关键词检索，使用加权或 RRF 等融合策略返回高质量候选。

示例 SQL（简化）：

WITH semantic AS (
  SELECT log_id, 1/(60 + RANK() OVER (ORDER BY vector <=> :query_vec)) as score
  FROM semantic_embeddings ORDER BY vector <=> :query_vec LIMIT 20
),
keyword AS (
  SELECT log_id, 1/(60 + RANK() OVER (ORDER BY ts_rank(to_tsvector('english', raw_text), plainto_tsquery(:query_text)) DESC)) as score
  FROM maintenance_logs WHERE to_tsvector('english', raw_text) @@ plainto_tsquery(:query_text) LIMIT 20
)
SELECT COALESCE(s.log_id, k.log_id) as id, (COALESCE(s.score,0)+COALESCE(k.score,0)) as final_score
FROM semantic s FULL OUTER JOIN keyword k ON s.log_id = k.log_id
ORDER BY final_score DESC LIMIT 10;
