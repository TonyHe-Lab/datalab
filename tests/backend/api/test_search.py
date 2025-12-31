"""
Tests for search API endpoints.
"""

import pytest
from datetime import date
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch

from src.backend.main import app


@pytest.mark.asyncio
async def test_hybrid_search_keyword_only() -> None:
    """
    Test hybrid search with keyword-only results.
    """
    mock_results = [
        {
            "noti_id": "NOTI-001",
            "equipment_id": "EQ-001",
            "date": "2025-12-31",
            "text": "Test bearing failure",
            "relevance": 0.95,
            "snippet": "[Match] bearing failure",
            "rank": 1,
            "final_score": 0.95,
        }
    ]

    with patch("src.backend.api.search.SearchService") as mock_service:
        instance = mock_service.return_value
        instance.hybrid_search = AsyncMock(
            return_value={
                "success": True,
                "query": "bearing failure",
                "results": mock_results,
                "metadata": {},
            }
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/search/", json={"query": "bearing failure", "limit": 10}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["results"]) == 1


@pytest.mark.asyncio
async def test_keyword_search() -> None:
    """
    Test keyword-only search endpoint.
    """
    mock_results = [
        {
            "noti_id": "NOTI-001",
            "equipment_id": "EQ-001",
            "date": "2025-12-31",
            "text": "Test motor failure",
            "relevance": 0.9,
            "snippet": "[Match] motor failure",
        }
    ]

    with patch("src.backend.api.search.SearchService") as mock_service:
        instance = mock_service.return_value
        instance.keyword_only_search = AsyncMock(
            return_value={
                "success": True,
                "query": "motor failure",
                "results": mock_results,
                "metadata": {},
            }
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/search/keyword", json={"query": "motor failure", "limit": 10}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["results"]) == 1


@pytest.mark.asyncio
async def test_search_with_filters() -> None:
    """
    Test search with date and equipment filters.
    """
    mock_results = []

    with patch("src.backend.api.search.SearchService") as mock_service:
        instance = mock_service.return_value
        instance.keyword_only_search = AsyncMock(
            return_value={
                "success": True,
                "query": "test",
                "results": mock_results,
                "metadata": {},
            }
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/search/?query=test&equipment_id=EQ-001&search_type=keyword"
            )

            assert response.status_code == 200


@pytest.mark.asyncio
async def test_search_with_invalid_type() -> None:
    """
    Test search with invalid search type.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/search/?query=test&search_type=invalid")

        assert response.status_code == 400
