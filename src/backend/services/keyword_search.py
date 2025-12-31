"""
Keyword search using PostgreSQL full-text search.
"""

from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)


class KeywordSearch:
    """Handle keyword search using full-text search."""

    def __init__(self, db: AsyncSession):
        """
        Initialize keyword search.

        Args:
            db: Async database session
        """
        self.db = db

    async def search(
        self,
        query: str,
        limit: int = 10,
        equipment_id: Optional[str] = None,
    ) -> List[Dict]:
        """
        Perform full-text search on notification text.

        Args:
            query: Search query string
            limit: Maximum number of results to return
            equipment_id: Optional equipment ID filter

        Returns:
            List of search results with relevance scores
        """
        # Build WHERE clause
        conditions = []
        params = {"query": query, "limit": limit}

        if equipment_id:
            conditions.append("sys_eq_id = :equipment_id")
            params["equipment_id"] = equipment_id

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # Full-text search query with BM25 ranking
        query = f"""
        SELECT
            notification_id as noti_id,
            sys_eq_id,
            noti_date,
            noti_text,
            ts_rank(to_tsvector('english', noti_text), plainto_tsquery('english', :query)) as relevance,
            ts_headline('english', noti_text, plainto_tsquery('english', :query),
                'StartSel=[Match], StopSel=[/Match], MaxWords=35, MinWords=15') as snippet
        FROM notification_text
        WHERE to_tsvector('english', noti_text) @@ plainto_tsquery('english', :query)
        AND {where_clause}
        ORDER BY relevance DESC
        LIMIT :limit
        """

        try:
            result = await self.db.execute(text(query), params)
            rows = result.fetchall()

            return [
                {
                    "noti_id": row[0],
                    "equipment_id": row[1],
                    "date": str(row[2]),
                    "text": row[3],
                    "relevance": float(row[4]),
                    "snippet": row[5],
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(f"Keyword search error: {e}")
            raise

    async def search_with_filters(
        self,
        query: str,
        limit: int = 10,
        equipment_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict]:
        """
        Perform keyword search with additional filters.

        Args:
            query: Search query string
            limit: Maximum number of results
            equipment_id: Optional equipment ID filter
            start_date: Optional start date filter (YYYY-MM-DD)
            end_date: Optional end date filter (YYYY-MM-DD)

        Returns:
            List of search results with relevance scores
        """
        # Build WHERE clause
        conditions = [
            "to_tsvector('english', noti_text) @@ plainto_tsquery('english', :query)"
        ]
        params = {"query": query, "limit": limit}

        if equipment_id:
            conditions.append("sys_eq_id = :equipment_id")
            params["equipment_id"] = equipment_id

        if start_date:
            conditions.append("noti_date >= :start_date")
            params["start_date"] = start_date

        if end_date:
            conditions.append("noti_date <= :end_date")
            params["end_date"] = end_date

        where_clause = " AND ".join(conditions)

        # Full-text search query with BM25 ranking
        query = f"""
        SELECT
            noti_id,
            sys_eq_id,
            noti_date,
            noti_text,
            ts_rank(to_tsvector('english', noti_text), plainto_tsquery('english', :query)) as relevance,
            snippet(
                to_tsvector('english', noti_text),
                plainto_tsquery('english', :query),
                '[Match]',
                '...',
                20
            ) as snippet
        FROM notification_text
        WHERE {where_clause}
        ORDER BY relevance DESC
        LIMIT :limit
        """

        try:
            result = await self.db.execute(text(query), params)
            rows = result.fetchall()

            return [
                {
                    "noti_id": row[0],
                    "equipment_id": row[1],
                    "date": str(row[2]),
                    "text": row[3],
                    "relevance": float(row[4]),
                    "snippet": row[5],
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(f"Keyword search with filters error: {e}")
            raise
