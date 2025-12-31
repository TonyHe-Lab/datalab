"""
Tests for keyword search service.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock

from src.backend.services.keyword_search import KeywordSearch


@pytest.mark.asyncio
async def test_keyword_search_basic() -> None:
    """
    Test basic keyword search.
    """
    # Mock database session
    db_mock = AsyncMock()

    # Mock query result
    mock_result = MagicMock()
    mock_result.fetchall.return_value = [
        (
            "NOTI-001",
            "EQ-001",
            "2025-12-31",
            "Bearing failure detected",
            0.95,
            "[Match] Bearing failure",
        )
    ]
    db_mock.execute.return_value = mock_result

    # Create keyword search instance
    keyword_search = KeywordSearch(db=db_mock)

    # Perform search
    results = await keyword_search.search(query="bearing failure", limit=10)

    # Verify results
    assert len(results) == 1
    assert results[0]["noti_id"] == "NOTI-001"
    assert results[0]["equipment_id"] == "EQ-001"
    assert results[0]["relevance"] == 0.95
    assert "[Match]" in results[0]["snippet"]


@pytest.mark.asyncio
async def test_keyword_search_with_equipment_filter() -> None:
    """
    Test keyword search with equipment ID filter.
    """
    # Mock database session
    db_mock = AsyncMock()

    # Mock query result
    mock_result = MagicMock()
    mock_result.fetchall.return_value = [
        ("NOTI-001", "EQ-001", "2025-12-31", "Test", 0.9, "[Match] Test")
    ]
    db_mock.execute.return_value = mock_result

    # Create keyword search instance
    keyword_search = KeywordSearch(db=db_mock)

    # Perform search with equipment filter
    results = await keyword_search.search(query="test", limit=10, equipment_id="EQ-001")

    # Verify results
    assert len(results) == 1

    # Verify SQL query was called with equipment filter
    db_mock.execute.assert_called_once()
    call_args = db_mock.execute.call_args[0][0]
    assert "sys_eq_id = :equipment_id" in call_args.text


@pytest.mark.asyncio
async def test_keyword_search_with_filters() -> None:
    """
    Test keyword search with date range filters.
    """
    # Mock database session
    db_mock = AsyncMock()

    # Mock query result
    mock_result = MagicMock()
    mock_result.fetchall.return_value = []
    db_mock.execute.return_value = mock_result

    # Create keyword search instance
    keyword_search = KeywordSearch(db=db_mock)

    # Perform search with date filters
    results = await keyword_search.search_with_filters(
        query="test",
        limit=10,
        equipment_id="EQ-001",
        start_date="2025-01-01",
        end_date="2025-12-31",
    )

    # Verify results structure
    assert isinstance(results, list)

    # Verify execute was called
    db_mock.execute.assert_called_once()


@pytest.mark.asyncio
async def test_keyword_search_with_no_results() -> None:
    """
    Test keyword search returns empty list when no matches.
    """
    # Mock database session
    db_mock = AsyncMock()

    # Mock query result - no matches
    mock_result = MagicMock()
    mock_result.fetchall.return_value = []
    db_mock.execute.return_value = mock_result

    # Create keyword search instance
    keyword_search = KeywordSearch(db=db_mock)

    # Perform search for non-existent term
    results = await keyword_search.search(query="nonexistent term", limit=10)

    # Verify empty results
    assert len(results) == 0


@pytest.mark.asyncio
async def test_keyword_search_error_handling() -> None:
    """
    Test keyword search handles database errors gracefully.
    """
    # Mock database session that raises error
    db_mock = AsyncMock()
    db_mock.execute.side_effect = Exception("Database connection error")

    # Create keyword search instance
    keyword_search = KeywordSearch(db=db_mock)

    # Perform search - should raise exception
    with pytest.raises(Exception) as exc_info:
        await keyword_search.search(query="test", limit=10)

    assert "Database connection error" in str(exc_info.value)
