"""Search API tests (MVP-017; BUILD_ORDER step 17).

Acceptance: the tier-filtering leak suite proves no above-ceiling result,
snippet, or count leaks (NFR-035; RAG-12; RAG-22); all three modes work;
hybrid fuses by RRF (ADR-17) with lexical and semantic independent before
fusion; embedding outages degrade with an explicit flag (RAG-25); results
carry privacy tier, provenance block, and citation-ready locators.
Requires LEGACY_TEST_DATABASE_URL; skipped when unset.
"""

import json
import os
import time
import uuid
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from legacy_api.rag.retrieval import FusionConfig, fuse_rrf

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


def auth(sub: str = "search-owner") -> dict[str, str]:
    return {"Authorization": f"Bearer {oidc_token(sub)}", "User-Agent": "s"}


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
        for sub, owner in (("search-owner", True), ("search-other", False)):
            conn.execute(
                """
                INSERT INTO app_user
                    (email, display_name, user_kind, is_owner, auth_subject, created_by)
                VALUES (%s, %s, 'human', %s, %s, %s)
                """,
                (f"{sub}@example.test", sub, owner, sub, SYSTEM_USER_ID),
            )
        yield conn


def _make_app(provider: Any, tmp_path_factory: Any) -> Any:
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
    return create_app(settings, verifier=verifier, embedding_provider=provider)


NOTES = [
    {"title": "Public zebra", "body": "The zebra fact everyone may read.",
     "privacy_tier": "P0"},
    {"title": "Trusted lion", "body": "The lion fact for trusted circles.",
     "privacy_tier": "P1"},
    {"title": "Private rhino", "body": "The rhino fact kept private by default.",
     "privacy_tier": "P2"},
]


@pytest.fixture(scope="module")
def client(db: "psycopg.Connection", tmp_path_factory: Any) -> Iterator["TestClient"]:
    with TestClient(_make_app(FakeEmbedding(), tmp_path_factory)) as test_client:
        response = test_client.post(
            "/v1/ingestion/jobs",
            files=[],
            data={"payload": json.dumps({"notes": NOTES})},
            headers=auth(),
        )
        assert response.status_code == 201
        yield test_client


@pytest.fixture(scope="module")
def client_no_embeddings(
    db: "psycopg.Connection", client: "TestClient", tmp_path_factory: Any
) -> Iterator["TestClient"]:
    with TestClient(_make_app(None, tmp_path_factory)) as test_client:
        yield test_client


def search(
    client: "TestClient", q: str, mode: str = "hybrid",
    headers: dict[str, str] | None = None, limit: int | None = None,
) -> Any:
    params: dict[str, Any] = {"q": q, "mode": mode}
    if limit is not None:
        params["limit"] = limit
    return client.get(
        "/v1/search", params=params, headers=headers if headers is not None else auth()
    )


# --- Leak suite (NFR-035; RAG-12; RAG-22) ----------------------------------


