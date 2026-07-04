"""Verification queue tests (MVP-020; BUILD_ORDER step 20; FS-009).

Acceptance: all six MASTER_CONTEXT section 12 items are listed; a claim
resolves end to end with audit entries; only the owner applies tier
changes. The resolve path must satisfy claim_tier_guard on its own terms
(never bypass it), reuse revision history, preserve provenance, and
require step-up. No automatic verification exists anywhere.
Requires LEGACY_TEST_DATABASE_URL; skipped when unset.
"""

import asyncio
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
    from legacy_api.seed.master_context_data import EXPECTED_FLAGGED_PREDICATES
    from legacy_api.seed.master_context_import import import_master_context
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


def auth(sub: str = "vq-owner", auth_age_s: int = 0) -> dict[str, str]:
    return {"Authorization": f"Bearer {oidc_token(sub, auth_age_s)}", "User-Agent": "vq"}


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
        for sub, owner in (("vq-owner", True), ("vq-other", False)):
            conn.execute(
                """
                INSERT INTO app_user
                    (email, display_name, user_kind, is_owner, auth_subject, created_by)
                VALUES (%s, %s, 'human', %s, %s, %s)
                """,
                (f"{sub}@example.test", sub, owner, sub, SYSTEM_USER_ID),
            )

        async def seed() -> None:
            aconn = await psycopg.AsyncConnection.connect(DB_URL)
            try:
                await import_master_context(aconn)
            finally:
                await aconn.close()

        asyncio.run(seed())
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


def get_queue(client: "TestClient") -> Any:
    response = client.get("/v1/verification/queue", headers=auth())
    assert response.status_code == 200
    return response.json()


def claim_by_predicate(queue: Any, predicate: str, keyword: str) -> Any:
    for item in queue["items"]:
        if item["predicate"] == predicate and keyword in item["statement"]:
            return item
    raise AssertionError(f"claim not in queue: {predicate} / {keyword}")


def test_queue_lists_all_six_section_12_items(client: "TestClient") -> None:
    queue = get_queue(client)
    assert queue["open_flagged"] == 6
    flagged = [i for i in queue["items"] if i["confidence_tier"] == "flagged"]
    assert len(flagged) == 6
    for predicate, keyword in EXPECTED_FLAGGED_PREDICATES:
        item = claim_by_predicate(queue, predicate, keyword)
        # The seed's provenance travels with the queue item.
        assert any(e["support_type"] == "mentions" for e in item["evidence"])


def test_queue_is_owner_only(client: "TestClient") -> None:
    assert (
        client.get("/v1/verification/queue", headers=auth("vq-other")).status_code == 403
    )
    assert client.get("/v1/verification/queue").status_code == 401


def test_stale_self_reported_claims_join_the_queue(
    client: "TestClient", db: "psycopg.Connection"
) -> None:
    claim_id = db.execute(
        "SELECT id FROM claim WHERE confidence_tier = 'self_reported' "
        "AND predicate = 'practices_methodology'"
    ).fetchone()[0]
    db.execute(
        "UPDATE claim SET review_due_at = CURRENT_DATE - 1 WHERE id = %s", (claim_id,)
    )
    queue = get_queue(client)
    assert queue["stale_self_reported"] == 1
    assert any(str(claim_id) == item["id"] for item in queue["items"])

    # A future review date leaves the queue again.
    db.execute(
        "UPDATE claim SET review_due_at = CURRENT_DATE + 30 WHERE id = %s", (claim_id,)
    )
    assert get_queue(client)["stale_self_reported"] == 0


def test_resolution_requires_fresh_authentication(client: "TestClient") -> None:
    queue = get_queue(client)
    item = claim_by_predicate(queue, "enrolled_at", "WorldQuant")
    stale = client.post(
        f"/v1/verification/claims/{item['id']}/resolve",
        json={"decision": "apply", "target_tier": "verified"},
        headers=auth(auth_age_s=3600),
    )
    assert stale.status_code == 401


