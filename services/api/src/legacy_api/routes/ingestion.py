"""Ingestion job endpoints (API_SPECIFICATION 4.4; FS-001; FR-ING-007).

Creation stores originals first (preservation before parsing), then records
the job and processes it off the request path. Jobs are the owner-visible
record of every capture, including review flags and failures.
"""

import json
import uuid as uuid_mod
from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Request, UploadFile
from fastapi.responses import JSONResponse
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
from legacy_api.auth import Principal, authenticate
from legacy_api.ingestion import (
    job_fingerprint,
    process_job,
    serialize_job,
    validate_tier,
)
from legacy_api.policy import Action, authorize, raise_uniform_not_found, resolve_context

router = APIRouter(prefix="/v1/ingestion/jobs", tags=["ingestion"])

MAX_FILE_BYTES = 50 * 1024 * 1024  # size ceiling with a clear error (FS-001)


def _owner_only(principal: Principal) -> None:
    if not principal.is_owner:
        raise ApiError(403, ErrorCode.FORBIDDEN, "Owner only.")


@router.post("", status_code=201)
async def create_job(
    request: Request,
    background: BackgroundTasks,
    principal: Annotated[Principal, Depends(authenticate)],
    files: Annotated[list[UploadFile], File()] = [],  # noqa: B006 - FastAPI form default
    payload: Annotated[str, Form()] = "{}",
) -> Any:
    pool = request.app.state.pool
    storage = request.app.state.storage
    request_id = getattr(request.state, "request_id", None)

    try:
        body = json.loads(payload)
        if not isinstance(body, dict):
            raise ValueError("payload must be an object")
    except ValueError as exc:
        raise ApiError(
            422, ErrorCode.VALIDATION_FAILED, "Invalid payload JSON.", {"reason": str(exc)}
        ) from None

    notes = body.get("notes", [])
    file_tiers = body.get("file_tiers", {})
    if not files and not notes:
        raise ApiError(
            422, ErrorCode.VALIDATION_FAILED, "Nothing to ingest.",
            {"reason": "provide files or notes"},
        )

    items: list[dict[str, Any]] = []
    file_hashes: list[str] = []
    try:
        for note in notes:
            if not isinstance(note, dict) or not note.get("body"):
                raise ValueError("each note requires a body")
            items.append(
                {
                    "index": len(items),
                    "type": "note",
                    "name": note.get("title") or "note",
                    "title": note.get("title"),
                    "body": note["body"],
                    "note_context": note.get("note_context"),
                    "privacy_tier": validate_tier(note.get("privacy_tier")),
                    "status": "pending",
                }
            )
        for upload in files:
            data = await upload.read()
            if len(data) > MAX_FILE_BYTES:
                raise ValueError(f"file exceeds the {MAX_FILE_BYTES} byte ceiling")
            if not data:
                raise ValueError("empty file")
            name = upload.filename or "upload"
            key = storage.put(data)  # preserve the original before anything else
            file_hashes.append(key)
            items.append(
                {
                    "index": len(items),
                    "type": "file",
                    "name": name,
                    "mime": upload.content_type or "application/octet-stream",
                    "storage_ref": key,
                    "privacy_tier": validate_tier(file_tiers.get(name)),
                    "status": "pending",
                }
            )
    except ValueError as exc:
        raise ApiError(
            422, ErrorCode.VALIDATION_FAILED, "Invalid ingestion item.", {"reason": str(exc)}
        ) from None

    async with pool.connection() as conn:
        ctx = await resolve_context(conn, principal)
        decision = await authorize(
            conn, ctx, Action.CONTENT_CREATE, request_id=request_id
        )
        if not decision.allow:
            raise ApiError(403, ErrorCode.FORBIDDEN, "Not permitted.")

        store: IdempotencyStore = request.app.state.idempotency
        idem_key = request.headers.get("idempotency-key")
        fingerprint_bytes = job_fingerprint(body, file_hashes)
        fp = f"POST/v1/ingestion/jobs:{fingerprint_bytes.hex()}"
        if idem_key:
            entry = store.check(idem_key, fp)
            if entry:
                return JSONResponse(
                    entry.body, status_code=entry.status,
                    headers={"Idempotency-Replayed": "true"},
                )

        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """
                INSERT INTO ingestion_job
                    (job_type, source_descriptor, status, progress_percent,
                     created_by, origin_type)
                VALUES (%s, %s, 'queued', 0, %s, 'manual')
                RETURNING id, job_type, status, progress_percent, source_descriptor,
                          items_created, error_detail, created_at
                """,
                (
                    "upload" if files else "bulk_import",
                    Jsonb({"kind": "capture", "items": items}),
                    principal.user_id,
                ),
            )
            job = await cur.fetchone()
        await write_audit_event(
            conn,
            actor_type="user",
            actor_id=principal.user_id,
            action="create",
            subject_type="IngestionJob",
            subject_id=str(job["id"]),
            payload={"item_count": len(items)},
            request_id=request_id,
        )

    result = serialize_job(job)
    if idem_key:
        store.store(idem_key, fp, 201, result)
    background.add_task(
        process_job, pool, storage, str(job["id"]),
        request.app.state.model_router, request.app.state.metrics,
    )
    return JSONResponse(result, status_code=201)


