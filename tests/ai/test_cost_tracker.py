from src.ai.cost_tracker import CostTracker, Pricing


class DummyClient:
    def __init__(self, p, c, e):
        self.total_prompt_tokens = p
        self.total_completion_tokens = c
        self.total_embedding_tokens = e


def test_cost_estimation():
    pricing = Pricing(
        prompt_per_1k=0.01, completion_per_1k=0.03, embedding_per_1k=0.0001
    )
    tracker = CostTracker(pricing)

    usage = {"prompt_tokens": 2500, "completion_tokens": 5000, "embedding_tokens": 1536}
    costs = tracker.estimate(usage)
    assert costs["prompt_cost"] == round((2.5 * 0.01), 6)
    assert costs["completion_cost"] == round((5.0 * 0.03), 6)
    # 1536 tokens ~ 1.536 * rate
    assert costs["embedding_cost"] == round((1.536 * 0.0001), 6)
    assert costs["total_cost"] == round(
        costs["prompt_cost"] + costs["completion_cost"] + costs["embedding_cost"], 6
    )


def test_cost_from_client():
    pricing = Pricing(
        prompt_per_1k=0.02, completion_per_1k=0.04, embedding_per_1k=0.0002
    )
    tracker = CostTracker(pricing)
    client = DummyClient(1000, 2000, 3000)
    costs = tracker.estimate_from_client(client)
    assert costs["total_cost"] > 0
