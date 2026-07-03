"""Personal access tokens (AUTHENTICATION 4.3; API_SPECIFICATION 4.5).

Tokens are minted for dedicated service principals, stored as SHA-256 hashes
only, scoped from the closed set, expiring within 12 months, revocable with
immediate effect, and audited on every use.
"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from psycopg import AsyncConnection
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from legacy_api.audit import write_audit_event

PAT_PREFIX = "lgy_pat_"
VALID_SCOPES = {"read:public", "read:trusted", "read:private", "write:content", "admin"}
MAX_TTL_DAYS = 365


def hash_token(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()


async def mint_pat(
    conn: AsyncConnection[Any],
    *,
    owner_id: str,
    label: str,
    scopes: list[str],
    ttl_days: int,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Create a service principal and its token; returns the plaintext secret
    exactly once, alongside token metadata."""
    if not set(scopes) <= VALID_SCOPES or not scopes:
        raise ValueError("invalid scopes")
    if not 1 <= ttl_days <= MAX_TTL_DAYS:
        raise ValueError("invalid ttl")

    secret = PAT_PREFIX + secrets.token_urlsafe(32)
    expires_at = datetime.now(tz=UTC) + timedelta(days=ttl_days)

    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            INSERT INTO app_user (email, display_name, user_kind, is_owner, created_by)
            VALUES (%s, %s, 'service', false, %s) RETURNING id
            """,
            (f"pat-{secrets.token_hex(8)}@legacy.invalid", f"PAT: {label}", owner_id),
        )
        user_row = await cur.fetchone()
        assert user_row is not None
        service_user_id = str(user_row["id"])

        await cur.execute(
            """
            INSERT INTO personal_access_token
                (user_id, label, token_hash, scopes, expires_at, created_by)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, label, scopes, expires_at, created_at
            """,
            (service_user_id, label, hash_token(secret), Jsonb(scopes), expires_at, owner_id),
        )
        token_row = await cur.fetchone()
        assert token_row is not None

    await write_audit_event(
        conn,
        actor_type="user",
        actor_id=owner_id,
        action="pat_created",
        subject_type="PersonalAccessToken",
        subject_id=str(token_row["id"]),
        payload={"scopes_count": len(scopes), "ttl_days": ttl_days},
        request_id=request_id,
    )
    return {
        "id": str(token_row["id"]),
        "token": secret,
        "label": token_row["label"],
        "scopes": token_row["scopes"],
        "expires_at": token_row["expires_at"].isoformat(),
        "service_user_id": service_user_id,
    }


async def lookup_pat(conn: AsyncConnection[Any], secret: str) -> dict[str, Any] | None:
    """Live lookup at the decision point: revocation and expiry take effect
    immediately (DATABASE_SCHEMA 4.6 rules)."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT t.id AS token_id, t.scopes, t.expires_at, t.revoked_at,
                   u.id AS user_id, u.email, u.display_name, u.account_status
            FROM personal_access_token t
            JOIN app_user u ON u.id = t.user_id AND u.deleted_at IS NULL
            WHERE t.token_hash = %s AND t.deleted_at IS NULL
            """,
            (hash_token(secret),),
        )
        return await cur.fetchone()
