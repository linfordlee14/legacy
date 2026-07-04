"""Owner document batch import tests (MVP-014; BUILD_ORDER step 14).

The batch completes with per-item statuses, failures become review flags
(never silent), originals are preserved byte-identical, every artifact
carries ingestion provenance, re-runs dedup by checksum, every run is
audited, and the corpus is listed in the workspace.
Requires LEGACY_TEST_DATABASE_URL; skipped when unset.
"""

import asyncio
import hashlib
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
    from legacy_api.db import create_pool
    from legacy_api.main import create_app
    from legacy_api.seed.documents import import_documents
    from legacy_api.storage import LocalObjectStorage
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
        conn.execute(
            """
            INSERT INTO app_user
                (email, display_name, user_kind, is_owner, auth_subject, created_by)
            VALUES ('docs-owner@example.test', 'docs-owner', 'human', true,
                    'docs-owner', %s)
            """,
            (SYSTEM_USER_ID,),
        )
        yield conn


@pytest.fixture(scope="module")
def storage_dir(tmp_path_factory: Any) -> Path:
    return tmp_path_factory.mktemp("objects")


@pytest.fixture(scope="module")
def corpus(tmp_path_factory: Any) -> Path:
    """An owner-document tree exercising every pipeline outcome."""
    from pypdf import PdfWriter

    root = tmp_path_factory.mktemp("corpus")
    (root / "readme.md").write_bytes(b"# Seed corpus\n\nThe owner's writing.")
    (root / "notes").mkdir()
    (root / "notes" / "plan.txt").write_bytes(b"Plans for Linfy Academy.")
    buffer = io.BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.write(buffer)
    (root / "deck.pdf").write_bytes(buffer.getvalue())
    (root / "broken.pdf").write_bytes(b"%PDF-1.4 not actually a pdf")
    (root / "photo.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 32)
    (root / "empty.txt").write_bytes(b"")
    (root / ".git").mkdir()
    (root / ".git" / "config").write_bytes(b"[core]")
    (root / ".DS_Store").write_bytes(b"junk")
    return root


def run_batch(
    storage_dir: Path,
    paths: list[Path],
    *,
    tier: str | None = None,
    extensions: set[str] | None = None,
) -> dict[str, Any]:
    async def _run() -> dict[str, Any]:
        pool = create_pool(DB_URL)
        await pool.open()
        try:
            return await import_documents(
                pool, LocalObjectStorage(storage_dir), paths,
                tier=tier, extensions=extensions,
            )
        finally:
            await pool.close()

    return asyncio.run(_run())


@pytest.fixture(scope="module")
def first_run(
    db: "psycopg.Connection", storage_dir: Path, corpus: Path
) -> dict[str, Any]:
    return run_batch(storage_dir, [corpus])


def artifact_count(db: "psycopg.Connection") -> int:
    return db.execute(
        "SELECT count(*) FROM artifact WHERE deleted_at IS NULL"
    ).fetchone()[0]


def test_batch_completes_with_per_item_statuses(
    db: "psycopg.Connection", corpus: Path, first_run: dict[str, Any]
) -> None:
    # md, txt, blank pdf, and png store; the broken pdf is a review flag.
    assert first_run["item_count"] == 5
    assert first_run["by_status"] == {"stored": 4, "review": 1}
    assert first_run["status"] == "review"  # failures are loud, not silent
    assert first_run["needs_review"] == [f"{corpus.name}/broken.pdf"]
    assert first_run["skipped"] == [{"name": f"{corpus.name}/empty.txt", "reason": "empty"}]
    row = db.execute(
        "SELECT job_type, status, source_descriptor FROM ingestion_job WHERE id = %s",
        (first_run["job_id"],),
    ).fetchone()
    assert row[0] == "bulk_import"
    assert row[1] == "review"
    assert row[2]["kind"] == "owner_document_batch"
    # VCS internals and hidden files were excluded (.git/config, .DS_Store).
    assert first_run["excluded_count"] == 2


def test_originals_preserved_with_provenance(
    db: "psycopg.Connection", storage_dir: Path, corpus: Path, first_run: dict[str, Any]
) -> None:
    original = (corpus / "readme.md").read_bytes()
    rows = db.execute(
        """
        SELECT title, storage_ref, checksum, privacy_tier,
               origin_type, origin_ref_type, origin_ref_id::text, extraction_status
        FROM artifact WHERE origin_ref_id = %s ORDER BY title
        """,
        (first_run["job_id"],),
    ).fetchall()
    # All five files persist as artifacts, including the review-flagged one:
    # preservation before parsing means failures never lose the original.
    assert len(rows) == 5
    for row in rows:
        assert row[3] == "P2"  # default tier (never invented, never upgraded)
        assert row[4] == "ingestion" and row[5] == "IngestionJob"
        assert row[6] == first_run["job_id"]
    readme = next(row for row in rows if row[0].endswith("readme.md"))
    storage = LocalObjectStorage(storage_dir)
    assert storage.get(readme[1]) == original  # byte-identical original
    assert readme[2] == hashlib.sha256(original).hexdigest()
    png = next(row for row in rows if row[0].endswith("photo.png"))
    assert png[7] == "not_applicable"  # preserved, extraction deferred post-MVP
    broken = next(row for row in rows if row[0].endswith("broken.pdf"))
    assert broken[7] == "failed"  # original kept; the flag awaits the owner
    assert storage.get(broken[1]) == (corpus / "broken.pdf").read_bytes()


def test_rerun_is_idempotent_and_audited(
    db: "psycopg.Connection", storage_dir: Path, corpus: Path, first_run: dict[str, Any]
) -> None:
    before = artifact_count(db)
    second = run_batch(storage_dir, [corpus])
    assert artifact_count(db) == before  # checksum dedup: no duplicate rows
    # Everything dedups, including the review-flagged artifact (its original
    # was preserved in run one; its review flag lives on that job's record).
    assert second["by_status"] == {"duplicate": 5}
    assert second["status"] == "complete"
    # Every run is recorded: its own job and its own audit entry.
    assert second["job_id"] != first_run["job_id"]
    audits = db.execute(
        "SELECT count(*) FROM audit_log_entry WHERE action = 'seed_import' "
        "AND payload_summary ->> 'seed' = 'owner_document_batch'"
    ).fetchone()[0]
    assert audits == 2


def test_extension_filter_limits_the_batch(
    db: "psycopg.Connection", storage_dir: Path, corpus: Path, first_run: dict[str, Any]
) -> None:
    summary = run_batch(storage_dir, [corpus], extensions={".md"})
    assert summary["item_count"] == 1
    assert summary["by_status"] == {"duplicate": 1}  # readme.md already ingested


def test_tier_applies_to_the_whole_batch(
    db: "psycopg.Connection", storage_dir: Path, tmp_path_factory: Any,
    first_run: dict[str, Any],
) -> None:
    root = tmp_path_factory.mktemp("trusted")
    (root / "cv.md").write_bytes(b"# CV\n\nShareable with trusted contacts.")
    summary = run_batch(storage_dir, [root], tier="P1")
    row = db.execute(
        "SELECT privacy_tier FROM artifact WHERE origin_ref_id = %s",
        (summary["job_id"],),
    ).fetchone()
    assert row[0] == "P1"
    with pytest.raises(ValueError):
        run_batch(storage_dir, [root], tier="P9")


def test_corpus_is_listed_in_the_workspace(
    db: "psycopg.Connection", corpus: Path, first_run: dict[str, Any],
    tmp_path_factory: Any,
) -> None:
    settings = Settings(  # type: ignore[call-arg]
        env="local",
        database_url=DB_URL,
        oidc_issuer=ISSUER,
        oidc_audience=AUDIENCE,
        storage_dir=str(tmp_path_factory.mktemp("app-objects")),
    )
    verifier = TokenVerifier(
        issuer=ISSUER, audience=AUDIENCE, key_provider=lambda _t: KEY.public_key()
    )
    with TestClient(create_app(settings, verifier=verifier)) as client:
        response = client.get(
            "/v1/artifacts?limit=100",
            headers={"Authorization": f"Bearer {oidc_token('docs-owner')}", "User-Agent": "t"},
        )
        assert response.status_code == 200
        titles = {item["title"] for item in response.json()["data"]}
    # The whole batch is listed, including the review-flagged item (its
    # extraction_status marks it failed; the original is never hidden).
    for name in ("readme.md", "notes/plan.txt", "deck.pdf", "photo.png", "broken.pdf"):
        assert f"{corpus.name}/{name}" in titles


def test_missing_path_is_loud(storage_dir: Path, db: "psycopg.Connection") -> None:
    with pytest.raises(ValueError, match="does not exist"):
        run_batch(storage_dir, [Path("/nonexistent/owner-docs")])


def test_summary_is_json_serializable(first_run: dict[str, Any]) -> None:
    json.dumps(first_run)  # the CLI prints exactly this