@router.get("")
async def list_jobs(
    request: Request,
    principal: Annotated[Principal, Depends(authenticate)],
    limit: LimitParam = DEFAULT_LIMIT,
    cursor: CursorParam = None,
) -> Page:
    _owner_only(principal)
    clauses = ["deleted_at IS NULL"]
    params: dict[str, Any] = {"limit": limit + 1}
    if cursor is not None:
        clauses.append("id < %(cursor)s")
        params["cursor"] = decode_cursor(cursor)
    async with request.app.state.pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                f"""
                SELECT id, job_type, status, progress_percent, source_descriptor,
                       items_created, error_detail, created_at
                FROM ingestion_job
                WHERE {" AND ".join(clauses)}
                ORDER BY id DESC
                LIMIT %(limit)s
                """,
                params,
            )
            rows = await cur.fetchall()
    return page_of([serialize_job(row) for row in rows], limit)


async def _load_job(request: Request, job_id: str) -> dict[str, Any]:
    try:
        uuid_mod.UUID(job_id)
    except ValueError:
        raise raise_uniform_not_found() from None
    async with request.app.state.pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """
                SELECT id, job_type, status, progress_percent, source_descriptor,
                       items_created, error_detail, created_at
                FROM ingestion_job WHERE id = %s AND deleted_at IS NULL
                """,
                (job_id,),
            )
            row = await cur.fetchone()
    if row is None:
        raise raise_uniform_not_found()
    return dict(row)


@router.get("/{job_id}")
async def get_job(
    job_id: str,
    request: Request,
    principal: Annotated[Principal, Depends(authenticate)],
) -> dict[str, Any]:
    _owner_only(principal)
    return serialize_job(await _load_job(request, job_id))


@router.post("/{job_id}/retry")
async def retry_job(
    job_id: str,
    request: Request,
    principal: Annotated[Principal, Depends(authenticate)],
) -> dict[str, Any]:
    """Reprocess review and failed items (FR-ING-007 retry path)."""
    _owner_only(principal)
    row = await _load_job(request, job_id)
    if row["status"] not in ("review", "failed"):
        raise ApiError(
            409, ErrorCode.CONFLICT, "Only review or failed jobs can be retried.",
            {"status": row["status"]},
        )
    # Failed and review items become pending again for this pass.
    descriptor = row["source_descriptor"]
    for item in descriptor.get("items", []):
        if item.get("status") in ("review", "failed"):
            item["status"] = "pending"
            item.pop("reason", None)
    async with request.app.state.pool.connection() as conn:
        await conn.execute(
            "UPDATE ingestion_job SET source_descriptor = %s WHERE id = %s",
            (Jsonb(descriptor), job_id),
        )
        await write_audit_event(
            conn,
            actor_type="user",
            actor_id=principal.user_id,
            action="update",
            subject_type="IngestionJob",
            subject_id=job_id,
            payload={"event": "retry"},
            request_id=getattr(request.state, "request_id", None),
        )
    await process_job(
        request.app.state.pool, request.app.state.storage, job_id,
        request.app.state.model_router, request.app.state.metrics,
    )
    return serialize_job(await _load_job(request, job_id))
