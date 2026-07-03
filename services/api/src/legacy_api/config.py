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

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    @property
    def auth_configured(self) -> bool:
        return bool(self.oidc_issuer and self.oidc_audience)


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
