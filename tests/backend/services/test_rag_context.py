"""
Tests for RAG context retrieval service.
"""

import pytest
from unittest.mock import AsyncMock
from src.backend.services.rag_context import RAGContextRetriever
from src.backend.services.search_service import SearchService


@pytest.fixture
def mock_search_service():
    """Create mock search service."""
    mock = AsyncMock(spec=SearchService)
    return mock


@pytest.fixture
def rag_retriever(mock_search_service):
    """Create RAG context retriever instance."""
    return RAGContextRetriever(
        search_service=mock_search_service,
        context_limit=5,
        similarity_threshold=0.6,
    )


class TestRAGContextRetriever:
    """Test suite for RAGContextRetriever."""

    def test_initialization(self, mock_search_service):
        """Test RAG context retriever initialization."""
        retriever = RAGContextRetriever(
            search_service=mock_search_service,
            context_limit=10,
            similarity_threshold=0.5,
        )
        assert retriever.search_service == mock_search_service
        assert retriever.context_limit == 10
        assert retriever.similarity_threshold == 0.5

    def test_initialization_defaults(self, mock_search_service):
        """Test initialization with default values."""
        retriever = RAGContextRetriever(search_service=mock_search_service)
        assert retriever.context_limit == 5
        assert retriever.similarity_threshold == 0.6

    @pytest.mark.asyncio
    async def test_retrieve_context_success(self, rag_retriever, mock_search_service):
        """Test successful context retrieval."""
        # Mock search service response
        mock_search_service.keyword_only_search = AsyncMock(
            return_value={
                "success": True,
                "query": "bearing failure",
                "results": [
                    {
                        "noti_id": "NOTI-001",
                        "equipment_id": "EQ-001",
                        "date": "2025-12-31",
                        "text": "Bearing failure detected",
                        "relevance": 0.95,
                    }
                ],
                "metadata": {},
            }
        )

        # Retrieve context
        result = await rag_retriever.retrieve_context(
            query="bearing failure",
            equipment_id="EQ-001",
        )

        # Verify result
        assert result["success"] is True
        assert "context" in result
        assert "search_results" in result
        assert "metadata" in result
        assert result["metadata"]["num_cases"] == 1
        assert result["metadata"]["equipment_id"] == "EQ-001"

        # Verify context contains expected information
        assert "Bearing failure detected" in result["context"]
        assert "NOTI-001" in result["context"]

    @pytest.mark.asyncio
    async def test_retrieve_context_no_filters(
        self, rag_retriever, mock_search_service
    ):
        """Test context retrieval without filters."""
        mock_search_service.keyword_only_search = AsyncMock(
            return_value={
                "success": True,
                "query": "motor",
                "results": [
                    {
                        "noti_id": "NOTI-001",
                        "equipment_id": "EQ-001",
                        "date": "2025-12-31",
                        "text": "Motor issue",
                    }
                ],
                "metadata": {},
            }
        )

        result = await rag_retriever.retrieve_context(query="motor")

        assert result["success"] is True
        assert result["metadata"]["equipment_id"] is None
        assert result["metadata"]["date_range"] is None

    @pytest.mark.asyncio
    async def test_retrieve_context_with_date_range(
        self, rag_retriever, mock_search_service
    ):
        """Test context retrieval with date range."""
        from datetime import date

        mock_search_service.keyword_only_search = AsyncMock(
            return_value={
                "success": True,
                "query": "pump",
                "results": [],
                "metadata": {},
            }
        )

        start = date(2025, 12, 1)
        end = date(2025, 12, 31)
        result = await rag_retriever.retrieve_context(
            query="pump", date_range=(start, end)
        )

        assert result["success"] is True
        assert result["metadata"]["date_range"] == (start, end)

    @pytest.mark.asyncio
    async def test_retrieve_context_search_failure(
        self, rag_retriever, mock_search_service
    ):
        """Test context retrieval when search fails."""
        mock_search_service.keyword_only_search = AsyncMock(
            return_value={
                "success": False,
                "error": "Database connection failed",
                "results": [],
                "metadata": {},
            }
        )

        result = await rag_retriever.retrieve_context(query="test")

        assert result["success"] is False
        assert "error" in result
        assert result["context"] == ""
        assert "Database connection failed" in result["error"]

    @pytest.mark.asyncio
    async def test_retrieve_context_exception(self, rag_retriever, mock_search_service):
        """Test context retrieval with exception."""
        mock_search_service.keyword_only_search = AsyncMock(
            side_effect=Exception("Unexpected error")
        )

        result = await rag_retriever.retrieve_context(query="test")

        assert result["success"] is False
        assert "error" in result
        assert "Unexpected error" in result["error"]

    def test_format_context_empty_results(self, rag_retriever):
        """Test formatting empty search results."""
        context = rag_retriever._format_context([])
        assert "No similar cases found" in context

    def test_format_context_single_result(self, rag_retriever):
        """Test formatting single search result."""
        results = [
            {
                "noti_id": "NOTI-123",
                "equipment_id": "PUMP-001",
                "date": "2025-12-31",
                "text": "Pump cavitation issue",
            }
        ]
        context = rag_retriever._format_context(results)

        assert "SIMILAR HISTORICAL CASES:" in context
        assert "--- Case 1 ---" in context
        assert "NOTI-123" in context
        assert "PUMP-001" in context
        assert "Pump cavitation issue" in context

    def test_format_context_multiple_results(self, rag_retriever):
        """Test formatting multiple search results."""
        results = [
            {
                "noti_id": "NOTI-001",
                "equipment_id": "EQ-001",
                "date": "2025-12-31",
                "text": "Issue 1",
            },
            {
                "noti_id": "NOTI-002",
                "equipment_id": "EQ-002",
                "date": "2025-12-30",
                "text": "Issue 2",
            },
            {
                "noti_id": "NOTI-003",
                "equipment_id": "EQ-003",
                "date": "2025-12-29",
                "text": "Issue 3",
            },
        ]
        context = rag_retriever._format_context(results)

        assert "--- Case 1 ---" in context
        assert "--- Case 2 ---" in context
        assert "--- Case 3 ---" in context
        assert "Issue 1" in context
        assert "Issue 2" in context
        assert "Issue 3" in context

    def test_format_context_with_snippet(self, rag_retriever):
        """Test formatting with snippet instead of full text."""
        results = [
            {
                "noti_id": "NOTI-001",
                "snippet": "...bearing [failure] detected...",
            }
        ]
        context = rag_retriever._format_context(results)
        assert "bearing [failure] detected..." in context

    def test_calculate_context_relevance_high_overlap(self, rag_retriever):
        """Test context relevance calculation with high overlap."""
        context = "motor bearing failure wear damage"
        query = "motor bearing failure"
        relevance = rag_retriever.calculate_context_relevance(context, query)

        assert relevance > 0.8  # High overlap

    def test_calculate_context_relevance_low_overlap(self, rag_retriever):
        """Test context relevance calculation with low overlap."""
        context = "pump valve leakage issue"
        query = "motor bearing failure"
        relevance = rag_retriever.calculate_context_relevance(context, query)

        assert relevance < 0.3  # Low overlap

    def test_calculate_context_relevance_empty_query(self, rag_retriever):
        """Test relevance with empty query."""
        context = "test context"
        query = ""
        relevance = rag_retriever.calculate_context_relevance(context, query)

        assert relevance == 0.0

    def test_calculate_context_relevance_match_all(self, rag_retriever):
        """Test relevance when all words match."""
        context = "motor bearing failure"
        query = "failure motor bearing"
        relevance = rag_retriever.calculate_context_relevance(context, query)

        assert relevance == 1.0

    def test_estimate_token_count(self, rag_retriever):
        """Test token count estimation."""
        # Rough approximation: 1 token ≈ 4 characters
        text = "This is a test"
        estimated = rag_retriever.estimate_token_count(text)
        # Should be approximately len(text) / 4
        expected = len(text) // 4
        assert estimated == expected

    def test_estimate_token_count_long_text(self, rag_retriever):
        """Test token count estimation for longer text."""
        text = "word " * 1000  # 5000 characters
        estimated = rag_retriever.estimate_token_count(text)
        expected = len(text) // 4
        assert estimated == expected

    @pytest.mark.asyncio
    async def test_full_workflow(self, rag_retriever, mock_search_service):
        """Test complete context retrieval workflow."""
        # Setup mock
        mock_search_service.keyword_only_search = AsyncMock(
            return_value={
                "success": True,
                "query": "bearing wear",
                "results": [
                    {
                        "noti_id": "NOTI-001",
                        "equipment_id": "MOTOR-001",
                        "date": "2025-12-30",
                        "text": "Motor bearing showing signs of wear",
                        "relevance": 0.9,
                    }
                ],
                "metadata": {},
            }
        )

        # Execute workflow
        result = await rag_retriever.retrieve_context(query="bearing wear")

        # Verify
        assert result["success"] is True
        assert "bearing" in result["context"].lower()
        assert "wear" in result["context"].lower()

        # Calculate relevance
        relevance = rag_retriever.calculate_context_relevance(
            result["context"], "bearing wear"
        )
        assert relevance > 0.5
