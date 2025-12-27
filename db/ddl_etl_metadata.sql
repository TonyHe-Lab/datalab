-- DDL for etl_metadata table used by incremental ETL and backfill processes
-- Run this in your Postgres database to create the metadata table

CREATE TABLE IF NOT EXISTS etl_metadata (
    table_name TEXT PRIMARY KEY,
    last_successful_extraction TIMESTAMP WITH TIME ZONE,
    last_backfill_cursor TEXT,
    records_processed BIGINT DEFAULT 0,
    last_run_duration_seconds DOUBLE PRECISION,
    last_error TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Example index if queries will frequently filter by last_successful_extraction
CREATE INDEX IF NOT EXISTS idx_etl_metadata_last_extraction ON etl_metadata (last_successful_extraction);
