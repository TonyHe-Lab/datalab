#!/usr/bin/env python3
"""Minimal script to verify Postgres connectivity using env vars."""

import os
import sys
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
if not DATABASE_URL:
    print("DATABASE_URL not set")
    sys.exit(2)

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT version();")
    print("Postgres version:", cur.fetchone())
    cur.execute("SELECT 1;")
    print("Simple query OK:", cur.fetchone())
    conn.close()
    print("verify_postgres_connection completed")
except Exception as e:
    print("Connection failed:", e)
    sys.exit(3)
