"""Error envelope and canonical codes (API_SPECIFICATION 4.2).

One envelope everywhere: {"error": {"code", "message", "request_id",
"details"}}. Canonical codes are a closed list; adding one is a spec change.
"""

import logging
import uuid
from enum import StrEnum
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

logger = logging.getLogger("legacy_api.api")


class ErrorCode(StrEnum):
    """The canonical error codes of API_SPECIFICATION 4.2, exactly."""

    UNAUTHENTICATED = "unauthenticated"
    FORBIDDEN = "forbidden"
    TIER_FORBIDDEN = "tier_forbidden"
    NOT_FOUND = "not_found"
    VALIDATION_FAILED = "validation_failed"
    CONFLICT = "conflict"
    RATE_LIMITED = "rate_limited"
    IDEMPOTENCY_REPLAY = "idempotency_replay"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    INTERNAL = "internal"


# Codes used by the auth layer that map onto the canonical list.
_CODE_ALIASES = {
    "mfa_required": ErrorCode.FORBIDDEN,
    "step_up_required": ErrorCode.UNAUTHENTICATED,
    "auth_not_configured": ErrorCode.PROVIDER_UNAVAILABLE,
}


class ApiError(Exception):
    def __init__(
        self,
        status: int,
        code: ErrorCode,
        message: str,
        details: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status = status
        self.code = code
        self.message = message
        self.details = details
        self.headers = headers


def _envelope(
    request: Request,
    status: int,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None) or "unknown"
    body: dict[str, Any] = {
        "error": {"code": code, "message": message, "request_id": request_id}
    }
    if details:
        body["error"]["details"] = details
    response = JSONResponse(status_code=status, content=body, headers=headers)
    response.headers["X-Request-ID"] = request_id
    return response


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Accept X-Request-ID or mint one; echo it on every response."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request.state.request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        response = await call_next(request)
        response.headers.setdefault("X-Request-ID", request.state.request_id)
        return response


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
        return _envelope(
            request, exc.status, exc.code.value, exc.message, exc.details, exc.headers
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        # The auth and policy layers raise HTTPException with a detail dict;
        # older shapes and framework-raised exceptions normalize here too.
        headers = dict(exc.headers) if exc.headers else None
        if isinstance(exc.detail, dict) and "code" in exc.detail:
            raw = str(exc.detail["code"])
            known = {c.value for c in ErrorCode}
            code = raw if raw in known else _CODE_ALIASES.get(raw, ErrorCode.INTERNAL).value
            message = str(exc.detail.get("message", "Request failed."))
            details = {"reason": raw} if raw not in known else None
            return _envelope(request, exc.status_code, code, message, details, headers)
        default = {
            401: ErrorCode.UNAUTHENTICATED,
            403: ErrorCode.FORBIDDEN,
            404: ErrorCode.NOT_FOUND,
            409: ErrorCode.CONFLICT,
            429: ErrorCode.RATE_LIMITED,
        }.get(exc.status_code, ErrorCode.INTERNAL)
        return _envelope(request, exc.status_code, default.value, str(exc.detail), None, headers)

    @app.exception_handler(RequestValidationError)
    async def validation_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details = {
            "errors": [
                {"loc": [str(part) for part in err["loc"]], "type": err["type"]}
                for err in exc.errors()
            ]
        }
        return _envelope(
            request, 422, ErrorCode.VALIDATION_FAILED.value, "Validation failed.", details
        )

    @app.exception_handler(Exception)
    async def internal_handler(request: Request, exc: Exception) -> JSONResponse:
        # Never leak internals; the request id correlates to server logs.
        logger.exception("unhandled error", extra={"request_id": request.state.request_id})
        return _envelope(
            request, 500, ErrorCode.INTERNAL.value, "An internal error occurred."
        )
