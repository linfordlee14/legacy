"""Runtime configuration.

DEP-06 (deployment/DEPLOYMENT.md): environment identity is set by exactly one
configuration value, LEGACY_ENV, and must be one of the three environments of
DEP-01. A missing or invalid value fails startup loudly; nothing defaults.
Secrets never appear here (DEP-18): this module carries non-secret settings only.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["local", "staging", "production"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LEGACY_")

    env: Environment
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Database (DEP-18: URL arrives via environment or secret manager only).
    database_url: str | None = None

    # OIDC resource-server settings (AUTHENTICATION 4.1: managed provider,
    # Supabase Auth as the default decision). Issuer and audience are
    # non-secret configuration; there is no client secret in this service.
    oidc_issuer: str | None = None
    oidc_audience: str | None = None
    oidc_jwks_url: str | None = None

    # Step-up window for sensitive actions (AUTHENTICATION 4.3): a sensitive
    # action requires an authentication event within this many seconds.
    step_up_max_age_s: int = 600

    # /v1 conventions (API_SPECIFICATION 4.1).
    rate_limit_per_minute: int = 240
    idempotency_ttl_s: int = 86400

    # Object storage root for the local backend (DEP-09: Supabase Storage
    # binds behind the same port at provisioning).
    storage_dir: str = "./storage"

    # Observability (OBSERVABILITY 4.1, 4.5). Production runs at info
    # (OBS-02); quiet hours are owner-configured UTC hours (OBS-20).
    log_level: str = "info"
    quiet_hours_start_utc: int | None = None
    quiet_hours_end_utc: int | None = None

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    @property
    def auth_configured(self) -> bool:
        return bool(self.oidc_issuer and self.oidc_audience)


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
