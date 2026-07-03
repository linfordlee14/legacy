"""Claims resource: the first real resource group on the /v1 surface.

Demonstrates every 4.1 to 4.3 convention on genuine data: cursor pagination,
allowlisted sorting, filtering, tier-filtered visibility through the policy
service, uniform not_found, and the mandatory provenance block.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request
from psycopg import AsyncConnection
from psycopg.rows import dict_row

from legacy_api.api.errors import ApiError, ErrorCode
from legacy_api.api.pagination import (
    DEFAULT_LIMIT,
    CursorParam,
    LimitParam,
    Page,
    decode_cursor,
    page_of,
)
from legacy_api.auth import Principal, authenticate_optional
from legacy_api.obs.tracing import span
from legacy_api.policy import (
    Action,
    Resource,
    decide,
    read_or_not_found,
    resolve_context,
    tiers_within,
)
from legacy_api.provenance import provenance_for_claims

router = APIRouter(prefix="/v1/claims", tags=["claims"])

SORTS = {"-created_at": "DESC", "created_at": "ASC"}
CONFIDENCE_TIERS = {"verified", "self_reported", "flagged"}


def serialize(row: dict[str, Any], provenance: Any) -> dict[str, Any]:
    return {
        "id": str(row["id"]),
        "subject_type": row["subject_type"],
        "subject_id": str(row["subject_id"]),
        "predicate": row["predicate"],
        "statement": row["statement"],
        "privacy_tier": row["privacy_tier"],
        "created_at": row["created_at"].isoformat(),
        "updated_at": row["updated_at"].isoformat(),
        "provenance": {
            "claims": [provenance.model_dump()] if provenance else [],
        },
    }


@router.get("")
async def list_claims(
    request: Request,
    principal: Annotated[Principal | None, Depends(authenticate_optional)],
    limit: LimitParam = DEFAULT_LIMIT,
    cursor: CursorParam = None,
    subject_type: Annotated[str | None, Query()] = None,
    tier: Annotated[str | None, Query()] = None,
    sort: Annotated[str, Query()] = "-created_at",
) -> Page:
    if sort not in SORTS:
        raise ApiError(
            422, ErrorCode.VALIDATION_FAILED, "Unsupported sort.", {"allowed": list(SORTS)}
        )
    if tier is not None and tier not in CONFIDENCE_TIERS:
        raise ApiError(
            422, ErrorCode.VALIDATION_FAILED, "Unknown confidence tier.",
            {"allowed": sorted(CONFIDENCE_TIERS)},
        )

    pool = request.app.state.pool
    async with pool.connection() as conn:
        ctx = await resolve_context(conn, principal)
        direction = SORTS[sort]
        comparator = "<" if direction == "DESC" else ">"
        clauses = ["deleted_at IS NULL", "privacy_tier = ANY(%(tiers)s)"]
        params: dict[str, Any] = {
            "tiers": tiers_within(ctx.ceiling),
            "limit": limit + 1,
        }
        if cursor is not None:
            clauses.append(f"id {comparator} %(cursor)s")
            params["cursor"] = decode_cursor(cursor)
        if subject_type is not None:
            clauses.append("subject_type = %(subject_type)s")
            params["subject_type"] = subject_type
        if tier is not None:
            clauses.append("confidence_tier = %(tier)s")
            params["tier"] = tier

        with span("db.claim_list"):
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    f"""
                    SELECT id, subject_type, subject_id, predicate, statement,
                           privacy_tier, confidence_tier, created_at, updated_at
                    FROM claim
                    WHERE {" AND ".join(clauses)}
                    ORDER BY id {direction}
                    LIMIT %(limit)s
                    """,
                    params,
                )
                rows = await cur.fetchall()

        rows = await _scope_filter(conn, ctx, rows)
        provenance = await provenance_for_claims(conn, [str(r["id"]) for r in rows])
        serialized = [serialize(r, provenance.get(str(r["id"]))) for r in rows]
        return page_of(serialized, limit)


async def _scope_filter(
    conn: AsyncConnection[Any], ctx: Any, rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Trusted contexts additionally require grant-scope coverage of each
    claim's subject (AUTHORIZATION 4.3); other contexts are tier-only."""
    if ctx.kind != "trusted":
        return rows
    kept = []
    for row in rows:
        resource = Resource(
            entity_type=row["subject_type"],
            entity_id=str(row["subject_id"]),
            privacy_tier=row["privacy_tier"],
        )
        if (await decide(conn, ctx, Action.CONTENT_READ, resource)).allow:
            kept.append(row)
    return kept


@router.get("/{claim_id}")
async def get_claim(
    claim_id: str,
    request: Request,
    principal: Annotated[Principal | None, Depends(authenticate_optional)],
) -> dict[str, Any]:
    pool = request.app.state.pool
    async with pool.connection() as conn:
        ctx = await resolve_context(conn, principal)
        row = None
        try:
            import uuid as uuid_mod

            uuid_mod.UUID(claim_id)
        except ValueError:
            pass
        else:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    """
                    SELECT id, subject_type, subject_id, predicate, statement,
                           privacy_tier, confidence_tier, created_at, updated_at
                    FROM claim WHERE id = %s AND deleted_at IS NULL
                    """,
                    (claim_id,),
                )
                row = await cur.fetchone()

        resource = (
            Resource(
                entity_type=row["subject_type"],
                entity_id=str(row["subject_id"]),
                privacy_tier=row["privacy_tier"],
            )
            if row
            else None
        )
        await read_or_not_found(
            conn, ctx, resource, request_id=getattr(request.state, "request_id", None)
        )
        assert row is not None
        provenance = await provenance_for_claims(conn, [str(row["id"])])
        return serialize(row, provenance.get(str(row["id"])))
