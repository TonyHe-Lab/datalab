import time
from statistics import mean

from types import SimpleNamespace

from src.ai.openai_client import AzureOpenAIClient


class MockSDK:
    def __init__(self, delay_chat=0.01, delay_embed=0.005):
        self.delay_chat = delay_chat
        self.delay_embed = delay_embed

    def get_chat_completions(self, *args, **kwargs):
        time.sleep(self.delay_chat)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))],
            usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5),
        )

    def get_embeddings(self, *args, **kwargs):
        time.sleep(self.delay_embed)
        vec = [0.0] * 1536
        return SimpleNamespace(
            data=[SimpleNamespace(embedding=vec)],
            usage=SimpleNamespace(total_tokens=16),
        )


def test_reliability_latency_10_runs(monkeypatch):
    client = AzureOpenAIClient(
        endpoint="e", api_key="k", chat_deployment="chat", embed_deployment="embed"
    )
    sdk = MockSDK()
    monkeypatch.setattr(client, "_client", sdk)

    chat_latencies = []
    embed_latencies = []
    chat_success = 0
    embed_success = 0

    messages = [{"role": "user", "content": "test"}]
    for _ in range(10):
        t0 = time.time()
        resp = client.chat_completion(messages=messages)
        chat_latencies.append(time.time() - t0)
        if resp.get("content") == "ok":
            chat_success += 1

        t0 = time.time()
        vecs = client.create_embeddings(["hello"])
        embed_latencies.append(time.time() - t0)
        if len(vecs) == 1 and len(vecs[0]) == 1536:
            embed_success += 1

    # Generate simple stats for QA evidence
    chat_avg = mean(chat_latencies)
    embed_avg = mean(embed_latencies)

    # Assert reliability >= 90% in synthetic env (mock should be 100%)
    assert chat_success >= 9
    assert embed_success >= 9

    # Attach as test output notes (would be captured in CI logs)
    print({"chat_avg_latency": chat_avg, "embed_avg_latency": embed_avg})
