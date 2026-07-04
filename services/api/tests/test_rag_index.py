"""Chunk store and retrieval tests (MVP-016; BUILD_ORDER step 16).

Acceptance: stored content is chunked and indexed with tier and provenance
metadata on every chunk row (RAG-05), the rebuild-from-source drill passes
(NFR-024), re-index is idempotent (RAG-03), tier changes propagate
synchronously (RAG-32), soft-deleted parents drop out of retrieval
immediately, tier predicates apply inside the store (RAG-12), versions are
never compared (AIA-11), and embedding outages queue instead of degrading
(RAG-08). Requires LEGACY_TEST_DATABASE_URL; skipped when unset.
"""

import asyncio
import hashlib
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

    from legacy_api.ai.router import EmbeddingUnavailable, ModelRouter
    from legacy_api.config import Settings
    from legacy_api.main import create_app
    from legacy_api.rag.indexer import index_entity, index_entity_or_queue
    from legacy_api.rag.reindex import reindex_all
    from legacy_api.rag.retrieval import lexical_search, vector_search
    from legacy_api.verifier import TokenVerifier

API_DIR = Path(__file__).resolve().parent.parent
SYSTEM_USER_ID = "00000000-0000-7000-8000-000000000001"
ISSUER = "https://auth.test.invalid"
AUDIENCE = "legacy-api"
KEY = None
ACTIVE_VERSION = "gemini-embedding-001:1536"


class FakeEmbedding:
    """Deterministic provider double injected behind the Model Router; the
    router seam is exercised, only the network call is replaced."""

    name = "fake"
    model = "gemini-embedding-001"
    dimensions = 1536

    def __init__(self) -> None:
        self.calls: list[tuple[str, list[str]]] = []
        self.fail_next = 0

    async def embed(self, texts: list[str], task_type: str) -> list[list[float]]:
        if self.fail_next > 0:
            self.fail_next -= 1
            raise RuntimeError("transient provider error")
        self.calls.append((task_type, list(texts)))
        return [self._vector(text) for text in texts]

    def _vector(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode()).digest()
        return [(digest[i % 32] + 1) / 256.0 for i in range(self.dimensions)]


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


