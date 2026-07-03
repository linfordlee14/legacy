"""Contract tests for the /v1 conventions layer (MVP-007).

API_SPECIFICATION 4.1 to 4.3: error envelope and canonical codes, request-id
echo, cursor pagination, filtering and allowlisted sorting, idempotency
replay, rate limiting, RFC 3339 timestamps, tier-filtered visibility, and the
provenance block. Requires LEGACY_TEST_DATABASE_URL; skipped when unset.
"""

import os
import time
import uuid
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Any

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
    from fastapi import Request
    from fastapi.responses import JSONResponse
    from fastapi.testclient import TestClient

    from legacy_api.api.errors import ErrorCode
    from legacy_api.api.idempotency import IdempotencyStore, fingerprint
    from legacy_api.api.ratelimit import TokenBucketLimiter
    from legacy_api.config import Settings
    from legacy_api.main import create_app
    from legacy_api.verifier import TokenVerifier

API_DIR = Path(__file__).resolve().parent.parent
SYSTEM_USER_ID = "00000000-0000-7000-8000-000000000001"
ISSUER = "https://auth.test.invalid"
AUDIENCE = "legacy-api"
KEY = None

SPEC_ERROR_CODES = {
    "unauthenticated", "forbidden", "tier_forbidden", "not_found",
    "validation_failed", "conflict", "rate_limited", "idempotency_replay",
    "provider_unavailable", "internal",
}


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
def seed(db: "psycopg.Connection") -> dict[str, Any]:
    out: dict[str, Any] = {}
    owner_id = db.execute(
        """
        INSERT INTO app_user (email, display_name, user_kind, is_owner, auth_subject, created_by)
        VALUES ('conv-owner@example.test', 'owner', 'human', true, 'conv-owner', %s)
        RETURNING id
        """,
        (SYSTEM_USER_ID,),
    ).fetchone()[0]
    out["owner"] = str(owner_id)

    trusted_id = db.execute(
        """
        INSERT INTO app_user (email, display_name, user_kind, is_owner, auth_subject, created_by)
        VALUES ('conv-trusted@example.test', 'trusted', 'human', false, 'conv-trusted', %s)
        RETURNING id
        """,
        (SYSTEM_USER_ID,),
    ).fetchone()[0]
    role_id = db.execute("SELECT id FROM role WHERE name = 'trusted'").fetchone()[0]
    db.execute(
        """
        INSERT INTO access_grant (user_id, role_id, scope_type, granted_by, created_by)
        VALUES (%s, %s, 'global', %s, %s)
        """,
        (trusted_id, role_id, owner_id, owner_id),
    )

    def add_claim(subject_type: str, tier: str, privacy: str, statement: str) -> str:
        return str(
            db.execute(
                """
                INSERT INTO claim (subject_type, subject_id, predicate, statement,
                                   confidence_tier, privacy_tier, created_by)
                VALUES (%s, %s, 'test_predicate', %s, %s, %s, %s) RETURNING id
                """,
                (subject_type, str(uuid.uuid4()), statement, tier, privacy, owner_id),
            ).fetchone()[0]
        )

    out["pag"] = [
        add_claim("PagTest", "flagged", "P0", f"pagination claim {i}") for i in range(30)
    ]
    out["tiered"] = {
        "P0": add_claim("VisTest", "self_reported", "P0", "public visible"),
        "P1": add_claim("VisTest", "self_reported", "P1", "trusted visible"),
        "P2": add_claim("VisTest", "self_reported", "P2", "owner visible"),
    }
    add_claim("SortTest", "self_reported", "P0", "self reported one")
    add_claim("SortTest", "flagged", "P0", "flagged one")

    prov_claim = add_claim("ProvTest", "self_reported", "P0", "provenance sample")
    out["prov_claim"] = prov_claim
    for title, url in (("GDG event page", "https://example.test/evidence"), ("Archive", None)):
        source_id = db.execute(
            """
            INSERT INTO source (source_type, title, url, created_by)
            VALUES ('url', %s, %s, %s) RETURNING id
            """,
            (title, url, owner_id),
        ).fetchone()[0]
        db.execute(
            """
            INSERT INTO claim_source (claim_id, source_id, support_type, created_by)
            VALUES (%s, %s, 'supports', %s)
            """,
            (prov_claim, source_id, owner_id),
        )
    return out


