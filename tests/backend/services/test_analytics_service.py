"""
Tests for analytics service.
"""

import pytest
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, MagicMock

from src.backend.services.analytics_service import AnalyticsService


@pytest.mark.asyncio
async def test_calculate_mtbf_basic(db_session: AsyncSession) -> None:
    """
    Test basic MTBF calculation.
    """
    service = AnalyticsService(db_session)

    # Mock the database query result
    mock_result = MagicMock()
    mock_result.fetchall = MagicMock(
        return_value=[
            ("EQ-001", 10, 30.5, 15.0, 45.0, 32.0),
        ]
    )

    with pytest.MagicMock() as mock_execute:
        mock_execute.return_value = mock_result
        db_session.execute = AsyncMock(return_value=mock_result)

        results = await service.calculate_mtbf()
        assert len(results) == 1
        assert results[0]["equipment_id"] == "EQ-001"
        assert results[0]["failure_count"] == 10


@pytest.mark.asyncio
async def test_calculate_mtbf_with_date_range(db_session: AsyncSession) -> None:
    """
    Test MTBF calculation with date range filter.
    """
    service = AnalyticsService(db_session)
    start_date = date(2025, 6, 1)
    end_date = date(2025, 12, 31)

    # Mock the database query
    mock_result = MagicMock()
    mock_result.fetchall = MagicMock(return_value=[])

    db_session.execute = AsyncMock(return_value=mock_result)

    results = await service.calculate_mtbf(start_date=start_date, end_date=end_date)

    # Verify query was called with date range
    assert db_session.execute.called
    call_args = db_session.execute.call_args
    query = call_args[0][0]
    assert "noti_date >= '2025-06-01'" in str(query)
    assert "noti_date <= '2025-12-31'" in str(query)


@pytest.mark.asyncio
async def test_calculate_pareto_basic(db_session: AsyncSession) -> None:
    """
    Test basic Pareto analysis.
    """
    service = AnalyticsService(db_session)

    # Mock the database query result
    mock_result = MagicMock()
    mock_result.fetchall = MagicMock(
        return_value=[
            ("Bearing", 50, 30.0, 30.0),
            ("Motor", 40, 24.0, 54.0),
        ]
    )

    db_session.execute = AsyncMock(return_value=mock_result)

    results = await service.calculate_pareto(limit=10)

    assert len(results) == 2
    assert results[0]["component"] == "Bearing"
    assert results[0]["count"] == 50
    assert results[0]["percentage"] == 30.0
    assert results[0]["cumulative"] == 30.0


@pytest.mark.asyncio
async def test_calculate_pareto_with_date_range(db_session: AsyncSession) -> None:
    """
    Test Pareto analysis with date range filter.
    """
    service = AnalyticsService(db_session)
    start_date = date(2025, 1, 1)
    end_date = date(2025, 12, 31)

    # Mock the database query
    mock_result = MagicMock()
    mock_result.fetchall = MagicMock(return_value=[])

    db_session.execute = AsyncMock(return_value=mock_result)

    results = await service.calculate_pareto(start_date=start_date, end_date=end_date)

    # Verify query was called
    assert db_session.execute.called
