"""GET /v1/search (MVP-017; API_SPECIFICATION 4.4; FS-004; NFR-035).

Lexical, semantic, and hybrid modes over the chunk store. The caller's
privacy-tier predicate executes inside the datastore query before any
ranking or response assembly (NFR-035; RAG-12; AUTHORIZATION 4.4 point 2);
trusted callers get per-row grant-scope refinement on top, exactly like
the content lists. Results carry the privacy tier, the provenance block
(FS-004: provenance tier and privacy tier are always displayed), and a
citation-ready chunk reference with its heading path (RAG-24). Hybrid and
semantic degrade to lexical-only with an explicit machine-readable flag
when the query cannot be embedded (RAG-25); zero results return an empty
list, never an invention. Counts in the response reflect only content at
or below the caller's ceiling: existence above it is never leaked, not
even as a number (RAG-22).
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request
from psycopg import AsyncConnection
from psycopg.rows import dict_row

from legacy_api.ai.router import EmbeddingUnavailable
from legacy_api.api.errors import ApiError, ErrorCode
from legacy_api.api.pagination import DEFAULT_LIMIT, LimitParam
from legacy_api.auth import Principal, authenticate_optional
from legacy_api.obs.tracing import span
from legacy_api.policy import (
    Action,
    AuthzContext,
    Resource,
    decide,
    resolve_context,
    tiers_within,
)
from legacy_api.provenance import provenance_for_entity
from legacy_api.rag.retrieval import (
    FusionConfig,
    fuse_rrf,
    hybrid_search,
    lexical_search,
    vector_search,
)

router = APIRouter(prefix="/v1", tags=["search"])

MODES = ("hybrid", "lexical", "semantic")
MAX_QUERY_CHARS = 500  # FS-004 edge case: very long queries truncate with notice
SNIPPET_CHARS = 280

TITLE_TABLES = {"Note": "note", "Artifact": "artifact"}


def _snippet(text: str) -> str:
    if len(text) <= SNIPPET_CHARS:
        return text
    return text[:SNIPPET_CHARS].rsplit(" ", 1)[0] + "…"


async def _scope_filter(
    conn: AsyncConnection[Any], ctx: AuthzContext, rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Grant-scope refinement for trusted callers (AUTHORIZATION 4.3): the
    in-store tier predicate bounds the ceiling; grants bound the scope."""
    if ctx.kind != "trusted":
        return rows
    kept = []
    for row in rows:
        resource = Resource(
            entity_type=row["entity_type"],
            entity_id=str(row["entity_id"]),
            privacy_tier=row["privacy_tier"],
        )
        if (await decide(conn, ctx, Action.CONTENT_READ, resource)).allow:
            kept.append(row)
    return kept


async def _titles(
    conn: AsyncConnection[Any], rows: list[dict[str, Any]]
) -> dict[tuple[str, str], str | None]:
    titles: dict[tuple[str, str], str | None] = {}
    for entity_type, table in TITLE_TABLES.items():
        ids = [
            str(row["entity_id"]) for row in rows if row["entity_type"] == entity_type
        ]
        if not ids:
            continue
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                f"SELECT id, title FROM {table} WHERE id = ANY(%s::uuid[])", (ids,)
            )
            for row in await cur.fetchall():
                titles[(entity_type, str(row["id"]))] = row["title"]
    return titles


def _score_of(row: dict[str, Any]) -> float:
    """Mode-specific relevance, higher is better; scores are not comparable
    across modes."""
    if "rrf_score" in row:
        return float(row["rrf_score"])
    if "distance" in row:
        return 1.0 - float(row["distance"])
    return float(row.get("score", 0.0))


@router.get("/search")
async def search(
    request: Request,
    principal: Annotated[Principal | None, Depends(authenticate_optional)],
    q: Annotated[str, Query()] = "",
    mode: Annotated[str, Query()] = "hybrid",
    limit: LimitParam = DEFAULT_LIMIT,
) -> dict[str, Any]:
    if mode not in MODES:
        raise ApiError(
            422, ErrorCode.VALIDATION_FAILED, "Unknown search mode.",
            {"mode": mode, "modes": list(MODES)},
        )
    query = q.strip()
    if not query:
        raise ApiError(
            422, ErrorCode.VALIDATION_FAILED, "Query is required.", {"parameter": "q"}
        )
    truncated = len(query) > MAX_QUERY_CHARS
    if truncated:
        query = query[:MAX_QUERY_CHARS]

    model_router = request.app.state.model_router
    degraded = False
    async with request.app.state.pool.connection() as conn:
        ctx = await resolve_context(conn, principal)
        tiers = tiers_within(ctx.ceiling)
        config = FusionConfig()

        with span(f"search.{mode}"):
            if mode == "lexical":
                rows = await lexical_search(
                    conn, query, tiers, model_router.embedding_version,
                    limit=config.pool_size,
                )
                rows = fuse_rrf({"lexical": rows}, config)
            elif mode == "semantic":
                try:
                    rows = await vector_search(
                        conn, model_router, query, tiers, limit=config.pool_size
                    )
                    rows = fuse_rrf({"semantic": rows}, config)
                except EmbeddingUnavailable:
                    # RAG 4.9 failure table: lexical-only, explicit flag.
                    degraded = True
                    rows = fuse_rrf(
                        {
                            "lexical": await lexical_search(
                                conn, query, tiers, model_router.embedding_version,
                                limit=config.pool_size,
                            )
                        },
                        config,
                    )
            else:
                rows, degraded = await hybrid_search(
                    conn, model_router, query, tiers, limit=config.pool_size,
                    config=config,
                )

        considered = len(rows)
        rows = (await _scope_filter(conn, ctx, rows))[:limit]
        titles = await _titles(conn, rows)

        results = []
        for row in rows:
            entity_key = (row["entity_type"], str(row["entity_id"]))
            provenance = await provenance_for_entity(
                conn, row["entity_type"], str(row["entity_id"]), tiers
            )
            results.append(
                {
                    "chunk_id": str(row["id"]),
                    "chunk_ref": f"{row['entity_id']}#c{row['chunk_index']}",
                    "entity_type": row["entity_type"],
                    "entity_id": str(row["entity_id"]),
                    "title": titles.get(entity_key),
                    "snippet": _snippet(row["chunk_text"]),
                    "heading_path": row["heading_path"],
                    "privacy_tier": row["privacy_tier"],
                    "score": _score_of(row),
                    "matched": row.get("matched", [mode]),
                    "provenance": provenance.model_dump(),
                }
            )

    return {
        "query": query,
        "mode": mode,
        "degraded": degraded,
        "truncated": truncated,
        "results": results,
        # Counts reflect only content at or below the caller's ceiling
        # (the tier predicate ran in-store): no existence leak (RAG-22).
        "retrieval": {
            "chunks_considered": considered,
            "chunks_returned": len(results),
            "tier_ceiling": ctx.ceiling,
        },
    }
