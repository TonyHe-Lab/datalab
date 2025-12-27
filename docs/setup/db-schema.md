# DB Schema: running migrations and required privileges

This document explains how to run the `db/init_schema.sql` migration and the privileges required.

Running the SQL file:

1. Ensure you have a Postgres connection URL in env var `DATABASE_URL` (or `POSTGRES_URL`).

2. Apply the migration using psql (no credentials should be hard-coded):

```bash
psql "$DATABASE_URL" -f db/init_schema.sql
```

Notes on privileges:
- Creating extensions such as `vector` typically requires a superuser or a role with CREATE privilege on the database. If you don't have permission, the migration will log a notice and continue; the schema will use a fallback `bytea` storage for embeddings.
- Application runtime user only needs standard DML privileges for inserts/selects; index creation may require elevated privileges depending on your DB hosting.

Rollback:
- This migration is primarily additive and idempotent. To rollback manually, DROP the created tables and indexes in the reverse order. Example:

```sql
DROP VIEW IF EXISTS public.semantic_embeddings_info;
DROP INDEX IF EXISTS semantic_embeddings_vector_hnsw_idx;
DROP INDEX IF EXISTS semantic_embeddings_vector_ivfflat_idx;
DROP INDEX IF EXISTS maintenance_logs_raw_text_idx;
DROP INDEX IF EXISTS ai_extracted_data_summary_idx;
DROP TABLE IF EXISTS semantic_embeddings;
DROP TABLE IF EXISTS ai_extracted_data;
DROP TABLE IF EXISTS maintenance_logs;
```

CI guidance:
- For CI, run the migration against an ephemeral test Postgres instance (e.g., via docker-compose or Testcontainers) and then run `dev/verify_db_schema.py` with `DATABASE_URL` set.
