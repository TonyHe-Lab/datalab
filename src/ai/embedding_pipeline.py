"""Embedding pipeline for batch generation, caching, and storage (AC-4).

Responsibilities:
- Configure embedding deployment via AzureOpenAIClient
- Batch generate embeddings for a list of texts
- Enforce 1536-dim vector length
- Write to semantic_embeddings table
- Provide a simple cache to reduce repeated API calls

Storage strategy:
- Uses PostgresWriter if provided, falling back to a simple in-memory store during tests.

Cache strategy:
- In-memory dict keyed by (deployment, text_hash). Can be swapped out in future.
"""

from typing import List, Dict, Optional, Tuple
import hashlib
import logging
import json

from src.ai.openai_client import AzureOpenAIClient

logger = logging.getLogger(__name__)


EMBED_DIMENSION = 1536


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class EmbeddingCache:
    """A simple in-memory cache for embeddings keyed by text hash and deployment."""

    def __init__(self):
        self._cache: Dict[Tuple[str, str], List[float]] = {}

    def get(self, deployment: str, text: str) -> Optional[List[float]]:
        return self._cache.get((deployment, _hash_text(text)))

    def set(self, deployment: str, text: str, vector: List[float]) -> None:
        self._cache[(deployment, _hash_text(text))] = vector


class EmbeddingPipeline:
    def __init__(
        self,
        client: AzureOpenAIClient,
        embed_deployment: Optional[str] = None,
        cache: Optional[EmbeddingCache] = None,
        writer: Optional[object] = None,  # PostgresWriter-like with .connection
    ):
        self.client = client
        self.embed_deployment = embed_deployment or client.embed_deployment
        self.cache = cache or EmbeddingCache()
        self.writer = writer

        if not self.embed_deployment:
            raise ValueError("Embedding deployment must be configured")

    def batch_generate(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings in batch with caching (calls Azure only for misses)."""
        to_compute: List[str] = []
        cached_vectors: List[Optional[List[float]]] = []

        for t in texts:
            v = self.cache.get(self.embed_deployment, t)
            cached_vectors.append(v)
            if v is None:
                to_compute.append(t)

        computed_vectors: List[List[float]] = []
        if to_compute:
            logger.info(
                f"Calling Azure embeddings for {len(to_compute)} items (cache hits={len(texts) - len(to_compute)})"
            )
            computed_vectors = self.client.create_embeddings(
                to_compute, deployment=self.embed_deployment
            )
            # Cache them
            for t, v in zip(to_compute, computed_vectors):
                # Enforce dimension
                if len(v) != EMBED_DIMENSION:
                    raise ValueError(
                        f"Embedding dimension mismatch: expected {EMBED_DIMENSION}, got {len(v)}"
                    )
                self.cache.set(self.embed_deployment, t, v)

        # Merge cached + newly computed in original order
        result: List[List[float]] = []
        comp_iter = iter(computed_vectors)
        for v in cached_vectors:
            if v is not None:
                result.append(v)
            else:
                result.append(next(comp_iter))

        return result

    def store_embeddings(
        self, notification_ids: List[str], texts: List[str], vectors: List[List[float]]
    ) -> int:
        """Store embeddings in semantic_embeddings table.

        Uses pgvector if available, otherwise stores as JSON in vector_bytea for simplicity.
        Returns number of inserted rows.
        """
        if len(notification_ids) != len(texts) or len(texts) != len(vectors):
            raise ValueError("notification_ids, texts, and vectors length must match")

        if not self.writer or not getattr(self.writer, "connection", None):
            logger.warning("No Postgres writer configured; skipping DB storage.")
            return 0

        # Prepare rows for UPSERT
        rows: List[Dict[str, object]] = []
        for nid, text, vec in zip(notification_ids, texts, vectors):
            # Ensure dimension
            if len(vec) != EMBED_DIMENSION:
                raise ValueError(
                    f"Embedding dimension mismatch: expected {EMBED_DIMENSION}, got {len(vec)}"
                )
            rows.append(
                {
                    "notification_id": nid,
                    "source_text_ai": text,
                    # store as JSON string into vector_bytea for compatibility
                    "vector_bytea": json.dumps(vec),
                }
            )

        query = """
            INSERT INTO semantic_embeddings (
                notification_id, source_text_ai, vector_bytea
            ) VALUES (
                %(notification_id)s, %(source_text_ai)s, %(vector_bytea)s
            )
            ON CONFLICT (notification_id)
            DO UPDATE SET
                source_text_ai = EXCLUDED.source_text_ai,
                vector_bytea = EXCLUDED.vector_bytea
            """

        try:
            cur = self.writer.connection.cursor()
            cur.executemany(query, rows)
            self.writer.connection.commit()
            cur.close()
            logger.info(f"Upserted {len(rows)} embeddings into semantic_embeddings")
            return len(rows)
        except Exception as e:
            logger.error(f"Failed to store embeddings: {e}")
            try:
                self.writer.connection.rollback()
            except Exception:
                pass
            raise
