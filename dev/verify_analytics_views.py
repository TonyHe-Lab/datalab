#!/usr/bin/env python3
"""
Script to verify analytics SQL views and materialized views creation.
"""

import psycopg2
from psycopg2 import sql
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.backend.core.config import settings


def get_connection():
    """Create database connection."""
    conn_string = settings.DATABASE_URL.replace("+asyncpg", "")
    return psycopg2.connect(conn_string)


def check_view_exists(conn, view_name):
    """Check if a view exists in the database."""
    query = """
    SELECT EXISTS (
        SELECT FROM information_schema.views
        WHERE table_name = %s
    );
    """
    cursor = conn.cursor()
    cursor.execute(query, (view_name,))
    exists = cursor.fetchone()[0]
    cursor.close()
    return exists


def check_materialized_view_exists(conn, mv_name):
    """Check if a materialized view exists."""
    query = """
    SELECT EXISTS (
        SELECT FROM pg_matviews
        WHERE matviewname = %s
    );
    """
    cursor = conn.cursor()
    cursor.execute(query, (mv_name,))
    exists = cursor.fetchone()[0]
    cursor.close()
    return exists


def get_view_definition(conn, view_name):
    """Get the definition of a view."""
    query = """
    SELECT definition
    FROM pg_views
    WHERE viewname = %s;
    """
    cursor = conn.cursor()
    cursor.execute(query, (view_name,))
    definition = cursor.fetchone()
    cursor.close()
    return definition[0] if definition else None


def test_view_query(conn, view_name):
    """Test querying a view to ensure it works."""
    try:
        query = sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(view_name))
        cursor = conn.cursor()
        cursor.execute(query)
        count = cursor.fetchone()[0]
        cursor.close()
        return True, count
    except Exception as e:
        return False, str(e)


def main():
    """Main verification function."""
    conn = None
    try:
        conn = get_connection()
        print("✓ Connected to database\n")

        # List of expected views
        views_to_check = [
            "vw_equipment_failure_events",
            "vw_mtbf_calculation_base",
            "vw_mtbf_summary_equipment",
            "vw_mtbf_summary_component",
            "vw_symptom_frequency",
            "vw_pareto_analysis",
            "vw_equipment_health_status",
        ]

        # List of expected materialized views
        materialized_views_to_check = [
            "mv_daily_mtbf_trends",
            "mv_monthly_pareto_summary",
        ]

        print("=" * 60)
        print("CHECKING REGULAR VIEWS")
        print("=" * 60)
        for view_name in views_to_check:
            exists = check_view_exists(conn, view_name)
            if exists:
                success, result = test_view_query(conn, view_name)
                if success:
                    print(f"✓ {view_name}: exists (count: {result} rows)")
                else:
                    print(f"✗ {view_name}: exists but query failed - {result}")
            else:
                print(f"✗ {view_name}: NOT found")

        print("\n" + "=" * 60)
        print("CHECKING MATERIALIZED VIEWS")
        print("=" * 60)
        for mv_name in materialized_views_to_check:
            exists = check_materialized_view_exists(conn, mv_name)
            if exists:
                success, result = test_view_query(conn, mv_name)
                if success:
                    print(f"✓ {mv_name}: exists (count: {result} rows)")
                else:
                    print(f"✗ {mv_name}: exists but query failed - {result}")
            else:
                print(f"✗ {mv_name}: NOT found")

        print("\n" + "=" * 60)
        print("CHECKING VIEW REFRESH FUNCTION")
        print("=" * 60)
        # Check if refresh function exists
        query = """
        SELECT EXISTS (
            SELECT FROM pg_proc
            WHERE proname = 'refresh_analytics_views'
        );
        """
        cursor = conn.cursor()
        cursor.execute(query)
        func_exists = cursor.fetchone()[0]
        cursor.close()

        if func_exists:
            print("✓ refresh_analytics_views() function exists")
        else:
            print("✗ refresh_analytics_views() function NOT found")

        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        views_found = sum(check_view_exists(conn, v) for v in views_to_check)
        mvs_found = sum(
            check_materialized_view_exists(conn, mv)
            for mv in materialized_views_to_check
        )

        print(f"Regular Views: {views_found}/{len(views_to_check)}")
        print(f"Materialized Views: {mvs_found}/{len(materialized_views_to_check)}")
        print(f"Refresh Function: {'✓' if func_exists else '✗'}")

        if (
            views_found == len(views_to_check)
            and mvs_found == len(materialized_views_to_check)
            and func_exists
        ):
            print("\n✓ All analytics views are properly set up!")
            return 0
        else:
            print("\n✗ Some views are missing. Please run the view creation script.")
            return 1

    except Exception as e:
        print(f"\n✗ Error during verification: {e}")
        return 1
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    sys.exit(main())
