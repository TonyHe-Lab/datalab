import pytest
from types import SimpleNamespace

from src.ai.openai_client import AzureOpenAIClient


class DummyHTTPError(Exception):
    def __init__(self, status_code):
        super().__init__(f"HTTP {status_code}")
        self.status_code = status_code


class DummyTimeoutError(Exception):
    pass


class MockSDK:
    def __init__(self, sequence):
        # sequence of ('chat'|'embed', 'ok'|status|timeout)
        self.seq = list(sequence)

    def get_chat_completions(self, *args, **kwargs):
        kind, outcome = self.seq.pop(0)
        assert kind == "chat"
        if outcome == "ok":
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="hello"))],
                usage=SimpleNamespace(prompt_tokens=5, completion_tokens=2),
            )
        if outcome == "timeout":
            raise DummyTimeoutError("timeout")
        raise DummyHTTPError(outcome)

    def get_embeddings(self, *args, **kwargs):
        kind, outcome = self.seq.pop(0)
        assert kind == "embed"
        if outcome == "ok":
            vec = [0.0] * 1536
            return SimpleNamespace(
                data=[SimpleNamespace(embedding=vec)],
                usage=SimpleNamespace(total_tokens=5),
            )
        if outcome == "timeout":
            raise DummyTimeoutError("timeout")
        raise DummyHTTPError(outcome)


def test_chat_retries_on_429_and_timeout(monkeypatch):
    client = AzureOpenAIClient(endpoint="e", api_key="k", chat_deployment="chat")
    sdk = MockSDK(
        [
            ("chat", 429),
            ("chat", "timeout"),
            ("chat", "ok"),
        ]
    )
    monkeypatch.setattr(client, "_client", sdk)

    resp = client.chat_completion(messages=[{"role": "user", "content": "hi"}])
    assert resp["content"] == "hello"
    assert client.total_prompt_tokens >= 0


def test_embed_retries_on_5xx(monkeypatch):
    client = AzureOpenAIClient(endpoint="e", api_key="k", embed_deployment="embed")
    sdk = MockSDK(
        [
            ("embed", 500),
            ("embed", "ok"),
        ]
    )
    monkeypatch.setattr(client, "_client", sdk)

    vecs = client.create_embeddings(["text"])
    assert len(vecs) == 1
    assert len(vecs[0]) == 1536


def test_circuit_breaker_opens_on_repeated_failures(monkeypatch):
    client = AzureOpenAIClient(endpoint="e", api_key="k", chat_deployment="chat")
    client.breaker.failure_threshold = 2

    sdk = MockSDK(
        [
            ("chat", 500),
            ("chat", 500),
        ]
    )
    monkeypatch.setattr(client, "_client", sdk)

    with pytest.raises(Exception):
        client.chat_completion(messages=[{"role": "user", "content": "hi"}])
    # After consecutive failures, circuit should be open and deny next call
    assert client.breaker.state == "OPEN"
    with pytest.raises(RuntimeError):
        client.chat_completion(messages=[{"role": "user", "content": "hi"}])
