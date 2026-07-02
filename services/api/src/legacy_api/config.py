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

    @property
    def is_production(self) -> bool:
        return self.env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
