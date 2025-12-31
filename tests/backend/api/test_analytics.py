"""
Tests for analytics API endpoints.
"""

import pytest
from datetime import date, datetime
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch, AsyncMock, MagicMock

from src.backend.main import app


@pytest.mark.asyncio
async def test_get_mtbf_analysis_success() -> None:
    """
    Test successful MTBF analysis retrieval.
    """
    mock_results = [
        {
            "equipment_id": "EQ-001",
            "failure_count": 10,
            "avg_mtbf_days": 30.5,
            "min_mtbf_days": 15.0,
            "max_mtbf_days": 45.0,
            "median_mtbf_days": 32.0,
        }
    ]

    with patch(
        "src.backend.services.analytics_service.AnalyticsService"
    ) as mock_service:
        instance = mock_service.return_value
        instance.calculate_mtbf = AsyncMock(return_value=mock_results)
        instance.get_date_range = AsyncMock(
            return_value={"min": "2025-01-01", "max": "2025-12-31"}
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/analytics/mtbf")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]) == 1
            assert data["data"][0]["equipment_id"] == "EQ-001"


@pytest.mark.asyncio
async def test_get_mtbf_with_filters() -> None:
    """
    Test MTBF analysis with date and equipment filters.
    """
    mock_results = []

    with patch(
        "src.backend.services.analytics_service.AnalyticsService"
    ) as mock_service:
        instance = mock_service.return_value
        instance.calculate_mtbf = AsyncMock(return_value=mock_results)
        instance.get_date_range = AsyncMock(
            return_value={"min": "2025-01-01", "max": "2025-12-31"}
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/analytics/mtbf?start_date=2025-06-01&end_date=2025-12-31&equipment_id=EQ-001"
            )

            assert response.status_code == 200
            instance.calculate_mtbf.assert_called_once()


@pytest.mark.asyncio
async def test_get_pareto_analysis_success() -> None:
    """
    Test successful Pareto analysis retrieval.
    """
    mock_results = [
        {"component": "Bearing", "count": 50, "percentage": 30.0, "cumulative": 30.0},
        {"component": "Motor", "count": 40, "percentage": 24.0, "cumulative": 54.0},
    ]

    with patch(
        "src.backend.services.analytics_service.AnalyticsService"
    ) as mock_service:
        instance = mock_service.return_value
        instance.calculate_pareto = AsyncMock(return_value=mock_results)
        instance.get_date_range = AsyncMock(
            return_value={"min": "2025-01-01", "max": "2025-12-31"}
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/analytics/pareto")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]) == 2


@pytest.mark.asyncio
async def test_get_pareto_with_limit() -> None:
    """
    Test Pareto analysis with custom limit.
    """
    mock_results = []

    with patch(
        "src.backend.services.analytics_service.AnalyticsService"
    ) as mock_service:
        instance = mock_service.return_value
        instance.calculate_pareto = AsyncMock(return_value=mock_results)
        instance.get_date_range = AsyncMock(
            return_value={"min": "2025-01-01", "max": "2025-12-31"}
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/analytics/pareto?limit=5")

            assert response.status_code == 200
            instance.calculate_pareto.assert_called_once()