def auth() -> dict[str, str]:
    return {"Authorization": f"Bearer {oidc_token('rag-owner')}", "User-Agent": "rag"}


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
            VALUES ('rag-owner@example.test', 'rag-owner', 'human', true,
                    'rag-owner', %s)
            """,
            (SYSTEM_USER_ID,),
        )
        yield conn


@pytest.fixture(scope="module")
def provider() -> "FakeEmbedding":
    return FakeEmbedding()


@pytest.fixture(scope="module")
def client(
    db: "psycopg.Connection", provider: "FakeEmbedding", tmp_path_factory: Any
) -> Iterator["TestClient"]:
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
    app = create_app(settings, verifier=verifier, embedding_provider=provider)
    with TestClient(app) as test_client:
        yield test_client


def run(coro: Any) -> Any:
    return asyncio.run(coro)


async def _with_conn(fn: Any, *args: Any) -> Any:
    conn = await psycopg.AsyncConnection.connect(DB_URL)
    try:
        result = await fn(conn, *args)
        await conn.commit()
        return result
    finally:
        await conn.close()


def make_note(client: "TestClient", body: str) -> str:
    response = client.post(
        "/v1/ingestion/jobs",
        files=[],
        data={"payload": json.dumps({"notes": [{"title": "note", "body": body}]})},
        headers=auth(),
    )
    assert response.status_code == 201
    job = client.get(f"/v1/ingestion/jobs/{response.json()['id']}", headers=auth()).json()
    return str(job["items"][0]["note_id"])


def chunk_rows(db: "psycopg.Connection", entity_id: str) -> list[tuple[Any, ...]]:
    return db.execute(
        """
        SELECT chunk_index, chunk_text, token_count, content_hash, heading_path,
               privacy_tier, embedding_model_version, injection_flag,
               origin_type, superseded_by
        FROM embedding_chunk WHERE entity_id = %s AND superseded_by IS NULL
        ORDER BY chunk_index
        """,
        (entity_id,),
    ).fetchall()


def test_ingested_note_is_chunked_with_full_provenance(
    client: "TestClient", db: "psycopg.Connection"
) -> None:
    note_id = make_note(client, "# Rhinos\n\nRhinos were observed at dawn near the river.")
    rows = chunk_rows(db, note_id)
    assert rows, "ingestion must index stored notes on the same pass (RAG-08)"
    for index, row in enumerate(rows):
        assert row[0] == index
        assert row[2] > 0  # token_count
        assert row[3] == hashlib.sha256(row[1].encode()).hexdigest()  # content hash
        assert row[5] == "P2"  # tier inherited from the parent (RAG-05)
        assert row[6] == ACTIVE_VERSION  # exact pinned version (AIA-07/11)
        assert row[7] is False  # injection_flag defaults false
        assert row[8] == "system"


def test_reindex_of_unchanged_source_is_a_noop(
    client: "TestClient", db: "psycopg.Connection", provider: "FakeEmbedding"
) -> None:
    note_id = make_note(client, "Unchanged content stays put.")
    before = chunk_rows(db, note_id)
    calls_before = len(provider.calls)
    router = ModelRouter(embedding_provider=provider)
    result = run(_with_conn(index_entity, router, "Note", note_id))
    assert result["status"] == "unchanged"  # RAG-03
    assert chunk_rows(db, note_id) == before
    assert len(provider.calls) == calls_before


def test_edit_supersedes_chunks_never_deletes(
    client: "TestClient", db: "psycopg.Connection"
) -> None:
    note_id = make_note(client, "First body about SpazaLink storefronts.")
    old_ids = {
        row[0]
        for row in db.execute(
            "SELECT id FROM embedding_chunk WHERE entity_id = %s", (note_id,)
        ).fetchall()
    }
    response = client.patch(
        f"/v1/notes/{note_id}",
        json={"body": "Second body about SpazaLink digital storefronts for traders."},
        headers=auth(),
    )
    assert response.status_code == 200
    live = chunk_rows(db, note_id)
    assert live and "Second body" in live[0][1]
    # The displaced generation is tombstoned, present, and points forward.
    tombstoned = db.execute(
        "SELECT count(*) FROM embedding_chunk WHERE id = ANY(%s) "
        "AND superseded_by IS NOT NULL",
        (list(old_ids),),
    ).fetchone()[0]
    assert tombstoned == len(old_ids)


def test_identical_content_reuses_cached_vectors(
    client: "TestClient", db: "psycopg.Connection", provider: "FakeEmbedding"
) -> None:
    body = "Cache-first embedding reuse is keyed by content hash."
    first = make_note(client, body)
    calls_before = len(provider.calls)
    second = make_note(client, body)
    assert first != second
    assert chunk_rows(db, second), "second note is indexed"
    # No new provider call: the vector came from the content-hash cache.
    assert len(provider.calls) == calls_before


def test_tier_change_propagates_to_chunks_synchronously(
    client: "TestClient", db: "psycopg.Connection"
) -> None:
    note_id = make_note(client, "Tier propagation body (RAG-32).")
    response = client.patch(
        f"/v1/notes/{note_id}",
        json={"action": "tier_change", "privacy_tier": "P1"},
        headers=auth(),
    )
    assert response.status_code == 200
    tiers = {row[5] for row in chunk_rows(db, note_id)}
    assert tiers == {"P1"}


def test_retrieval_filters_tier_in_store_and_hides_deleted(
    client: "TestClient", db: "psycopg.Connection", provider: "FakeEmbedding"
) -> None:
    note_id = make_note(client, "The kudu grazed beside the waterhole at sunset.")
    router = ModelRouter(embedding_provider=provider)

    async def searches(conn: Any, tiers: list[str]) -> tuple[Any, Any]:
        lexical = await lexical_search(conn, "kudu waterhole", tiers, ACTIVE_VERSION)
        vector = await vector_search(conn, router, "kudu waterhole", tiers)
        return lexical, vector

    lexical, vector = run(_with_conn(searches, ["P0", "P1", "P2"]))
    assert any(str(row["entity_id"]) == note_id for row in lexical)
    assert any(str(row["entity_id"]) == note_id for row in vector)

    # RAG-12: the tier predicate applies inside the store; a P0 ceiling
    # sees nothing.
    lexical_p0, vector_p0 = run(_with_conn(searches, ["P0"]))
    assert not any(str(row["entity_id"]) == note_id for row in lexical_p0)
    assert not any(str(row["entity_id"]) == note_id for row in vector_p0)

    # Soft-deleted parents drop out immediately (DATABASE_SCHEMA 4.8)...
    assert client.delete(f"/v1/notes/{note_id}", headers=auth()).status_code == 204
    lexical_deleted, vector_deleted = run(_with_conn(searches, ["P0", "P1", "P2"]))
    assert not any(str(row["entity_id"]) == note_id for row in lexical_deleted)
    assert not any(str(row["entity_id"]) == note_id for row in vector_deleted)

    # ...and restore brings them straight back (undo, MVP-015).
    client.post(f"/v1/notes/{note_id}/restore", headers=auth())
    lexical_back, _vector_back = run(_with_conn(searches, ["P0", "P1", "P2"]))
    assert any(str(row["entity_id"]) == note_id for row in lexical_back)


def test_versions_are_never_compared(
    client: "TestClient", db: "psycopg.Connection", provider: "FakeEmbedding"
) -> None:
    note_id = make_note(client, "Version isolation body for AIA-11.")
    # A row from a hypothetical older model version, different dimension.
    db.execute(
        """
        INSERT INTO embedding_chunk
            (entity_type, entity_id, chunk_index, chunk_text, token_count,
             content_hash, embedding, embedding_model_version, privacy_tier,
             created_by, origin_type)
        VALUES ('Note', %s, 0, 'Version isolation body for AIA-11.', 5,
                'oldhash', '[0.1,0.2,0.3]'::vector, 'old-model:3', 'P2', %s, 'system')
        """,
        (note_id, SYSTEM_USER_ID),
    )
    router = ModelRouter(embedding_provider=provider)

    async def searches(conn: Any) -> tuple[Any, Any]:
        lexical = await lexical_search(
            conn, "isolation", ["P0", "P1", "P2"], ACTIVE_VERSION
        )
        vector = await vector_search(conn, router, "isolation", ["P0", "P1", "P2"])
        return lexical, vector

    lexical, vector = run(_with_conn(searches))
    versions = {row["embedding_model_version"] for row in [*lexical, *vector]}
    assert versions <= {ACTIVE_VERSION}


def test_rebuild_from_source_drill(
    client: "TestClient", db: "psycopg.Connection", provider: "FakeEmbedding"
) -> None:
    """NFR-024: loss of the whole chunk store never loses knowledge."""
    make_note(client, "Rebuild drill content one, about conservation drones.")
    make_note(client, "Rebuild drill content two, about township commerce.")
    before = db.execute(
        "SELECT entity_id, chunk_index, content_hash FROM embedding_chunk "
        "WHERE superseded_by IS NULL AND embedding_model_version = %s "
        "ORDER BY entity_id, chunk_index",
        (ACTIVE_VERSION,),
    ).fetchall()
    assert before

    db.execute("DELETE FROM embedding_chunk WHERE superseded_by IS NOT NULL")
    db.execute("UPDATE embedding_chunk SET superseded_by = NULL")  # detach FKs
    db.execute("DELETE FROM embedding_chunk")
    router = ModelRouter(embedding_provider=provider)
    summary = run(_with_conn(reindex_all, router))
    assert summary["version"] == ACTIVE_VERSION

    after = db.execute(
        "SELECT entity_id, chunk_index, content_hash FROM embedding_chunk "
        "WHERE superseded_by IS NULL AND embedding_model_version = %s "
        "ORDER BY entity_id, chunk_index",
        (ACTIVE_VERSION,),
    ).fetchall()
    assert after == before


def test_embedding_outage_queues_and_is_visible(
    client: "TestClient", db: "psycopg.Connection"
) -> None:
    unconfigured = ModelRouter(embedding_provider=None)

    class Signal:
        deferred = 0

        def record_embedding_deferred(self) -> None:
            Signal.deferred += 1

    note_id = make_note(client, "Content that arrives during an outage window.")
    db.execute("UPDATE embedding_chunk SET superseded_by = NULL WHERE entity_id = %s", (note_id,))
    db.execute("DELETE FROM embedding_chunk WHERE entity_id = %s", (note_id,))
    result = run(
        _with_conn(index_entity_or_queue, unconfigured, "Note", note_id, Signal())
    )
    assert result["status"] == "queued"  # RAG-08: queued, never degraded
    assert Signal.deferred == 1
    assert not chunk_rows(db, note_id)


def test_router_retries_once_then_fails_loudly(provider: "FakeEmbedding") -> None:
    router = ModelRouter(embedding_provider=provider)
    provider.fail_next = 1  # transient: retry succeeds (AIA-06)
    vectors = run(router.embed_documents(["retry me"]))
    assert len(vectors) == 1 and len(vectors[0]) == 1536

    provider.fail_next = 2  # persistent: fails after one retry
    with pytest.raises(EmbeddingUnavailable):
        run(router.embed_documents(["still failing"]))
    provider.fail_next = 0
