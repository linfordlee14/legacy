"""Gemini embedding provider adapter (ADR-16; ADR-06 provider set).

Called only by the ModelRouter. Batches texts to the pinned model with
output_dimensionality fixed by the routing configuration, and L2-normalizes
every vector client-side (the provider documents that non-default
dimensions require manual normalization).
"""

import math
from typing import Any

import httpx

from legacy_api.ai.routing import EMBEDDING_DIMENSIONS, EMBEDDING_MODEL

API_ROOT = "https://generativelanguage.googleapis.com/v1beta"
# The documented batch ceiling is generous; a conservative page size keeps
# request bodies small and failures cheap to retry.
BATCH_SIZE = 64


def l2_normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(component * component for component in vector))
    if norm == 0.0:
        return vector
    return [component / norm for component in vector]


class GeminiEmbeddingProvider:
    """Embeds text through the exact pinned model (never an alias)."""

    name = "gemini"
    model = EMBEDDING_MODEL
    dimensions = EMBEDDING_DIMENSIONS

    def __init__(self, api_key: str, timeout_s: float = 30.0) -> None:
        self._api_key = api_key
        self._timeout_s = timeout_s

    async def embed(self, texts: list[str], task_type: str) -> list[list[float]]:
        """task_type is RETRIEVAL_DOCUMENT for chunk writes and
        RETRIEVAL_QUERY for query embedding (provider-documented types)."""
        vectors: list[list[float]] = []
        async with httpx.AsyncClient(timeout=self._timeout_s) as client:
            for start in range(0, len(texts), BATCH_SIZE):
                page = texts[start : start + BATCH_SIZE]
                response = await client.post(
                    f"{API_ROOT}/models/{self.model}:batchEmbedContents",
                    params={"key": self._api_key},
                    json={
                        "requests": [
                            {
                                "model": f"models/{self.model}",
                                "content": {"parts": [{"text": text}]},
                                "taskType": task_type,
                                "outputDimensionality": self.dimensions,
                            }
                            for text in page
                        ]
                    },
                )
                response.raise_for_status()
                payload: dict[str, Any] = response.json()
                for embedding in payload["embeddings"]:
                    vector = embedding["values"]
                    if len(vector) != self.dimensions:
                        raise ValueError(
                            f"provider returned {len(vector)} dimensions, "
                            f"expected {self.dimensions}"
                        )
                    vectors.append(l2_normalize(vector))
        return vectors
