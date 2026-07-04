"""Golden query set baseline and latency checks (MVP-017 acceptance).

Ingests the repository specification corpus (the Phase 1 seed corpus)
through the real batch importer, runs the golden queries of
tests/golden/search_golden.json, and enforces the recorded recall floor
plus the NFR-001 lexical latency budget. NFR-002 is measured here with
the deterministic test embedder, which exercises the full fusion and
store path but excludes real provider latency; the with-provider numbers
are an outstanding verification item until the API key is provisioned.
Requires LEGACY_TEST_DATABASE_URL; skipped when unset.
"""

import asyncio
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
    from tests.test_rag_index import FakeEmbedding

    from legacy_api.ai.router import ModelRouter
    from legacy_api.config import Settings
    from legacy_api.db import create_pool
    from legacy_api.main import create_app
    from legacy_api.seed.documents import import_documents
    from legacy_api.storage import LocalObjectStorage
    from legacy_api.verifier import TokenVerifier

API_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = API_DIR.parent.parent
GOLDEN = json.loads((Path(__file__).parent / "golden" / "search_golden.json").read_text())
SYSTEM_USER_ID = "00000000-0000-7000-8000-000000000001"
ISSUER = "https://auth.test.invalid"
AUDIENCE = "legacy-api"
KEY = None

# Baseline v1, recorded at MVP-017 on the repository corpus: lexical
# recall@10 of 1.0. The floor leaves headroom for corpus growth while
# catching real regressions (RAG-26: regression-blocked).
RECALL_FLOOR = 0.75


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
            VALUES ('golden-owner@example.test', 'golden-owner', 'human', true,
                    'golden-owner', %s)
            """,
            (SYSTEM_USER_ID,),
        )
        yield conn


@pytest.fixture(scope="module")
def client(db: "psycopg.Connection", tmp_path_factory: Any) -> Iterator["TestClient"]:
    storage_dir = tmp_path_factory.mktemp("objects")
    provider = FakeEmbedding()

    async def ingest() -> dict[str, Any]:
        pool = create_pool(DB_URL)
        await pool.open()
        try:
            return await import_documents(
                pool,
                LocalObjectStorage(storage_dir),
                [REPO_ROOT / d for d in GOLDEN["corpus_dirs"]],
                extensions={".md"},
                router=ModelRouter(embedding_provider=provider),
            )
        finally:
            await pool.close()

    summary = asyncio.run(ingest())
    assert summary["by_status"].get("stored", 0) > 10, summary

    settings = Settings(  # type: ignore[call-arg]
        env="local",
        database_url=DB_URL,
        oidc_issuer=ISSUER,
        oidc_audience=AUDIENCE,
        storage_dir=str(storage_dir),
    )
    verifier = TokenVerifier(
        issuer=ISSUER, audience=AUDIENCE, key_provider=lambda _t: KEY.public_key()
    )
    with TestClient(create_app(settings, verifier=verifier, embedding_provider=provider)) as c:
        yield c


def run_query(client: "TestClient", q: str, mode: str) -> tuple[Any, float]:
    started = time.perf_counter()
    response = client.get(
        "/v1/search",
        params={"q": q, "mode": mode, "limit": GOLDEN["k"]},
        headers={"Authorization": f"Bearer {oidc_token('golden-owner')}", "User-Agent": "g"},
    )
    elapsed_ms = (time.perf_counter() - started) * 1000
    assert response.status_code == 200
    return response.json(), elapsed_ms


def p95(samples: list[float]) -> float:
    ordered = sorted(samples)
    return ordered[min(len(ordered) - 1, int(round(0.95 * len(ordered))) - 1)]


def test_golden_lexical_recall_meets_baseline(client: "TestClient") -> None:
    hits = 0
    misses = []
    for entry in GOLDEN["queries"]:
        payload, _ = run_query(client, entry["query"], "lexical")
        titles = {result["title"] for result in payload["results"]}
        if any(
            any(expected in (title or "") for title in titles)
            for expected in entry["expect_any"]
        ):
            hits += 1
        else:
            misses.append(entry["query"])
    recall = hits / len(GOLDEN["queries"])
    print(f"\ngolden lexical recall@{GOLDEN['k']}: {recall:.2f} (misses: {misses})")
    assert recall >= RECALL_FLOOR, misses


def test_nfr001_lexical_latency_budget(client: "TestClient") -> None:
    samples = []
    for entry in GOLDEN["queries"]:
        _, elapsed_ms = run_query(client, entry["query"], "lexical")
        samples.append(elapsed_ms)
    print(f"\nlexical latency ms: p95={p95(samples):.0f} max={max(samples):.0f}")
    assert p95(samples) < 300  # NFR-001 (Should): 300 ms at p95


def test_nfr002_hybrid_latency_budget_store_path(client: "TestClient") -> None:
    """Full fusion and store path; the deterministic embedder stands in
    for the provider, so real network latency is measured at provisioning
    (outstanding verification item)."""
    samples = []
    for entry in GOLDEN["queries"]:
        _, elapsed_ms = run_query(client, entry["query"], "hybrid")
        samples.append(elapsed_ms)
    print(f"\nhybrid latency ms: p95={p95(samples):.0f} max={max(samples):.0f}")
    assert p95(samples) < 1500  # NFR-002 (Must): 1.5 s at p95
