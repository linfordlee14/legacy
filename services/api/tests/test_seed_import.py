"""Seed import tests (MVP-013; BUILD_ORDER step 13 acceptance).

Tiers land exactly as transcribed, the six section 12 items exist as
flagged claims, the import is idempotent and re-runnable, every claim
carries provenance, and every run is recorded in the audit log.
Requires LEGACY_TEST_DATABASE_URL; skipped when unset.
"""

import asyncio
import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from legacy_api.seed.master_context_data import (
    CLAIMS,
    EXPECTED_FLAGGED_PREDICATES,
    PROJECTS,
    SOURCES,
)

DB_URL = os.environ.get("LEGACY_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not DB_URL, reason="LEGACY_TEST_DATABASE_URL not set (disposable database required)"
)

if DB_URL:
    import psycopg
    from alembic import command
    from alembic.config import Config

    from legacy_api.seed.master_context_import import check_dataset, import_master_context

API_DIR = Path(__file__).resolve().parent.parent


def run_import() -> dict[str, Any]:
    async def _run() -> dict[str, Any]:
        conn = await psycopg.AsyncConnection.connect(DB_URL)
        try:
            return await import_master_context(conn)
        finally:
            await conn.close()

    return asyncio.run(_run())


@pytest.fixture(scope="module")
def db() -> Iterator["psycopg.Connection[Any]"]:
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
def first_run(db: "psycopg.Connection[Any]") -> dict[str, Any]:
    return run_import()


def count(db: "psycopg.Connection[Any]", sql: str, params: tuple[Any, ...] = ()) -> int:
    row = db.execute(sql, params).fetchone()
    assert row is not None
    return int(row[0])


def test_dataset_invariants_hold() -> None:
    check_dataset()


def test_import_creates_full_dataset(
    db: "psycopg.Connection[Any]", first_run: dict[str, Any]
) -> None:
    assert first_run["claims_created"] == len(CLAIMS)
    assert first_run["claims_existing"] == 0
    assert first_run["sources_created"] == len(SOURCES)
    assert first_run["persons_created"] == 1
    assert first_run["projects_created"] == len(PROJECTS)
    assert count(db, "SELECT count(*) FROM claim WHERE deleted_at IS NULL") == len(CLAIMS)
    assert count(
        db, "SELECT count(*) FROM person WHERE relationship_to_owner = 'self'"
    ) == 1
    assert count(db, "SELECT count(*) FROM project WHERE deleted_at IS NULL") == len(PROJECTS)


def test_tiers_preserved_exactly(
    db: "psycopg.Connection[Any]", first_run: dict[str, Any]
) -> None:
    # Aggregate: the database tier distribution matches the transcription.
    expected: dict[str, int] = {}
    for claim in CLAIMS:
        expected[claim["tier"]] = expected.get(claim["tier"], 0) + 1
    for tier, expected_count in expected.items():
        assert (
            count(
                db,
                "SELECT count(*) FROM claim WHERE confidence_tier = %s "
                "AND deleted_at IS NULL",
                (tier,),
            )
            == expected_count
        )
    # Spot-check: every dataset claim landed at its transcribed tier
    # (a superset of the 20-claim sample in the acceptance criteria).
    for claim in CLAIMS:
        row = db.execute(
            "SELECT confidence_tier, verified_at, verified_by, tier_rationale "
            "FROM claim WHERE predicate = %s AND md5(statement) = md5(%s) "
            "AND deleted_at IS NULL",
            (claim["predicate"], claim["statement"]),
        ).fetchone()
        assert row is not None, claim["predicate"]
        assert row[0] == claim["tier"]
        # Import never marks human verification (that is the owner's queue).
        assert row[1] is None and row[2] is None
        assert f"section {claim['section']}" in row[3]


