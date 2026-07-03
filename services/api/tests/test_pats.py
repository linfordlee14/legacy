"""Personal access token tests (MVP-005, AUTHENTICATION 4.3,
API_SPECIFICATION 4.5): lifecycle, scope enforcement per scope, immediate
revocation, expiry, per-use auditing, and step-up denial for machines.
Requires LEGACY_TEST_DATABASE_URL; skipped when unset.
"""

import os
import time
import uuid
from collections.abc import Iterator
from pathlib import Path
from typing import Annotated, Any

import pytest

DB_URL = os.environ.get("LEGACY_TEST_DATABASE_URL")

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

    from legacy_api.auth import Principal, require_step_up
    from legacy_api.config import Settings
    from legacy_api.main import create_app
    from legacy_api.policy import Action, decide, resolve_context
    from legacy_api.verifier import TokenVerifier

API_DIR = Path(__file__).resolve().parent.parent
SYSTEM_USER_ID = "00000000-0000-7000-8000-000000000001"
ISSUER = "https://auth.test.invalid"
AUDIENCE = "legacy-api"
KEY = None


def setup_module() -> None:
    global KEY
    KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def oidc_token(sub: str, auth_age_s: int = 0) -> str:
    now = int(time.time())
    return pyjwt.encode(
        {
            "iss": ISSUER, "aud": AUDIENCE, "sub": sub, "iat": now, "exp": now + 900,
            "auth_time": now - auth_age_s, "session_id": uuid.uuid4().hex, "aal": "aal2",
        },
        KEY,
        algorithm="RS256",
    )


@pytest.fixture(scope="module")
def db() -> Iterator["psycopg.Connection"]:
    cfg = Config(str(API_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(API_DIR / "migrations"))
    os.environ["LEGACY_DATABASE_URL"] = DB_URL or ""
    with psycopg.connect(DB_URL, autocommit=True) as conn:
        for (table,) in conn.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
        ).fetchall():
            conn.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
        command.upgrade(cfg, "head")
        yield conn


@pytest.fixture(scope="module")
def seed(db: "psycopg.Connection") -> dict[str, str]:
    out = {}
    for sub, owner in (("pat-owner", True), ("pat-human", False)):
        out[sub] = str(
            db.execute(
                """
                INSERT INTO app_user
                    (email, display_name, user_kind, is_owner, auth_subject, created_by)
                VALUES (%s, %s, 'human', %s, %s, %s) RETURNING id
                """,
                (f"{sub}@example.test", sub, owner, sub, SYSTEM_USER_ID),
            ).fetchone()[0]
        )
    for key, tier in (("c_p0", "P0"), ("c_p1", "P1"), ("c_p2", "P2"), ("c_p3", "P3")):
        out[key] = str(
            db.execute(
                """
                INSERT INTO claim (subject_type, subject_id, predicate, statement,
                                   confidence_tier, privacy_tier, created_by)
                VALUES ('PatVis', %s, 'p', %s, 'flagged', %s, %s) RETURNING id
                """,
                (str(uuid.uuid4()), f"claim {key}", tier, out["pat-owner"]),
            ).fetchone()[0]
        )
    return out


@pytest.fixture(scope="module")
def client(db: "psycopg.Connection", seed: dict[str, str]) -> Iterator["TestClient"]:
    settings = Settings(  # type: ignore[call-arg]
        env="local", database_url=DB_URL, oidc_issuer=ISSUER, oidc_audience=AUDIENCE
    )
    verifier = TokenVerifier(
        issuer=ISSUER, audience=AUDIENCE, key_provider=lambda _t: KEY.public_key()
    )
    app = create_app(settings, verifier=verifier)

    @app.get("/v1/_test/sensitive")
    async def sensitive(
        principal: Annotated["Principal", Depends(require_step_up)],
    ) -> dict[str, str]:
        return {"ok": principal.user_id}

    with TestClient(app) as test_client:
        yield test_client


def mint(client: "TestClient", scopes: list[str], ttl_days: int = 30, label: str = "t") -> Any:
    return client.post(
        "/v1/auth/tokens",
        json={"label": label, "scopes": scopes, "ttl_days": ttl_days},
        headers={"Authorization": f"Bearer {oidc_token('pat-owner')}", "User-Agent": "pt"},
    )


def visible_tiers(client: "TestClient", pat: str) -> set[str]:
    body = client.get(
        "/v1/claims",
        params={"subject_type": "PatVis", "limit": 50},
        headers={"Authorization": f"Bearer {pat}", "User-Agent": "pt"},
    ).json()
    return {item["privacy_tier"] for item in body["data"]}


def audit_count(db: "psycopg.Connection", action: str, actor: str | None = None) -> int:
    query = "SELECT count(*) FROM audit_log_entry WHERE action = %s"
    params: list[Any] = [action]
    if actor:
        query += " AND actor_id = %s"
        params.append(actor)
    return db.execute(query, params).fetchone()[0]


def test_create_returns_secret_once_and_lists_metadata_only(
    client: "TestClient", db: "psycopg.Connection", seed: dict
) -> None:
    created = mint(client, ["read:public"], label="ci-reader")
    assert created.status_code == 201
    body = created.json()
    assert body["token"].startswith("lgy_pat_")
    assert audit_count(db, "pat_created") == 1

    listing = client.get(
        "/v1/auth/tokens",
        headers={"Authorization": f"Bearer {oidc_token('pat-owner')}", "User-Agent": "pt"},
    ).json()
    entry = next(e for e in listing["data"] if e["id"] == body["id"])
    assert entry["label"] == "ci-reader"
    assert "token" not in entry
    assert "token_hash" not in entry


