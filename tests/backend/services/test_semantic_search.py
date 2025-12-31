"""
Tests for semantic search service.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock

from src.backend.services.semantic_search import SemanticSearch


@pytest.mark.asyncio
async def test_semantic_search_basic() -> None:
    """
    Test basic semantic search with vector similarity.
    """
    # Mock database session
    db_mock = AsyncMock()

    # Mock query result
    mock_result = MagicMock()
    mock_result.fetchall.return_value = [
        ("NOTI-001", "NOTI-001", "EQ-001", "2025-12-31", "Test bearing failure", 0.85)
    ]
    db_mock.execute.return_value = mock_result

    # Create semantic search instance
    semantic_search = SemanticSearch(db=db_mock)

    # Perform search
    query_vector = [0.1] * 1536  # 1536-dimensional vector
    results = await semantic_search.search(
        query_vector=query_vector, limit=10, similarity_threshold=0.7
    )

    # Verify results
    assert len(results) == 1
    assert results[0]["noti_id"] == "NOTI-001"
    assert results[0]["equipment_id"] == "EQ-001"
    assert results[0]["similarity"] == 0.85

    # Verify SQL query was called
    db_mock.execute.assert_called_once()
    call_args = db_mock.execute.call_args
    assert call_args[0][0].text  # Verify query text contains similarity


@pytest.mark.asyncio
async def test_semantic_search_with_equipment_filter() -> None:
    """
    Test semantic search with equipment ID filter.
    """
    # Mock database session
    db_mock = AsyncMock()

    # Mock query result
    mock_result = MagicMock()
    mock_result.fetchall.return_value = [
        ("NOTI-001", "NOTI-001", "EQ-001", "2025-12-31", "Test", 0.85)
    ]
    db_mock.execute.return_value = mock_result

    # Create semantic search instance
    semantic_search = SemanticSearch(db=db_mock)

    # Perform search with equipment filter
    query_vector = [0.1] * 1536
    results = await semantic_search.search(
        query_vector=query_vector,
        limit=10,
        similarity_threshold=0.7,
        equipment_id="EQ-001",
    )

    # Verify results
    assert len(results) == 1


@pytest.mark.asyncio
async def test_semantic_search_below_threshold() -> None:
    """
    Test semantic search filters results below similarity threshold.
    """
    # Mock database session
    db_mock = AsyncMock()

    # Mock query result with low similarity (will be filtered out)
    mock_result = MagicMock()
    mock_result.fetchall.return_value = []
    db_mock.execute.return_value = mock_result

    # Create semantic search instance
    semantic_search = SemanticSearch(db=db_mock)

    # Perform search with high threshold
    query_vector = [0.1] * 1536
    results = await semantic_search.search(
        query_vector=query_vector, limit=10, similarity_threshold=0.9
    )

    # Verify no results returned
    assert len(results) == 0


@pytest.mark.asyncio
async def test_semantic_search_with_text_not_implemented() -> None:
    """
    Test semantic search with text raises NotImplementedError.
    """
    # Mock database session
    db_mock = AsyncMock()

    # Create semantic search instance
    semantic_search = SemanticSearch(db=db_mock)

    # Perform search with text (should raise NotImplementedError)
    with pytest.raises(NotImplementedError) as exc_info:
        await semantic_search.search_by_text(
            query_text="bearing failure", limit=10, similarity_threshold=0.7
        )

    assert "Text-to-embedding conversion" in str(exc_info.value)
