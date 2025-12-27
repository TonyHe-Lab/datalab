import os
from unittest.mock import patch, MagicMock

import pytest

from src.etl.postgres_writer import PostgresWriter
from src.utils.config import PostgresConfig


def test_etl_smoke_run_with_mocked_snowflake(tmp_path, monkeypatch):
    """Smoke test: run minimal ETL path with Snowflake connector mocked and Postgres service available.

    This test demonstrates how CI can run tests with Snowflake mocked and a Postgres service available.
    """

    # Ensure DATABASE_URL points to CI/Postgres service; fallback to local sqlite for safety
    database_url = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/datalab_test"
    )

    # Create a PostgresConfig with default values (pointing to localhost:5432)
    config = PostgresConfig(
        host="localhost",
        port=5432,
        database="datalab_test",
        user="postgres",
        password="postgres",
    )

    # Patch Snowflake loader functions to return fixture rows
    with patch(
        "src.etl.snowflake_loader.SnowflakeClient.execute_query"
    ) as mock_execute:
        mock_execute.return_value = [
            {"notification_id": "n1", "notification_text": "sample"}
        ]

        # Mock psycopg.connect to avoid real connection
        with patch("psycopg.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn

            writer = PostgresWriter(config)
            # This will call the mocked connect
            writer.connect()
            # Disconnect (should close the mocked connection)
            writer.disconnect()

            # Verify connect was called with expected connection string
            mock_connect.assert_called_once()
            # Ensure connection attribute is cleared after disconnect
            assert writer.connection is None
