"""Content editing endpoints (API_SPECIFICATION 4.4; MVP-015): PATCH with
revision capture, soft delete with undo, and revision history.

Every edit preserves the displaced version as a Revision row in the same
transaction (DATABASE_SCHEMA 4.6). Deletes are soft and reversible via
restore while the row is retained (4.8; NFR-022); permanent erasure exists
only in the redaction workflow, which is post-MVP. Privacy tier changes
require the explicit tier_change sub-action with step-up confirmation and
stay within P0 to P2 (P3 transitions are SEAL_CHANGE territory, arriving
with the journal workflow). Mutations honor Idempotency-Key, flow through
the policy service, and write audit entries.
"""

import hashlib
import json
import uuid as uuid_mod
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse
from psycopg import AsyncConnection
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from legacy_api.api.errors import ApiError, ErrorCode
from legacy_api.api.idempotency import IdempotencyStore
from legacy_api.api.pagination import (
    DEFAULT_LIMIT,
    CursorParam,
    LimitParam,
    Page,
    decode_cursor,
    page_of,
)
from legacy_api.audit import write_audit_event
from legacy_api.auth import Principal, _auth_time_fresh, authenticate
from legacy_api.obs.tracing import span
from legacy_api.policy import (
    Action,
    AuthzContext,
    Resource,
    authorize,
    raise_uniform_not_found,
    read_or_not_found,
    resolve_context,
    tiers_within,
)
from legacy_api.provenance import provenance_for_entity
from legacy_api.rag.indexer import index_entity_or_queue
from legacy_api.routes.content import COLLECTIONS, serialize

router = APIRouter(prefix="/v1", tags=["content"])

# P3 transitions are seal/unseal ceremonies (AUTHORIZATION 4.2 SEAL_CHANGE),
# not plain tier changes; they arrive with the journal workflow.
TIER_CHANGE_TARGETS = ("P0", "P1", "P2")


async def _json_body(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        body = None
    if not isinstance(body, dict):
        raise ApiError(
            422, ErrorCode.VALIDATION_FAILED, "Request body must be a JSON object."
        )
    return body


def _replay_or_none(
    request: Request, body: dict[str, Any] | None
) -> tuple[IdempotencyStore, str | None, str]:
    """Idempotency-Key support on mutating routes (API_SPECIFICATION 4.1)."""
    store: IdempotencyStore = request.app.state.idempotency
    key = request.headers.get("idempotency-key")
    digest = hashlib.sha256(
        json.dumps(body or {}, sort_keys=True).encode()
    ).hexdigest()
    fingerprint = f"{request.method}{request.url.path}:{digest}"
    return store, key, fingerprint


async def _load_row(
    conn: AsyncConnection[Any],
    spec: dict[str, Any],
    item_id: str,
    *,
    include_deleted: bool = False,
) -> dict[str, Any] | None:
    try:
        uuid_mod.UUID(item_id)
    except ValueError:
        return None
    clause = "" if include_deleted else " AND deleted_at IS NULL"
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            f"SELECT {spec['columns']}, row_version, deleted_at "
            f"FROM {spec['table']} WHERE id = %s{clause}",
            (item_id,),
        )
        return await cur.fetchone()


def _resource(spec: dict[str, Any], row: dict[str, Any] | None) -> Resource | None:
    if row is None:
        return None
    return Resource(
        entity_type=spec["entity_type"],
        entity_id=str(row["id"]),
        privacy_tier=row["privacy_tier"],
    )


async def _forbid_unless(
    conn: AsyncConnection[Any],
    ctx: AuthzContext,
    action: Action,
    resource: Resource,
    request_id: str | None,
) -> None:
    decision = await authorize(conn, ctx, action, resource, request_id=request_id)
    if not decision.allow:
        raise ApiError(403, ErrorCode.FORBIDDEN, "Not permitted.")