def test_creation_requires_owner_and_step_up(client: "TestClient") -> None:
    non_owner = client.post(
        "/v1/auth/tokens",
        json={"label": "x", "scopes": ["read:public"]},
        headers={"Authorization": f"Bearer {oidc_token('pat-human')}", "User-Agent": "pt"},
    )
    assert non_owner.status_code == 403

    stale = client.post(
        "/v1/auth/tokens",
        json={"label": "x", "scopes": ["read:public"]},
        headers={
            "Authorization": f"Bearer {oidc_token('pat-owner', auth_age_s=3600)}",
            "User-Agent": "pt",
        },
    )
    assert stale.status_code == 401
    assert stale.json()["error"]["details"]["reason"] == "step_up_required"


def test_creation_validation(client: "TestClient") -> None:
    bad_scope = mint(client, ["read:everything"])
    assert bad_scope.status_code == 422
    assert bad_scope.json()["error"]["code"] == "validation_failed"
    bad_ttl = mint(client, ["read:public"], ttl_days=999)
    assert bad_ttl.status_code == 422


def test_scope_enforcement_per_scope(client: "TestClient", seed: dict) -> None:
    public_pat = mint(client, ["read:public"]).json()["token"]
    trusted_pat = mint(client, ["read:trusted"]).json()["token"]
    private_pat = mint(client, ["read:private", "admin"]).json()["token"]

    assert visible_tiers(client, public_pat) == {"P0"}
    assert visible_tiers(client, trusted_pat) == {"P0", "P1"}
    # Machine ceiling is P2, never P3, even with the widest scopes.
    assert visible_tiers(client, private_pat) == {"P0", "P1", "P2"}


def test_write_scope_widens_actions(client: "TestClient", db: "psycopg.Connection") -> None:
    import asyncio

    async def check(scopes: tuple[str, ...], action: "Action") -> bool:
        pool = client.app.state.pool  # type: ignore[attr-defined]
        principal = Principal(
            user_id=str(uuid.uuid4()), email="m@x", display_name="m", is_owner=False,
            mfa_satisfied=False, auth_time=None, session_ref="t", new_device=False,
            pat_scopes=scopes,
        )
        async with pool.connection() as conn:
            ctx = await resolve_context(conn, principal)
            return (await decide(conn, ctx, action)).allow

    assert asyncio.run(check(("read:private", "write:content"), Action.CONTENT_CREATE))
    assert not asyncio.run(check(("read:private",), Action.CONTENT_CREATE))
    assert asyncio.run(check(("admin",), Action.AUDIT_READ))
    assert not asyncio.run(check(("read:private",), Action.TIER_CHANGE))


def test_every_use_is_audited_and_last_used_maintained(
    client: "TestClient", db: "psycopg.Connection"
) -> None:
    created = mint(client, ["read:public"], label="audited").json()
    pat, token_id = created["token"], created["id"]
    before = audit_count(db, "pat_use")
    visible_tiers(client, pat)
    visible_tiers(client, pat)
    assert audit_count(db, "pat_use") == before + 2
    last_used = db.execute(
        "SELECT last_used_at FROM personal_access_token WHERE id = %s", (token_id,)
    ).fetchone()[0]
    assert last_used is not None


def test_revocation_is_immediate(client: "TestClient", db: "psycopg.Connection") -> None:
    created = mint(client, ["read:public"], label="doomed").json()
    pat, token_id = created["token"], created["id"]
    assert visible_tiers(client, pat) == {"P0"}

    revoked = client.delete(
        f"/v1/auth/tokens/{token_id}",
        headers={"Authorization": f"Bearer {oidc_token('pat-owner')}", "User-Agent": "pt"},
    )
    assert revoked.status_code == 204
    assert audit_count(db, "pat_revoked") == 1

    denied = client.get(
        "/v1/claims",
        headers={"Authorization": f"Bearer {pat}", "User-Agent": "pt"},
    )
    assert denied.status_code == 401


def test_expired_token_denied(client: "TestClient", db: "psycopg.Connection") -> None:
    created = mint(client, ["read:public"], label="stale").json()
    db.execute(
        """
        UPDATE personal_access_token
        SET created_at = now() - interval '2 days', expires_at = now() - interval '1 day'
        WHERE id = %s
        """,
        (created["id"],),
    )
    denied = client.get(
        "/v1/claims",
        headers={"Authorization": f"Bearer {created['token']}", "User-Agent": "pt"},
    )
    assert denied.status_code == 401


def test_garbage_pat_denied(client: "TestClient") -> None:
    denied = client.get(
        "/v1/claims",
        headers={"Authorization": "Bearer lgy_pat_not-a-real-token", "User-Agent": "pt"},
    )
    assert denied.status_code == 401


def test_machines_cannot_step_up(client: "TestClient") -> None:
    pat = mint(client, ["read:private"]).json()["token"]
    denied = client.get(
        "/v1/_test/sensitive",
        headers={"Authorization": f"Bearer {pat}", "User-Agent": "pt"},
    )
    assert denied.status_code == 401
    assert denied.json()["error"]["details"]["reason"] == "step_up_required"
