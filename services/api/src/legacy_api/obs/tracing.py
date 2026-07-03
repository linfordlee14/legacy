"""Log-emitted tracing (OBS-10 to OBS-14).

Spans are emitted as structured log events sharing a trace id, so a request
is reconstructable end to end from the log stream alone. At single-owner
volumes every span is retained (OBS-14). Span attributes ride the same
redaction path as all logs (OBS-12). Export to a dedicated trace backend
binds when the telemetry vendor is provisioned (DEPLOYMENT 4.2 TODO).
"""

import logging
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("legacy_api.trace")

_trace_id: ContextVar[str | None] = ContextVar("legacy_trace_id", default=None)
_span_stack: ContextVar[tuple[str, ...]] = ContextVar("legacy_span_stack", default=())


def current_trace_id() -> str | None:
    return _trace_id.get()


def current_span_name() -> str | None:
    stack = _span_stack.get()
    return stack[-1] if stack else None


@contextmanager
def span(name: str, **attributes: Any) -> Iterator[None]:
    """Record one span; attributes must follow the ID-only rules (OBS-12)."""
    parent = current_span_name()
    token = _span_stack.set(_span_stack.get() + (name,))
    started = time.perf_counter()
    outcome = "ok"
    try:
        yield
    except BaseException:
        outcome = "error"
        raise
    finally:
        _span_stack.reset(token)
        logger.info(
            "span",
            extra={
                "event": "span",
                "span": name,
                "parent_span": parent,
                "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                "outcome": outcome,
                **attributes,
            },
        )


class TracingMiddleware(BaseHTTPMiddleware):
    """Root span per request; the trace id is the request id (OBS-10)."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        trace_id = getattr(request.state, "request_id", None) or uuid.uuid4().hex
        token = _trace_id.set(trace_id)
        try:
            route = request.url.path
            status_code = 500
            started = time.perf_counter()
            with span("api.request", method=request.method, route=route):
                response = await call_next(request)
                status_code = response.status_code
            metrics = getattr(request.app.state, "metrics", None)
            if metrics is not None and route.startswith("/v1"):
                metrics.observe_request(
                    method=request.method,
                    route_group=route_group(route),
                    status_code=status_code,
                    duration_s=time.perf_counter() - started,
                )
            response.headers.setdefault("X-Trace-ID", trace_id)
            return response
        finally:
            _trace_id.reset(token)


def route_group(path: str) -> str:
    """Bounded-cardinality route grouping for metrics (OBS-07): the first two
    path segments, so /v1/claims/{id} and /v1/claims group together."""
    parts = [p for p in path.split("/") if p]
    return "/" + "/".join(parts[:2]) if parts else "/"
