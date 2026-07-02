"""Health endpoint tests: DEP-01 environment names, DEP-06 identity exposure."""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from legacy_api import __version__
from legacy_api.config import Settings
from legacy_api.main import create_app


def make_client(env: str) -> TestClient:
    return TestClient(create_app(Settings(env=env)))  # type: ignore[arg-type]


@pytest.mark.parametrize("endpoint", ["/healthz", "/readyz"])
def test_health_reports_status_and_environment(endpoint: str) -> None:
    response = make_client("local").get(endpoint)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "legacy-api"
    assert body["version"] == __version__
    assert body["environment"] == "local"


@pytest.mark.parametrize("env", ["local", "staging", "production"])
def test_all_three_environments_are_valid(env: str) -> None:
    body = make_client(env).get("/healthz").json()
    assert body["environment"] == env


def test_invalid_environment_fails_loudly() -> None:
    with pytest.raises(ValidationError):
        Settings(env="dev")  # type: ignore[arg-type]


def test_missing_environment_fails_loudly(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LEGACY_ENV", raising=False)
    with pytest.raises(ValidationError):
        Settings()  # type: ignore[call-arg]
