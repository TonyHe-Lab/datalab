```markdown
## 1. Goals and Background Context

### 1.1 Goals

本项目的核心目标是构建一个基于 AI 的智能化分析系统，将非结构化的医疗设备维护日志转化为高价值的结构化知识库。

- **智能化核心**: 利用 Azure OpenAI (GPT-4o) 实现多语言文本的理解与结构化提取，解决术语不统一问题。

- **五维数据提取**: 精准提取 **部件(Component)**、**故障(Fault)**、**原因(Cause)**、**总结(Summary)** 以及 **诊断与修复步骤(Resolution Steps)**，形成可检索的知识资产。

- **业务价值交付**: 提供混合搜索 (Hybrid Search) 和 RAG 智能问答辅助维修决策，并提供 MTBF (平均故障间隔时间) 等关键指标监控。

- **单人极简运维**: 基于 **WSL 2 Bare Metal** (无容器化) 和 **Python 3.12** 的架构，连接宿主机 Postgres 18，最小化运维负担。

### 1.2 Background Context

- **当前痛点**: 医疗设备全生命周期管理 (HTM) 中，海量的维护数据沉淀在 ERP/CMMS 中，多为非结构化文本。由于语言混合（德/英/中）和书写随意，传统基于关键词的检索效率低下，无法有效辅助工程师排查疑难杂症。

- **技术机会**: 利用 LLM 的语义理解和 JSON 结构化输出能力，配合 pgvector 向量检索，可以低成本地挖掘数据价值。

- **实施约束**: 项目由单人全栈负责，必须摒弃 Kubernetes 等复杂架构，采用“模块化单体”和本地原生运行方式 。

### 1.3 Change Log

| Version | Date       | Description                                                                                                         | Author      |
| :------ | :--------- | :------------------------------------------------------------------------------------------------------------------ | :---------- |
| 1.0     | 2024-05-22 | Initial PRD based on Technical Proposal & User Discussion. Defines Hybrid Architecture (WSL+WinDB) and React Stack. | BMAD_METHOD |

```
