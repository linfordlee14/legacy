"""Application entry point.

Health endpoints live outside the /v1 API surface (api/API_SPECIFICATION.md
governs /v1; these are infrastructure endpoints). Both expose the environment
identity required by DEP-06. Authentication per security/AUTHENTICATION.md.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.responses import Response
from pydantic import BaseModel

from legacy_api import __version__
from legacy_api.ai.gemini import GeminiEmbeddingProvider
from legacy_api.ai.router import EmbeddingProvider, ModelRouter
from legacy_api.api.errors import RequestIdMiddleware, install_error_handlers
from legacy_api.api.idempotency import IdempotencyStore
from legacy_api.api.ratelimit import RateLimitMiddleware, TokenBucketLimiter
from legacy_api.auth import (
    FailureRateLimiter,
    LogNotifier,
    OwnerNotifier,
    Principal,
    authenticate,
)
from legacy_api.config import Environment, Settings, get_settings
from legacy_api.db import create_pool
from legacy_api.obs.alerts import AlertRouter
from legacy_api.obs.logging import setup_logging
from legacy_api.obs.metrics import Metrics
from legacy_api.obs.tracing import TracingMiddleware
from legacy_api.routes.claims import router as claims_router
from legacy_api.routes.content import router as content_router
from legacy_api.routes.content_edit import router as content_edit_router
from legacy_api.routes.ingestion import router as ingestion_router
from legacy_api.routes.search import router as search_router
from legacy_api.routes.tokens import router as tokens_router
from legacy_api.storage import LocalObjectStorage
from legacy_api.verifier import TokenVerifier, jwks_key_provider

logger = logging.getLogger("legacy_api")


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: Environment


class SessionResponse(BaseModel):
    user_id: str
    email: str
    display_name: str
    is_owner: bool
    mfa: bool
    new_device: bool


def default_verifier(settings: Settings) -> TokenVerifier | None:
    if not settings.auth_configured:
        return None
    issuer = settings.oidc_issuer or ""
    jwks_url = settings.oidc_jwks_url or f"{issuer.rstrip('/')}/.well-known/jwks.json"
    return TokenVerifier(
        issuer=issuer,
        audience=settings.oidc_audience or "",
        key_provider=jwks_key_provider(jwks_url),
    )


def create_app(
    settings: Settings | None = None,
    verifier: TokenVerifier | None = None,
    notifier: OwnerNotifier | None = None,
    embedding_provider: EmbeddingProvider | None = None,
) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        if settings.database_url:
            app.state.pool = create_pool(settings.database_url)
            await app.state.pool.open()
        try:
            yield
        finally:
            if app.state.pool is not None:
                await app.state.pool.close()

    app = FastAPI(
        title="Legacy API", version=__version__, docs_url=None, redoc_url=None, lifespan=lifespan
    )
    app.state.settings = settings
    app.state.pool = None
    app.state.verifier = verifier or default_verifier(settings)
    app.state.notifier = notifier or LogNotifier()
    app.state.rate_limiter = FailureRateLimiter()
    app.state.request_bucket = TokenBucketLimiter(per_minute=settings.rate_limit_per_minute)
    app.state.idempotency = IdempotencyStore(ttl_s=settings.idempotency_ttl_s)
    app.state.metrics = Metrics()
    # Every provider call goes through the Model Router (ADR-06); the
    # embedding task class is pinned by ADR-16. No key means embedding
    # writes queue (RAG-08) rather than degrade.
    if embedding_provider is None and settings.gemini_api_key:
        embedding_provider = GeminiEmbeddingProvider(settings.gemini_api_key)
    app.state.model_router = ModelRouter(
        embedding_provider=embedding_provider, metrics=app.state.metrics
    )
    app.state.storage = LocalObjectStorage(Path(settings.storage_dir))
    app.state.alerts = AlertRouter(
        notifier=app.state.notifier,
        quiet_start_hour=settings.quiet_hours_start_utc,
        quiet_end_hour=settings.quiet_hours_end_utc,
    )

    # Middleware order (outermost first): RequestId so every response carries
    # the id (API_SPECIFICATION 4.2), then Tracing so even rate-limited
    # requests appear as spans, then the rate limiter.
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(TracingMiddleware)
    app.add_middleware(RequestIdMiddleware)
    install_error_handlers(app)
    app.include_router(claims_router)
    app.include_router(tokens_router)
    app.include_router(ingestion_router)
    app.include_router(search_router)
    # Path-parameterized collections register last so specific routes win.
    app.include_router(content_router)
    app.include_router(content_edit_router)

    @app.get("/metrics", include_in_schema=False)
    def metrics() -> Response:
        """Prometheus exposition; the platform scrapes this internally
        (DEP-12: not reachable through the public entry point)."""
        return Response(
            content=app.state.metrics.render(), media_type="text/plain; version=0.0.4"
        )

    # Structured JSON logging with redaction (OBS-01 to OBS-06); emission is
    # queued off the request path outside local development.
    setup_logging(
        environment=settings.env,
        level=settings.log_level,
        async_mode=settings.env in ("staging", "production"),
    )
    logger.info(
        "legacy-api starting", extra={"environment": settings.env, "version": __version__}
    )

    def _health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            service="legacy-api",
            version=__version__,
            environment=settings.env,
        )

    @app.get("/healthz", response_model=HealthResponse)
    def healthz() -> HealthResponse:
        """Liveness: the process is up."""
        return _health()

    @app.get("/readyz", response_model=HealthResponse)
    async def readyz() -> HealthResponse:
        """Readiness: the service can take traffic, including its database
        dependency when one is configured."""
        if app.state.pool is not None:
            async with app.state.pool.connection() as conn:
                await conn.execute("SELECT 1")
        return _health()

    @app.get("/v1/auth/session", response_model=SessionResponse)
    async def session(
        principal: Annotated[Principal, Depends(authenticate)],
    ) -> SessionResponse:
        """The authenticated principal's own session identity."""
        return SessionResponse(
            user_id=principal.user_id,
            email=principal.email,
            display_name=principal.display_name,
            is_owner=principal.is_owner,
            mfa=principal.mfa_satisfied,
            new_device=principal.new_device,
        )

    return app


app = create_app()
