"""
RAG context retrieval and formatting.
"""

from typing import List, Dict, Optional
from datetime import date
import logging

from .search_service import SearchService

logger = logging.getLogger(__name__)


class RAGContextRetriever:
    """Retrieve and format context for RAG chat."""

    def __init__(
        self,
        search_service: SearchService,
        context_limit: int = 5,
        similarity_threshold: float = 0.6,
    ):
        """
        Initialize RAG context retriever.

        Args:
            search_service: Search service for retrieving similar cases
            context_limit: Maximum number of cases to retrieve
            similarity_threshold: Minimum similarity for semantic search
        """
        self.search_service = search_service
        self.context_limit = context_limit
        self.similarity_threshold = similarity_threshold

    async def retrieve_context(
        self,
        query: str,
        equipment_id: Optional[str] = None,
        date_range: Optional[tuple] = None,
    ) -> Dict[str, any]:
        """
        Retrieve relevant context for RAG generation.

        Args:
            query: User query to search for
            equipment_id: Optional equipment ID filter
            date_range: Optional tuple of (start_date, end_date)

        Returns:
            Dictionary with retrieved context and metadata
        """
        try:
            # Use keyword search for context retrieval (faster and more predictable)
            result = await self.search_service.keyword_only_search(
                query=query,
                limit=self.context_limit,
                equipment_id=equipment_id,
                start_date=date_range[0] if date_range else None,
                end_date=date_range[1] if date_range else None,
            )

            if not result.get("success"):
                return {
                    "success": False,
                    "error": result.get("error", "Failed to retrieve context"),
                    "context": "",
                    "metadata": {},
                }

            # Format search results
            search_results = result.get("results", [])

            return {
                "success": True,
                "context": self._format_context(search_results),
                "search_results": search_results,
                "metadata": {
                    "query": query,
                    "num_cases": len(search_results),
                    "equipment_id": equipment_id,
                    "date_range": date_range,
                },
            }
        except Exception as e:
            logger.error(f"Context retrieval error: {e}")
            return {
                "success": False,
                "error": str(e),
                "context": "",
                "metadata": {},
            }

    def _format_context(self, search_results: List[Dict]) -> str:
        """
        Format search results for prompt context.

        Args:
            search_results: List of search results

        Returns:
            Formatted context string
        """
        if not search_results:
            return "No similar cases found in the database."

        context_parts = []

        context_parts.append("SIMILAR HISTORICAL CASES:\n")

        for idx, result in enumerate(search_results, start=1):
            context_parts.append(f"\n--- Case {idx} ---")
            context_parts.append(f"Notification ID: {result.get('noti_id', 'N/A')}")
            context_parts.append(f"Equipment ID: {result.get('equipment_id', 'N/A')}")
            context_parts.append(f"Date: {result.get('date', 'N/A')}")

            # Include text or snippet
            text = result.get("text") or result.get("snippet", "N/A")
            context_parts.append(f"Issue Description: {text}")

        return "\n".join(context_parts)

    def calculate_context_relevance(
        self,
        context: str,
        query: str,
    ) -> float:
        """
        Calculate relevance score of context to query.

        Args:
            context: Retrieved context
            query: Original query

        Returns:
            Relevance score (0-1)
        """
        # Simple keyword overlap calculation
        query_words = set(query.lower().split())
        context_words = set(context.lower().split())

        if not query_words:
            return 0.0

        overlap = len(query_words & context_words)
        return min(overlap / len(query_words), 1.0)

    def estimate_token_count(self, text: str) -> int:
        """
        Estimate token count for text (rough approximation).

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        # Rough approximation: 1 token ≈ 4 characters
        return len(text) // 4
