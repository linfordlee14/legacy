"""Personal access token lifecycle (API_SPECIFICATION 4.4, owner-only):
create with step-up (secret returned exactly once), metadata listing, and
immediate revocation.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, Response
from psycopg.rows import dict_row
from pydantic import BaseModel, Field

from legacy_api.api.errors import ApiError, ErrorCode
from legacy_api.audit import write_audit_event
from legacy_api.auth import Principal, authenticate, require_step_up
from legacy_api.pats import MAX_TTL_DAYS, VALID_SCOPES, mint_pat
from legacy_api.policy import raise_uniform_not_found

router = APIRouter(prefix="/v1/auth/tokens", tags=["tokens"])


class TokenCreate(BaseModel):
    label: str = Field(min_length=1, max_length=80)
    scopes: list[str] = Field(min_length=1)
    ttl_days: int = Field(default=90, ge=1, le=MAX_TTL_DAYS)


def _owner_only(principal: Principal) -> None:
    if not principal.is_owner:
        raise ApiError(403, ErrorCode.FORBIDDEN, "Owner only.")


@router.post("", status_code=201)
async def create_token(
    body: TokenCreate,
    request: Request,
    principal: Annotated[Principal, Depends(require_step_up)],
) -> dict[str, Any]:
    _owner_only(principal)
    unknown = set(body.scopes) - VALID_SCOPES
    if unknown:
        raise ApiError(
            422,
            ErrorCode.VALIDATION_FAILED,
            "Unknown scopes.",
            {"allowed": sorted(VALID_SCOPES)},
        )
    async with request.app.state.pool.connection() as conn:
        return await mint_pat(
            conn,
            owner_id=principal.user_id,
            label=body.label,
            scopes=body.scopes,
            ttl_days=body.ttl_days,
            request_id=getattr(request.state, "request_id", None),
        )


@router.get("")
async def list_tokens(
    request: Request,
    principal: Annotated[Principal, Depends(authenticate)],
) -> dict[str, Any]:
    _owner_only(principal)
    async with request.app.state.pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """
                SELECT id, label, scopes, expires_at, last_used_at, revoked_at, created_at
                FROM personal_access_token
                WHERE deleted_at IS NULL
                ORDER BY created_at DESC
                """
            )
            rows = await cur.fetchall()
    return {
        "data": [
            {
                "id": str(row["id"]),
                "label": row["label"],
                "scopes": row["scopes"],
                "expires_at": row["expires_at"].isoformat(),
                "last_used_at": row["last_used_at"].isoformat()
                if row["last_used_at"]
                else None,
                "revoked_at": row["revoked_at"].isoformat() if row["revoked_at"] else None,
                "created_at": row["created_at"].isoformat(),
            }
            for row in rows
        ],
        "next_cursor": None,
    }


@router.delete("/{token_id}", status_code=204)
async def revoke_token(
    token_id: str,
    request: Request,
    principal: Annotated[Principal, Depends(authenticate)],
) -> Response:
    _owner_only(principal)
    import uuid as uuid_mod

    try:
        uuid_mod.UUID(token_id)
    except ValueError:
        raise raise_uniform_not_found() from None
    async with request.app.state.pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                UPDATE personal_access_token
                SET revoked_at = coalesce(revoked_at, now())
                WHERE id = %s AND deleted_at IS NULL
                RETURNING id
                """,
                (token_id,),
            )
            row = await cur.fetchone()
        if row is None:
            raise raise_uniform_not_found()
        await write_audit_event(
            conn,
            actor_type="user",
            actor_id=principal.user_id,
            action="pat_revoked",
            subject_type="PersonalAccessToken",
            subject_id=token_id,
            payload={},
            request_id=getattr(request.state, "request_id", None),
        )
    return Response(status_code=204)
