"""Content read endpoints (MVP-012 server slice; API_SPECIFICATION 4.4).

Tier filtering, uniform not_found, and the provenance block on detail reads
for the notes and artifacts collections.
"""

import os
import time
import uuid
from collections.abc import Iterator
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
    from fastapi.testclient import TestClient

    from legacy_api.config import Settings
    from legacy_api.main import create_app
    from legacy_api.verifier import TokenVerifier

API_DIR = Path(__file__).resolve().parent.parent
SYSTEM_USER_ID = "00000000-0000-7000-8000-000000000001"
ISSUER = "https://auth.test.invalid"
AUDIENCE = "legacy-api"
KEY = None


def setup_module() -> None:
    global KEY
    KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def oidc_token(sub: str) -> str:
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
def ids(db: "psycopg.Connection") -> dict[str, str]:
    out: dict[str, str] = {}
    owner = db.execute(
        """
        INSERT INTO app_user (email, display_name, user_kind, is_owner, auth_subject, created_by)
        VALUES ('content-owner@example.test', 'owner', 'human', true, 'content-owner', %s)
        RETURNING id
        """,
        (SYSTEM_USER_ID,),
    ).fetchone()[0]
    out["owner"] = str(owner)

    for key, tier in (("note_p0", "P0"), ("note_p2", "P2")):
        out[key] = str(
            db.execute(
                "INSERT INTO note (title, body, privacy_tier, created_by) "
                "VALUES (%s, 'body text', %s, %s) RETURNING id",
                (key, tier, owner),
            ).fetchone()[0]
        )
    out["artifact"] = str(
        db.execute(
            """
            INSERT INTO artifact (title, artifact_type, storage_ref, mime_type,
                                  byte_size, checksum, extraction_status,
                                  privacy_tier, created_by)
            VALUES ('doc.md', 'document', 'k1', 'text/markdown', 5, 'chk-1',
                    'extracted', 'P0', %s) RETURNING id
            """,
            (owner,),
        ).fetchone()[0]
    )
    claim = db.execute(
        """
        INSERT INTO claim (subject_type, subject_id, predicate, statement,
                           confidence_tier, privacy_tier, created_by)
        VALUES ('Note', %s, 'mentions', 'a claim about the note',
                'self_reported', 'P0', %s) RETURNING id
        """,
        (out["note_p0"], owner),
    ).fetchone()[0]
    out["claim"] = str(claim)
    return out


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
def client(db: "psycopg.Connection", ids: dict[str, str]) -> Iterator["TestClient"]:
    settings = Settings(  # type: ignore[call-arg]
        env="local", database_url=DB_URL, oidc_issuer=ISSUER, oidc_audience=AUDIENCE
    )
    verifier = TokenVerifier(
        issuer=ISSUER, audience=AUDIENCE, key_provider=lambda _t: KEY.public_key()
    )
    with TestClient(create_app(settings, verifier=verifier)) as test_client:
        yield test_client


def get(client: "TestClient", path: str, sub: str | None = None) -> Any:
    headers = {"User-Agent": "content-tests"}
    if sub:
        headers["Authorization"] = f"Bearer {oidc_token(sub)}"
    return client.get(path, headers=headers)


def test_public_sees_only_p0_notes(client: "TestClient", ids: dict) -> None:
    body = get(client, "/v1/notes").json()
    listed = {item["id"] for item in body["data"]}
    assert ids["note_p0"] in listed
    assert ids["note_p2"] not in listed


def test_owner_sees_all_notes(client: "TestClient", ids: dict) -> None:
    body = get(client, "/v1/notes", "content-owner").json()
    listed = {item["id"] for item in body["data"]}
    assert {ids["note_p0"], ids["note_p2"]} <= listed


def test_above_ceiling_and_missing_are_identical(client: "TestClient", ids: dict) -> None:
    headers = {"User-Agent": "content-tests", "X-Request-ID": "content-leak"}
    above = client.get(f"/v1/notes/{ids['note_p2']}", headers=headers)
    missing = client.get(f"/v1/notes/{uuid.uuid4()}", headers=headers)
    assert above.status_code == missing.status_code == 404
    assert above.json() == missing.json()


def test_detail_carries_provenance_block(client: "TestClient", ids: dict) -> None:
    body = get(client, f"/v1/notes/{ids['note_p0']}").json()
    assert body["body"] == "body text"
    claims = body["provenance"]["claims"]
    assert len(claims) == 1
    assert claims[0]["claim_id"] == ids["claim"]
    assert claims[0]["tier"] == "self_reported"


def test_artifact_collection_reads(client: "TestClient", ids: dict) -> None:
    listing = get(client, "/v1/artifacts").json()
    assert any(item["id"] == ids["artifact"] for item in listing["data"])
    detail = get(client, f"/v1/artifacts/{ids['artifact']}").json()
    assert detail["extraction_status"] == "extracted"
    assert "provenance" in detail


def test_unknown_collection_is_not_found(client: "TestClient") -> None:
    assert get(client, "/v1/journals").status_code == 404
    assert get(client, "/v1/journals").json()["error"]["code"] == "not_found"
