"""Chunk indexing: source rows into EmbeddingChunk (RAG-01 to RAG-08).

Every chunk row carries the RAG-05 provenance packet: parent reference,
ordinal, heading path, inherited privacy tier, timestamps, content hash,
injection-flag status (false until the Curation Agent ships), and the
exact pinned embedding model version. Idempotency per RAG-03: an
unchanged source (same chunk hashes) is a no-op; a change supersedes the
old chunks (tombstoned via superseded_by, never deleted here). Embedding
reuse is cache-first by content hash (MASTER_ARCHITECTURE cost control).
Embeddings are a rebuildable cache: reindex rebuilds everything from the
source rows (NFR-024).
"""

import logging
from typing import Any

from psycopg import AsyncConnection
from psycopg.rows import dict_row

from legacy_api.ai.router import EmbeddingUnavailable, ModelRouter
from legacy_api.audit import SYSTEM_USER_ID
from legacy_api.rag.chunking import Chunk, ChunkingConfig, chunk_document

logger = logging.getLogger("legacy_api.rag.indexer")

# The indexable corpus in this phase: the workspace collections. The text
# expression yields the canonical Markdown the chunks embed (ADR-13).
SOURCES: dict[str, dict[str, str]] = {
    "Note": {
        "table": "note",
        "text_sql": "COALESCE(title || E'\\n\\n', '') || body",
    },
    "Artifact": {
        "table": "artifact",
        "text_sql": "COALESCE(title || E'\\n\\n', '') || COALESCE(canonical_markdown, '')",
    },
}


def vector_literal(vector: list[float]) -> str:
    return "[" + ",".join(repr(component) for component in vector) + "]"


async def _live_chunks(
    conn: AsyncConnection[Any], entity_type: str, entity_id: str, version: str
) -> list[dict[str, Any]]:
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT id, chunk_index, content_hash FROM embedding_chunk
            WHERE entity_type = %s AND entity_id = %s
              AND embedding_model_version = %s AND superseded_by IS NULL
            ORDER BY chunk_index
            """,
            (entity_type, entity_id, version),
        )
        return await cur.fetchall()


async def _cached_vectors(
    conn: AsyncConnection[Any], hashes: list[str], version: str
) -> dict[str, str]:
    """Cache-first embedding reuse keyed by content hash: any existing row
    for the same text and model version already holds the vector."""
    if not hashes:
        return {}
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT DISTINCT ON (content_hash) content_hash, embedding::text AS embedding
            FROM embedding_chunk
            WHERE content_hash = ANY(%s) AND embedding_model_version = %s
            """,
            (hashes, version),
        )
        rows = await cur.fetchall()
    return {row["content_hash"]: row["embedding"] for row in rows}


async def index_entity(
    conn: AsyncConnection[Any],
    router: ModelRouter,
    entity_type: str,
    entity_id: str,
    config: ChunkingConfig | None = None,
) -> dict[str, Any]:
    """Chunk and embed one source row; returns a status summary.

    Raises EmbeddingUnavailable when new vectors are needed but the
    provider is not reachable; callers queue the entity (RAG-08) rather
    than storing partial or degraded rows.
    """
    spec = SOURCES[entity_type]
    version = router.embedding_version
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            f"""
            SELECT id, privacy_tier, ({spec["text_sql"]}) AS content
            FROM {spec["table"]}
            WHERE id = %s AND deleted_at IS NULL
            """,
            (entity_id,),
        )
        parent = await cur.fetchone()
    if parent is None or not (parent["content"] or "").strip():
        return {"status": "no_content", "chunks": 0}

    chunks: list[Chunk] = chunk_document(parent["content"], config)
    existing = await _live_chunks(conn, entity_type, entity_id, version)
    if [(c.index, c.content_hash) for c in chunks] == [
        (row["chunk_index"], row["content_hash"]) for row in existing
    ]:
        return {"status": "unchanged", "chunks": len(chunks)}  # RAG-03 no-op

    cached = await _cached_vectors(conn, [c.content_hash for c in chunks], version)
    to_embed = [c for c in chunks if c.content_hash not in cached]
    if to_embed:
        vectors = await router.embed_documents([c.text for c in to_embed])
        for chunk, vector in zip(to_embed, vectors, strict=True):
            cached[chunk.content_hash] = vector_literal(vector)

    new_ids: list[str] = []
    async with conn.cursor(row_factory=dict_row) as cur:
        # Tombstone the displaced generation first so its positions leave
        # the live-position uniqueness index before successors claim them.
        # The interim self-reference satisfies the foreign key and is
        # repointed at the real positional successor below, inside this
        # same transaction (RAG-03: tombstoned until consistency confirmed).
        for old in existing:
            await cur.execute(
                "UPDATE embedding_chunk SET superseded_by = id WHERE id = %s",
                (old["id"],),
            )

        for chunk in chunks:
            await cur.execute(
                """
                INSERT INTO embedding_chunk
                    (entity_type, entity_id, chunk_index, chunk_text, token_count,
                     content_hash, embedding, embedding_model_version, heading_path,
                     injection_flag, privacy_tier, created_by, origin_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s::vector, %s, %s, false, %s, %s, 'system')
                RETURNING id
                """,
                (
                    entity_type,
                    entity_id,
                    chunk.index,
                    chunk.text,
                    chunk.token_count,
                    chunk.content_hash,
                    cached[chunk.content_hash],
                    version,
                    chunk.heading_path,
                    parent["privacy_tier"],
                    SYSTEM_USER_ID,
                ),
            )
            row = await cur.fetchone()
            assert row is not None
            new_ids.append(str(row["id"]))

        # Each old chunk points at its positional successor, or the first
        # new chunk when the new sequence is shorter.
        for old in existing:
            successor = new_ids[min(old["chunk_index"], len(new_ids) - 1)]
            await cur.execute(
                "UPDATE embedding_chunk SET superseded_by = %s WHERE id = %s",
                (successor, old["id"]),
            )
    return {
        "status": "indexed",
        "chunks": len(chunks),
        "embedded": len(to_embed),
        "reused": len(chunks) - len(to_embed),
        "superseded": len(existing),
    }


async def index_entity_or_queue(
    conn: AsyncConnection[Any],
    router: ModelRouter,
    entity_type: str,
    entity_id: str,
    metrics: Any = None,
) -> dict[str, Any]:
    """RAG-08 write path: index now, or leave the entity queued (it has no
    live chunks) and make the gap visible via the searchable-lag signal.
    Vector-only gaps are never silently ignored."""
    try:
        return await index_entity(conn, router, entity_type, entity_id)
    except EmbeddingUnavailable as exc:
        logger.warning(
            "embedding unavailable, entity queued for reindex",
            extra={"entity_type": entity_type, "entity_id": entity_id, "reason": str(exc)},
        )
        if metrics is not None:
            metrics.record_embedding_deferred()
        return {"status": "queued", "chunks": 0}
