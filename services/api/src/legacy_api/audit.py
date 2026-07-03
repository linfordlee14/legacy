"""Audit log writes (AUTHENTICATION 4.6, ADR-11).

Every authentication event becomes an append-only AuditLogEntry. Payloads are
content-free: hashes and flags only, never tokens, user agents, or addresses
in the clear (NFR-033).
"""

import json
from typing import Any

from psycopg import AsyncConnection

SYSTEM_USER_ID = "00000000-0000-7000-8000-000000000001"


async def write_auth_event(
    conn: AsyncConnection[Any],
    *,
    action: str,
    actor_id: str | None,
    payload: dict[str, Any],
    token_ref: str | None = None,
    request_id: str | None = None,
) -> None:
    """Record an authentication event.

    actor_id is the app_user id when the principal resolved; denied events
    for unknown principals are attributed to the system principal.
    """
    await conn.execute(
        """
        INSERT INTO audit_log_entry
            (actor_type, actor_id, action, subject_type, subject_id,
             payload_summary, token_ref, request_id, created_by, origin_type)
        VALUES ('user', %(actor)s, %(action)s, 'User', %(subject)s,
                %(payload)s, %(token_ref)s, %(request_id)s, %(created_by)s, 'system')
        """,
        {
            "actor": actor_id or SYSTEM_USER_ID,
            "action": action,
            "subject": actor_id,
            "payload": json.dumps(payload),
            "token_ref": token_ref,
            "request_id": request_id,
            "created_by": actor_id or SYSTEM_USER_ID,
        },
    )
