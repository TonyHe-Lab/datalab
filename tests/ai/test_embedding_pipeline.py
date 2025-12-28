import pytest
from unittest.mock import MagicMock

from src.ai.embedding_pipeline import EmbeddingPipeline, EmbeddingCache, EMBED_DIMENSION


class DummyClient:
    def __init__(self, vec):
        self.embed_deployment = "text-embedding-3-small"
        self._vec = vec

    def create_embeddings(self, texts, deployment=None):
        assert deployment == self.embed_deployment
        return [self._vec for _ in texts]


class DummyWriter:
    def __init__(self):
        self.connection = MagicMock()


def test_batch_generate_with_cache_hits():
    vec = [0.1] * EMBED_DIMENSION
    client = DummyClient(vec)
    cache = EmbeddingCache()
    pipeline = EmbeddingPipeline(client, cache=cache)

    texts = ["a", "b", "c"]
    # Prime cache for one entry
    cache.set(client.embed_deployment, "b", vec)

    out = pipeline.batch_generate(texts)
    assert len(out) == 3
    for v in out:
        assert len(v) == EMBED_DIMENSION


def test_store_embeddings_success():
    vec = [0.2] * EMBED_DIMENSION
    client = DummyClient(vec)
    writer = DummyWriter()
    pipeline = EmbeddingPipeline(client, writer=writer)

    ids = ["N1", "N2"]
    texts = ["t1", "t2"]
    vectors = [vec, vec]

    # Mock cursor behavior
    cursor = MagicMock()
    writer.connection.cursor.return_value = cursor

    count = pipeline.store_embeddings(ids, texts, vectors)
    assert count == 2
    writer.connection.cursor.assert_called_once()
    writer.connection.commit.assert_called_once()


def test_store_embeddings_no_writer():
    vec = [0.3] * EMBED_DIMENSION
    client = DummyClient(vec)
    pipeline = EmbeddingPipeline(client)

    ids = ["N1"]
    texts = ["t1"]
    vectors = [vec]

    count = pipeline.store_embeddings(ids, texts, vectors)
    assert count == 0