def test_verified_without_supporting_evidence_is_refused_by_the_guard(
    client: "TestClient", db: "psycopg.Connection"
) -> None:
    queue = get_queue(client)
    item = claim_by_predicate(queue, "enrolled_at", "WorldQuant")
    assert item["supporting_count"] == 0  # only the mentions link exists

    response = client.post(
        f"/v1/verification/claims/{item['id']}/resolve",
        json={"decision": "apply", "target_tier": "verified"},
        headers=auth(),
    )
    assert response.status_code == 409
    assert "supporting ClaimSource" in response.json()["error"]["details"]["reason"]
    tier = db.execute(
        "SELECT confidence_tier FROM claim WHERE id = %s", (item["id"],)
    ).fetchone()[0]
    assert tier == "flagged"  # nothing moved
    revisions = db.execute(
        "SELECT count(*) FROM revision WHERE entity_id = %s", (item["id"],)
    ).fetchone()[0]
    assert revisions == 0  # the refused transaction left no trace


def test_full_resolution_end_to_end(
    client: "TestClient", db: "psycopg.Connection"
) -> None:
    """The MVP-020 acceptance journey: evidence attached, owner resolves,
    guard satisfied, audit written, revision preserved, provenance intact."""
    queue = get_queue(client)
    item = claim_by_predicate(queue, "enrolled_at", "WorldQuant")
    evidence_before = len(item["evidence"])

    attached = client.post(
        f"/v1/verification/claims/{item['id']}/evidence",
        json={
            "support_type": "supports",
            "note": "Official enrollment confirmation email.",
            "source": {
                "source_type": "document",
                "title": "WorldQuant University enrollment confirmation",
            },
        },
        headers=auth(),
    )
    assert attached.status_code == 201
    body = attached.json()
    assert body["supporting_count"] == 1
    assert len(body["evidence"]) == evidence_before + 1

    resolved = client.post(
        f"/v1/verification/claims/{item['id']}/resolve",
        json={"decision": "apply", "target_tier": "verified", "note": "Confirmed."},
        headers=auth(),
    )
    assert resolved.status_code == 200
    payload = resolved.json()
    assert payload["outcome"] == "applied"
    assert payload["claim"]["confidence_tier"] == "verified"
    assert payload["claim"]["verified_at"] is not None

    row = db.execute(
        "SELECT confidence_tier, verified_at, verified_by FROM claim WHERE id = %s",
        (item["id"],),
    ).fetchone()
    assert row[0] == "verified" and row[1] is not None and row[2] is not None

    # Revision history preserved the displaced tier state.
    snapshot = db.execute(
        "SELECT change_kind, snapshot FROM revision "
        "WHERE entity_type = 'Claim' AND entity_id = %s",
        (item["id"],),
    ).fetchone()
    assert snapshot[0] == "tier_change"
    assert snapshot[1]["confidence_tier"] == "flagged"

    # Audit trail: evidence attachment, sensitive-allow from the policy
    # service, and the resolution itself.
    actions = {
        r[0]
        for r in db.execute(
            "SELECT action FROM audit_log_entry WHERE subject_id = %s", (item["id"],)
        ).fetchall()
    }
    assert {"evidence_attached", "verify_claim"} <= actions

    # Provenance is preserved: the original mentions link is still there.
    links = db.execute(
        "SELECT count(*) FROM claim_source WHERE claim_id = %s AND deleted_at IS NULL",
        (item["id"],),
    ).fetchone()[0]
    assert links == evidence_before + 1

    # And the claim has left the queue.
    remaining = get_queue(client)
    assert remaining["open_flagged"] == 5
    assert all(i["id"] != item["id"] for i in remaining["items"])


def test_flagged_to_self_reported_needs_no_evidence_but_stays_authorized(
    client: "TestClient", db: "psycopg.Connection"
) -> None:
    queue = get_queue(client)
    item = claim_by_predicate(queue, "placed_at", "SA Startup Week")
    resolved = client.post(
        f"/v1/verification/claims/{item['id']}/resolve",
        json={"decision": "apply", "target_tier": "self_reported"},
        headers=auth(),
    )
    assert resolved.status_code == 200
    row = db.execute(
        "SELECT confidence_tier, verified_at, verified_by FROM claim WHERE id = %s",
        (item["id"],),
    ).fetchone()
    # Attribution tier, never marked human-verified.
    assert row == ("self_reported", None, None)


