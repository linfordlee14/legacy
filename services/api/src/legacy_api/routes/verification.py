"""Verification queue endpoints (MVP-020; FS-009; API_SPECIFICATION 4.4).

The owner-only surface for working the queue seeded from MASTER_CONTEXT
section 12: list open flagged and stale self-reported claims with their
evidence, attach evidence Sources, and resolve tier changes. There is no
agent automation and no alternate verification mechanism: resolutions go
through the policy service (TIER_CHANGE), require a fresh authentication
event (step-up), and satisfy the claim_tier_guard trigger on its own
terms; the transaction-local legacy.tier_change_authorized assertion is
made only here, on this authenticated owner path, and the guard still
demands a human verifier plus a supporting ClaimSource before 'verified'.
Every attachment and resolution is audited; the displaced tier state is
preserved as a Revision row; existing provenance links are never removed.
"""

import hashlib
import json
import uuid as uuid_mod
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from psycopg import AsyncConnection, errors
from psycopg.rows import dict_row

from legacy_api.api.errors import ApiError, ErrorCode
from legacy_api.api.idempotency import IdempotencyStore
from legacy_api.audit import write_audit_event
from legacy_api.auth import Principal, _auth_time_fresh, authenticate
from legacy_api.obs.tracing import span
from legacy_api.policy import Action, authorize, raise_uniform_not_found, resolve_context

router = APIRouter(prefix="/v1/verification", tags=["verification"])

TIERS = ("verified", "self_reported", "flagged")
SUPPORT_TYPES = ("supports", "contradicts")
SOURCE_TYPES = ("url", "document", "artifact", "testimony", "system_record", "external_api")

CLAIM_COLUMNS = (
    "id, subject_type, subject_id, predicate, statement, confidence_tier, "
    "tier_rationale, verified_at, verified_by, review_due_at, privacy_tier, "
    "created_at, updated_at"
)


def _owner_only(principal: Principal) -> None:
    if not principal.is_owner:
        raise ApiError(403, ErrorCode.FORBIDDEN, "Owner only.")


def _replay(
    request: Request, body: dict[str, Any] | None
) -> tuple[IdempotencyStore, str | None, str]:
    store: IdempotencyStore = request.app.state.idempotency
    key = request.headers.get("idempotency-key")
    digest = hashlib.sha256(json.dumps(body or {}, sort_keys=True).encode()).hexdigest()
    return store, key, f"{request.method}{request.url.path}:{digest}"


async def _json_body(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        body = None
    if not isinstance(body, dict):
        raise ApiError(422, ErrorCode.VALIDATION_FAILED, "Request body must be a JSON object.")
    return body


async def _load_claim(
    conn: AsyncConnection[Any], claim_id: str
) -> dict[str, Any] | None:
    try:
        uuid_mod.UUID(claim_id)
    except ValueError:
        return None
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            f"SELECT {CLAIM_COLUMNS} FROM claim WHERE id = %s AND deleted_at IS NULL",
            (claim_id,),
        )
        return await cur.fetchone()


