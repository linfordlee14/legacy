"""Ingestion pipeline tests (MVP-010; FS-001; FR-ING-001, 007, 008).

Document and note scenarios, checksum dedup, review flags with preserved
originals, retry, provenance, authorization, and idempotency.
Requires LEGACY_TEST_DATABASE_URL; skipped when unset.
"""

import io
import json
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
        for sub, owner in (("ing-owner", True), ("ing-human", False)):
            conn.execute(
                """
                INSERT INTO app_user
                    (email, display_name, user_kind, is_owner, auth_subject, created_by)
                VALUES (%s, %s, 'human', %s, %s, %s)
                """,
                (f"{sub}@example.test", sub, owner, sub, SYSTEM_USER_ID),
            )
        yield conn


@pytest.fixture(scope="module")
def client(db: "psycopg.Connection", tmp_path_factory: Any) -> Iterator["TestClient"]:
    settings = Settings(  # type: ignore[call-arg]
        env="local",
        database_url=DB_URL,
        oidc_issuer=ISSUER,
        oidc_audience=AUDIENCE,
        storage_dir=str(tmp_path_factory.mktemp("objects")),
    )
    verifier = TokenVerifier(
        issuer=ISSUER, audience=AUDIENCE, key_provider=lambda _t: KEY.public_key()
    )
    with TestClient(create_app(settings, verifier=verifier)) as test_client:
        yield test_client


