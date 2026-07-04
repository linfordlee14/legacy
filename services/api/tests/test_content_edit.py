"""Revision history and soft delete tests (MVP-015; BUILD_ORDER step 15).

Acceptance: an edit produces a revision; delete is reversible (undo works);
the NFR-022 data-layer test passes (deletion is soft by default, permanent
erasure only through the redaction workflow). Plus: tier changes demand the
explicit sub-action with step-up, revisions are owner-only and immutable,
mutations are audited and honor Idempotency-Key, and no path leaks
existence. Requires LEGACY_TEST_DATABASE_URL; skipped when unset.
"""

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


def auth(sub: str = "edit-owner", auth_age_s: int = 0) -> dict[str, str]:
    return {"Authorization": f"Bearer {oidc_token(sub, auth_age_s)}", "User-Agent": "edit"}


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
        for sub, owner in (("edit-owner", True), ("edit-other", False)):
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


def note_id_of(client: "TestClient", body: str = "first draft") -> str:
    response = client.post(
        "/v1/ingestion/jobs",
        files=[],
        data={"payload": json.dumps({"notes": [{"title": "note", "body": body}]})},
        headers=auth(),
    )
    assert response.status_code == 201
    job = client.get(f"/v1/ingestion/jobs/{response.json()['id']}", headers=auth()).json()
    return str(job["items"][0]["note_id"])


def revisions_of(client: "TestClient", note_id: str) -> list[dict[str, Any]]:
    response = client.get(f"/v1/notes/{note_id}/revisions", headers=auth())
    assert response.status_code == 200
    return list(response.json()["data"])


def test_edit_produces_a_revision(client: "TestClient", db: "psycopg.Connection") -> None:
    note_id = note_id_of(client, body="the original body")
    response = client.patch(
        f"/v1/notes/{note_id}", json={"body": "the corrected body"}, headers=auth()
    )
    assert response.status_code == 200
    assert response.json()["body"] == "the corrected body"
    assert "provenance" in response.json()

    revisions = revisions_of(client, note_id)
    assert len(revisions) == 1
    assert revisions[0]["change_kind"] == "update"
    assert revisions[0]["snapshot"]["body"] == "the original body"
    assert revisions[0]["snapshot"]["privacy_tier"] == "P2"
    assert revisions[0]["row_version"] == 1

    # A second edit preserves the second version, newest first.
    client.patch(f"/v1/notes/{note_id}", json={"title": "renamed"}, headers=auth())
    revisions = revisions_of(client, note_id)
    assert [r["row_version"] for r in revisions] == [2, 1]
    assert revisions[0]["snapshot"]["body"] == "the corrected body"

    audit = db.execute(
        "SELECT count(*) FROM audit_log_entry WHERE action = 'update' "
        "AND subject_type = 'Note' AND subject_id = %s",
        (note_id,),
    ).fetchone()[0]
    assert audit == 2


def test_delete_is_soft_and_reversible(
    client: "TestClient", db: "psycopg.Connection"
) -> None:
    note_id = note_id_of(client, body="do not lose me")

    deleted = client.delete(f"/v1/notes/{note_id}", headers=auth())
    assert deleted.status_code == 204

    # NFR-022 data layer: the row and its content survive; only the marker set.
    row = db.execute(
        "SELECT body, deleted_at FROM note WHERE id = %s", (note_id,)
    ).fetchone()
    assert row is not None
    assert row[0] == "do not lose me"
    assert row[1] is not None

    # Hidden from every default read path immediately (4.8).
    assert client.get(f"/v1/notes/{note_id}", headers=auth()).status_code == 404
    listed = client.get("/v1/notes?limit=100", headers=auth()).json()["data"]
    assert note_id not in {item["id"] for item in listed}

    # Undo works: restore brings it back, byte-identical.
    restored = client.post(f"/v1/notes/{note_id}/restore", headers=auth())
    assert restored.status_code == 200
    assert restored.json()["body"] == "do not lose me"
    assert client.get(f"/v1/notes/{note_id}", headers=auth()).status_code == 200

    # Restoring a live row is a conflict, and both actions were audited.
    assert client.post(f"/v1/notes/{note_id}/restore", headers=auth()).status_code == 409
    actions = [
        r[0]
        for r in db.execute(
            "SELECT action FROM audit_log_entry WHERE subject_id = %s "
            "AND action IN ('soft_delete', 'restore') ORDER BY sequence_number",
            (note_id,),
        ).fetchall()
    ]
    assert actions == ["soft_delete", "restore"]


def test_no_hard_delete_path_exists(client: "TestClient", db: "psycopg.Connection") -> None:
    """NFR-022: permanent erasure only through the (post-MVP) redaction
    workflow; the DELETE endpoint never removes rows."""
    note_id = note_id_of(client, body="counted")
    before = db.execute("SELECT count(*) FROM note").fetchone()[0]
    client.delete(f"/v1/notes/{note_id}", headers=auth())
    assert db.execute("SELECT count(*) FROM note").fetchone()[0] == before


