"""Request-rate limiting for /v1 (API_SPECIFICATION 4.1).

A token bucket per source: capacity of one minute's budget, continuous
refill. Exceeding the budget answers 429 with Retry-After. Keyed by client
address until per-PAT quotas arrive with machine principals (step 9); the
brute-force failure limiter in auth.py is a separate, stricter control.
In-process and per-instance by the same DEP-31 reasoning as that limiter.
"""

import time
from dataclasses import dataclass, field

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response


@dataclass
class TokenBucketLimiter:
    per_minute: int = 240
    _state: dict[str, tuple[float, float]] = field(default_factory=dict)  # tokens, at

    def acquire(self, key: str) -> int:
        """Take one token; return 0 when allowed, else seconds to wait."""
        now = time.monotonic()
        tokens, at = self._state.get(key, (float(self.per_minute), now))
        tokens = min(float(self.per_minute), tokens + (now - at) * (self.per_minute / 60.0))
        if tokens >= 1.0:
            self._state[key] = (tokens - 1.0, now)
            return 0
        self._state[key] = (tokens, now)
        deficit = 1.0 - tokens
        return max(1, int(deficit / (self.per_minute / 60.0)))


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Applies the request budget to every /v1 path (health stays open)."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if request.url.path.startswith("/v1"):
            limiter: TokenBucketLimiter = request.app.state.request_bucket
            key = request.client.host if request.client else "unknown"
            wait = limiter.acquire(key)
            if wait > 0:
                request_id = getattr(request.state, "request_id", None) or "unknown"
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": {
                            "code": "rate_limited",
                            "message": "Request budget exceeded.",
                            "request_id": request_id,
                        }
                    },
                    headers={"Retry-After": str(wait), "X-Request-ID": request_id},
                )
        return await call_next(request)
