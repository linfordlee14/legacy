"""Authorization matrix, grant, and existence-leak tests (MVP-006).

AUTHORIZATION 4.1 to 4.5 and 4.7 against a real database: context resolution,
grant lifecycle (expiry, immediate revocation, scopes), the uniform not_found
guarantee, denial and sensitive-allow audits, and agent ceiling inheritance.
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
    from fastapi import Depends, Request
    from fastapi.testclient import TestClient
    from psycopg.rows import dict_row

    from legacy_api.auth import Principal, authenticate, authenticate_optional
    from legacy_api.config import Settings
    from legacy_api.main import create_app
    from legacy_api.policy import (
        Action,
        Resource,
        agent_context,
        authorize,
        read_or_not_found,
        resolve_context,
    )
    from legacy_api.verifier import TokenVerifier

API_DIR = Path(__file__).resolve().parent.parent
SYSTEM_USER_ID = "00000000-0000-7000-8000-000000000001"
ISSUER = "https://auth.test.invalid"
AUDIENCE = "legacy-api"
KEY = None


def setup_module() -> None:
    global KEY
    KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def issue_token(sub: str) -> str:
    now = int(time.time())
    return pyjwt.encode(
        {
            "iss": ISSUER, "aud": AUDIENCE, "sub": sub, "iat": now, "exp": now + 900,
            "auth_time": now, "session_id": uuid.uuid4().hex, "aal": "aal2",
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
def ids(db: "psycopg.Connection") -> dict[str, str]:
    """Users, grants, and content the matrix tests exercise."""
    out: dict[str, str] = {}

    def add_user(sub: str, owner: bool = False) -> str:
        return str(
            db.execute(
                """
                INSERT INTO app_user
                    (email, display_name, user_kind, is_owner, auth_subject, created_by)
                VALUES (%s, %s, 'human', %s, %s, %s) RETURNING id
                """,
                (f"{sub}@example.test", sub, owner, sub, SYSTEM_USER_ID),
            ).fetchone()[0]
        )

    out["owner"] = add_user("authz-owner", owner=True)
    out["trusted_global"] = add_user("authz-trusted-global")
    out["trusted_scoped"] = add_user("authz-trusted-scoped")
    out["expired"] = add_user("authz-expired")
    out["revoked"] = add_user("authz-revoked")
    out["nogrories"] = add_user("authz-nogrant")
    out["pre_steward"] = add_user("authz-presteward")
    out["steward"] = add_user("authz-steward")

    roles = dict(db.execute("SELECT name, id FROM role").fetchall())

    def add_grant(user_key: str, role: str, **cols: Any) -> None:
        fields = {
            "user_id": out[user_key], "role_id": roles[role], "scope_type": "global",
            "scope_ref_type": None, "scope_ref_id": None, "granted_by": out["owner"],
            "expires_at": None, "activation_condition": None,
        }
        fields.update(cols)
        db.execute(
            """
            INSERT INTO access_grant
                (user_id, role_id, scope_type, scope_ref_type, scope_ref_id,
                 granted_by, expires_at, activation_condition, created_by)
            VALUES (%(user_id)s, %(role_id)s, %(scope_type)s, %(scope_ref_type)s,
                    %(scope_ref_id)s, %(granted_by)s, %(expires_at)s,
                    %(activation_condition)s, %(user_id)s)
            """,
            fields,
        )

    # Content: P0, P1, and P2 notes.
    for key, tier in (("note_p0", "P0"), ("note_p1", "P1"), ("note_p2", "P2")):
        out[key] = str(
            db.execute(
                "INSERT INTO note (body, privacy_tier, created_by) "
                "VALUES (%s, %s, %s) RETURNING id",
                (f"body {key}", tier, out["owner"]),
            ).fetchone()[0]
        )
    # A second P1 note outside any entity scope.
    out["note_p1_other"] = str(
        db.execute(
            "INSERT INTO note (body, privacy_tier, created_by) "
            "VALUES ('other', 'P1', %s) RETURNING id",
            (out["owner"],),
        ).fetchone()[0]
    )

    add_grant("trusted_global", "trusted")
    add_grant(
        "trusted_scoped", "trusted",
        scope_type="entity", scope_ref_type="Note", scope_ref_id=out["note_p1"],
    )
    add_grant("expired", "trusted", expires_at="2000-01-01T00:00:00Z")
    add_grant("revoked", "trusted")
    db.execute(
        "UPDATE access_grant SET deleted_at = now() WHERE user_id = %s", (out["revoked"],)
    )
    add_grant("pre_steward", "steward", activation_condition='{"type": "succession"}')
    add_grant("steward", "steward")
    return out


@pytest.fixture(scope="module")
def client(db: "psycopg.Connection") -> Iterator["TestClient"]:
    settings = Settings(  # type: ignore[call-arg]
        env="local", database_url=DB_URL, oidc_issuer=ISSUER, oidc_audience=AUDIENCE
    )
    verifier = TokenVerifier(
        issuer=ISSUER, audience=AUDIENCE, key_provider=lambda _t: KEY.public_key()
    )
    app = create_app(settings, verifier=verifier)

    @app.get("/v1/_test/notes/{note_id}")
    async def read_note(
        note_id: str,
        request: Request,
        principal: Annotated["Principal | None", Depends(authenticate_optional)],
    ) -> dict[str, str]:
        async with request.app.state.pool.connection() as conn:
            ctx = await resolve_context(conn, principal)
            try:
                row_id = uuid.UUID(note_id)
            except ValueError:
                row_id = None
            resource = None
            if row_id is not None:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(
                        "SELECT id, privacy_tier FROM note "
                        "WHERE id = %s AND deleted_at IS NULL",
                        (row_id,),
                    )
                    row = await cur.fetchone()
                if row:
                    resource = Resource(
                        entity_type="Note",
                        entity_id=str(row["id"]),
                        privacy_tier=row["privacy_tier"],
                    )
            await read_or_not_found(conn, ctx, resource)
            return {"id": note_id}

    @app.post("/v1/_test/tier-change/{note_id}")
    async def tier_change(
        note_id: str,
        request: Request,
        principal: Annotated["Principal", Depends(authenticate)],
    ) -> dict[str, str]:
        async with request.app.state.pool.connection() as conn:
            ctx = await resolve_context(conn, principal)
            resource = Resource(entity_type="Note", entity_id=note_id, privacy_tier="P2")
            decision = await authorize(conn, ctx, Action.TIER_CHANGE, resource)
            if not decision.allow:
                from fastapi import HTTPException

                raise HTTPException(status_code=403, detail={"code": "forbidden"})
            return {"policy_version": decision.policy_version}

    @app.get("/v1/_test/agent-read/{note_id}")
    async def agent_read(
        note_id: str,
        request: Request,
        principal: Annotated["Principal", Depends(authenticate)],
    ) -> dict[str, bool]:
        async with request.app.state.pool.connection() as conn:
            ctx = agent_context(await resolve_context(conn, principal), "retrieval")
            resource = Resource(entity_type="Note", entity_id=note_id, privacy_tier="P2")
            decision = await authorize(conn, ctx, Action.CONTENT_READ, resource)
            return {"allow": decision.allow}

    with TestClient(app) as test_client:
        yield test_client


def get(client: "TestClient", path: str, sub: str | None = None) -> Any:
    headers = {"User-Agent": "authz-tests"}
    if sub:
        headers["Authorization"] = f"Bearer {issue_token(sub)}"
    return client.get(path, headers=headers)


def audit_rows(db: "psycopg.Connection", action: str) -> list[dict]:
    with db.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT actor_type, payload_summary FROM audit_log_entry WHERE action = %s",
            (action,),
        )
        return cur.fetchall()


# --- context resolution (4.1, 4.3) -------------------------------------------

def ctx_for(client: "TestClient", db: "psycopg.Connection", sub: str | None) -> Any:
    import asyncio

    async def resolve() -> Any:
        pool = client.app.state.pool  # type: ignore[attr-defined]
        async with pool.connection() as conn:
            principal = None
            if sub is not None:
                row = db.execute(
                    "SELECT id, email, display_name, is_owner FROM app_user "
                    "WHERE auth_subject = %s",
                    (sub,),
                ).fetchone()
                principal = Principal(
                    user_id=str(row[0]), email=row[1], display_name=row[2],
                    is_owner=row[3], mfa_satisfied=True, auth_time=None,
                    session_ref="t", new_device=False,
                )
            return await resolve_context(conn, principal)

    return asyncio.run(resolve())


def test_owner_context(client: "TestClient", db: "psycopg.Connection", ids: dict) -> None:
    ctx = ctx_for(client, db, "authz-owner")
    assert (ctx.kind, ctx.ceiling) == ("owner", "P3")


def test_public_context(client: "TestClient", db: "psycopg.Connection", ids: dict) -> None:
    ctx = ctx_for(client, db, None)
    assert (ctx.kind, ctx.ceiling) == ("public", "P0")


def test_ungranted_human_defaults_to_public(
    client: "TestClient", db: "psycopg.Connection", ids: dict
) -> None:
    ctx = ctx_for(client, db, "authz-nogrant")
    assert (ctx.kind, ctx.ceiling) == ("public", "P0")


def test_trusted_context_with_scopes(
    client: "TestClient", db: "psycopg.Connection", ids: dict
) -> None:
    ctx = ctx_for(client, db, "authz-trusted-scoped")
    assert (ctx.kind, ctx.ceiling) == ("trusted", "P1")
    assert ctx.scopes[0].scope_type == "entity"


def test_expired_grant_confers_nothing(
    client: "TestClient", db: "psycopg.Connection", ids: dict
) -> None:
    ctx = ctx_for(client, db, "authz-expired")
    assert (ctx.kind, ctx.ceiling) == ("public", "P0")


def test_revocation_is_immediate(
    client: "TestClient", db: "psycopg.Connection", ids: dict
) -> None:
    ctx = ctx_for(client, db, "authz-revoked")
    assert (ctx.kind, ctx.ceiling) == ("public", "P0")


def test_steward_activation_states(
    client: "TestClient", db: "psycopg.Connection", ids: dict
) -> None:
    pre = ctx_for(client, db, "authz-presteward")
    assert (pre.kind, pre.ceiling) == ("steward_preactivation", "P1")
    post = ctx_for(client, db, "authz-steward")
    assert (post.kind, post.ceiling) == ("steward", "P2")


# --- existence leak (4.4) -----------------------------------------------------

def test_missing_and_above_ceiling_are_indistinguishable(
    client: "TestClient", db: "psycopg.Connection", ids: dict
) -> None:
    missing = get(client, f"/v1/_test/notes/{uuid.uuid4()}")
    above = get(client, f"/v1/_test/notes/{ids['note_p2']}")
    assert missing.status_code == above.status_code == 404
    assert missing.json() == above.json()

    denied = audit_rows(db, "authz_denied")
    assert any(
        row["payload_summary"]["reason"] == "above_ceiling" for row in denied
    )
    assert all("policy_version" in row["payload_summary"] for row in denied)


def test_public_reads_p0_only(client: "TestClient", ids: dict) -> None:
    assert get(client, f"/v1/_test/notes/{ids['note_p0']}").status_code == 200
    assert get(client, f"/v1/_test/notes/{ids['note_p1']}").status_code == 404


def test_owner_reads_everything(client: "TestClient", ids: dict) -> None:
    for key in ("note_p0", "note_p1", "note_p2"):
        assert get(client, f"/v1/_test/notes/{ids[key]}", "authz-owner").status_code == 200


def test_trusted_global_reads_p1_not_p2(client: "TestClient", ids: dict) -> None:
    sub = "authz-trusted-global"
    assert get(client, f"/v1/_test/notes/{ids['note_p1']}", sub).status_code == 200
    assert get(client, f"/v1/_test/notes/{ids['note_p2']}", sub).status_code == 404


def test_trusted_entity_scope_limits_reads(client: "TestClient", ids: dict) -> None:
    sub = "authz-trusted-scoped"
    assert get(client, f"/v1/_test/notes/{ids['note_p1']}", sub).status_code == 200
    assert get(client, f"/v1/_test/notes/{ids['note_p1_other']}", sub).status_code == 404


# --- sensitive allows and denials (4.2, 4.7) ----------------------------------

def test_owner_tier_change_allowed_and_audited(
    client: "TestClient", db: "psycopg.Connection", ids: dict
) -> None:
    response = client.post(
        f"/v1/_test/tier-change/{ids['note_p2']}",
        headers={
            "Authorization": f"Bearer {issue_token('authz-owner')}",
            "User-Agent": "authz-tests",
        },
    )
    assert response.status_code == 200
    allows = audit_rows(db, "authz_sensitive_allow")
    assert any(
        row["payload_summary"]["requested_action"] == "tier_change" for row in allows
    )


def test_trusted_tier_change_denied_and_audited(
    client: "TestClient", db: "psycopg.Connection", ids: dict
) -> None:
    before = len(audit_rows(db, "authz_denied"))
    response = client.post(
        f"/v1/_test/tier-change/{ids['note_p1']}",
        headers={
            "Authorization": f"Bearer {issue_token('authz-trusted-global')}",
            "User-Agent": "authz-tests",
        },
    )
    assert response.status_code == 403
    assert len(audit_rows(db, "authz_denied")) == before + 1


# --- agent inheritance (4.5) ---------------------------------------------------

def test_agent_inherits_owner_ceiling(client: "TestClient", ids: dict) -> None:
    response = get(client, f"/v1/_test/agent-read/{ids['note_p2']}", "authz-owner")
    assert response.json() == {"allow": True}


def test_agent_cannot_exceed_trusted_ceiling(
    client: "TestClient", db: "psycopg.Connection", ids: dict
) -> None:
    response = get(
        client, f"/v1/_test/agent-read/{ids['note_p2']}", "authz-trusted-global"
    )
    assert response.json() == {"allow": False}
    denied = audit_rows(db, "authz_denied")
    assert any(row["actor_type"] == "agent" for row in denied)
