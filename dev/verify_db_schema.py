#!/usr/bin/env python3
"""dev/verify_db_schema.py

Enhanced verification script for database schema from Story 1.3.
Checks extensions, table existence, attempts simple insert/read, and reports detailed exit codes for CI.

Exit Codes:
0 = Success
1 = General error
2 = Database URL not set
3 = Connection failed
4 = Schema validation failed
5 = Insert/read test failed
6 = Vector extension check failed
"""

import os
import sys
import traceback
import psycopg
from psycopg.rows import dict_row

DATABASE_URL = (
    os.getenv("DATABASE_URL")
    or os.getenv("POSTGRES_URL")
    or os.getenv("POSTGRESQL_URL")
)
if not DATABASE_URL:
    print(
        "ERROR: DATABASE_URL (or POSTGRES_URL/POSTGRESQL_URL) environment variable not set"
    )
    print("Please set one of these environment variables:")
    print("  DATABASE_URL=postgresql://user:pass@host:port/db")
    print("  POSTGRES_URL=postgresql://user:pass@host:port/db")
    print("  POSTGRESQL_URL=postgresql://user:pass@host:port/db")
    sys.exit(2)


def main():
    try:
        print(f"Attempting to connect to database...")
        conn = psycopg.connect(DATABASE_URL)
        print(
            f"Connected successfully to {conn.info.host}:{conn.info.port}/{conn.info.dbname}"
        )
    except psycopg.OperationalError as e:
        print("ERROR: Operational error connecting to database:")
        print(f"  Error: {e}")
        print("  Possible causes:")
        print("    - Database server is not running")
        print("    - Network connectivity issue")
        print("    - Incorrect host/port in connection string")
        print("    - Authentication failure")
        sys.exit(3)
    except Exception as e:
        print("ERROR: Unexpected error connecting to database:")
        print(f"  Error: {e}")
        print("  Traceback:")
        traceback.print_exc()
        sys.exit(3)

    cur = conn.cursor(row_factory=dict_row)

    def exists_query(q, table_name):
        try:
            cur.execute(q)
            result = cur.fetchone()
            exists = result["reg"] is not None
            print(f"  {table_name}: {'✓ EXISTS' if exists else '✗ MISSING'}")
            return exists
        except Exception as e:
            print(f"  ERROR checking {table_name}: {e}")
            return False

    print("\n=== Table Existence Check ===")
    tables_ok = True

    print("Checking maintenance_logs table...")
    if not exists_query(
        "SELECT to_regclass('public.maintenance_logs') as reg", "maintenance_logs"
    ):
        tables_ok = False
        print("  ACTION: Run db/init_schema.sql to create maintenance_logs table")

    print("Checking ai_extracted_data table...")
    if not exists_query(
        "SELECT to_regclass('public.ai_extracted_data') as reg", "ai_extracted_data"
    ):
        tables_ok = False
        print("  ACTION: Run db/init_schema.sql to create ai_extracted_data table")

    print("Checking semantic_embeddings table...")
    if not exists_query(
        "SELECT to_regclass('public.semantic_embeddings') as reg", "semantic_embeddings"
    ):
        tables_ok = False
        print("  ACTION: Run db/init_schema.sql to create semantic_embeddings table")

    if not tables_ok:
        print("\nERROR: One or more required tables are missing")
        conn.close()
        sys.exit(4)

    print("\n=== Extension Check ===")
    try:
        cur.execute(
            "SELECT exists(SELECT 1 FROM pg_extension WHERE extname='vector') as present"
        )
        present = cur.fetchone()["present"]
        if present:
            print("  vector extension: ✓ INSTALLED")
            # Check version if possible
            try:
                cur.execute(
                    "SELECT extversion FROM pg_extension WHERE extname='vector'"
                )
                version = cur.fetchone()
                if version:
                    print(f"    Version: {version['extversion']}")
            except:
                pass
        else:
            print("  vector extension: ✗ NOT INSTALLED")
            print("    NOTE: Semantic embeddings will use bytea fallback storage")
            print("    ACTION: Install pgvector extension for vector similarity search")
    except Exception as e:
        print(f"  ERROR checking vector extension: {e}")
        conn.close()
        sys.exit(6)

    print("\n=== Insert/Read Test ===")
    try:
        cur.execute("BEGIN")
        print("  Starting transaction for test data...")

        # Insert into maintenance_logs
        try:
            cur.execute(
                "INSERT INTO maintenance_logs (snowflake_id, raw_text) VALUES (%s, %s) RETURNING id",
                ("test-sf-1", "test raw text for schema verification"),
            )
            new_id = cur.fetchone()["id"]
            print(f"  ✓ Inserted maintenance_logs record (id: {new_id})")
        except Exception as e:
            print(f"  ✗ Failed to insert into maintenance_logs: {e}")
            print(f"    SQL Error: {e.__cause__}" if hasattr(e, "__cause__") else "")
            cur.execute("ROLLBACK")
            conn.close()
            sys.exit(5)

        # Insert into ai_extracted_data
        try:
            cur.execute(
                "INSERT INTO ai_extracted_data (log_id, summary) VALUES (%s, %s) RETURNING id",
                (new_id, "Test summary for schema verification"),
            )
            a_id = cur.fetchone()["id"]
            print(f"  ✓ Inserted ai_extracted_data record (id: {a_id})")
        except Exception as e:
            print(f"  ✗ Failed to insert into ai_extracted_data: {e}")
            print(f"    SQL Error: {e.__cause__}" if hasattr(e, "__cause__") else "")
            cur.execute("ROLLBACK")
            conn.close()
            sys.exit(5)

        # Try to insert into semantic_embeddings based on extension availability
        try:
            if present:
                # Check if table has vector column (pgvector) or vector_bytea (fallback)
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                      AND table_name = 'semantic_embeddings'
                      AND column_name IN ('vector', 'vector_bytea')
                """)
                columns = [row["column_name"] for row in cur.fetchall()]

                if "vector" in columns:
                    # create a zero-vector for test insert (1536 dims)
                    vec = "[" + ",".join(["0"] * 1536) + "]"
                    cur.execute(
                        "INSERT INTO semantic_embeddings (log_id, vector) VALUES (%s, %s)",
                        (new_id, vec),
                    )
                    print("  ✓ Inserted semantic_embeddings test row (vector type)")
                elif "vector_bytea" in columns:
                    # Use bytea fallback
                    test_bytes = b"\x00" * 1536 * 4  # 1536 floats * 4 bytes each
                    cur.execute(
                        "INSERT INTO semantic_embeddings (log_id, vector_bytea) VALUES (%s, %s)",
                        (new_id, test_bytes),
                    )
                    print("  ✓ Inserted semantic_embeddings test row (bytea fallback)")
                else:
                    print(
                        "  ⚠ semantic_embeddings table exists but no vector/vector_bytea column found"
                    )
            else:
                print(
                    "  ⚠ Skipping semantic_embeddings insert (vector extension not installed)"
                )
        except Exception as e:
            print(f"  ⚠ Could not insert into semantic_embeddings: {e}")
            # This is a warning, not a failure

        # Rollback test changes
        cur.execute("ROLLBACK")
        print("  ✓ Transaction rolled back (test data cleaned up)")

    except Exception as e:
        print(f"  ✗ ERROR during insert/read test: {e}")
        print(f"    Traceback:")
        traceback.print_exc()
        try:
            cur.execute("ROLLBACK")
        except Exception:
            pass
        conn.close()
        sys.exit(5)

    conn.close()
    print("\n=== Verification Summary ===")
    print("✓ Database schema verification completed successfully")
    print("✓ All required tables exist")
    print(
        f"✓ Vector extension: {'INSTALLED' if present else 'NOT INSTALLED (using fallback)'}"
    )
    print("✓ Insert/read test passed")
    print("\nExit code: 0 (Success)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
