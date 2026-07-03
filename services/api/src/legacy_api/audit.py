"""Audit log writes (ADR-11; AUTHENTICATION 4.6; AUTHORIZATION 4.7).

Every authentication event and every authorization denial or sensitive allow
becomes an append-only AuditLogEntry. Payloads are content-free: hashes,
reasons, and flags only, never tokens, content, user agents, or addresses in
the clear (NFR-033).
"""

import json
from typing import Any

from psycopg import AsyncConnection

SYSTEM_USER_ID = "00000000-0000-7000-8000-000000000001"


async def write_audit_event(
    conn: AsyncConnection[Any],
    *,
    actor_type: str,
    actor_id: str | None,
    action: str,
    subject_type: str | None = None,
    subject_id: str | None = None,
    payload: dict[str, Any] | None = None,
    token_ref: str | None = None,
    request_id: str | None = None,
) -> None:
    """Record an audit event; unknown actors attribute to the system principal."""
    await conn.execute(
        """
        INSERT INTO audit_log_entry
            (actor_type, actor_id, action, subject_type, subject_id,
             payload_summary, token_ref, request_id, created_by, origin_type)
        VALUES (%(actor_type)s, %(actor)s, %(action)s, %(subject_type)s, %(subject)s,
                %(payload)s, %(token_ref)s, %(request_id)s, %(created_by)s, 'system')
        """,
        {
            "actor_type": actor_type,
            "actor": actor_id or SYSTEM_USER_ID,
            "action": action,
            "subject_type": subject_type,
            "subject": subject_id,
            "payload": json.dumps(payload or {}),
            "token_ref": token_ref,
            "request_id": request_id,
            "created_by": actor_id or SYSTEM_USER_ID,
        },
    )


async def write_auth_event(
    conn: AsyncConnection[Any],
    *,
    action: str,
    actor_id: str | None,
    payload: dict[str, Any],
    token_ref: str | None = None,
    request_id: str | None = None,
) -> None:
    """Authentication events: actor and subject are the same principal."""
    await write_audit_event(
        conn,
        actor_type="user",
        actor_id=actor_id,
        action=action,
        subject_type="User",
        subject_id=actor_id,
        payload=payload,
        token_ref=token_ref,
        request_id=request_id,
    )
