"""Application entry point.

Health endpoints live outside the /v1 API surface (api/API_SPECIFICATION.md
governs /v1; these are infrastructure endpoints). Both expose the environment
identity required by DEP-06.
"""

import logging

from fastapi import FastAPI
from pydantic import BaseModel

from legacy_api import __version__
from legacy_api.config import Environment, Settings, get_settings

logger = logging.getLogger("legacy_api")


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: Environment


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    app = FastAPI(title="Legacy API", version=__version__, docs_url=None, redoc_url=None)

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
    def readyz() -> HealthResponse:
        """Readiness: the service can take traffic.

        No downstream dependencies exist yet; dependency checks are added with
        the components that introduce them (the API consumes the database from
        MVP-006 onward; the schema itself is managed by Alembic migrations).
        """
        return _health()

    return app


app = create_app()
