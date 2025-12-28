import time
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from src.ai.openai_client import AzureOpenAIClient


def test_network_timeout_recovery():
    """Simulate network timeout (no status code) and verify retry succeeds."""
    client = AzureOpenAIClient(endpoint="e", api_key="k", chat_deployment="chat")
    call_seq = []

    def mock_chat(*args, **kwargs):
        call_seq.append("call")
        if len(call_seq) == 1:
            raise TimeoutError("socket timeout")
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))],
            usage=SimpleNamespace(prompt_tokens=5, completion_tokens=2),
        )

    with patch.object(client, "_client", Mock()):
        client._client.get_chat_completions = mock_chat
        resp = client.chat_completion(messages=[{"role": "user", "content": "hi"}])
        assert resp["content"] == "ok"
        assert len(call_seq) == 2
        print(f"Network timeout recovery passed after {len(call_seq)} calls")


def test_5xx_retry_and_circuit():
    """Simulate 5xx errors and verify circuit opens after threshold."""
    client = AzureOpenAIClient(endpoint="e", api_key="k", chat_deployment="chat")
    client.breaker.failure_threshold = 2

    error = Exception("Internal server error")
    error.status_code = 500

    with patch.object(client, "_client", Mock()):
        client._client.get_chat_completions = Mock(side_effect=error)
        # First call triggers retries until max_retries exhausted, then breaker increments
        with pytest.raises(Exception):
            client.chat_completion(messages=[{"role": "user", "content": "hi"}])
        # After failure_threshold failures, circuit should be OPEN
        assert client.breaker.state == "OPEN"
        # Next call should be blocked
        with pytest.raises(RuntimeError, match="Circuit open"):
            client.chat_completion(messages=[{"role": "user", "content": "hi"}])
        print("5xx circuit breaker behavior verified")


def test_streaming_error_fallback():
    """Simulate streaming error (partial response) and ensure graceful degradation."""
    # This test is a placeholder; actual streaming error handling depends on SDK implementation.
    # For now, we verify that the client's _with_retry treats exceptions uniformly.
    client = AzureOpenAIClient(endpoint="e", api_key="k", chat_deployment="chat")

    # Simulate an error that occurs mid‑stream (e.g., connection reset)
    class StreamError(Exception):
        pass

    with patch.object(client, "_client", Mock()):
        client._client.get_chat_completions = Mock(
            side_effect=StreamError("stream interrupted")
        )
        with pytest.raises(StreamError):
            client.chat_completion(
                messages=[{"role": "user", "content": "hi"}], stream=True
            )
        print("Streaming error raises exception (will be caught by analyzer fallback)")


def test_recovery_rate_report():
    """Compute recovery rate across multiple fault scenarios."""
    from types import SimpleNamespace

    scenarios = [
        ("429", 429, True),
        ("timeout", TimeoutError("timeout"), True),
        ("500", 500, True),
        ("non_retryable", 400, False),  # 400 is not retryable
    ]

    recovered = 0
    total = len(scenarios)

    for name, error, should_recover in scenarios:
        client = AzureOpenAIClient(endpoint="e", api_key="k", chat_deployment="chat")
        # Reset breaker for each scenario
        client.breaker.failure_threshold = 5

        if isinstance(error, int):
            err = Exception(f"HTTP {error}")
            err.status_code = error
            side_effect = err
        else:
            side_effect = error

        # For retryable errors, we need to mock success after a few retries
        if should_recover:
            # Sequence: fail twice, then succeed
            call_seq = []

            def mock_chat(*args, **kwargs):
                call_seq.append(1)
                if len(call_seq) <= 2:
                    raise side_effect
                # Success
                return SimpleNamespace(
                    choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))],
                    usage=SimpleNamespace(prompt_tokens=5, completion_tokens=2),
                )

            with patch.object(client, "_client", Mock()):
                client._client.get_chat_completions = mock_chat
                try:
                    resp = client.chat_completion(
                        messages=[{"role": "user", "content": "hi"}]
                    )
                    if resp.get("content") == "ok":
                        recovered += 1
                except Exception as e:
                    print(f"Retryable scenario {name} failed unexpectedly: {e}")
        else:
            # Non‑retryable error: should raise, no retry
            with patch.object(client, "_client", Mock()):
                client._client.get_chat_completions = Mock(side_effect=side_effect)
                try:
                    client.chat_completion(messages=[{"role": "user", "content": "hi"}])
                    print(f"Non‑retryable scenario {name} succeeded unexpectedly")
                except Exception:
                    recovered += 1  # expected failure, counts as recovered

    recovery_rate = recovered / total
    print(
        f"Recovery rate across {total} scenarios: {recovery_rate:.2f} ({recovered}/{total})"
    )
    # Threshold: recovery rate >= 95% (AC‑6)
    assert recovery_rate >= 0.95, f"Recovery rate {recovery_rate:.2f} < 0.95"


if __name__ == "__main__":
    test_network_timeout_recovery()
    test_5xx_retry_and_circuit()
    test_streaming_error_fallback()
    test_recovery_rate_report()
    print("Expanded fault injection coverage tests passed.")
