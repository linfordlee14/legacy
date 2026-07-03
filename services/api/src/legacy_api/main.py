"""Application entry point.

Health endpoints live outside the /v1 API surface (api/API_SPECIFICATION.md
governs /v1; these are infrastructure endpoints). Both expose the environment
identity required by DEP-06. Authentication per security/AUTHENTICATION.md.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI
from pydantic import BaseModel

from legacy_api import __version__
from legacy_api.auth import (
    FailureRateLimiter,
    LogNotifier,
    OwnerNotifier,
    Principal,
    authenticate,
)
from legacy_api.config import Environment, Settings, get_settings
from legacy_api.db import create_pool
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

    logging.basicConfig(level=logging.INFO)
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