def post_job(
    client: "TestClient",
    *,
    sub: str = "ing-owner",
    files: list[tuple[str, bytes, str]] | None = None,
    payload: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> Any:
    request_headers = {"Authorization": f"Bearer {oidc_token(sub)}", "User-Agent": "ing"}
    request_headers.update(headers or {})
    return client.post(
        "/v1/ingestion/jobs",
        files=[("files", (name, data, mime)) for name, data, mime in (files or [])],
        data={"payload": json.dumps(payload or {})},
        headers=request_headers,
    )


def artifact_count(db: "psycopg.Connection") -> int:
    return db.execute(
        "SELECT count(*) FROM artifact WHERE deleted_at IS NULL"
    ).fetchone()[0]


def test_note_batch_ingests_with_provenance_and_tiers(
    client: "TestClient", db: "psycopg.Connection"
) -> None:
    response = post_job(
        client,
        payload={
            "notes": [
                {"title": "plain", "body": "a captured thought"},
                {"title": "shared", "body": "a P1 note", "privacy_tier": "P1"},
            ]
        },
    )
    assert response.status_code == 201
    job = response.json()
    final = client.get(
        f"/v1/ingestion/jobs/{job['id']}",
        headers={"Authorization": f"Bearer {oidc_token('ing-owner')}", "User-Agent": "ing"},
    ).json()
    assert final["status"] == "complete"
    assert final["progress_percent"] == 100
    assert final["items_created"]["Note"] == 2
    assert all("body" not in item for item in final["items"])

    rows = db.execute(
        """
        SELECT privacy_tier, origin_type, origin_ref_type, origin_ref_id::text
        FROM note WHERE origin_ref_id = %s ORDER BY privacy_tier
        """,
        (job["id"],),
    ).fetchall()
    assert [r[0] for r in rows] == ["P1", "P2"]
    assert all(r[1] == "ingestion" and r[2] == "IngestionJob" for r in rows)


def test_document_upload_extracts_and_preserves_original(
    client: "TestClient", db: "psycopg.Connection"
) -> None:
    content = b"# Field Notes\n\nRhinos observed at dawn."
    started = time.monotonic()
    response = post_job(client, files=[("notes.md", content, "text/markdown")])
    assert response.status_code == 201
    elapsed = time.monotonic() - started
    assert elapsed < 30  # provisional NFR-005 stand-in until search exists

    job = response.json()
    row = db.execute(
        """
        SELECT storage_ref, canonical_markdown, extraction_status, byte_size, checksum
        FROM artifact WHERE origin_ref_id = %s
        """,
        (job["id"],),
    ).fetchone()
    assert row[1] == content.decode()
    assert row[2] == "extracted"
    assert row[3] == len(content)

    storage = client.app.state.storage  # type: ignore[attr-defined]
    assert storage.get(row[0]) == content  # original preserved byte-identical


def test_blank_pdf_stores_with_partial_extraction(
    client: "TestClient", db: "psycopg.Connection"
) -> None:
    from pypdf import PdfWriter

    buffer = io.BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.write(buffer)

    response = post_job(client, files=[("blank.pdf", buffer.getvalue(), "application/pdf")])
    job_id = response.json()["id"]
    status, extraction = db.execute(
        """
        SELECT j.status, a.extraction_status
        FROM ingestion_job j JOIN artifact a ON a.origin_ref_id = j.id
        WHERE j.id = %s
        """,
        (job_id,),
    ).fetchone()
    assert status == "complete"
    assert extraction == "partial"


def test_duplicate_upload_dedups_by_checksum(
    client: "TestClient", db: "psycopg.Connection"
) -> None:
    content = b"identical bytes for dedup"
    first = post_job(client, files=[("one.txt", content, "text/plain")])
    assert first.status_code == 201
    before = artifact_count(db)

    second = post_job(client, files=[("two.txt", content, "text/plain")])
    job = client.get(
        f"/v1/ingestion/jobs/{second.json()['id']}",
        headers={"Authorization": f"Bearer {oidc_token('ing-owner')}", "User-Agent": "ing"},
    ).json()
    item = job["items"][0]
    assert item["status"] == "duplicate"
    assert item["duplicate_of"]
    assert job["items_created"]["duplicates"] == 1
    assert artifact_count(db) == before  # no second artifact row


def test_corrupt_file_becomes_review_flag_with_original_preserved(
    client: "TestClient", db: "psycopg.Connection"
) -> None:
    garbage = b"%PDF-1.7 this is not really a pdf at all"
    response = post_job(client, files=[("broken.pdf", garbage, "application/pdf")])
    job = client.get(
        f"/v1/ingestion/jobs/{response.json()['id']}",
        headers={"Authorization": f"Bearer {oidc_token('ing-owner')}", "User-Agent": "ing"},
    ).json()
    assert job["status"] == "review"
    item = job["items"][0]
    assert item["status"] == "review"
    assert item["reason"] == "extraction_failed"

    row = db.execute(
        "SELECT storage_ref, extraction_status FROM artifact WHERE id = %s",
        (item["artifact_id"],),
    ).fetchone()
    assert row[1] == "failed"
    storage = client.app.state.storage  # type: ignore[attr-defined]
    assert storage.get(row[0]) == garbage


def test_retry_reprocesses_review_items(client: "TestClient") -> None:
    garbage = b"%PDF-1.7 still broken bytes"
    created = post_job(client, files=[("again.pdf", garbage, "application/pdf")])
    job_id = created.json()["id"]
    headers = {"Authorization": f"Bearer {oidc_token('ing-owner')}", "User-Agent": "ing"}

    retried = client.post(f"/v1/ingestion/jobs/{job_id}/retry", headers=headers)
    assert retried.status_code == 200
    body = retried.json()
    assert body["status"] == "review"  # same bytes, same honest outcome
    assert body["items"][0]["reason"] == "extraction_failed"

    complete_job = post_job(client, payload={"notes": [{"body": "fine"}]}).json()
    conflict = client.post(
        f"/v1/ingestion/jobs/{complete_job['id']}/retry", headers=headers
    )
    assert conflict.status_code == 409


def test_unsupported_binary_stores_as_not_applicable(
    client: "TestClient", db: "psycopg.Connection"
) -> None:
    response = post_job(client, files=[("blob.bin", b"\x00\x01\x02", "application/octet-stream")])
    job_id = response.json()["id"]
    status, extraction = db.execute(
        """
        SELECT j.status, a.extraction_status
        FROM ingestion_job j JOIN artifact a ON a.origin_ref_id = j.id
        WHERE j.id = %s
        """,
        (job_id,),
    ).fetchone()
    assert status == "complete"
    assert extraction == "not_applicable"


def test_validation_rules(client: "TestClient") -> None:
    empty = post_job(client)
    assert empty.status_code == 422
    bad_tier = post_job(
        client, payload={"notes": [{"body": "x", "privacy_tier": "P9"}]}
    )
    assert bad_tier.status_code == 422
    bodyless = post_job(client, payload={"notes": [{"title": "no body"}]})
    assert bodyless.status_code == 422


def test_authorization_matrix(client: "TestClient") -> None:
    denied = post_job(client, sub="ing-human", payload={"notes": [{"body": "x"}]})
    assert denied.status_code == 403

    unauth = client.post(
        "/v1/ingestion/jobs", data={"payload": "{}"}, headers={"User-Agent": "ing"}
    )
    assert unauth.status_code == 401

    owner_headers = {"Authorization": f"Bearer {oidc_token('ing-owner')}", "User-Agent": "ing"}
    writer_pat = client.post(
        "/v1/auth/tokens",
        json={"label": "writer", "scopes": ["read:private", "write:content"]},
        headers=owner_headers,
    ).json()["token"]
    reader_pat = client.post(
        "/v1/auth/tokens",
        json={"label": "reader", "scopes": ["read:public"]},
        headers=owner_headers,
    ).json()["token"]

    machine_ok = client.post(
        "/v1/ingestion/jobs",
        data={"payload": json.dumps({"notes": [{"body": "from machine"}]})},
        headers={"Authorization": f"Bearer {writer_pat}", "User-Agent": "ing"},
    )
    assert machine_ok.status_code == 201

    machine_denied = client.post(
        "/v1/ingestion/jobs",
        data={"payload": json.dumps({"notes": [{"body": "nope"}]})},
        headers={"Authorization": f"Bearer {reader_pat}", "User-Agent": "ing"},
    )
    assert machine_denied.status_code == 403

    list_denied = client.get(
        "/v1/ingestion/jobs",
        headers={"Authorization": f"Bearer {oidc_token('ing-human')}", "User-Agent": "ing"},
    )
    assert list_denied.status_code == 403


def test_idempotency_replay_on_job_creation(
    client: "TestClient", db: "psycopg.Connection"
) -> None:
    payload = {"notes": [{"body": "idempotent capture"}]}
    key = {"Idempotency-Key": "ing-k1"}
    first = post_job(client, payload=payload, headers=key)
    replay = post_job(client, payload=payload, headers=key)
    assert first.json()["id"] == replay.json()["id"]
    assert replay.headers["Idempotency-Replayed"] == "true"
    count = db.execute(
        "SELECT count(*) FROM note WHERE body = 'idempotent capture'"
    ).fetchone()[0]
    assert count == 1

    mismatch = post_job(
        client, payload={"notes": [{"body": "different"}]}, headers=key
    )
    assert mismatch.status_code == 409


def test_job_listing_pagination(client: "TestClient") -> None:
    headers = {"Authorization": f"Bearer {oidc_token('ing-owner')}", "User-Agent": "ing"}
    listing = client.get("/v1/ingestion/jobs", params={"limit": 3}, headers=headers).json()
    assert len(listing["data"]) == 3
    assert listing["next_cursor"]
