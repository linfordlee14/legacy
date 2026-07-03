"""Read endpoints for captured content collections (API_SPECIFICATION 4.4:
content entities; the read subset serving the workspace shell). Writes go
through ingestion; editing arrives with revision support (MVP-015).

Every response is tier-filtered through the policy service; single reads use
the uniform not_found path and carry the 4.3 provenance block.
"""

import uuid as uuid_mod
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from psycopg import AsyncConnection
from psycopg.rows import dict_row

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
    AuthzContext,
    Resource,
    decide,
    read_or_not_found,
    resolve_context,
    tiers_within,
)
from legacy_api.provenance import provenance_for_entity

router = APIRouter(prefix="/v1", tags=["content"])

COLLECTIONS: dict[str, dict[str, Any]] = {
    "notes": {
        "table": "note",
        "entity_type": "Note",
        "columns": "id, title, body, note_context, privacy_tier, created_at, updated_at",
    },
    "artifacts": {
        "table": "artifact",
        "entity_type": "Artifact",
        "columns": (
            "id, title, artifact_type, mime_type, byte_size, extraction_status, "
            "canonical_markdown, privacy_tier, created_at, updated_at"
        ),
    },
}


def serialize(row: dict[str, Any]) -> dict[str, Any]:
    out = {}
    for key, value in row.items():
        if hasattr(value, "isoformat"):
            out[key] = value.isoformat()
        elif key == "id":
            out[key] = str(value)
        else:
            out[key] = value
    return out


async def _scope_filter(
    conn: AsyncConnection[Any], ctx: AuthzContext, entity_type: str, rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    if ctx.kind != "trusted":
        return rows
    kept = []
    for row in rows:
        resource = Resource(
            entity_type=entity_type, entity_id=str(row["id"]), privacy_tier=row["privacy_tier"]
        )
        if (await decide(conn, ctx, Action.CONTENT_READ, resource)).allow:
            kept.append(row)
    return kept


async def list_content(
    collection: str,
    request: Request,
    principal: Principal | None,
    limit: int,
    cursor: str | None,
) -> Page:
    spec = COLLECTIONS[collection]
    async with request.app.state.pool.connection() as conn:
        ctx = await resolve_context(conn, principal)
        clauses = ["deleted_at IS NULL", "privacy_tier = ANY(%(tiers)s)"]
        params: dict[str, Any] = {"tiers": tiers_within(ctx.ceiling), "limit": limit + 1}
        if cursor is not None:
            clauses.append("id < %(cursor)s")
            params["cursor"] = decode_cursor(cursor)
        with span(f"db.{spec['table']}_list"):
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    f"""
                    SELECT {spec["columns"]}
                    FROM {spec["table"]}
                    WHERE {" AND ".join(clauses)}
                    ORDER BY id DESC
                    LIMIT %(limit)s
                    """,
                    params,
                )
                rows = await cur.fetchall()
        rows = await _scope_filter(conn, ctx, spec["entity_type"], rows)
        return page_of([serialize(row) for row in rows], limit)


async def get_content(
    collection: str,
    item_id: str,
    request: Request,
    principal: Principal | None,
) -> dict[str, Any]:
    spec = COLLECTIONS[collection]
    async with request.app.state.pool.connection() as conn:
        ctx = await resolve_context(conn, principal)
        row = None
        try:
            uuid_mod.UUID(item_id)
        except ValueError:
            pass
        else:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    f"SELECT {spec['columns']} FROM {spec['table']} "
                    "WHERE id = %s AND deleted_at IS NULL",
                    (item_id,),
                )
                row = await cur.fetchone()
        resource = (
            Resource(
                entity_type=spec["entity_type"],
                entity_id=str(row["id"]),
                privacy_tier=row["privacy_tier"],
            )
            if row
            else None
        )
        await read_or_not_found(
            conn, ctx, resource, request_id=getattr(request.state, "request_id", None)
        )
        assert row is not None
        provenance = await provenance_for_entity(
            conn, spec["entity_type"], str(row["id"]), tiers_within(ctx.ceiling)
        )
        return {**serialize(row), "provenance": provenance.model_dump()}


# Explicit per-collection routes (API_SPECIFICATION 4.4). Registering concrete
# paths rather than a single-segment catch-all keeps content routes from
# shadowing sibling /v1 routes like /v1/auth/session.
def _register(collection: str) -> None:
    async def list_route(
        request: Request,
        principal: Annotated[Principal | None, Depends(authenticate_optional)],
        limit: LimitParam = DEFAULT_LIMIT,
        cursor: CursorParam = None,
    ) -> Page:
        return await list_content(collection, request, principal, limit, cursor)

    async def get_route(
        item_id: str,
        request: Request,
        principal: Annotated[Principal | None, Depends(authenticate_optional)],
    ) -> dict[str, Any]:
        return await get_content(collection, item_id, request, principal)

    router.add_api_route(f"/{collection}", list_route, methods=["GET"], tags=["content"])
    router.add_api_route(
        f"/{collection}/{{item_id}}", get_route, methods=["GET"], tags=["content"]
    )


for _collection in COLLECTIONS:
    _register(_collection)
