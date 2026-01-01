"""
Tests for chat API endpoints.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, MagicMock, AsyncMock, AsyncMockMixin
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.main import app
from src.backend.services.chat_service import ChatResponse


# Mock ChatService to avoid database dependency
@pytest.fixture
def mock_chat_service():
    """Create mock chat service."""
    service = MagicMock()
    service.chat = AsyncMock()
    return service


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.mark.asyncio
async def test_chat_endpoint_basic():
    """
    Test basic chat endpoint.
    """
    # Mock chat service response
    mock_response = ChatResponse(
        success=True,
        query="bearing failure",
        response="Analysis: Based on similar cases...",
        context_count=2,
        sources=["NOTI-001", "NOTI-002"],
        metadata={},
    )

    mock_chat_instance = MagicMock()
    mock_chat_instance.chat = AsyncMock(return_value=mock_response)

    with patch("src.backend.api.chat.ChatService", return_value=mock_chat_instance):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/chat/",
                json={
                    "query": "bearing failure",
                    "context_limit": 5,
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["query"] == "bearing failure"
            assert "Analysis" in data["response"]
            assert data["context_count"] == 2


@pytest.mark.asyncio
async def test_chat_endpoint_with_history():
    """
    Test chat endpoint with conversation history.
    """
    mock_response = ChatResponse(
        success=True,
        query="follow-up question",
        response="Based on our conversation...",
        context_count=1,
        sources=["NOTI-001"],
        metadata={"has_conversation_history": True},
    )

    mock_chat_instance = MagicMock()
    mock_chat_instance.chat = AsyncMock(return_value=mock_response)

    with patch("src.backend.api.chat.ChatService", return_value=mock_chat_instance):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/chat/",
                json={
                    "query": "follow-up question",
                    "conversation_history": [
                        {"role": "user", "content": "question 1"},
                        {"role": "assistant", "content": "answer 1"},
                    ],
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True


@pytest.mark.asyncio
async def test_chat_endpoint_with_equipment_filter():
    """
    Test chat endpoint with equipment ID filter.
    """
    mock_response = ChatResponse(
        success=True,
        query="motor issue",
        response="Motor-specific analysis...",
        context_count=1,
        sources=["NOTI-001"],
        metadata={"equipment_id": "MOTOR-001"},
    )

    with patch("src.backend.api.chat.ChatService") as mock_service:
        instance = mock_service.return_value
        instance.chat = AsyncMock(return_value=mock_response)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/chat/",
                json={
                    "query": "motor issue",
                    "equipment_id": "MOTOR-001",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["metadata"]["equipment_id"] == "MOTOR-001"


@pytest.mark.asyncio
async def test_chat_endpoint_invalid_context_limit():
    """
    Test chat endpoint with invalid context limit (should be within range).
    """
    # FastAPI Pydantic validation should handle this
    # context_limit must be between 0 and 20
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/chat/",
            json={
                "query": "motor issue",
                "context_limit": 25,  # Invalid: > 20
            },
        )

        # Should return validation error
        assert response.status_code == 422  # Unprocessable Entity


@pytest.mark.asyncio
async def test_chat_endpoint_with_long_query():
    """
    Test chat endpoint with very long query.
    """
    # Prompt engineer will sanitize and limit query length
    mock_response = ChatResponse(
        success=True,
        query="shortened query",
        response="Response...",
        context_count=0,
        sources=[],
        metadata={},
    )

    with patch("src.backend.api.chat.ChatService") as mock_service:
        instance = mock_service.return_value
        instance.chat = AsyncMock(return_value=mock_response)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Very long query
            long_query = "test " * 1000
            response = await client.post(
                "/api/chat/",
                json={"query": long_query},
            )

            # Should succeed (sanitized internally)
            assert response.status_code == 200


@pytest.mark.asyncio
async def test_chat_endpoint_service_failure():
    """
    Test chat endpoint when service returns failure.
    """
    # Mock service failure
    mock_response = ChatResponse(
        success=False,
        query="test query",
        response="Service error occurred",
        context_count=0,
        sources=[],
        metadata={"error": "Database error"},
    )

    with patch("src.backend.api.chat.ChatService") as mock_service:
        instance = mock_service.return_value
        instance.chat = AsyncMock(return_value=mock_response)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/chat/",
                json={"query": "test query"},
            )

            # Should return 500 for service failure
            assert response.status_code == 500


@pytest.mark.asyncio
async def test_simple_chat_endpoint():
    """
    Test simplified chat endpoint with query param.
    """
    mock_response = ChatResponse(
        success=True,
        query="bearing failure",
        response="Analysis...",
        context_count=1,
        sources=["NOTI-001"],
        metadata={},
    )

    with patch("src.backend.api.chat.ChatService") as mock_service:
        instance = mock_service.return_value
        instance.chat = AsyncMock(return_value=mock_response)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/chat/simple",
                params={"query": "bearing failure", "equipment_id": "EQ-001"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True


@pytest.mark.asyncio
async def test_chat_health_check():
    """
    Test chat service health check.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/chat/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "rag-chat-diagnostic-assistance" in data["service"]
        assert "context retrieval" in data["features"][0].lower()


@pytest.mark.asyncio
async def test_chat_endpoint_exception_handling():
    """
    Test chat endpoint exception handling.
    """
    with patch("src.backend.api.chat.ChatService") as mock_service:
        # Service raises exception
        instance = mock_service.return_value
        instance.chat = AsyncMock(side_effect=Exception("Unexpected error"))

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/chat/",
                json={"query": "test"},
            )

            # Should handle exception gracefully
            assert response.status_code == 500
            detail = response.json()["detail"].lower()
            # Check for any error indication
            assert any(word in detail for word in ["error", "fail", "exception"])
