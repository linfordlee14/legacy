"""Performance baseline harness (MVP-019; NON_FUNCTIONAL_REQUIREMENTS 4.1).

Measures NFR-001 (lexical search p95), NFR-002 (hybrid search p95), and
NFR-005 (capture-to-searchable freshness) plus API, ingestion, and
indexing timings against the reference corpus (the repository
specification documents), served by a real uvicorn server over HTTP with
the production code path end to end.

Honesty notes (never fabricate, never estimate):
- Embeddings use a deterministic in-process stand-in with the pinned
  dimension (1536), so semantic and hybrid numbers cover the full store,
  fusion, and HTTP path but EXCLUDE real provider round-trips. The
  with-provider run is an outstanding verification item until
  LEGACY_GEMINY_API_KEY exists; nothing here pretends otherwise.
- The database given via LEGACY_PERF_DATABASE_URL is DROPPED and rebuilt:
  point it only at a disposable database (CI-09 discipline).

Usage:
  LEGACY_PERF_DATABASE_URL=postgresql://... python scripts/perf/measure_baseline.py
"""

import asyncio
import io
import json
import os
import statistics
import sys
import threading
import time
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
API_DIR = REPO_ROOT / "services" / "api"
sys.path.insert(0, str(API_DIR / "src"))

import httpx  # noqa: E402
import jwt as pyjwt  # noqa: E402
import psycopg  # noqa: E402
import uvicorn  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from cryptography.hazmat.primitives.asymmetric import rsa  # noqa: E402

from legacy_api.ai.router import ModelRouter  # noqa: E402
from legacy_api.config import Settings  # noqa: E402
from legacy_api.db import create_pool  # noqa: E402
from legacy_api.main import create_app  # noqa: E402
from legacy_api.seed.documents import import_documents  # noqa: E402
from legacy_api.seed.master_context_import import import_master_context  # noqa: E402
from legacy_api.storage import LocalObjectStorage  # noqa: E402
from legacy_api.verifier import TokenVerifier  # noqa: E402

DB_URL = os.environ.get("LEGACY_PERF_DATABASE_URL")
PORT = int(os.environ.get("LEGACY_PERF_PORT", "8123"))
BASE = f"http://127.0.0.1:{PORT}"
ISSUER = "https://auth.perf.invalid"
AUDIENCE = "legacy-api"
SYSTEM_USER_ID = "00000000-0000-7000-8000-000000000001"
CORPUS_DIRS = ["knowledge", "ai", "api", "database", "security", "deployment"]
GOLDEN = json.loads(
    (API_DIR / "tests" / "golden" / "search_golden.json").read_text()
)["queries"]


class DeterministicEmbedding:
    """Test-embedder stand-in: full pipeline shape, zero network."""

    name = "deterministic-perf"
    model = "gemini-embedding-001"
    dimensions = 1536

    async def embed(self, texts: list[str], task_type: str) -> list[list[float]]:
        import hashlib

        out = []
        for text in texts:
            digest = hashlib.sha256(text.encode()).digest()
            out.append([(digest[i % 32] + 1) / 256.0 for i in range(self.dimensions)])
        return out


def percentile(samples: list[float], q: float) -> float:
    ordered = sorted(samples)
    index = min(len(ordered) - 1, max(0, round(q * len(ordered)) - 1))
    return ordered[index]


def summarize(samples: list[float]) -> dict:
    return {
        "n": len(samples),
        "p50_ms": round(statistics.median(samples), 1),
        "p95_ms": round(percentile(samples, 0.95), 1),
        "max_ms": round(max(samples), 1),
    }


def token(key, sub: str = "perf-owner") -> str:
    now = int(time.time())
    return pyjwt.encode(
        {
            "iss": ISSUER, "aud": AUDIENCE, "sub": sub, "iat": now, "exp": now + 3600,
            "auth_time": now, "session_id": uuid.uuid4().hex, "aal": "aal2",
        },
        key,
        algorithm="RS256",
    )


