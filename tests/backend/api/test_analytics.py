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
async def test_get_mtbf_visualization() -> None:
    """
    Test MTBF visualization data retrieval.
    """
    mock_viz_data = {
        "bar_chart": {
            "labels": ["EQ-001", "EQ-002"],
            "avg_mtbf_data": [30.5, 25.0],
            "median_mtbf_data": [32.0, 26.0],
            "failure_counts": [10, 8],
            "title": "MTBF by Equipment",
        },
        "detailed_view": [],
        "chart_config": {},
        "metadata": {},
    }

    with patch(
        "src.backend.api.analytics.AnalyticsService"
    ) as mock_service:
        instance = mock_service.return_value
        instance.get_mtbf_for_visualization = AsyncMock(return_value=mock_viz_data)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/analytics/mtbf/visualization")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "bar_chart" in data["data"]


@pytest.mark.asyncio
async def test_get_pareto_visualization() -> None:
    """
    Test Pareto visualization data retrieval.
    """
    mock_viz_data = {
        "bar_chart": {
            "labels": ["Bearing", "Motor"],
            "data": [50, 40],
            "title": "Top Failure Symptoms",
        },
        "pie_chart": {
            "labels": ["Bearing", "Motor"],
            "data": [30.0, 24.0],
            "title": "Failure Symptom Distribution",
        },
        "pareto_chart": {},
        "raw_data": [],
        "chart_config": {},
    }

    with patch(
        "src.backend.api.analytics.AnalyticsService"
    ) as mock_service:
        instance = mock_service.return_value
        instance.get_pareto_for_visualization = AsyncMock(return_value=mock_viz_data)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/analytics/pareto/visualization")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "bar_chart" in data["data"]
            assert "pie_chart" in data["data"]


@pytest.mark.asyncio
async def test_get_analytics_dashboard() -> None:
    """
    Test comprehensive analytics dashboard data retrieval.
    """
    mock_dashboard_data = {
        "mtbf": {
            "bar_chart": {},
            "detailed_view": [],
            "chart_config": {},
            "metadata": {},
        },
        "pareto": {
            "bar_chart": {},
            "pie_chart": {},
            "pareto_chart": {},
            "raw_data": [],
            "chart_config": {},
        },
        "equipment_health": {"data": [], "chart_config": {}},
        "date_range": {"start": "2025-01-01", "end": "2025-12-31"},
    }

    with patch(
        "src.backend.api.analytics.AnalyticsService"
    ) as mock_service:
        instance = mock_service.return_value
        instance.get_analytics_dashboard_data = AsyncMock(
            return_value=mock_dashboard_data
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/analytics/dashboard")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "mtbf" in data["data"]
            assert "pareto" in data["data"]
            assert "equipment_health" in data["data"]


@pytest.mark.asyncio
async def test_refresh_analytics_views() -> None:
    """
    Test materialized view refresh endpoint.
    """
    mock_refresh_result = {
        "success": True,
        "refreshed_views": ["mv_daily_mtbf_trends", "mv_monthly_pareto_summary"],
        "timestamp": "2025-12-31T00:00:00",
    }

    with patch(
        "src.backend.api.analytics.AnalyticsService"
    ) as mock_service:
        instance = mock_service.return_value
        instance.refresh_materialized_views = AsyncMock(
            return_value=mock_refresh_result
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/analytics/refresh-views")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]["refreshed_views"]) == 2


@pytest.mark.asyncio
async def test_mtbf_with_rolling_average() -> None:
    """
    Test MTBF calculation with rolling average parameter.
    """
    mock_results = [
        {
            "equipment_id": "EQ-001",
            "failed_component": "Motor",
            "failure_count": 10,
            "avg_mtbf_days": 30.5,
            "min_mtbf_days": 15.0,
            "max_mtbf_days": 45.0,
            "median_mtbf_days": 32.0,
            "first_failure_date": "2025-01-01",
            "last_failure_date": "2025-12-31",
        }
    ]

    with patch(
        "src.backend.api.analytics.AnalyticsService"
    ) as mock_service:
        instance = mock_service.return_value
        instance.calculate_mtbf = AsyncMock(return_value=mock_results)
        instance.get_date_range = AsyncMock(return_value={"start": "2025-01-01", "end": "2025-12-31"})

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/analytics/mtbf")

            assert response.status_code == 200
            instance.calculate_mtbf.assert_called_once()


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
        "src.backend.api.analytics.AnalyticsService"
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
        "src.backend.api.analytics.AnalyticsService"
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
        "src.backend.api.analytics.AnalyticsService"
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
        "src.backend.api.analytics.AnalyticsService"
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
