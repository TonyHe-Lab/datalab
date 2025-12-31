"""
Semantic search using pgvector embeddings.
"""

from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)


class SemanticSearch:
    """Handle semantic search using vector similarity."""

    def __init__(self, db: AsyncSession, embedding_dim: int = 1536):
        """
        Initialize semantic search.

        Args:
            db: Async database session
            embedding_dim: Embedding dimension (default: 1536 for OpenAI)
        """
        self.db = db
        self.embedding_dim = embedding_dim

    async def search(
        self,
        query_vector: List[float],
        limit: int = 10,
        similarity_threshold: float = 0.7,
        equipment_id: Optional[str] = None,
    ) -> List[Dict]:
        """
        Perform semantic search using vector similarity.

        Args:
            query_vector: Query embedding vector
            limit: Maximum number of results to return
            similarity_threshold: Minimum similarity threshold (0-1)
            equipment_id: Optional equipment ID filter

        Returns:
            List of search results with similarity scores
        """
        # Convert vector to PostgreSQL array string
        vector_str = f"[{','.join(map(str, query_vector))}]"

        # Build WHERE clause
        conditions = ["similarity >= :threshold"]
        params = {"threshold": similarity_threshold, "limit": limit}

        if equipment_id:
            conditions.append("nt.sys_eq_id = :equipment_id")
            params["equipment_id"] = equipment_id

        where_clause = " AND ".join(conditions)

        # Semantic search query using pgvector <=> operator (cosine distance)
        # Lower distance means higher similarity
        query = f"""
        SELECT
            se.notification_id,
            se.notification_id as noti_id,
            nt.sys_eq_id,
            nt.noti_date,
            nt.noti_text,
            1.0 / (61 + se.vector <=> :vector) as similarity
        FROM semantic_embeddings se
        JOIN notification_text nt ON se.notification_id = nt.notification_id
        WHERE {where_clause}
        ORDER BY se.vector <=> :vector ASC
        LIMIT :limit
        """

        try:
            result = await self.db.execute(text(query), params | {"vector": vector_str})
            rows = result.fetchall()

            return [
                {
                    "notification_id": row[0],
                    "noti_id": row[1],
                    "equipment_id": row[2],
                    "date": str(row[3]),
                    "text": row[4],
                    "similarity": float(row[5]),
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            raise

    async def search_by_text(
        self,
        query_text: str,
        limit: int = 10,
        similarity_threshold: float = 0.7,
        equipment_id: Optional[str] = None,
    ) -> List[Dict]:
        """
        Perform semantic search by query text (requires embedding generation).

        Args:
            query_text: Query text to search
            limit: Maximum number of results
            similarity_threshold: Minimum similarity threshold
            equipment_id: Optional equipment ID filter

        Returns:
            List of search results
        """
        # Note: This requires embedding generation service
        # For now, raise NotImplementedError
        # In production, integrate with Azure OpenAI embedding service from Epic 2
        raise NotImplementedError(
            "Text-to-embedding conversion requires AI integration from Epic 2.3"
        )
