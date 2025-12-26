```markdown
## 4. Technical Constraints & Assumptions

### 4.1 Technology Stack

- **Frontend**: React + Ant Design + Recharts (Monorepo /frontend).
- **Backend**: Python 3.12 + FastAPI (Monorepo /backend).
- **ETL**: Python 3.12 Scripts + Snowflake Connector.
- **Database**: PostgreSQL 18 (Windows Host) + pgvector extension.
- **AI**: Azure OpenAI (GPT-4o, text-embedding-3-small).

### 4.2 Code Organization

- **Repository**: Monorepo structure.
- **Process Manager**: PM2 (running inside WSL).

```