def test_reject_keeps_the_tier_and_audits(
    client: "TestClient", db: "psycopg.Connection"
) -> None:
    queue = get_queue(client)
    item = claim_by_predicate(queue, "holds_role", "IUS Africa")
    resolved = client.post(
        f"/v1/verification/claims/{item['id']}/resolve",
        json={"decision": "reject", "note": "No official listing found yet."},
        headers=auth(),
    )
    assert resolved.status_code == 200
    assert resolved.json()["outcome"] == "rejected"
    row = db.execute(
        "SELECT confidence_tier, tier_rationale FROM claim WHERE id = %s", (item["id"],)
    ).fetchone()
    assert row[0] == "flagged"
    assert "No official listing found yet." in row[1]
    assert any(str(item["id"]) == i["id"] for i in get_queue(client)["items"])


def test_only_the_owner_resolves_or_attaches(client: "TestClient") -> None:
    queue = get_queue(client)
    item = queue["items"][0]
    for path, body in (
        (f"/v1/verification/claims/{item['id']}/resolve",
         {"decision": "apply", "target_tier": "verified"}),
        (f"/v1/verification/claims/{item['id']}/evidence",
         {"support_type": "supports",
          "source": {"source_type": "url", "title": "x"}}),
    ):
        assert client.post(path, json=body, headers=auth("vq-other")).status_code == 403


def test_direct_sql_upgrade_stays_impossible(db: "psycopg.Connection") -> None:
    """No alternate mechanism: outside the authorized service path the
    database guard refuses upgrades unconditionally."""
    claim_id = db.execute(
        "SELECT id FROM claim WHERE confidence_tier = 'flagged' LIMIT 1"
    ).fetchone()[0]
    with pytest.raises(psycopg.errors.RaiseException):
        db.execute(
            "UPDATE claim SET confidence_tier = 'verified' WHERE id = %s", (claim_id,)
        )


def test_duplicate_evidence_link_conflicts(client: "TestClient") -> None:
    queue = get_queue(client)
    item = claim_by_predicate(queue, "accepted_into", "HBS Foundry")
    first = client.post(
        f"/v1/verification/claims/{item['id']}/evidence",
        json={"support_type": "supports",
              "source": {"source_type": "url", "title": "Aspire cohort page"}},
        headers=auth(),
    )
    assert first.status_code == 201
    source_id = next(
        e["source_id"] for e in first.json()["evidence"] if e["title"] == "Aspire cohort page"
    )
    duplicate = client.post(
        f"/v1/verification/claims/{item['id']}/evidence",
        json={"support_type": "supports", "source_id": source_id},
        headers=auth(),
    )
    assert duplicate.status_code == 409


def test_resolve_honors_idempotency_key(
    client: "TestClient", db: "psycopg.Connection"
) -> None:
    queue = get_queue(client)
    item = claim_by_predicate(queue, "submitted_to_program", "ADEL")
    key = uuid.uuid4().hex
    first = client.post(
        f"/v1/verification/claims/{item['id']}/resolve",
        json={"decision": "apply", "target_tier": "self_reported"},
        headers={**auth(), "Idempotency-Key": key},
    )
    assert first.status_code == 200
    replay = client.post(
        f"/v1/verification/claims/{item['id']}/resolve",
        json={"decision": "apply", "target_tier": "self_reported"},
        headers={**auth(), "Idempotency-Key": key},
    )
    assert replay.status_code == 200
    assert replay.headers.get("Idempotency-Replayed") == "true"
    revisions = db.execute(
        "SELECT count(*) FROM revision WHERE entity_id = %s", (item["id"],)
    ).fetchone()[0]
    assert revisions == 1  # the retry did not run the resolution again
