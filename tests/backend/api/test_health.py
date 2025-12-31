"""
Tests for health check endpoints.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.main import app
from src.backend.db.session import test_connection


@pytest.mark.asyncio
async def test_health_check_endpoint() -> None:
    """
    Test the basic health check endpoint.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "medical-work-order-analysis"


@pytest.mark.asyncio
async def test_db_health_check(db_session: AsyncSession) -> None:
    """
    Test the database health check endpoint.
    Note: This requires an actual database connection.
    """
    # Mock test_connection for testing without DB
    from unittest.mock import patch, AsyncMock

    with patch(
        "src.backend.db.session.test_connection", new_callable=AsyncMock
    ) as mock_conn:
        mock_conn.return_value = True

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/health/db")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["database"] == "connected"


@pytest.mark.asyncio
async def test_root_endpoint() -> None:
    """
    Test the root endpoint.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
