"""Retrieval primitives over the chunk store (RAG-07, RAG-11, RAG-12).

Both searches apply the caller's privacy-tier predicate INSIDE the store
query (post-retrieval filtering alone is forbidden), scope to the active
embedding model version (vectors from different versions are never
compared, AIA-11), skip superseded chunks, and exclude chunks whose parent
row is soft-deleted (DATABASE_SCHEMA 4.8: immediate exclusion).

Hybrid retrieval fuses the two independent lists by reciprocal rank
fusion (ADR-17): scale-free, no score calibration, k and pool sizes are
configuration. When the query cannot be embedded, hybrid degrades to
lexical-only with an explicit flag (RAG-25: never silent).
"""

from dataclasses import dataclass
from typing import Any

from psycopg import AsyncConnection
from psycopg.rows import dict_row

from legacy_api.ai.router import EmbeddingUnavailable, ModelRouter
from legacy_api.rag.indexer import vector_literal


@dataclass(frozen=True)
class FusionConfig:
    """ADR-17: configuration, not code constants; k tuned on the retrieval
    label set as it grows (RAG-27)."""

    rrf_k: int = 60
    pool_size: int = 30

CHUNK_COLUMNS = (
    "id, entity_type, entity_id, chunk_index, chunk_text, heading_path, "
    "privacy_tier, embedding_model_version, created_at"
)

# Parent liveness per source type: soft-deleted parents drop out of every
# read path immediately. Tier filtering never needs this join (the tier is
# denormalized onto the chunk); deletion visibility does.
PARENT_LIVE = """
    (
        (c.entity_type = 'Note' AND EXISTS (
            SELECT 1 FROM note p WHERE p.id = c.entity_id AND p.deleted_at IS NULL))
        OR (c.entity_type = 'Artifact' AND EXISTS (
            SELECT 1 FROM artifact p WHERE p.id = c.entity_id AND p.deleted_at IS NULL))
    )
"""


def lexical_query(query: str) -> str:
    """Recall-oriented query form for websearch_to_tsquery: bare terms are
    OR-joined (websearch space means AND, which makes verbose queries
    demand every word in one chunk); ts_rank still favors chunks matching
    more terms. Quoted phrases and explicit operators pass through
    untouched, preserving exact-phrase support (RAG-07b)."""
    if '"' in query or " OR " in query or " -" in query:
        return query
    terms = query.split()
    return " OR ".join(terms) if len(terms) > 1 else query


async def lexical_search(
    conn: AsyncConnection[Any],
    query: str,
    tiers: list[str],
    version: str,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Full-text retrieval with stemming and phrase support (RAG-07b)."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            f"""
            SELECT {CHUNK_COLUMNS},
                   ts_rank(to_tsvector('english', chunk_text),
                           websearch_to_tsquery('english', %(query)s)) AS score
            FROM embedding_chunk c
            WHERE to_tsvector('english', chunk_text)
                      @@ websearch_to_tsquery('english', %(query)s)
              AND embedding_model_version = %(version)s
              AND superseded_by IS NULL
              AND privacy_tier = ANY(%(tiers)s)
              AND {PARENT_LIVE}
            ORDER BY score DESC, id DESC
            LIMIT %(limit)s
            """,
            {
                "query": lexical_query(query),
                "tiers": tiers,
                "version": version,
                "limit": limit,
            },
        )
        return list(await cur.fetchall())


async def vector_search(
    conn: AsyncConnection[Any],
    router: ModelRouter,
    query: str,
    tiers: list[str],
    limit: int = 20,
) -> list[dict[str, Any]]:
    """ANN retrieval at the active model version. The cast expression
    matches the version-scoped index definition so the planner can use it."""
    query_vector = vector_literal(await router.embed_query(query))
    dimensions = router.embedding_dimensions
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            f"""
            SELECT {CHUNK_COLUMNS},
                   (embedding::vector({dimensions})
                        <=> %(query_vector)s::vector({dimensions})) AS distance
            FROM embedding_chunk c
            WHERE embedding_model_version = %(version)s
              AND superseded_by IS NULL
              AND privacy_tier = ANY(%(tiers)s)
              AND {PARENT_LIVE}
            ORDER BY embedding::vector({dimensions})
                         <=> %(query_vector)s::vector({dimensions})
            LIMIT %(limit)s
            """,
            {
                "query_vector": query_vector,
                "tiers": tiers,
                "version": router.embedding_version,
                "limit": limit,
            },
        )
        return list(await cur.fetchall())


def fuse_rrf(
    ranked_lists: dict[str, list[dict[str, Any]]], config: FusionConfig | None = None
) -> list[dict[str, Any]]:
    """Reciprocal rank fusion (ADR-17): each list contributes 1/(k + rank)
    for every chunk it returned; a chunk found by both lists accumulates
    both contributions. Deterministic: ties break on chunk id."""
    config = config or FusionConfig()
    fused: dict[str, dict[str, Any]] = {}
    for source, rows in ranked_lists.items():
        for rank, row in enumerate(rows, start=1):
            chunk_id = str(row["id"])
            entry = fused.setdefault(
                chunk_id, {**row, "rrf_score": 0.0, "matched": []}
            )
            entry["rrf_score"] += 1.0 / (config.rrf_k + rank)
            entry["matched"].append(source)
    return sorted(
        fused.values(), key=lambda entry: (-entry["rrf_score"], str(entry["id"]))
    )


async def hybrid_search(
    conn: AsyncConnection[Any],
    router: ModelRouter,
    query: str,
    tiers: list[str],
    limit: int = 20,
    config: FusionConfig | None = None,
) -> tuple[list[dict[str, Any]], bool]:
    """RAG-11: vector and lexical candidates retrieved independently (each
    with the tier predicate in-store), fused by RRF. Returns (results,
    degraded): embedding failure degrades to lexical-only, flagged, never
    silent (RAG-25 and the RAG 4.9 failure table)."""
    config = config or FusionConfig()
    lexical = await lexical_search(
        conn, query, tiers, router.embedding_version, limit=config.pool_size
    )
    degraded = False
    try:
        vector = await vector_search(conn, router, query, tiers, limit=config.pool_size)
    except EmbeddingUnavailable:
        vector = []
        degraded = True
    fused = fuse_rrf({"lexical": lexical, "semantic": vector}, config)
    return fused[:limit], degraded
