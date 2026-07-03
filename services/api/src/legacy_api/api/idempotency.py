"""Idempotency-Key replay (API_SPECIFICATION 4.1 and 4.2).

Semantics: a mutating request bearing an Idempotency-Key executes once. A
retry with the same key and an identical request fingerprint returns the
original result (marked with the Idempotency-Replayed header); the same key
with a different fingerprint is refused with the idempotency_replay error
code, because silently answering with a different request's result would be
worse than failing.

The store is in-process with a TTL, matching the single-instance posture of
DEP-31 (the same explicitly-noted trade as the auth rate limiter). Client
retry storms happen within seconds; a durable cross-restart ledger would
need an operational table that DATABASE_SCHEMA does not define, so promoting
this store is raised as a spec question when content mutations ship.
"""

import hashlib
import time
from dataclasses import dataclass, field
from typing import Any

from legacy_api.api.errors import ApiError, ErrorCode


def fingerprint(method: str, path: str, body: bytes) -> str:
    return hashlib.sha256(b"|".join([method.encode(), path.encode(), body])).hexdigest()


@dataclass
class _Entry:
    fingerprint: str
    status: int
    body: Any
    stored_at: float


@dataclass
class IdempotencyStore:
    ttl_s: int = 86400
    _entries: dict[str, _Entry] = field(default_factory=dict)

    def _prune(self) -> None:
        now = time.monotonic()
        expired = [k for k, e in self._entries.items() if now - e.stored_at > self.ttl_s]
        for key in expired:
            del self._entries[key]

    def check(self, key: str, request_fingerprint: str) -> _Entry | None:
        """Return the stored entry for a true replay; raise on key misuse."""
        self._prune()
        entry = self._entries.get(key)
        if entry is None:
            return None
        if entry.fingerprint != request_fingerprint:
            raise ApiError(
                409,
                ErrorCode.IDEMPOTENCY_REPLAY,
                "Idempotency-Key was already used for a different request.",
            )
        return entry

    def store(self, key: str, request_fingerprint: str, status: int, body: Any) -> None:
        self._entries[key] = _Entry(
            fingerprint=request_fingerprint,
            status=status,
            body=body,
            stored_at=time.monotonic(),
        )
