"""Azure OpenAI client wrapper (initial skeleton).

This module provides a thin wrapper around the Azure OpenAI REST/SDK
for chat completions and embeddings. It is intentionally small for
the first iteration so tests can mock its interface.
"""

from typing import List, Dict, Any, Optional
import os

try:
    from azure.ai.openai import OpenAIClient
    from azure.core.credentials import AzureKeyCredential
except Exception:  # pragma: no cover - SDK may not be installed in test env
    OpenAIClient = None
    AzureKeyCredential = None


class AzureOpenAIClient:
    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        chat_deployment: Optional[str] = None,
        embed_deployment: Optional[str] = None,
    ):
        # Load from env if not provided
        self.endpoint = endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY")
        self.chat_deployment = chat_deployment or os.getenv("AZURE_OPENAI_DEPLOYMENT")
        self.embed_deployment = embed_deployment or os.getenv(
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
        )

        if OpenAIClient and self.endpoint and self.api_key:
            self._client = OpenAIClient(self.endpoint, AzureKeyCredential(self.api_key))
        else:
            self._client = None

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1024,
        deployment: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Perform a chat completion request using Azure SDK when available.

        messages: list of {'role': 'user'|'system'|'assistant', 'content': '...'}
        Returns a dict with 'content' and raw SDK response under 'raw'.
        """
        if not self._client:
            raise RuntimeError("Azure OpenAI SDK not configured or missing credentials")

        deployment = deployment or self.chat_deployment
        if not deployment:
            raise ValueError("chat deployment name is required")

        resp = self._client.get_chat_completions(
            deployment, messages=messages, max_tokens=max_tokens, **kwargs
        )
        try:
            choice = resp.choices[0]
            return {"content": choice.message.content, "raw": resp}
        except Exception:
            return {"raw": resp}

    def create_embeddings(
        self, texts: List[str], deployment: Optional[str] = None
    ) -> List[List[float]]:
        """Generate embeddings for the provided list of texts using Azure SDK.

        Returns a list of vectors (list of floats).
        """
        if not self._client:
            raise RuntimeError("Azure OpenAI SDK not configured or missing credentials")

        deployment = deployment or self.embed_deployment
        if not deployment:
            raise ValueError("embedding deployment name is required")

        resp = self._client.get_embeddings(deployment, input=texts)
        vectors = [d.embedding for d in resp.data]
        return vectors
