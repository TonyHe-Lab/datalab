-- db/init_schema.sql
-- Idempotent schema setup for maintenance_logs, ai_extracted_data, semantic_embeddings
-- Create pgvector extension if available (requires superuser)
CREATE EXTENSION IF NOT EXISTS vector;
-- maintenance_logs
CREATE TABLE IF NOT EXISTS maintenance_logs (
    id SERIAL PRIMARY KEY,
    snowflake_id TEXT UNIQUE,
    raw_text TEXT NOT NULL,
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT now()
);
-- ai_extracted_data
CREATE TABLE IF NOT EXISTS ai_extracted_data (
    id SERIAL PRIMARY KEY,
    log_id INTEGER NOT NULL REFERENCES maintenance_logs(id) ON DELETE CASCADE,
    component TEXT,
    fault TEXT,
    cause TEXT,
    resolution_steps JSONB,
    summary TEXT
);
-- semantic_embeddings (pgvector)
CREATE TABLE IF NOT EXISTS semantic_embeddings (
    log_id INTEGER NOT NULL REFERENCES maintenance_logs(id) ON DELETE CASCADE,
    vector vector(1536),
    PRIMARY KEY (log_id)
);
-- Example index for vector search (adjust based on pgvector version and capabilities)
-- Note: ivfflat requires additional steps like `ANALYZE` and may need special parameters
DO $$ BEGIN IF NOT EXISTS (
    SELECT 1
    FROM pg_class
    WHERE relname = 'semantic_embeddings_vector_idx'
) THEN EXECUTE 'CREATE INDEX semantic_embeddings_vector_idx ON semantic_embeddings USING ivfflat (vector) WITH (lists = 100);';
END IF;
EXCEPTION
WHEN others THEN RAISE NOTICE 'Could not create ivfflat index; extension or feature may be missing.';
END $$;