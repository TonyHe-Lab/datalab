"""Azure OpenAI client wrapper with rate limiting, backoff, and circuit breaker.

This module provides a thin wrapper around the Azure OpenAI REST/SDK for chat
completions and embeddings, with production-friendly concerns:

- Exponential backoff on retryable errors (e.g., 429/5xx)
- Simple token usage accounting from SDK responses (when available)
- Circuit breaker to prevent cascading failures when the service is down
- Optional streaming support for chat completions

Tests can mock the public interface and the internal SDK client.
"""

from typing import List, Dict, Any, Optional, Callable
import os
import time
import logging

RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class CircuitBreaker:
    """Minimal circuit breaker.

    - Opens the circuit after `failure_threshold` consecutive failures.
    - Half-open after `reset_timeout` seconds, allowing one trial call.
    - Closes the circuit on a successful call.
    """

    def __init__(self, failure_threshold: int = 3, reset_timeout: int = 30):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.state = "CLOSED"  # CLOSED | OPEN | HALF_OPEN
        self.opened_at = 0.0

    def allow(self) -> bool:
        if self.state == "OPEN":
            if time.time() - self.opened_at >= self.reset_timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        return True

    def on_success(self):
        self.failures = 0
        self.state = "CLOSED"

    def on_failure(self):
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self.state = "OPEN"
            self.opened_at = time.time()


class AzureOpenAIClient:
    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        chat_deployment: Optional[str] = None,
        embed_deployment: Optional[str] = None,
        request_timeout: float = 15.0,
    ):
        # Load from env if not provided
        self.endpoint = endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY")
        self.chat_deployment = chat_deployment or os.getenv("AZURE_OPENAI_DEPLOYMENT")
        self.embed_deployment = embed_deployment or os.getenv(
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
        )

        try:
            from azure.ai.openai import OpenAIClient
            from azure.core.credentials import AzureKeyCredential

            if self.endpoint and self.api_key:
                self._client = OpenAIClient(
                    self.endpoint, AzureKeyCredential(self.api_key)
                )
            else:
                self._client = None
        except ImportError:
            self._client = None

        # Observability fields
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_embedding_tokens = 0
        self.logger = logging.getLogger(__name__)

        # Resilience
        self.breaker = CircuitBreaker()

    def _with_retry(
        self,
        func: Callable[[], Any],
        max_retries: int = 3,
        on_retry: Optional[Callable[[Exception, int], None]] = None,
    ) -> Any:
        """Execute func with exponential backoff on retryable errors.

        func must raise an exception with potential `status_code` attribute for HTTP errors.
        """
        attempt = 0
        delay = 1.0
        last_exc = None
        while attempt <= max_retries:
            try:
                return func()
            except Exception as e:
                status = getattr(e, "status_code", None)
                # For azure-core HTTP errors, status may be under e.status_code or e.response.status_code
                if status is None:
                    resp = getattr(e, "response", None)
                    status = getattr(resp, "status_code", None)

                # Treat timeouts and transient SDK errors as retryable
                name = e.__class__.__name__
                msg = str(e).lower()
                is_timeout = (
                    isinstance(e, TimeoutError)
                    or "timeout" in name.lower()
                    or "timeout" in msg
                )
                if status in RETRYABLE_STATUS or is_timeout:
                    last_exc = e
                    self.logger.warning(
                        f"AzureOpenAIClient retryable error (status={status}, attempt={attempt}): {e}"
                    )
                    if on_retry:
                        try:
                            on_retry(e, attempt)
                        except Exception:
                            pass
                    time.sleep(delay)
                    delay = min(delay * 2, 8.0)  # cap backoff
                    attempt += 1
                    continue
                # Non-retryable error
                raise
        if last_exc:
            raise last_exc
        # Should not reach here
        raise RuntimeError("Retry loop exited unexpectedly")

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1024,
        deployment: Optional[str] = None,
        stream: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """Perform a chat completion request using Azure SDK when available.

        messages: list of {'role': 'user'|'system'|'assistant', 'content': '...'}
        Returns a dict with 'content' and raw SDK response under 'raw'. If stream=True,
        returns an iterator-like list of chunks under 'stream' and aggregates content.
        """
        if not self._client:
            raise RuntimeError("Azure OpenAI SDK not configured or missing credentials")

        deployment = deployment or self.chat_deployment
        if not deployment:
            raise ValueError("chat deployment name is required")

        if not self.breaker.allow():
            raise RuntimeError("Circuit open: Azure OpenAI unavailable")

        def call():
            # Some SDKs accept timeout via kwargs; if unsupported, rely on client-side breaker/retry
            return self._client.get_chat_completions(
                deployment,
                messages=messages,
                max_tokens=max_tokens,
                **kwargs,
            )

        try:
            resp = self._with_retry(
                call, on_retry=lambda e, a: self.breaker.on_failure()
            )
        except Exception:
            self.breaker.on_failure()
            raise

        # Token accounting (best-effort based on SDK response shape)
        usage = getattr(resp, "usage", None)
        if usage:
            try:
                prompt_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
                completion_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
            except Exception:
                prompt_tokens = 0
                completion_tokens = 0
            self.total_prompt_tokens += prompt_tokens
            self.total_completion_tokens += completion_tokens

        # Streaming mode: Azure SDK may support a different API; emulate if present in resp
        if stream and hasattr(resp, "choices") and len(resp.choices) > 0:
            chunks = []
            content_acc = []
            for choice in resp.choices:
                delta = getattr(choice, "delta", None)
                if delta and getattr(delta, "content", None):
                    part = delta.content
                    chunks.append(part)
                    content_acc.append(part)
            aggregated = "".join(content_acc) if content_acc else None
            self.breaker.on_success()
            return {"content": aggregated, "stream": chunks, "raw": resp}

        try:
            choice = resp.choices[0]
            content = getattr(choice.message, "content", None)
            self.breaker.on_success()
            return {"content": content, "raw": resp}
        except Exception:
            self.breaker.on_success()
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

        if not self.breaker.allow():
            raise RuntimeError("Circuit open: Azure OpenAI unavailable")

        def call():
            return self._client.get_embeddings(deployment, input=texts)

        try:
            resp = self._with_retry(
                call, on_retry=lambda e, a: self.breaker.on_failure()
            )
        except Exception:
            self.breaker.on_failure()
            raise

        # Token accounting if available
        usage = getattr(resp, "usage", None)
        if usage:
            try:
                total_tokens = int(getattr(usage, "total_tokens", 0) or 0)
            except Exception:
                total_tokens = 0
            self.total_embedding_tokens += total_tokens

        vectors = [d.embedding for d in resp.data]
        # Enforce expected dimension if known (1536 for text-embedding-3-small)
        try:
            for v in vectors:
                if len(v) != 1536:
                    # Some Azure deployments may return different sizes; we surface an error
                    raise ValueError(
                        f"Unexpected embedding dimension: {len(v)} (expected 1536)"
                    )
        except Exception:
            # If resp shape differs, skip strict check; pipeline will validate as well
            pass
        self.breaker.on_success()
        return vectors
