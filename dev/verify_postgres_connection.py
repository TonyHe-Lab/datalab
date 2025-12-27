#!/usr/bin/env python3
"""Minimal script to verify Postgres connectivity using env vars or CLI args.

Exit codes:
 0 - success
 2 - DATABASE_URL not set
 3 - missing dependency (psycopg2)
 4 - connection or query failure
"""

import os
import sys
import argparse
# no local time usage

try:
    import psycopg2
    from psycopg2 import OperationalError
except Exception:
    print(
        "psycopg2 is required to run this script. Install with: pip install psycopg2-binary"
    )
    sys.exit(3)


def parse_args():
    parser = argparse.ArgumentParser(description="Verify Postgres connectivity")
    parser.add_argument(
        "--database-url", "-d", help="Full DATABASE_URL (overrides env)"
    )
    parser.add_argument(
        "--timeout", "-t", type=int, default=5, help="Connection timeout seconds"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    database_url = (
        args.database_url or os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
    )
    if not database_url:
        print("DATABASE_URL not set; provide via --database-url or env var")
        sys.exit(2)

    try:
        # psycopg2 uses connect timeout via options or by setting connection string parameter
        conn = psycopg2.connect(database_url, connect_timeout=args.timeout)
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()
        print("Postgres version:", version)
        cur.execute("SELECT 1;")
        print("Simple query OK:", cur.fetchone())
        conn.close()
        print("verify_postgres_connection completed")
        sys.exit(0)
    except OperationalError as oe:
        print("Operational error (connection failed):", oe)
        sys.exit(4)
    except Exception as e:
        print("Connection/query failed:", e)
        sys.exit(4)


if __name__ == "__main__":
    main()
