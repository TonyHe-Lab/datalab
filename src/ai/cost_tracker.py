"""Cost tracking metrics for Azure OpenAI usage (AC-5).

Provides a simple estimator based on token usage counters collected
in AzureOpenAIClient. Prices are configurable per-1K tokens.
"""

import logging
from dataclasses import dataclass
from typing import Dict


@dataclass
class Pricing:
    prompt_per_1k: float
    completion_per_1k: float
    embedding_per_1k: float


class CostTracker:
    def __init__(self, pricing: Pricing, alert_threshold: float = 10.0):
        self.pricing = pricing
        self.alert_threshold = alert_threshold
        self.logger = logging.getLogger(__name__)

    def estimate(self, usage: Dict[str, int]) -> Dict[str, float]:
        """Estimate cost from usage dict with keys: prompt_tokens, completion_tokens, embedding_tokens."""
        pt = float(usage.get("prompt_tokens", 0) or 0)
        ct = float(usage.get("completion_tokens", 0) or 0)
        et = float(usage.get("embedding_tokens", 0) or 0)

        prompt_cost = (pt / 1000.0) * self.pricing.prompt_per_1k
        completion_cost = (ct / 1000.0) * self.pricing.completion_per_1k
        embedding_cost = (et / 1000.0) * self.pricing.embedding_per_1k
        total = prompt_cost + completion_cost + embedding_cost

        result = {
            "prompt_cost": round(prompt_cost, 6),
            "completion_cost": round(completion_cost, 6),
            "embedding_cost": round(embedding_cost, 6),
            "total_cost": round(total, 6),
        }

        self._check_alert(total)
        return result

    def _check_alert(self, total_cost: float):
        if total_cost > self.alert_threshold:
            self.logger.warning(
                f"High usage alert: Total cost {total_cost:.6f} exceeds threshold {self.alert_threshold}"
            )

    def estimate_from_client(self, client) -> Dict[str, float]:
        usage = {
            "prompt_tokens": getattr(client, "total_prompt_tokens", 0),
            "completion_tokens": getattr(client, "total_completion_tokens", 0),
            "embedding_tokens": getattr(client, "total_embedding_tokens", 0),
        }
        return self.estimate(usage)