@pytest.mark.parametrize("mode", ["lexical", "semantic", "hybrid"])
def test_anonymous_ceiling_is_p0_in_every_mode(client: "TestClient", mode: str) -> None:
    response = search(client, "fact", mode=mode, headers={"User-Agent": "s"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["retrieval"]["tier_ceiling"] == "P0"
    tiers = {result["privacy_tier"] for result in payload["results"]}
    assert tiers <= {"P0"}
    text = json.dumps(payload)
    assert "lion" not in text and "rhino" not in text  # no snippet leak
    # Counts reflect only at-or-below-ceiling chunks: no existence leak.
    assert payload["retrieval"]["chunks_considered"] <= 1


@pytest.mark.parametrize("mode", ["lexical", "semantic", "hybrid"])
def test_non_owner_never_sees_private_content(client: "TestClient", mode: str) -> None:
    response = search(client, "fact", mode=mode, headers=auth("search-other"))
    assert response.status_code == 200
    payload = response.json()
    text = json.dumps(payload)
    assert "rhino" not in text  # P2 stays invisible without a grant


def test_owner_sees_all_tiers(client: "TestClient") -> None:
    payload = search(client, "fact", mode="lexical").json()
    tiers = {result["privacy_tier"] for result in payload["results"]}
    assert tiers == {"P0", "P1", "P2"}
    assert payload["retrieval"]["tier_ceiling"] == "P3"


# --- Modes and fusion --------------------------------------------------------


def test_lexical_mode_finds_keyword(client: "TestClient") -> None:
    payload = search(client, "zebra", mode="lexical").json()
    assert payload["mode"] == "lexical"
    assert payload["degraded"] is False
    assert payload["results"], "keyword must match"
    top = payload["results"][0]
    assert "zebra" in top["snippet"]
    assert top["title"] == "Public zebra"
    assert top["chunk_ref"].endswith("#c0")
    assert "provenance" in top


def test_semantic_mode_ranks_exact_vector_match_first(client: "TestClient") -> None:
    # The deterministic test provider embeds identical text to identical
    # vectors, so querying a chunk's exact text is a distance-zero match.
    exact = "Private rhino\n\nThe rhino fact kept private by default."
    payload = search(client, exact, mode="semantic").json()
    assert payload["degraded"] is False
    assert payload["results"]
    assert payload["results"][0]["title"] == "Private rhino"
    assert payload["results"][0]["matched"] == ["semantic"]


def test_hybrid_fuses_both_lists(client: "TestClient") -> None:
    exact = "Public zebra\n\nThe zebra fact everyone may read."
    payload = search(client, exact, mode="hybrid").json()
    assert payload["results"]
    top = payload["results"][0]
    # The zebra chunk is both the distance-zero semantic hit and a strong
    # lexical hit; RRF accumulates both contributions and ranks it first.
    assert top["title"] == "Public zebra"
    assert set(top["matched"]) == {"lexical", "semantic"}


def test_fuse_rrf_is_deterministic_and_additive() -> None:
    a = {"id": "a"}
    b = {"id": "b"}
    c = {"id": "c"}
    fused = fuse_rrf(
        {"lexical": [a, b], "semantic": [b, c]}, FusionConfig(rrf_k=60)
    )
    assert [entry["id"] for entry in fused] == ["b", "a", "c"]
    assert fused[0]["rrf_score"] == pytest.approx(1 / 62 + 1 / 61)
    assert fused[0]["matched"] == ["lexical", "semantic"]


# --- Degraded behavior (RAG-25; failure table) -------------------------------


@pytest.mark.parametrize("mode", ["semantic", "hybrid"])
def test_embedding_outage_degrades_to_lexical_with_flag(
    client_no_embeddings: "TestClient", mode: str
) -> None:
    response = search(client_no_embeddings, "zebra", mode=mode)
    assert response.status_code == 200
    payload = response.json()
    assert payload["degraded"] is True  # machine-readable, never silent
    assert payload["results"]
    assert payload["results"][0]["matched"] == ["lexical"]


def test_lexical_mode_is_unaffected_by_outage(
    client_no_embeddings: "TestClient",
) -> None:
    payload = search(client_no_embeddings, "zebra", mode="lexical").json()
    assert payload["degraded"] is False
    assert payload["results"]


# --- Validation and edges ----------------------------------------------------


def test_empty_query_and_unknown_mode_are_refused(client: "TestClient") -> None:
    assert search(client, "").status_code == 422
    assert search(client, "   ").status_code == 422
    response = search(client, "x", mode="psychic")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_failed"


def test_very_long_query_truncates_with_notice(client: "TestClient") -> None:
    payload = search(client, "zebra " + "waffle " * 200).json()
    assert payload["truncated"] is True  # FS-004 edge case
    assert len(payload["query"]) <= 500


def test_zero_results_are_empty_never_fabricated(client: "TestClient") -> None:
    # Lexical mode: no match means an empty list, never an invention.
    # (Semantic ANN always returns nearest neighbors; the not-in-corpus
    # confidence threshold remains an open TODO(decision) in RAG_PIPELINE
    # section 10 and is deliberately not resolved here.)
    payload = search(client, "quixotic nonexistent theremin", mode="lexical").json()
    assert payload["results"] == []
    assert payload["retrieval"]["chunks_returned"] == 0


def test_limit_is_honored(client: "TestClient") -> None:
    payload = search(client, "fact", mode="lexical", limit=1).json()
    assert len(payload["results"]) == 1
