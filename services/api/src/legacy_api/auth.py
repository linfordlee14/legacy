"""Authentication layer (AUTHENTICATION 4.1 to 4.3, 4.6).

Verifies bearer tokens, maps auth_subject to app_user, enforces mandatory MFA
for the owner with no bypass path, detects new devices from audit history,
rate-limits failures progressively, and audits every event.
"""

import hashlib
import logging
import time
from dataclasses import dataclass, field
from typing import Annotated, Any, Protocol

from fastapi import Depends, HTTPException, Request
from psycopg.rows import dict_row

from legacy_api.audit import write_auth_event
from legacy_api.config import Settings
from legacy_api.pats import PAT_PREFIX, hash_token, lookup_pat
from legacy_api.verifier import TokenError, TokenVerifier, VerifiedToken

logger = logging.getLogger("legacy_api.auth")


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:16]


class OwnerNotifier(Protocol):
    def notify(self, subject: str, body: str) -> None: ...


class LogNotifier:
    """Default notifier: structured log line the alerting pipeline picks up
    (OBSERVABILITY owner channels; a direct channel binds at provisioning)."""

    def notify(self, subject: str, body: str) -> None:
        logger.warning("owner-notification: %s | %s", subject, body)


@dataclass
class FailureRateLimiter:
    """Progressive delays against brute force (AUTHENTICATION 4.2).

    Per-key sliding window: after `threshold` failures, the key must wait
    `base_cooldown_s * 2^(extra failures)` seconds, capped. In-memory and
    per-instance, which matches the single-instance posture of DEP-31; a
    shared store is a scaling follow-up, not a v1 need.
    """

    threshold: int = 5
    window_s: int = 300
    base_cooldown_s: int = 30
    max_cooldown_s: int = 3600
    _failures: dict[str, list[float]] = field(default_factory=dict)

    def _prune(self, key: str, now: float) -> list[float]:
        entries = [t for t in self._failures.get(key, []) if now - t < self.window_s]
        self._failures[key] = entries
        return entries

    def retry_after(self, key: str) -> int:
        now = time.monotonic()
        entries = self._prune(key, now)
        excess = len(entries) - self.threshold
        if excess < 0:
            return 0
        cooldown = min(self.base_cooldown_s * (2**excess), self.max_cooldown_s)
        elapsed = now - entries[-1]
        return max(0, int(cooldown - elapsed))

    def record_failure(self, key: str) -> None:
        now = time.monotonic()
        self._prune(key, now)
        self._failures.setdefault(key, []).append(now)

    def reset(self, key: str) -> None:
        self._failures.pop(key, None)


@dataclass(frozen=True)
class Principal:
    user_id: str
    email: str
    display_name: str
    is_owner: bool
    mfa_satisfied: bool
    auth_time: int | None
    session_ref: str
    new_device: bool
    # Set only for PAT-authenticated machine principals (AUTHENTICATION 4.3).
    pat_scopes: tuple[str, ...] | None = None


def _deny(status: int, code: str, message: str, retry_after: int | None = None) -> HTTPException:
    headers = {"Retry-After": str(retry_after)} if retry_after else None
    return HTTPException(
        status_code=status,
        detail={"code": code, "message": message},
        headers=headers,
    )