@pytest.fixture(scope="module")
def client(db: "psycopg.Connection", seed: dict[str, Any]) -> Iterator["TestClient"]:
    settings = Settings(  # type: ignore[call-arg]
        env="local", database_url=DB_URL, oidc_issuer=ISSUER, oidc_audience=AUDIENCE
    )
    verifier = TokenVerifier(
        issuer=ISSUER, audience=AUDIENCE, key_provider=lambda _t: KEY.public_key()
    )
    app = create_app(settings, verifier=verifier)

    effects = {"count": 0}
    app.state.effects = effects

    @app.post("/v1/_test/items", status_code=201)
    async def create_item(request: Request) -> JSONResponse:
        store: IdempotencyStore = request.app.state.idempotency
        body = await request.body()
        key = request.headers.get("idempotency-key")
        fp = fingerprint("POST", "/v1/_test/items", body)
        if key:
            entry = store.check(key, fp)
            if entry:
                return JSONResponse(
                    entry.body, status_code=entry.status,
                    headers={"Idempotency-Replayed": "true"},
                )
        effects["count"] += 1
        result = {"item": effects["count"]}
        if key:
            store.store(key, fp, 201, result)
        return JSONResponse(result, status_code=201)

    @app.get("/v1/_test/boom")
    async def boom() -> None:
        raise RuntimeError("intentional")

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def generous_budget(client: "TestClient") -> None:
    client.app.state.request_bucket = TokenBucketLimiter(per_minute=100000)  # type: ignore[attr-defined]


def test_canonical_error_codes_match_spec_exactly() -> None:
    assert {code.value for code in ErrorCode} == SPEC_ERROR_CODES


def test_error_envelope_and_request_id_echo(client: "TestClient") -> None:
    response = client.get("/v1/claims/not-a-uuid", headers={"X-Request-ID": "req-42"})
    assert response.status_code == 404
    error = response.json()["error"]
    assert error["code"] == "not_found"
    assert error["request_id"] == "req-42"
    assert response.headers["X-Request-ID"] == "req-42"


def test_request_id_minted_when_absent(client: "TestClient") -> None:
    response = client.get(f"/v1/claims/{uuid.uuid4()}")
    assert response.json()["error"]["request_id"]
    assert response.headers["X-Request-ID"]


def test_unknown_route_uses_envelope(client: "TestClient") -> None:
    assert client.get("/v1/definitely-not-a-route").json()["error"]["code"] == "not_found"


def test_validation_failed_on_bad_limit(client: "TestClient") -> None:
    response = client.get("/v1/claims", params={"limit": 1000})
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_failed"
    assert any("limit" in e["loc"] for e in error["details"]["errors"])


def test_validation_failed_on_bad_cursor_and_sort(client: "TestClient") -> None:
    bad_cursor = client.get("/v1/claims", params={"cursor": "@@@"})
    assert bad_cursor.json()["error"]["code"] == "validation_failed"
    bad_sort = client.get("/v1/claims", params={"sort": "chaos"})
    assert bad_sort.json()["error"]["code"] == "validation_failed"


def test_cursor_pagination_walk(client: "TestClient", seed: dict[str, Any]) -> None:
    seen: list[str] = []
    cursor: str | None = None
    pages = 0
    while True:
        params: dict[str, Any] = {"subject_type": "PagTest", "limit": 10}
        if cursor:
            params["cursor"] = cursor
        body = client.get("/v1/claims", params=params).json()
        seen.extend(item["id"] for item in body["data"])
        pages += 1
        cursor = body["next_cursor"]
        if cursor is None:
            break
    assert pages == 3
    assert len(seen) == 30
    assert len(set(seen)) == 30
    assert set(seen) == set(seed["pag"])


def test_default_limit_is_25(client: "TestClient") -> None:
    body = client.get("/v1/claims", params={"subject_type": "PagTest"}).json()
    assert len(body["data"]) == 25
    assert body["next_cursor"] is not None


