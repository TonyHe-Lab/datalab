# 系统架构 — 概览

| Attribute        | Details                                                   |
| :--------------- | :-------------------------------------------------------- |
| **Project Name** | AI-Driven Medical Work Order Analysis System              |
| **Version**      | 2.0 (Native WSL Edition)                                  |
| **Status**       | **Approved**                                              |
| **Author**       | Architect Agent                                           |
| **Tech Stack**   | Python 3.12, React 18, PostgreSQL 18 (Host), Azure OpenAI |

## 架构概述

本系统采用 **WSL 2 原生混合架构 (Hybrid Native Architecture)**。主要决策点：

- 计算层：后端 API、ETL Worker 与前端构建运行在 WSL 2 (Ubuntu/Debian) 内，使用 venv 隔离，PM2 管理进程。
- 数据层：使用 Windows 宿主机上的 PostgreSQL 18（含 pgvector）作为持久化与向量检索引擎。
- 智能层：外部调用 Azure OpenAI（模型与 Embeddings）。

设计目标：消除容器化带来的卷与网络复杂性，提供接近“本机开发”的体验，同时保留 Linux 开发环境优势。
