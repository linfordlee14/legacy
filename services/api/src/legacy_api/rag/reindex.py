"""Rebuild the chunk store from source rows (NFR-024; `make reindex`).

Embeddings are a rebuildable cache: this walks every live source row and
indexes it at the active model version. Safe to re-run (RAG-03 makes
unchanged entities no-ops) and it is the recovery path both for queued
entities (embedding provider was down at write time) and for the
rebuild-from-source drill.
"""

import asyncio
import json
import sys
from typing import Any

from psycopg import AsyncConnection
from psycopg.rows import dict_row

from legacy_api.ai.gemini import GeminiEmbeddingProvider
from legacy_api.ai.router import EmbeddingUnavailable, ModelRouter
from legacy_api.rag.indexer import SOURCES, index_entity


async def reindex_all(conn: AsyncConnection[Any], router: ModelRouter) -> dict[str, Any]:
    summary: dict[str, Any] = {"version": router.embedding_version, "entities": {}}
    for entity_type, spec in SOURCES.items():
        counts = {"indexed": 0, "unchanged": 0, "no_content": 0}
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                f"SELECT id FROM {spec['table']} WHERE deleted_at IS NULL ORDER BY id"
            )
            rows = await cur.fetchall()
        for row in rows:
            result = await index_entity(conn, router, entity_type, str(row["id"]))
            counts[result["status"]] = counts.get(result["status"], 0) + 1
        summary["entities"][entity_type] = counts
    await conn.commit()
    return summary


async def _amain() -> int:
    from legacy_api.config import get_settings

    settings = get_settings()
    if not settings.database_url:
        print("LEGACY_DATABASE_URL is required (DEP-18)", file=sys.stderr)
        return 2
    if not settings.gemini_api_key:
        print("LEGACY_GEMINI_API_KEY is required to build embeddings", file=sys.stderr)
        return 2
    router = ModelRouter(GeminiEmbeddingProvider(settings.gemini_api_key))
    conn = await AsyncConnection.connect(settings.database_url)
    try:
        summary = await reindex_all(conn, router)
    except EmbeddingUnavailable as exc:
        print(f"embedding provider unavailable: {exc}", file=sys.stderr)
        return 1
    finally:
        await conn.close()
    print(json.dumps(summary, indent=2))
    return 0


def main() -> None:
    raise SystemExit(asyncio.run(_amain()))


if __name__ == "__main__":
    main()
