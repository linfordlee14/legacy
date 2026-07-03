"""Authentication matrix tests (MVP-004, AUTHENTICATION 4.1 to 4.3 and 4.6).

Owner matrix rows, the no-MFA-bypass guarantee, new-device behavior, step-up,
rate limiting, and audit coverage. Requires LEGACY_TEST_DATABASE_URL (a
disposable database); skipped when unset.
"""

import time
import uuid
from collections.abc import Iterator
from pathlib import Path
from typing import Annotated, Any

import pytest

DB_URL = __import__("os").environ.get("LEGACY_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not DB_URL, reason="LEGACY_TEST_DATABASE_URL not set (disposable database required)"
)

if DB_URL:
    import jwt as pyjwt
    import psycopg
    from alembic import command
    from alembic.config import Config
    from cryptography.hazmat.primitives.asymmetric import rsa
    from fastapi import Depends
    from fastapi.testclient import TestClient

    from legacy_api.auth import FailureRateLimiter, Principal, require_step_up
    from legacy_api.config import Settings
    from legacy_api.main import create_app
    from legacy_api.verifier import TokenVerifier

API_DIR = Path(__file__).resolve().parent.parent
SYSTEM_USER_ID = "00000000-0000-7000-8000-000000000001"
ISSUER = "https://auth.test.invalid"
AUDIENCE = "legacy-api"

KEY = None
OTHER_KEY = None


def setup_module() -> None:
    global KEY, OTHER_KEY
    KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    OTHER_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def issue_token(
    sub: str,
    *,
    mfa: bool = True,
    auth_age_s: int = 0,
    session: str | None = None,
    issuer: str = ISSUER,
    audience: str = AUDIENCE,
    expired: bool = False,
    key: Any = None,
) -> str:
    now = int(time.time())
    claims: dict[str, Any] = {
        "iss": issuer,
        "aud": audience,
        "sub": sub,
        "iat": now,
        "exp": now - 60 if expired else now + 900,
        "auth_time": now - auth_age_s,
        "session_id": session or uuid.uuid4().hex,
    }
    if mfa:
        claims["aal"] = "aal2"
        claims["amr"] = ["totp"]
    return pyjwt.encode(claims, key or KEY, algorithm="RS256")


class RecordingNotifier:
    def __init__(self) -> None:
        self.messages: list[tuple[str, str]] = []

    def notify(self, subject: str, body: str) -> None:
        self.messages.append((subject, body))


@pytest.fixture(scope="module")
def db() -> Iterator["psycopg.Connection"]:
    cfg = Config(str(API_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(API_DIR / "migrations"))
    __import__("os").environ["LEGACY_DATABASE_URL"] = DB_URL or ""
    with psycopg.connect(DB_URL, autocommit=True) as conn:
        for (table,) in conn.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
        ).fetchall():
            conn.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
        command.upgrade(cfg, "head")
        yield conn


@pytest.fixture(scope="module")
def users(db: "psycopg.Connection") -> dict[str, str]:
    created = {}
    rows = [
        ("owner-sub", "owner@example.test", "human", True, "active"),
        ("human-sub", "human@example.test", "human", False, "active"),
        ("svc-sub", "svc@example.test", "service", False, "active"),
        ("susp-sub", "suspended@example.test", "human", False, "suspended"),
    ]
    for sub, email, kind, owner, status in rows:
        created[sub] = db.execute(
            """
            INSERT INTO app_user
                (email, display_name, user_kind, is_owner, account_status,
                 auth_subject, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
            """,
            (email, email.split("@")[0], kind, owner, status, sub, SYSTEM_USER_ID),
        ).fetchone()[0]
    return {k: str(v) for k, v in created.items()}


@pytest.fixture(scope="module")
def notifier() -> "RecordingNotifier":
    return RecordingNotifier()


@pytest.fixture(scope="module")
def client(
    db: "psycopg.Connection", notifier: "RecordingNotifier"
) -> Iterator["TestClient"]:
    settings = Settings(  # type: ignore[call-arg]
        env="local",
        database_url=DB_URL,
        oidc_issuer=ISSUER,
        oidc_audience=AUDIENCE,
        step_up_max_age_s=600,
    )
    verifier = TokenVerifier(
        issuer=ISSUER, audience=AUDIENCE, key_provider=lambda _t: KEY.public_key()
    )
    app = create_app(settings, verifier=verifier, notifier=notifier)

    @app.get("/v1/_test/sensitive")
    async def sensitive(
        principal: Annotated["Principal", Depends(require_step_up)],
    ) -> dict[str, str]:
        return {"ok": principal.user_id}

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def fresh_rate_limiter(client: "TestClient") -> None:
    client.app.state.rate_limiter = FailureRateLimiter()  # type: ignore[attr-defined]


def get_session(client: "TestClient", token: str, ua: str = "test-browser") -> Any:
    return client.get(
        "/v1/auth/session",
        headers={"Authorization": f"Bearer {token}", "User-Agent": ua},
    )


def audit_count(db: "psycopg.Connection", action: str, actor: str | None = None) -> int:
    query = "SELECT count(*) FROM audit_log_entry WHERE action = %s"
    params: list[Any] = [action]
    if actor:
        query += " AND actor_id = %s"
        params.append(actor)
    return db.execute(query, params).fetchone()[0]


def test_health_endpoints_open_and_db_ready(client: "TestClient") -> None:
    assert client.get("/healthz").status_code == 200
    assert client.get("/readyz").status_code == 200