def test_six_section_12_items_flagged(
    db: "psycopg.Connection[Any]", first_run: dict[str, Any]
) -> None:
    assert count(
        db,
        "SELECT count(*) FROM claim WHERE confidence_tier = 'flagged' "
        "AND deleted_at IS NULL",
    ) == 6
    for predicate, keyword in EXPECTED_FLAGGED_PREDICATES:
        assert (
            count(
                db,
                "SELECT count(*) FROM claim WHERE confidence_tier = 'flagged' "
                "AND predicate = %s AND statement LIKE %s AND deleted_at IS NULL",
                (predicate, f"%{keyword}%"),
            )
            == 1
        ), (predicate, keyword)


def test_every_claim_has_provenance(
    db: "psycopg.Connection[Any]", first_run: dict[str, Any]
) -> None:
    # Ingestion provenance on the row itself (origin_ref -> the run's job).
    assert (
        count(
            db,
            "SELECT count(*) FROM claim WHERE origin_type = 'ingestion' "
            "AND origin_ref_type = 'IngestionJob' AND origin_ref_id = %s",
            (first_run["job_id"],),
        )
        == len(CLAIMS)
    )
    # Every claim is mentioned by the MASTER_CONTEXT document source.
    assert (
        count(
            db,
            """
            SELECT count(*) FROM claim c
            JOIN claim_source cs ON cs.claim_id = c.id AND cs.deleted_at IS NULL
            JOIN source s ON s.id = cs.source_id
            WHERE s.title LIKE 'MASTER_CONTEXT.md%%' AND cs.support_type = 'mentions'
              AND c.deleted_at IS NULL
            """,
        )
        == len(CLAIMS)
    )
    # Listed platform sources support their claims.
    expected_supports = sum(len(claim["sources"]) for claim in CLAIMS)
    assert (
        count(
            db,
            "SELECT count(*) FROM claim_source WHERE support_type = 'supports' "
            "AND deleted_at IS NULL",
        )
        == expected_supports
    )


def test_rerun_is_idempotent(db: "psycopg.Connection[Any]", first_run: dict[str, Any]) -> None:
    before = {
        table: count(db, f"SELECT count(*) FROM {table}")
        for table in ("claim", "source", "claim_source", "person", "project")
    }
    second = run_import()
    assert second["claims_created"] == 0
    assert second["claims_existing"] == len(CLAIMS)
    assert second["sources_created"] == 0
    assert second["links_created"] == 0
    assert second["persons_created"] == 0
    assert second["projects_created"] == 0
    for table, table_count in before.items():
        assert count(db, f"SELECT count(*) FROM {table}") == table_count, table
    # Every run is recorded: a job and an audit entry per import (ADR-11).
    assert count(
        db,
        "SELECT count(*) FROM ingestion_job WHERE job_type = 'bulk_import' "
        "AND status = 'complete' AND source_descriptor ->> 'kind' = 'master_context_seed'",
    ) == 2
    assert count(
        db,
        "SELECT count(*) FROM audit_log_entry WHERE action = 'seed_import'",
    ) == 2


def test_rerun_never_restores_a_changed_tier(db: "psycopg.Connection[Any]") -> None:
    """Re-import must not push an existing claim back up to its transcribed
    tier: tier changes belong solely to the owner-verified path (4.4)."""
    db.execute(
        "UPDATE claim SET confidence_tier = 'flagged' "
        "WHERE predicate = 'has_full_name' AND deleted_at IS NULL"
    )
    run_import()
    row = db.execute(
        "SELECT confidence_tier FROM claim WHERE predicate = 'has_full_name' "
        "AND deleted_at IS NULL"
    ).fetchone()
    assert row is not None and row[0] == "flagged"
    # Restore for any later assertions (a downgrade-then-upgrade needs the
    # authorized path; recreate via delete + reimport instead).
    db.execute(
        "UPDATE claim SET deleted_at = now() "
        "WHERE predicate = 'has_full_name' AND deleted_at IS NULL"
    )
    summary = run_import()
    assert summary["claims_created"] == 1
