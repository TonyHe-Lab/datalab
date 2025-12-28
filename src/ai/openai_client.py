"""Azure OpenAI client wrapper (initial skeleton).

This module provides a thin wrapper around the Azure OpenAI REST/SDK
for chat completions and embeddings. It is intentionally small for
the first iteration so tests can mock its interface.
"""

from typing import List, Dict, Any, Optional
import os


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

    def chat_completion(
        self, messages: List[Dict[str, str]], max_tokens: int = 1024, **kwargs
    ) -> Dict[str, Any]:
        """Perform a chat completion request.

        For tests this method will be mocked. Production implementation
        should use official Azure OpenAI SDK or requests to REST endpoints.
        """
        raise NotImplementedError(
            "chat_completion must be implemented using Azure SDK or REST API"
        )

    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for the provided list of texts.

        Returns a list of vectors (list of floats).
        """
        raise NotImplementedError(
            "create_embeddings must be implemented using Azure SDK or REST API"
        )