def test_unauthenticated_request_rejected(client: "TestClient") -> None:
    response = client.get("/v1/auth/session")
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "unauthenticated"


def test_owner_with_mfa_succeeds_and_is_audited(
    client: "TestClient", db: "psycopg.Connection", users: dict, notifier: "RecordingNotifier"
) -> None:
    response = get_session(client, issue_token("owner-sub", session="s1"))
    assert response.status_code == 200
    body = response.json()
    assert body["is_owner"] is True
    assert body["mfa"] is True
    assert body["new_device"] is True

    assert audit_count(db, "login", users["owner-sub"]) == 1
    assert len(notifier.messages) == 1
    last_login = db.execute(
        "SELECT last_login_at FROM app_user WHERE id = %s", (users["owner-sub"],)
    ).fetchone()[0]
    assert last_login is not None


def test_same_session_does_not_duplicate_login_audit(
    client: "TestClient", db: "psycopg.Connection", users: dict
) -> None:
    token = issue_token("owner-sub", session="s1")
    assert get_session(client, token).status_code == 200
    assert audit_count(db, "login", users["owner-sub"]) == 1


def test_new_session_on_known_device_is_not_new_device(
    client: "TestClient", db: "psycopg.Connection", users: dict, notifier: "RecordingNotifier"
) -> None:
    response = get_session(client, issue_token("owner-sub", session="s2"))
    assert response.status_code == 200
    assert response.json()["new_device"] is False
    assert audit_count(db, "login", users["owner-sub"]) == 2
    assert len(notifier.messages) == 1


def test_new_device_with_stale_auth_requires_step_up(
    client: "TestClient", db: "psycopg.Connection", users: dict
) -> None:
    response = get_session(
        client,
        issue_token("owner-sub", session="s3", auth_age_s=3600),
        ua="different-device",
    )
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "step_up_required"
    assert audit_count(db, "login_denied", users["owner-sub"]) >= 1


def test_new_device_with_fresh_auth_notifies_owner(
    client: "TestClient", users: dict, notifier: "RecordingNotifier"
) -> None:
    response = get_session(
        client, issue_token("owner-sub", session="s4"), ua="brand-new-device"
    )
    assert response.status_code == 200
    assert response.json()["new_device"] is True
    assert len(notifier.messages) == 2


def test_owner_without_mfa_is_denied_no_bypass(
    client: "TestClient", db: "psycopg.Connection", users: dict
) -> None:
    before = audit_count(db, "login_denied", users["owner-sub"])
    response = get_session(client, issue_token("owner-sub", mfa=False))
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "mfa_required"
    assert audit_count(db, "login_denied", users["owner-sub"]) == before + 1


def test_non_owner_without_mfa_is_allowed(client: "TestClient") -> None:
    response = get_session(client, issue_token("human-sub", mfa=False))
    assert response.status_code == 200
    assert response.json()["mfa"] is False
    assert response.json()["is_owner"] is False


def test_service_principal_cannot_authenticate_interactively(
    client: "TestClient", db: "psycopg.Connection", users: dict
) -> None:
    response = get_session(client, issue_token("svc-sub"))
    assert response.status_code == 403
    assert audit_count(db, "login_denied", users["svc-sub"]) == 1


def test_suspended_account_denied(client: "TestClient") -> None:
    response = get_session(client, issue_token("susp-sub"))
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "forbidden"


def test_unknown_subject_denied_and_audited(
    client: "TestClient", db: "psycopg.Connection"
) -> None:
    before = audit_count(db, "login_denied")
    response = get_session(client, issue_token("ghost-sub"))
    assert response.status_code == 401
    assert audit_count(db, "login_denied") == before + 1


@pytest.mark.parametrize(
    "kwargs",
    [
        {"issuer": "https://evil.invalid"},
        {"audience": "someone-else"},
        {"expired": True},
        {"key": "OTHER"},
    ],
)
def test_invalid_tokens_rejected(client: "TestClient", kwargs: dict) -> None:
    if kwargs.get("key") == "OTHER":
        kwargs = {**kwargs, "key": OTHER_KEY}
    response = get_session(client, issue_token("owner-sub", **kwargs))
    assert response.status_code == 401


def test_progressive_rate_limiting(client: "TestClient") -> None:
    client.app.state.rate_limiter = FailureRateLimiter(  # type: ignore[attr-defined]
        threshold=2, base_cooldown_s=60
    )
    for _ in range(2):
        assert get_session(client, "garbage-token").status_code == 401
    response = get_session(client, "garbage-token")
    assert response.status_code == 429
    assert int(response.headers["Retry-After"]) > 0
    # Even a valid token is refused while the source is cooling down.
    assert get_session(client, issue_token("owner-sub", session="s1")).status_code == 429


def test_step_up_required_for_sensitive_actions(client: "TestClient") -> None:
    fresh = issue_token("owner-sub", session="s1")
    stale = issue_token("owner-sub", session="s1", auth_age_s=3600)

    ok = client.get(
        "/v1/_test/sensitive",
        headers={"Authorization": f"Bearer {fresh}", "User-Agent": "test-browser"},
    )
    assert ok.status_code == 200

    denied = client.get(
        "/v1/_test/sensitive",
        headers={"Authorization": f"Bearer {stale}", "User-Agent": "test-browser"},
    )
    assert denied.status_code == 401
    assert denied.json()["detail"]["code"] == "step_up_required"