def prepare_database() -> None:
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
            VALUES ('perf-owner@example.test', 'perf-owner', 'human', true,
                    'perf-owner', %s)
            """,
            (SYSTEM_USER_ID,),
        )


def synthetic_batch(root: Path, count: int = 100) -> None:
    """NFR-006 evidence: a 100-document mixed batch (60 md, 30 txt, 10 pdf)."""
    from pypdf import PdfWriter

    for i in range(60):
        (root / f"doc_{i:03}.md").write_text(
            f"# Synthetic document {i}\n\n"
            + "\n\n".join(
                f"Paragraph {p} of synthetic document {i} discussing topic {i * 7 + p}."
                for p in range(12)
            )
        )
    for i in range(30):
        (root / f"note_{i:03}.txt").write_text(
            f"Synthetic note {i}. " + " ".join(f"Sentence {s}." for s in range(40))
        )
    for i in range(10):
        buffer = io.BytesIO()
        writer = PdfWriter()
        # Unique page size per file so checksum dedup cannot collapse the
        # batch: NFR-006 wants 100 distinct documents.
        writer.add_blank_page(width=72 + i, height=72)
        writer.write(buffer)
        (root / f"deck_{i:02}.pdf").write_bytes(buffer.getvalue())


async def ingest_corpus(storage_dir: Path, provider) -> dict:
    pool = create_pool(DB_URL)
    await pool.open()
    storage = LocalObjectStorage(storage_dir)
    router = ModelRouter(embedding_provider=provider)
    timings: dict = {}
    try:
        conn = await psycopg.AsyncConnection.connect(DB_URL)
        try:
            started = time.perf_counter()
            await import_master_context(conn)
            timings["seed_claims_s"] = round(time.perf_counter() - started, 2)
        finally:
            await conn.close()

        started = time.perf_counter()
        summary = await import_documents(
            pool, storage, [REPO_ROOT / d for d in CORPUS_DIRS],
            extensions={".md"}, router=router,
        )
        timings["reference_corpus"] = {
            "documents_stored": summary["by_status"].get("stored", 0),
            "ingest_and_index_s": round(time.perf_counter() - started, 2),
        }

        batch_dir = storage_dir / "synthetic"
        batch_dir.mkdir()
        synthetic_batch(batch_dir)
        started = time.perf_counter()
        batch = await import_documents(pool, storage, [batch_dir], router=router)
        timings["synthetic_batch_100"] = {
            "by_status": batch["by_status"],
            "ingest_and_index_s": round(time.perf_counter() - started, 2),
        }
    finally:
        await pool.close()
    return timings


def measure_endpoint(client: httpx.Client, path: str, rounds: int, headers) -> dict:
    samples = []
    for _ in range(rounds):
        started = time.perf_counter()
        response = client.get(f"{BASE}{path}", headers=headers)
        response.raise_for_status()
        samples.append((time.perf_counter() - started) * 1000)
    return summarize(samples)


def measure_search(client: httpx.Client, mode: str, rounds: int, headers) -> dict:
    samples = []
    for _ in range(rounds):
        for entry in GOLDEN:
            started = time.perf_counter()
            response = client.get(
                f"{BASE}/v1/search",
                params={"q": entry["query"], "mode": mode, "limit": 10},
                headers=headers,
            )
            response.raise_for_status()
            samples.append((time.perf_counter() - started) * 1000)
    return summarize(samples)


def measure_freshness(client: httpx.Client, headers) -> dict:
    """NFR-005: one text document, upload to searchable, wall seconds."""
    marker = f"freshness{uuid.uuid4().hex[:12]}"
    started = time.perf_counter()
    response = client.post(
        f"{BASE}/v1/ingestion/jobs",
        data={"payload": json.dumps({"notes": [{"title": "freshness probe",
                                                 "body": f"The {marker} arrived."}]})},
        headers=headers,
    )
    response.raise_for_status()
    deadline = time.time() + 180
    while time.time() < deadline:
        found = client.get(
            f"{BASE}/v1/search",
            params={"q": marker, "mode": "lexical"},
            headers=headers,
        ).json()
        if found["results"]:
            return {"searchable_after_s": round(time.perf_counter() - started, 2)}
        time.sleep(0.5)
    return {"searchable_after_s": None, "note": "not searchable within 180 s"}


def main() -> int:
    if not DB_URL:
        print("LEGACY_PERF_DATABASE_URL is required (a DISPOSABLE database)",
              file=sys.stderr)
        return 2

    import tempfile

    storage_dir = Path(tempfile.mkdtemp(prefix="legacy-perf-"))
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    provider = DeterministicEmbedding()

    print("perf: preparing disposable database and corpus", file=sys.stderr)
    prepare_database()
    ingest_timings = asyncio.run(ingest_corpus(storage_dir, provider))

    settings = Settings(
        env="local", database_url=DB_URL,
        oidc_issuer=ISSUER, oidc_audience=AUDIENCE,
        storage_dir=str(storage_dir / "objects"),
    )
    verifier = TokenVerifier(
        issuer=ISSUER, audience=AUDIENCE, key_provider=lambda _t: key.public_key()
    )
    app = create_app(settings, verifier=verifier, embedding_provider=provider)
    server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=PORT, log_level="warning")
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    while not server.started:
        time.sleep(0.05)

    headers = {"Authorization": f"Bearer {token(key)}", "User-Agent": "perf"}
    report: dict = {
        "environment": {
            "note": "sandbox container; deterministic test embedder "
                    "(store path only, no provider round-trips)",
            "corpus_dirs": CORPUS_DIRS,
        },
        "ingestion_and_indexing": ingest_timings,
    }
    try:
        with httpx.Client(timeout=30) as client:
            client.get(f"{BASE}/healthz").raise_for_status()  # warm-up
            report["api"] = {
                "healthz": measure_endpoint(client, "/healthz", 50, headers),
                "claims_list": measure_endpoint(client, "/v1/claims", 30, headers),
                "notes_list": measure_endpoint(client, "/v1/notes", 30, headers),
            }
            report["search"] = {
                "lexical_nfr001": measure_search(client, "lexical", 5, headers),
                "hybrid_nfr002_store_path": measure_search(client, "hybrid", 5, headers),
                "semantic_store_path": measure_search(client, "semantic", 5, headers),
            }
            report["freshness_nfr005"] = measure_freshness(client, headers)
            metrics = client.get(f"{BASE}/metrics")
            report["observability"] = {
                "metrics_exposed": metrics.status_code == 200
                and "legacy_api_requests_total" in metrics.text,
                "embedding_deferred_counter_present":
                    "legacy_embedding_deferred_total" in metrics.text,
            }
    finally:
        server.should_exit = True
        thread.join(timeout=10)

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