def test_sort_allowlist_and_order(client: "TestClient") -> None:
    newest = client.get(
        "/v1/claims", params={"subject_type": "PagTest", "limit": 30}
    ).json()["data"]
    oldest = client.get(
        "/v1/claims", params={"subject_type": "PagTest", "limit": 30, "sort": "created_at"}
    ).json()["data"]
    assert [i["id"] for i in oldest] == [i["id"] for i in newest][::-1]


def test_confidence_tier_filter(client: "TestClient") -> None:
    body = client.get(
        "/v1/claims", params={"subject_type": "SortTest", "tier": "flagged"}
    ).json()
    assert len(body["data"]) == 1
    assert body["data"][0]["provenance"]["claims"][0]["tier"] == "flagged"


def test_tier_visibility_by_principal(client: "TestClient", seed: dict[str, Any]) -> None:
    def visible(sub: str | None) -> set[str]:
        headers = {"User-Agent": "conv-tests"}
        if sub:
            headers["Authorization"] = f"Bearer {issue_token(sub)}"
        body = client.get(
            "/v1/claims", params={"subject_type": "VisTest"}, headers=headers
        ).json()
        return {item["privacy_tier"] for item in body["data"]}

    assert visible(None) == {"P0"}
    assert visible("conv-trusted") == {"P0", "P1"}
    assert visible("conv-owner") == {"P0", "P1", "P2"}


def test_provenance_block_present_with_sources(
    client: "TestClient", seed: dict[str, Any]
) -> None:
    body = client.get(f"/v1/claims/{seed['prov_claim']}").json()
    claims = body["provenance"]["claims"]
    assert len(claims) == 1
    entry = claims[0]
    assert entry["claim_id"] == seed["prov_claim"]
    assert entry["tier"] == "self_reported"
    labels = {s["label"] for s in entry["sources"]}
    assert labels == {"GDG event page", "Archive"}
    urls = {s["url"] for s in entry["sources"]}
    assert urls == {"https://example.test/evidence", None}


def test_timestamps_are_rfc3339_utc(client: "TestClient", seed: dict[str, Any]) -> None:
    body = client.get(f"/v1/claims/{seed['prov_claim']}").json()
    for field in ("created_at", "updated_at"):
        parsed = datetime.fromisoformat(body[field])
        assert parsed.tzinfo is not None
        assert "T" in body[field]


def test_idempotency_replay_and_conflict(client: "TestClient") -> None:
    effects = client.app.state.effects  # type: ignore[attr-defined]
    start = effects["count"]

    first = client.post("/v1/_test/items", json={"a": 1}, headers={"Idempotency-Key": "k1"})
    assert first.status_code == 201
    assert effects["count"] == start + 1

    replay = client.post("/v1/_test/items", json={"a": 1}, headers={"Idempotency-Key": "k1"})
    assert replay.status_code == 201
    assert replay.json() == first.json()
    assert replay.headers["Idempotency-Replayed"] == "true"
    assert effects["count"] == start + 1  # no double side effect

    mismatch = client.post(
        "/v1/_test/items", json={"a": 2}, headers={"Idempotency-Key": "k1"}
    )
    assert mismatch.status_code == 409
    assert mismatch.json()["error"]["code"] == "idempotency_replay"
    assert effects["count"] == start + 1

    fresh = client.post("/v1/_test/items", json={"a": 1}, headers={"Idempotency-Key": "k2"})
    assert fresh.status_code == 201
    assert effects["count"] == start + 2


def test_rate_limited_with_retry_after(client: "TestClient") -> None:
    client.app.state.request_bucket = TokenBucketLimiter(per_minute=2)  # type: ignore[attr-defined]
    assert client.get("/v1/claims").status_code == 200
    assert client.get("/v1/claims").status_code == 200
    limited = client.get("/v1/claims")
    assert limited.status_code == 429
    assert limited.json()["error"]["code"] == "rate_limited"
    assert int(limited.headers["Retry-After"]) >= 1
    assert client.get("/healthz").status_code == 200  # health stays open


def test_internal_errors_never_leak(client: "TestClient") -> None:
    quiet = TestClient(client.app, raise_server_exceptions=False)
    response = quiet.get("/v1/_test/boom")
    assert response.status_code == 500
    error = response.json()["error"]
    assert error["code"] == "internal"
    assert "intentional" not in response.text