async def _write_revision(
    conn: AsyncConnection[Any],
    spec: dict[str, Any],
    row: dict[str, Any],
    change_kind: str,
    editor: str,
) -> None:
    """Preserve the displaced version (DATABASE_SCHEMA 4.6: the snapshot is
    the editable-field set plus privacy_tier, exactly as it was)."""
    snapshot = {field: row[field] for field in spec["editable"]}
    snapshot["privacy_tier"] = row["privacy_tier"]
    await conn.execute(
        """
        INSERT INTO revision
            (created_by, entity_type, entity_id, row_version, change_kind, snapshot)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (
            editor,
            spec["entity_type"],
            str(row["id"]),
            row["row_version"],
            change_kind,
            Jsonb(snapshot),
        ),
    )


async def _serialized_with_provenance(
    conn: AsyncConnection[Any],
    spec: dict[str, Any],
    item_id: str,
    ctx: AuthzContext,
) -> dict[str, Any]:
    row = await _load_row(conn, spec, item_id, include_deleted=True)
    assert row is not None
    row.pop("row_version", None)
    row.pop("deleted_at", None)
    provenance = await provenance_for_entity(
        conn, spec["entity_type"], item_id, tiers_within(ctx.ceiling)
    )
    return {**serialize(row), "provenance": provenance.model_dump()}


async def patch_content(
    collection: str,
    item_id: str,
    request: Request,
    principal: Principal,
) -> Any:
    spec = COLLECTIONS[collection]
    body = await _json_body(request)
    request_id = getattr(request.state, "request_id", None)
    store, idem_key, fingerprint = _replay_or_none(request, body)

    is_tier_change = body.get("action") == "tier_change"
    if is_tier_change:
        # Confirmation semantics (API_SPECIFICATION 4.4): an explicit
        # sub-action plus a fresh authentication event (AUTHENTICATION 4.3).
        if not _auth_time_fresh(principal.auth_time, request.app.state.settings):
            raise ApiError(
                401, ErrorCode.UNAUTHENTICATED,
                "Recent authentication required for tier changes.",
            )
        extras = set(body) - {"action", "privacy_tier"}
        if extras:
            raise ApiError(
                422, ErrorCode.VALIDATION_FAILED,
                "tier_change accepts only privacy_tier.",
                {"unexpected_fields": sorted(extras)},
            )
        if body.get("privacy_tier") not in TIER_CHANGE_TARGETS:
            raise ApiError(
                422, ErrorCode.VALIDATION_FAILED,
                "privacy_tier must be P0, P1, or P2 (P3 sealing has its own workflow).",
            )
        fields: dict[str, Any] = {"privacy_tier": body["privacy_tier"]}
    else:
        if "privacy_tier" in body or "action" in body:
            raise ApiError(
                422, ErrorCode.VALIDATION_FAILED,
                "Tier changes require the explicit tier_change sub-action.",
            )
        unknown = set(body) - set(spec["editable"])
        if unknown:
            raise ApiError(
                422, ErrorCode.VALIDATION_FAILED,
                "Unknown fields for this collection.",
                {"unexpected_fields": sorted(unknown), "editable": list(spec["editable"])},
            )
        if not body:
            raise ApiError(
                422, ErrorCode.VALIDATION_FAILED, "Nothing to update.",
                {"editable": list(spec["editable"])},
            )
        fields = dict(body)

    async with request.app.state.pool.connection() as conn:
        ctx = await resolve_context(conn, principal)
        row = await _load_row(conn, spec, item_id)
        await read_or_not_found(conn, ctx, _resource(spec, row), request_id=request_id)
        assert row is not None
        resource = _resource(spec, row)
        assert resource is not None
        action = Action.TIER_CHANGE if is_tier_change else Action.CONTENT_UPDATE
        await _forbid_unless(conn, ctx, action, resource, request_id)

        if idem_key:
            entry = store.check(idem_key, fingerprint)
            if entry:
                return JSONResponse(
                    entry.body, status_code=entry.status,
                    headers={"Idempotency-Replayed": "true"},
                )

        with span(f"db.{spec['table']}_update"):
            await _write_revision(
                conn, spec, row,
                "tier_change" if is_tier_change else "update",
                principal.user_id,
            )
            assignments = ", ".join(f"{field} = %({field})s" for field in fields)
            await conn.execute(
                f"UPDATE {spec['table']} SET {assignments} WHERE id = %(id)s",
                {**fields, "id": item_id},
            )
        if is_tier_change:
            # RAG-32: the denormalized chunk tier recomputes synchronously
            # in the same transaction as the parent tier change.
            await conn.execute(
                "UPDATE embedding_chunk SET privacy_tier = %s "
                "WHERE entity_type = %s AND entity_id = %s",
                (fields["privacy_tier"], spec["entity_type"], item_id),
            )
        else:
            # Text changed: supersede and re-embed (RAG-03); queued, never
            # silent, when the embedding provider is unavailable (RAG-08).
            await index_entity_or_queue(
                conn,
                request.app.state.model_router,
                spec["entity_type"],
                item_id,
                metrics=request.app.state.metrics,
            )
        await write_audit_event(
            conn,
            actor_type="user",
            actor_id=principal.user_id,
            action="tier_change" if is_tier_change else "update",
            subject_type=spec["entity_type"],
            subject_id=item_id,
            payload=(
                {"from": row["privacy_tier"], "to": fields["privacy_tier"]}
                if is_tier_change
                else {"fields": sorted(fields), "row_version_before": row["row_version"]}
            ),
            request_id=request_id,
        )
        result = await _serialized_with_provenance(conn, spec, item_id, ctx)

    if idem_key:
        store.store(idem_key, fingerprint, 200, result)
    return result


async def delete_content(
    collection: str,
    item_id: str,
    request: Request,
    principal: Principal,
) -> Response:
    spec = COLLECTIONS[collection]
    request_id = getattr(request.state, "request_id", None)
    store, idem_key, fingerprint = _replay_or_none(request, None)

    async with request.app.state.pool.connection() as conn:
        ctx = await resolve_context(conn, principal)
        row = await _load_row(conn, spec, item_id)
        await read_or_not_found(conn, ctx, _resource(spec, row), request_id=request_id)
        assert row is not None
        resource = _resource(spec, row)
        assert resource is not None
        await _forbid_unless(conn, ctx, Action.SOFT_DELETE, resource, request_id)

        if idem_key and store.check(idem_key, fingerprint):
            return Response(status_code=204, headers={"Idempotency-Replayed": "true"})

        # Soft only (NFR-022): the row and its content survive for undo;
        # default reads exclude it immediately (DATABASE_SCHEMA 4.8).
        await conn.execute(
            f"UPDATE {spec['table']} SET deleted_at = now() WHERE id = %s",
            (item_id,),
        )
        await write_audit_event(
            conn,
            actor_type="user",
            actor_id=principal.user_id,
            action="soft_delete",
            subject_type=spec["entity_type"],
            subject_id=item_id,
            payload={"undo": "restore"},
            request_id=request_id,
        )

    if idem_key:
        store.store(idem_key, fingerprint, 204, None)
    return Response(status_code=204)


async def restore_content(
    collection: str,
    item_id: str,
    request: Request,
    principal: Principal,
) -> Any:
    spec = COLLECTIONS[collection]
    request_id = getattr(request.state, "request_id", None)
    store, idem_key, fingerprint = _replay_or_none(request, None)

    async with request.app.state.pool.connection() as conn:
        ctx = await resolve_context(conn, principal)
        row = await _load_row(conn, spec, item_id, include_deleted=True)
        await read_or_not_found(conn, ctx, _resource(spec, row), request_id=request_id)
        assert row is not None
        resource = _resource(spec, row)
        assert resource is not None
        await _forbid_unless(conn, ctx, Action.SOFT_DELETE, resource, request_id)
        if row["deleted_at"] is None:
            raise ApiError(
                409, ErrorCode.CONFLICT, "This item is not deleted.", {"id": item_id}
            )

        if idem_key:
            entry = store.check(idem_key, fingerprint)
            if entry:
                return JSONResponse(
                    entry.body, status_code=entry.status,
                    headers={"Idempotency-Replayed": "true"},
                )

        await conn.execute(
            f"UPDATE {spec['table']} SET deleted_at = NULL WHERE id = %s",
            (item_id,),
        )
        await write_audit_event(
            conn,
            actor_type="user",
            actor_id=principal.user_id,
            action="restore",
            subject_type=spec["entity_type"],
            subject_id=item_id,
            payload={"undo_of": "soft_delete"},
            request_id=request_id,
        )
        result = await _serialized_with_provenance(conn, spec, item_id, ctx)

    if idem_key:
        store.store(idem_key, fingerprint, 200, result)
    return result


async def list_revisions(
    collection: str,
    item_id: str,
    request: Request,
    principal: Principal,
    limit: int,
    cursor: str | None,
) -> Page:
    """Owner-only (API_SPECIFICATION 4.4): snapshots carry full content."""
    if not principal.is_owner:
        raise ApiError(403, ErrorCode.FORBIDDEN, "Owner only.")
    spec = COLLECTIONS[collection]
    async with request.app.state.pool.connection() as conn:
        # The owner sees history for deleted items too (undo window).
        row = await _load_row(conn, spec, item_id, include_deleted=True)
        if row is None:
            raise raise_uniform_not_found()
        clauses = ["entity_type = %(entity_type)s", "entity_id = %(entity_id)s"]
        params: dict[str, Any] = {
            "entity_type": spec["entity_type"],
            "entity_id": item_id,
            "limit": limit + 1,
        }
        if cursor is not None:
            clauses.append("id < %(cursor)s")
            params["cursor"] = decode_cursor(cursor)
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                f"""
                SELECT id, row_version, change_kind, snapshot, created_at, created_by
                FROM revision
                WHERE {" AND ".join(clauses)}
                ORDER BY id DESC
                LIMIT %(limit)s
                """,
                params,
            )
            rows = await cur.fetchall()
    items = []
    for revision in rows:
        items.append(
            {
                "id": str(revision["id"]),
                "row_version": revision["row_version"],
                "change_kind": revision["change_kind"],
                "snapshot": revision["snapshot"],
                "created_at": revision["created_at"].isoformat(),
                "created_by": str(revision["created_by"]),
            }
        )
    return page_of(items, limit)


# Explicit per-collection registration, matching content.py: concrete paths
# keep these from shadowing sibling /v1 routes.
def _register(collection: str) -> None:
    async def patch_route(
        item_id: str,
        request: Request,
        principal: Annotated[Principal, Depends(authenticate)],
    ) -> Any:
        return await patch_content(collection, item_id, request, principal)

    async def delete_route(
        item_id: str,
        request: Request,
        principal: Annotated[Principal, Depends(authenticate)],
    ) -> Response:
        return await delete_content(collection, item_id, request, principal)

    async def restore_route(
        item_id: str,
        request: Request,
        principal: Annotated[Principal, Depends(authenticate)],
    ) -> Any:
        return await restore_content(collection, item_id, request, principal)

    async def revisions_route(
        item_id: str,
        request: Request,
        principal: Annotated[Principal, Depends(authenticate)],
        limit: LimitParam = DEFAULT_LIMIT,
        cursor: CursorParam = None,
    ) -> Page:
        return await list_revisions(collection, item_id, request, principal, limit, cursor)

    router.add_api_route(
        f"/{collection}/{{item_id}}", patch_route, methods=["PATCH"], tags=["content"]
    )
    router.add_api_route(
        f"/{collection}/{{item_id}}", delete_route, methods=["DELETE"],
        tags=["content"], status_code=204,
    )
    router.add_api_route(
        f"/{collection}/{{item_id}}/restore", restore_route, methods=["POST"],
        tags=["content"],
    )
    router.add_api_route(
        f"/{collection}/{{item_id}}/revisions", revisions_route, methods=["GET"],
        tags=["content"],
    )


for _collection in COLLECTIONS:
    _register(_collection)
