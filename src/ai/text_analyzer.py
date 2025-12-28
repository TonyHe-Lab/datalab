"""Orchestrator for text analysis: scrubbing, extraction and embeddings.

Initial orchestration wiring to be expanded in subsequent iterations.
"""

from typing import Dict, Any
from .pii_scrubber import redact_pii
from .openai_client import AzureOpenAIClient


class TextAnalyzer:
    def __init__(self, client: AzureOpenAIClient):
        self.client = client

    def analyze(self, text: str) -> Dict[str, Any]:
        # Step 1: redact PII
        redacted, details = redact_pii(text)

        # Step 2: placeholder for structured extraction (call to client.chat_completion)
        # For now, we return redacted text and detected details to allow unit testing.
        return {
            "redacted_text": redacted,
            "pii_details": details,
        }