def test_tier_change_requires_subaction_and_step_up(
    client: "TestClient", db: "psycopg.Connection"
) -> None:
    note_id = note_id_of(client, body="tiered")

    # Plain PATCH may not move tiers.
    refused = client.patch(
        f"/v1/notes/{note_id}", json={"privacy_tier": "P1"}, headers=auth()
    )
    assert refused.status_code == 422

    # Stale authentication is refused (AUTHENTICATION 4.3 step-up).
    stale = client.patch(
        f"/v1/notes/{note_id}",
        json={"action": "tier_change", "privacy_tier": "P1"},
        headers=auth(auth_age_s=3600),
    )
    assert stale.status_code == 401

    # P3 is a seal, not a tier change.
    sealed = client.patch(
        f"/v1/notes/{note_id}",
        json={"action": "tier_change", "privacy_tier": "P3"},
        headers=auth(),
    )
    assert sealed.status_code == 422

    changed = client.patch(
        f"/v1/notes/{note_id}",
        json={"action": "tier_change", "privacy_tier": "P1"},
        headers=auth(),
    )
    assert changed.status_code == 200
    assert changed.json()["privacy_tier"] == "P1"

    revisions = revisions_of(client, note_id)
    assert revisions[0]["change_kind"] == "tier_change"
    assert revisions[0]["snapshot"]["privacy_tier"] == "P2"
    audit = db.execute(
        "SELECT count(*) FROM audit_log_entry WHERE action = 'tier_change' "
        "AND subject_id = %s",
        (note_id,),
    ).fetchone()[0]
    assert audit == 1


def test_revisions_are_owner_only_and_immutable(
    client: "TestClient", db: "psycopg.Connection"
) -> None:
    note_id = note_id_of(client, body="private history")
    client.patch(f"/v1/notes/{note_id}", json={"body": "edited"}, headers=auth())

    denied = client.get(f"/v1/notes/{note_id}/revisions", headers=auth("edit-other"))
    assert denied.status_code == 403

    # The database guard blocks updates and deletes outside redaction.
    revision_id = db.execute(
        "SELECT id FROM revision WHERE entity_id = %s", (note_id,)
    ).fetchone()[0]
    with pytest.raises(psycopg.errors.RaiseException):
        db.execute("DELETE FROM revision WHERE id = %s", (revision_id,))
    with pytest.raises(psycopg.errors.RaiseException):
        db.execute(
            "UPDATE revision SET snapshot = '{}'::jsonb WHERE id = %s", (revision_id,)
        )


def test_edits_do_not_leak_existence(client: "TestClient") -> None:
    missing = str(uuid.uuid4())
    for method, path in (
        ("patch", f"/v1/notes/{missing}"),
        ("delete", f"/v1/notes/{missing}"),
        ("post", f"/v1/notes/{missing}/restore"),
    ):
        response = getattr(client, method)(
            path, headers=auth(),
            **({"json": {"body": "x"}} if method == "patch" else {}),
        )
        assert response.status_code == 404, (method, path)
        assert response.json()["error"]["code"] == "not_found"

    # A non-owner gets the same 404 for a real P2 note (above ceiling).
    note_id = note_id_of(client, body="above your ceiling")
    other = client.patch(
        f"/v1/notes/{note_id}", json={"body": "x"}, headers=auth("edit-other")
    )
    assert other.status_code == 404
    assert other.json()["error"]["code"] == "not_found"


def test_validation_refuses_unknown_and_empty(client: "TestClient") -> None:
    note_id = note_id_of(client, body="strict")
    unknown = client.patch(
        f"/v1/notes/{note_id}", json={"artifact_type": "x"}, headers=auth()
    )
    assert unknown.status_code == 422
    empty = client.patch(f"/v1/notes/{note_id}", json={}, headers=auth())
    assert empty.status_code == 422


def test_idempotency_key_replays(client: "TestClient", db: "psycopg.Connection") -> None:
    note_id = note_id_of(client, body="idempotent")
    key = uuid.uuid4().hex
    first = client.patch(
        f"/v1/notes/{note_id}", json={"body": "edited once"},
        headers={**auth(), "Idempotency-Key": key},
    )
    assert first.status_code == 200
    replay = client.patch(
        f"/v1/notes/{note_id}", json={"body": "edited once"},
        headers={**auth(), "Idempotency-Key": key},
    )
    assert replay.status_code == 200
    assert replay.headers.get("Idempotency-Replayed") == "true"
    # The retry did not run again: exactly one revision was written.
    count = db.execute(
        "SELECT count(*) FROM revision WHERE entity_id = %s", (note_id,)
    ).fetchone()[0]
    assert count == 1


def test_artifact_edit_and_undo(client: "TestClient", db: "psycopg.Connection") -> None:
    upload = client.post(
        "/v1/ingestion/jobs",
        files=[("files", ("essay.md", b"# Draft\n\nraw text", "text/markdown"))],
        data={"payload": "{}"},
        headers=auth(),
    )
    assert upload.status_code == 201
    job = client.get(f"/v1/ingestion/jobs/{upload.json()['id']}", headers=auth()).json()
    artifact_id = str(job["items"][0]["artifact_id"])

    edited = client.patch(
        f"/v1/artifacts/{artifact_id}",
        json={"canonical_markdown": "# Draft\n\ncorrected extraction"},
        headers=auth(),
    )
    assert edited.status_code == 200
    revisions = client.get(
        f"/v1/artifacts/{artifact_id}/revisions", headers=auth()
    ).json()["data"]
    assert revisions[0]["snapshot"]["canonical_markdown"] == "# Draft\n\nraw text"

    # The stored original is untouched by the edit (FR-DATA-003).
    storage_ref = db.execute(
        "SELECT storage_ref FROM artifact WHERE id = %s", (artifact_id,)
    ).fetchone()[0]
    assert client.app.state.storage.get(storage_ref) == b"# Draft\n\nraw text"  # type: ignore[attr-defined]

    assert client.delete(f"/v1/artifacts/{artifact_id}", headers=auth()).status_code == 204
    assert (
        client.post(f"/v1/artifacts/{artifact_id}/restore", headers=auth()).status_code
        == 200
    )