async def authenticate(request: Request) -> Principal:
    """FastAPI dependency: the only path onto authenticated endpoints."""
    settings: Settings = request.app.state.settings
    verifier: TokenVerifier | None = request.app.state.verifier
    limiter: FailureRateLimiter = request.app.state.rate_limiter
    notifier: OwnerNotifier = request.app.state.notifier
    pool = request.app.state.pool

    if verifier is None or pool is None:
        raise _deny(503, "auth_not_configured", "Authentication is not configured.")

    client_key = _hash(request.client.host if request.client else "unknown")
    wait = limiter.retry_after(client_key)
    if wait > 0:
        raise _deny(429, "rate_limited", "Too many failed attempts.", retry_after=wait)

    header = request.headers.get("authorization", "")
    if not header.startswith("Bearer "):
        raise _deny(401, "unauthenticated", "Bearer token required.")

    raw = header.removeprefix("Bearer ")
    if raw.startswith(PAT_PREFIX):
        return await _authenticate_pat(request, raw, limiter, pool, client_key)

    try:
        token: VerifiedToken = verifier.verify(raw)
    except TokenError:
        limiter.record_failure(client_key)
        raise _deny(401, "unauthenticated", "Token verification failed.") from None

    device_hash = _hash(request.headers.get("user-agent", "unknown"))
    session_ref = _hash(token.session_ref or token.subject)
    request_id = request.headers.get("x-request-id")

    async with pool.connection() as conn:
        # Per-cursor row factory only: the pool does not reset connection
        # state on return, so a connection-level factory would leak into
        # whichever request borrows this connection next.
        cur = conn.cursor(row_factory=dict_row)
        row = await (
            await cur.execute(
                """
                SELECT id, email, display_name, user_kind, account_status, is_owner
                FROM app_user
                WHERE auth_subject = %s AND deleted_at IS NULL
                """,
                (token.subject,),
            )
        ).fetchone()

        async def denied(code: str, detail: dict[str, Any]) -> None:
            limiter.record_failure(client_key)
            await write_auth_event(
                conn,
                action="login_denied",
                actor_id=str(row["id"]) if row else None,
                payload={"reason": code, **detail},
                token_ref=session_ref,
                request_id=request_id,
            )
            # The denial raises out of this connection context; commit now so
            # the audit entry survives the rollback-on-exception (4.6).
            await conn.commit()

        if row is None:
            await denied("unknown_subject", {"subject_hash": _hash(token.subject)})
            raise _deny(401, "unauthenticated", "Unknown principal.")
        if row["account_status"] != "active":
            await denied("account_inactive", {"status": row["account_status"]})
            raise _deny(403, "forbidden", "Account is not active.")
        if row["user_kind"] == "service":
            await denied("service_principal_interactive", {})
            raise _deny(403, "forbidden", "Service principals cannot authenticate interactively.")
        if row["is_owner"] and not token.mfa_satisfied:
            await denied("mfa_required", {})
            raise _deny(
                403, "mfa_required", "Multi-factor authentication is mandatory for this account."
            )

        user_id = str(row["id"])

        seen_session = await (
            await cur.execute(
                """
                SELECT EXISTS (
                    SELECT 1 FROM audit_log_entry
                    WHERE action = 'login' AND actor_id = %s AND token_ref = %s
                )
                """,
                (user_id, session_ref),
            )
        ).fetchone()
        new_device = False
        if not seen_session or not seen_session["exists"]:
            known_device = await (
                await cur.execute(
                    """
                    SELECT EXISTS (
                        SELECT 1 FROM audit_log_entry
                        WHERE action = 'login' AND actor_id = %s
                          AND payload_summary->>'device_hash' = %s
                    )
                    """,
                    (user_id, device_hash),
                )
            ).fetchone()
            new_device = not (known_device and known_device["exists"])

            # New-device sign-in requires a fresh authentication event
            # (AUTHENTICATION 4.2 step-up on new devices).
            if new_device and not _auth_time_fresh(token.auth_time, settings):
                await denied("step_up_required_new_device", {"device_hash": device_hash})
                raise _deny(
                    401, "step_up_required", "Recent authentication required on a new device."
                )

            await write_auth_event(
                conn,
                action="login",
                actor_id=user_id,
                payload={
                    "device_hash": device_hash,
                    "new_device": new_device,
                    "mfa": token.mfa_satisfied,
                },
                token_ref=session_ref,
                request_id=request_id,
            )
            await conn.execute(
                "UPDATE app_user SET last_login_at = now() WHERE id = %s", (user_id,)
            )
            if new_device:
                notifier.notify(
                    "New device sign-in",
                    f"Account {row['email']} signed in from an unrecognized device "
                    f"(device {device_hash}).",
                )

    limiter.reset(client_key)
    return Principal(
        user_id=user_id,
        email=row["email"],
        display_name=row["display_name"],
        is_owner=row["is_owner"],
        mfa_satisfied=token.mfa_satisfied,
        auth_time=token.auth_time,
        session_ref=session_ref,
        new_device=new_device,
    )


def _auth_time_fresh(auth_time: int | None, settings: Settings) -> bool:
    if auth_time is None:
        return False
    return (time.time() - auth_time) <= settings.step_up_max_age_s


async def _authenticate_pat(
    request: Request,
    secret: str,
    limiter: FailureRateLimiter,
    pool: Any,
    client_key: str,
) -> Principal:
    """PAT authentication (AUTHENTICATION 4.3): live revocation and expiry
    checks, last_used_at maintenance, and an audit entry on every use."""
    token_ref = hash_token(secret)[:16]
    request_id = request.headers.get("x-request-id")

    async with pool.connection() as conn:
        row = await lookup_pat(conn, secret)

        async def denied(code: str, status: int = 401) -> HTTPException:
            limiter.record_failure(client_key)
            await write_auth_event(
                conn,
                action="login_denied",
                actor_id=str(row["user_id"]) if row else None,
                payload={"reason": code, "kind": "pat"},
                token_ref=token_ref,
                request_id=request_id,
            )
            await conn.commit()
            return _deny(status, "unauthenticated" if status == 401 else "forbidden", "Denied.")

        if row is None:
            raise await denied("unknown_token")
        if row["revoked_at"] is not None:
            raise await denied("pat_revoked")
        if row["expires_at"].timestamp() <= time.time():
            raise await denied("pat_expired")
        if row["account_status"] != "active":
            raise await denied("account_inactive", status=403)

        await conn.execute(
            "UPDATE personal_access_token SET last_used_at = now() WHERE id = %s",
            (row["token_id"],),
        )
        await write_auth_event(
            conn,
            action="pat_use",
            actor_id=str(row["user_id"]),
            payload={"kind": "pat"},
            token_ref=token_ref,
            request_id=request_id,
        )

    limiter.reset(client_key)
    return Principal(
        user_id=str(row["user_id"]),
        email=row["email"],
        display_name=row["display_name"],
        is_owner=False,
        mfa_satisfied=False,
        auth_time=None,
        session_ref=token_ref,
        new_device=False,
        pat_scopes=tuple(row["scopes"]),
    )


async def authenticate_optional(request: Request) -> Principal | None:
    """Like authenticate, but an absent bearer token resolves to None (the
    public visitor context of AUTHORIZATION 4.1). Present-but-invalid tokens
    are still rejected: anonymous is a choice, a bad credential is an error.
    """
    if not request.headers.get("authorization", ""):
        return None
    return await authenticate(request)


async def require_step_up(
    request: Request, principal: Annotated[Principal, Depends(authenticate)]
) -> Principal:
    """Dependency for sensitive actions (AUTHENTICATION 4.3): tier changes,
    grant changes, unsealing, vault export, succession controls."""
    settings: Settings = request.app.state.settings
    if not _auth_time_fresh(principal.auth_time, settings):
        raise _deny(401, "step_up_required", "Recent authentication required for this action.")
    return principal
