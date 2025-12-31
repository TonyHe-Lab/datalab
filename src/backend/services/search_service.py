"""
Hybrid search service combining semantic and keyword search.
"""

from typing import List, Dict, Optional
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from .semantic_search import SemanticSearch
from .keyword_search import KeywordSearch
from ..core.rrf_fusion import RRFFusion

logger = logging.getLogger(__name__)


class SearchService:
    """Hybrid search service with semantic and keyword search fusion."""

    def __init__(self, db: AsyncSession, rrf_k: int = 60):
        """
        Initialize search service.

        Args:
            db: Async database session
            rrf_k: RRF constant
        """
        self.db = db
        self.semantic_search = SemanticSearch(db)
        self.keyword_search = KeywordSearch(db)
        self.rrf = RRFFusion(k=rrf_k)

    async def hybrid_search(
        self,
        query: str,
        limit: int = 10,
        semantic_weight: float = 1.0,
        keyword_weight: float = 1.0,
        equipment_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, any]:
        """
        Perform hybrid search combining semantic and keyword search.

        Args:
            query: Search query
            limit: Maximum number of results
            semantic_weight: Weight for semantic search
            keyword_weight: Weight for keyword search
            equipment_id: Optional equipment ID filter
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Search results with metadata
        """
        try:
            # Perform semantic search (skipped for now as it requires embedding)
            semantic_results: List[Dict] = []

            # Perform keyword search
            keyword_results = await self._do_keyword_search(
                query=query,
                limit=limit,
                equipment_id=equipment_id,
                start_date=start_date,
                end_date=end_date,
            )

            # Fuse results using RRF
            fused_results = self.rrf.fuse(
                semantic_results=semantic_results,
                keyword_results=keyword_results,
                semantic_weight=semantic_weight,
                keyword_weight=keyword_weight,
            )

            # Limit results
            final_results = fused_results[:limit]

            return {
                "success": True,
                "query": query,
                "results": final_results,
                "metadata": {
                    "total_results": len(final_results),
                    "semantic_count": len(semantic_results),
                    "keyword_count": len(keyword_results),
                    "fusion_method": "RRF",
                    "semantic_weight": semantic_weight,
                    "keyword_weight": keyword_weight,
                },
            }
        except Exception as e:
            logger.error(f"Hybrid search error: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "results": [],
            }

    async def keyword_only_search(
        self,
        query: str,
        limit: int = 10,
        equipment_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, any]:
        """
        Perform keyword-only search.

        Args:
            query: Search query
            limit: Maximum number of results
            equipment_id: Optional equipment ID filter
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Search results with metadata
        """
        try:
            results = await self._do_keyword_search(
                query=query,
                limit=limit,
                equipment_id=equipment_id,
                start_date=start_date,
                end_date=end_date,
            )

            return {
                "success": True,
                "query": query,
                "results": results,
                "metadata": {
                    "total_results": len(results),
                    "search_type": "keyword_only",
                },
            }
        except Exception as e:
            logger.error(f"Keyword search error: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "results": [],
            }

    async def semantic_only_search(
        self,
        query_vector: List[float],
        limit: int = 10,
        similarity_threshold: float = 0.7,
        equipment_id: Optional[str] = None,
    ) -> Dict[str, any]:
        """
        Perform semantic-only search using vector similarity.

        Args:
            query_vector: Query embedding vector
            limit: Maximum number of results
            similarity_threshold: Minimum similarity threshold
            equipment_id: Optional equipment ID filter

        Returns:
            Search results with metadata
        """
        try:
            results = await self.semantic_search.search(
                query_vector=query_vector,
                limit=limit,
                similarity_threshold=similarity_threshold,
                equipment_id=equipment_id,
            )

            return {
                "success": True,
                "results": results,
                "metadata": {
                    "total_results": len(results),
                    "search_type": "semantic_only",
                    "similarity_threshold": similarity_threshold,
                },
            }
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": [],
            }

    async def _do_keyword_search(
        self,
        query: str,
        limit: int,
        equipment_id: Optional[str],
        start_date: Optional[date],
        end_date: Optional[date],
    ) -> List[Dict]:
        """
        Internal method to perform keyword search with filters.

        Args:
            query: Search query
            limit: Maximum number of results
            equipment_id: Optional equipment ID filter
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            List of search results
        """
        start_date_str = str(start_date) if start_date else None
        end_date_str = str(end_date) if end_date else None

        if start_date or end_date:
            return await self.keyword_search.search_with_filters(
                query=query,
                limit=limit,
                equipment_id=equipment_id,
                start_date=start_date_str,
                end_date=end_date_str,
            )
        else:
            return await self.keyword_search.search(
                query=query,
                limit=limit,
                equipment_id=equipment_id,
            )