async def _evidence_of(
    conn: AsyncConnection[Any], claim_ids: list[str]
) -> dict[str, list[dict[str, Any]]]:
    if not claim_ids:
        return {}
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT cs.claim_id, cs.support_type, cs.note,
                   s.id AS source_id, s.source_type, s.title, s.url, s.publisher,
                   s.reliability_note
            FROM claim_source cs
            JOIN source s ON s.id = cs.source_id AND s.deleted_at IS NULL
            WHERE cs.claim_id = ANY(%s::uuid[]) AND cs.deleted_at IS NULL
            ORDER BY cs.created_at
            """,
            (claim_ids,),
        )
        rows = await cur.fetchall()
    evidence: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        evidence.setdefault(str(row["claim_id"]), []).append(
            {
                "source_id": str(row["source_id"]),
                "source_type": row["source_type"],
                "title": row["title"],
                "url": row["url"],
                "publisher": row["publisher"],
                "reliability_note": row["reliability_note"],
                "support_type": row["support_type"],
                "note": row["note"],
            }
        )
    return evidence


def _serialize_claim(row: dict[str, Any], evidence: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "id": str(row["id"]),
        "subject_type": row["subject_type"],
        "subject_id": str(row["subject_id"]),
        "predicate": row["predicate"],
        "statement": row["statement"],
        "confidence_tier": row["confidence_tier"],
        "tier_rationale": row["tier_rationale"],
        "verified_at": row["verified_at"].isoformat() if row["verified_at"] else None,
        "review_due_at": row["review_due_at"].isoformat() if row["review_due_at"] else None,
        "privacy_tier": row["privacy_tier"],
        "evidence": evidence,
        "supporting_count": sum(1 for e in evidence if e["support_type"] == "supports"),
        "contradicting_count": sum(1 for e in evidence if e["support_type"] == "contradicts"),
    }


@router.get("/queue")
async def queue(
    request: Request,
    principal: Annotated[Principal, Depends(authenticate)],
) -> dict[str, Any]:
    """Open flagged claims plus self-reported claims past review_due_at
    (FS-009: 'open 🔴 and stale 🟡'). Owner-only: rationale and evidence
    can reference private context."""
    _owner_only(principal)
    async with request.app.state.pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                f"""
                SELECT {CLAIM_COLUMNS} FROM claim
                WHERE deleted_at IS NULL AND (
                    confidence_tier = 'flagged'
                    OR (confidence_tier = 'self_reported'
                        AND review_due_at IS NOT NULL
                        AND review_due_at <= CURRENT_DATE)
                )
                ORDER BY confidence_tier, created_at
                """
            )
            rows = await cur.fetchall()
        evidence = await _evidence_of(conn, [str(row["id"]) for row in rows])
    items = [_serialize_claim(row, evidence.get(str(row["id"]), [])) for row in rows]
    return {
        "items": items,
        "open_flagged": sum(1 for i in items if i["confidence_tier"] == "flagged"),
        "stale_self_reported": sum(
            1 for i in items if i["confidence_tier"] == "self_reported"
        ),
    }


@router.post("/claims/{claim_id}/evidence", status_code=201)
async def attach_evidence(
    claim_id: str,
    request: Request,
    principal: Annotated[Principal, Depends(authenticate)],
) -> Any:
    """Owner attaches an evidence Source (supports or contradicts). Links
    are only ever added here; existing provenance is never removed."""
    _owner_only(principal)
    body = await _json_body(request)
    request_id = getattr(request.state, "request_id", None)
    store, idem_key, fingerprint = _replay(request, body)

    support_type = body.get("support_type")
    if support_type not in SUPPORT_TYPES:
        raise ApiError(
            422, ErrorCode.VALIDATION_FAILED,
            "support_type must be supports or contradicts.",
        )
    source = body.get("source")
    source_id = body.get("source_id")
    if not source_id:
        if not isinstance(source, dict) or not source.get("title"):
            raise ApiError(
                422, ErrorCode.VALIDATION_FAILED,
                "Provide source_id or a source object with a title.",
            )
        if source.get("source_type") not in SOURCE_TYPES:
            raise ApiError(
                422, ErrorCode.VALIDATION_FAILED, "Unknown source_type.",
                {"source_types": list(SOURCE_TYPES)},
            )

    async with request.app.state.pool.connection() as conn:
        claim = await _load_claim(conn, claim_id)
        if claim is None:
            raise raise_uniform_not_found()

        if idem_key:
            entry = store.check(idem_key, fingerprint)
            if entry:
                return JSONResponse(
                    entry.body, status_code=entry.status,
                    headers={"Idempotency-Replayed": "true"},
                )

        async with conn.cursor(row_factory=dict_row) as cur:
            if source_id:
                await cur.execute(
                    "SELECT id FROM source WHERE id = %s AND deleted_at IS NULL",
                    (source_id,),
                )
                if await cur.fetchone() is None:
                    raise raise_uniform_not_found()
            else:
                assert isinstance(source, dict)
                await cur.execute(
                    """
                    INSERT INTO source (source_type, title, url, publisher,
                                        reliability_note, accessed_at, created_by)
                    VALUES (%s, %s, %s, %s, %s, now(), %s)
                    RETURNING id
                    """,
                    (
                        source["source_type"],
                        source["title"],
                        source.get("url"),
                        source.get("publisher"),
                        source.get("reliability_note"),
                        principal.user_id,
                    ),
                )
                created = await cur.fetchone()
                assert created is not None
                source_id = str(created["id"])

            await cur.execute(
                """
                INSERT INTO claim_source (claim_id, source_id, support_type, note,
                                          created_by)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (claim_id, source_id) WHERE deleted_at IS NULL DO NOTHING
                RETURNING id
                """,
                (claim_id, source_id, support_type, body.get("note"), principal.user_id),
            )
            linked = await cur.fetchone()
        if linked is None:
            raise ApiError(
                409, ErrorCode.CONFLICT,
                "This source is already linked to the claim.",
                {"source_id": source_id},
            )
        await write_audit_event(
            conn,
            actor_type="user",
            actor_id=principal.user_id,
            action="evidence_attached",
            subject_type="Claim",
            subject_id=claim_id,
            payload={"source_id": source_id, "support_type": support_type},
            request_id=request_id,
        )
        evidence = await _evidence_of(conn, [claim_id])
        refreshed = await _load_claim(conn, claim_id)
        assert refreshed is not None
        result = _serialize_claim(refreshed, evidence.get(claim_id, []))

    if idem_key:
        store.store(idem_key, fingerprint, 201, result)
    return JSONResponse(result, status_code=201)


@router.post("/claims/{claim_id}/resolve")
async def resolve(
    claim_id: str,
    request: Request,
    principal: Annotated[Principal, Depends(authenticate)],
) -> Any:
    """Owner applies or rejects a tier change (FS-009: only the owner
    applies). The upgrade path runs through the policy service and the
    claim_tier_guard trigger; nothing here weakens either."""
    _owner_only(principal)
    if not _auth_time_fresh(principal.auth_time, request.app.state.settings):
        raise ApiError(
            401, ErrorCode.UNAUTHENTICATED,
            "Recent authentication required to resolve a claim.",
        )
    body = await _json_body(request)
    request_id = getattr(request.state, "request_id", None)
    store, idem_key, fingerprint = _replay(request, body)

    decision = body.get("decision")
    if decision not in ("apply", "reject"):
        raise ApiError(
            422, ErrorCode.VALIDATION_FAILED, "decision must be apply or reject."
        )
    target_tier = body.get("target_tier")
    if decision == "apply" and target_tier not in TIERS:
        raise ApiError(
            422, ErrorCode.VALIDATION_FAILED,
            "target_tier must be verified, self_reported, or flagged.",
        )
    note = body.get("note")

    async with request.app.state.pool.connection() as conn:
        ctx = await resolve_context(conn, principal)
        claim = await _load_claim(conn, claim_id)
        if claim is None:
            raise raise_uniform_not_found()

        # The one authorization path for tier movement (AUTHORIZATION 4.2):
        # owner-only in the matrix, hard-denied for agents, sensitive-audited.
        auth_decision = await authorize(
            conn, ctx, Action.TIER_CHANGE, request_id=request_id
        )
        if not auth_decision.allow:
            raise ApiError(403, ErrorCode.FORBIDDEN, "Not permitted.")

        if idem_key:
            entry = store.check(idem_key, fingerprint)
            if entry:
                return JSONResponse(
                    entry.body, status_code=entry.status,
                    headers={"Idempotency-Replayed": "true"},
                )

        outcome = "rejected"
        if decision == "apply" and target_tier != claim["confidence_tier"]:
            outcome = "applied"
            async with conn.cursor(row_factory=dict_row) as cur:
                # Preserve the displaced tier state (Revision reuse; the
                # Claim snapshot shape per DATABASE_SCHEMA 4.6).
                await cur.execute(
                    """
                    INSERT INTO revision (created_by, entity_type, entity_id,
                                          row_version, change_kind, snapshot)
                    SELECT %s, 'Claim', id, row_version, 'tier_change',
                           jsonb_build_object(
                               'confidence_tier', confidence_tier,
                               'tier_rationale', tier_rationale,
                               'verified_at', verified_at,
                               'verified_by', verified_by,
                               'privacy_tier', privacy_tier)
                    FROM claim WHERE id = %s
                    """,
                    (principal.user_id, claim_id),
                )
                rationale = (
                    f"Resolved by owner on {request_id or 'api'}: {note}"
                    if note
                    else "Resolved by owner through the verification queue."
                )
                try:
                    with span("db.claim_tier_resolve"):
                        # The service-layer assertion the guard demands,
                        # transaction-local and only on this owner path.
                        await cur.execute(
                            "SET LOCAL legacy.tier_change_authorized = 'true'"
                        )
                        if target_tier == "verified":
                            await cur.execute(
                                """
                                UPDATE claim
                                SET confidence_tier = 'verified',
                                    verified_at = now(), verified_by = %s,
                                    tier_rationale = %s, review_due_at = NULL
                                WHERE id = %s
                                """,
                                (principal.user_id, rationale, claim_id),
                            )
                        else:
                            await cur.execute(
                                """
                                UPDATE claim
                                SET confidence_tier = %s,
                                    verified_at = NULL, verified_by = NULL,
                                    tier_rationale = %s, review_due_at = NULL
                                WHERE id = %s
                                """,
                                (target_tier, rationale, claim_id),
                            )
                except errors.RaiseException as exc:
                    # The guard refused (for example verified without a
                    # supporting source): surface its rule, change nothing.
                    raise ApiError(
                        409, ErrorCode.CONFLICT,
                        "The claim tier guard refused this resolution.",
                        {"reason": str(exc.diag.message_primary or exc)},
                    ) from None
        elif decision == "reject":
            await conn.execute(
                "UPDATE claim SET tier_rationale = %s WHERE id = %s",
                (
                    f"Reviewed and kept at {claim['confidence_tier']}: {note}"
                    if note
                    else f"Reviewed and kept at {claim['confidence_tier']}.",
                    claim_id,
                ),
            )

        await write_audit_event(
            conn,
            actor_type="user",
            actor_id=principal.user_id,
            action="verify_claim",
            subject_type="Claim",
            subject_id=claim_id,
            payload={
                "decision": decision,
                "outcome": outcome,
                "from": claim["confidence_tier"],
                "to": target_tier if outcome == "applied" else claim["confidence_tier"],
            },
            request_id=request_id,
        )
        refreshed = await _load_claim(conn, claim_id)
        assert refreshed is not None
        evidence = await _evidence_of(conn, [claim_id])
        result = {
            "outcome": outcome,
            "claim": _serialize_claim(refreshed, evidence.get(claim_id, [])),
        }

    if idem_key:
        store.store(idem_key, fingerprint, 200, result)
    return result
