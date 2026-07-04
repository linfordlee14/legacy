"""Model Router: the single choke point for provider calls (ADR-06; AIA-05
to AIA-07).

Only the embedding task class is live in this phase (MVP-016); generation
routing arrives with the stretch ask (MVP-024). Embedding requests go to
the exact pinned model of the routing configuration; per AIA-06 a failed
call is retried once, and because vectors from different models are never
mixed (AIA-11) there is no lower-quality fallback: the router raises
EmbeddingUnavailable and the write path queues work instead (RAG-08).
"""

import logging
from typing import Any, Protocol

from legacy_api.ai.routing import (
    EMBEDDING_DIMENSIONS,
    EMBEDDING_MODEL,
    EMBEDDING_MODEL_VERSION,
    EMBEDDING_PROVIDER,
)

logger = logging.getLogger("legacy_api.ai.router")


class EmbeddingUnavailable(RuntimeError):
    """Embedding cannot be produced now; callers queue, never degrade."""


class EmbeddingProvider(Protocol):
    name: str
    model: str
    dimensions: int

    async def embed(self, texts: list[str], task_type: str) -> list[list[float]]: ...


def estimate_tokens(text: str) -> int:
    """Coarse accounting estimate (roughly four characters per token); the
    embeddings endpoint reports no usage, and the spend counter needs a
    consistent signal more than a exact one."""
    return max(1, len(text) // 4)


class ModelRouter:
    embedding_model = EMBEDDING_MODEL
    embedding_version = EMBEDDING_MODEL_VERSION
    embedding_dimensions = EMBEDDING_DIMENSIONS

    def __init__(
        self,
        embedding_provider: EmbeddingProvider | None = None,
        metrics: Any = None,
    ) -> None:
        self._embedding_provider = embedding_provider
        self._metrics = metrics

    @property
    def embedding_configured(self) -> bool:
        return self._embedding_provider is not None

    async def _embed(self, texts: list[str], task_type: str) -> list[list[float]]:
        if self._embedding_provider is None:
            raise EmbeddingUnavailable(
                "embedding provider not configured (LEGACY_GEMINI_API_KEY absent)"
            )
        try:
            vectors = await self._embedding_provider.embed(texts, task_type)
        except Exception:
            # AIA-06: retry once on the same model, then fail loudly.
            logger.warning("embedding call failed, retrying once", exc_info=True)
            try:
                vectors = await self._embedding_provider.embed(texts, task_type)
            except Exception as exc:
                raise EmbeddingUnavailable(str(exc)) from exc
        if self._metrics is not None:
            self._metrics.record_tokens(
                EMBEDDING_PROVIDER,
                self.embedding_model,
                "input",
                sum(estimate_tokens(text) for text in texts),
            )
        return vectors

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return await self._embed(texts, "RETRIEVAL_DOCUMENT")

    async def embed_query(self, text: str) -> list[float]:
        return (await self._embed([text], "RETRIEVAL_QUERY"))[0]
