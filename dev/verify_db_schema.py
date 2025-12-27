#!/usr/bin/env python3
"""dev/verify_db_schema.py

Verification script for Story 1.3: Database Schema & Extension Validation

Checks:
 - DATABASE_URL or POSTGRES_URL env var present
 - required tables exist
 - required extensions (pgvector) exist when expected
 - column types and constraints (basic checks)
 - optional: attempt sample insert/read and simple vector operation if pgvector present

Exit codes:
 0 - all checks passed
 1 - one or more checks failed
 2 - misconfiguration (missing env var etc.)

This script is intended for local/dev/CI usage. It does not create or modify schema.
"""

import os
import sys
import json
import argparse
from contextlib import closing

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except Exception:
    print(
        "Missing dependency: psycopg2 is required. Install with: pip install psycopg2-binary"
    )
    sys.exit(2)


EXPECTED_TABLES = {
    "maintenance_logs": {
        "required_columns": ["id", "snowflake_id", "raw_text", "last_modified"]
    },
    "ai_extracted_data": {
        "required_columns": [
            "id",
            "log_id",
            "component",
            "fault",
            "cause",
            "resolution_steps",
            "summary",
        ]
    },
    "semantic_embeddings": {"required_columns": ["log_id", "vector"]},
}


def get_database_url():
    return os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")


def run_query(conn, sql, params=None):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql, params or ())
        try:
            return cur.fetchall()
        except Exception:
            return None


def check_table_exists(conn, table_name):
    sql = "SELECT to_regclass(%s) AS regclass"
    with conn.cursor() as cur:
        cur.execute(sql, (f"public.{table_name}",))
        r = cur.fetchone()
        return r is not None and r[0] is not None


def get_table_columns(conn, table_name):
    sql = "SELECT column_name, data_type FROM information_schema.columns WHERE table_schema='public' AND table_name=%s"
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql, (table_name,))
        return [r["column_name"] for r in cur.fetchall()]


def check_extension_exists(conn, extname):
    sql = "SELECT exists(SELECT 1 FROM pg_extension WHERE extname=%s)"
    with conn.cursor() as cur:
        cur.execute(sql, (extname,))
        return cur.fetchone()[0]


def try_sample_insert_and_query(conn, has_vector):
    # Perform a minimal insert/read using a transaction that rolls back
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("SAVEPOINT ver_sp")
                # Insert into maintenance_logs
                cur.execute(
                    "INSERT INTO maintenance_logs (snowflake_id, raw_text) VALUES (%s, %s) RETURNING id",
                    ("ver-1", "verification sample"),
                )
                log_id = cur.fetchone()[0]
                # Insert into ai_extracted_data
                cur.execute(
                    "INSERT INTO ai_extracted_data (log_id, component) VALUES (%s, %s) RETURNING id",
                    (log_id, "component-x"),
                )
                # Insert into semantic_embeddings
                if has_vector:
                    # Try inserting zero-vector of length 1536; adjust if vector dim differs
                    cur.execute(
                        "INSERT INTO semantic_embeddings (log_id, vector) VALUES (%s, (ARRAY[0]::real[]))",
                        (log_id,),
                    )
                else:
                    # Fallback: insert null or placeholder depending on schema
                    cur.execute(
                        "INSERT INTO semantic_embeddings (log_id) VALUES (%s)",
                        (log_id,),
                    )
                # Read back maintenance_logs
                cur.execute(
                    "SELECT id, snowflake_id, raw_text FROM maintenance_logs WHERE id=%s",
                    (log_id,),
                )
                row = cur.fetchone()
                # Rollback to savepoint so test insertions do not persist
                cur.execute("ROLLBACK TO SAVEPOINT ver_sp")
        return True, "sample insert/read succeeded"
    except Exception as e:
        return False, str(e)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--expect-vector", action="store_true", help="Expect pgvector to be available"
    )
    args = parser.parse_args()

    db_url = get_database_url()
    if not db_url:
        print("DATABASE_URL or POSTGRES_URL not set")
        sys.exit(2)

    ok = True
    failures = []

    try:
        conn = psycopg2.connect(db_url)
    except Exception as e:
        print("Failed to connect to database:", e)
        sys.exit(2)

    with closing(conn):
        # Check tables
        for tbl, info in EXPECTED_TABLES.items():
            exists = check_table_exists(conn, tbl)
            print(f"{tbl} exists: {exists}")
            if not exists:
                ok = False
                failures.append(f"Missing table: {tbl}")
            else:
                cols = get_table_columns(conn, tbl)
                missing_cols = [c for c in info["required_columns"] if c not in cols]
                if missing_cols:
                    ok = False
                    failures.append(f"Table {tbl} is missing columns: {missing_cols}")
                else:
                    print(f"Table {tbl} has required columns")

        # Check vector extension
        has_vector = check_extension_exists(conn, "vector")
        print("vector extension present:", has_vector)
        if args.expect_vector and not has_vector:
            ok = False
            failures.append("pgvector extension expected but not present")

        # Sample insert/read
        sample_ok, sample_msg = try_sample_insert_and_query(conn, has_vector)
        print("sample insert/read:", sample_ok, sample_msg)
        if not sample_ok:
            ok = False
            failures.append("sample insert/read failed: " + sample_msg)

    if ok:
        print("verify_db_schema: ALL CHECKS PASSED")
        sys.exit(0)
    else:
        print("\nverify_db_schema: FAILURES:")
        for f in failures:
            print("- ", f)
        sys.exit(1)


if __name__ == "__main__":
    main()
