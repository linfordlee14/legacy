"""Retrieval primitives over the chunk store (RAG-07, RAG-11, RAG-12).

Both searches apply the caller's privacy-tier predicate INSIDE the store
query (post-retrieval filtering alone is forbidden), scope to the active
embedding model version (vectors from different versions are never
compared, AIA-11), skip superseded chunks, and exclude chunks whose parent
row is soft-deleted (DATABASE_SCHEMA 4.8: immediate exclusion). The fused
hybrid query pipeline and its API arrive with MVP-017.
"""

from typing import Any

from psycopg import AsyncConnection
from psycopg.rows import dict_row

from legacy_api.ai.router import ModelRouter
from legacy_api.rag.indexer import vector_literal

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
            {"query": query, "tiers": tiers, "version": version, "limit": limit},
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
