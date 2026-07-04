"""Seed importer: MASTER_CONTEXT.md claims into the provenance model (MVP-013).

Imports the curated dataset in master_context_data as Claim rows with their
exact confidence tiers (DATABASE_SCHEMA 4.4), Source stubs, and ClaimSource
links, attributed to the owner Person and the section 6 Projects.

Invariants enforced here:
- Tiers land exactly as transcribed and are never touched on re-run: claim
  inserts use ON CONFLICT DO NOTHING against uq_claim_statement, so an
  existing row keeps whatever tier it has (upgrades belong solely to the
  owner-verified path guarded by claim_tier_guard).
- Idempotent and re-runnable (MVP-013 acceptance): claims, sources,
  projects, the owner Person, and claim_source links are find-or-create;
  a re-run creates none of them again.
- Every imported row carries ingestion provenance: origin_type 'ingestion'
  with origin_ref pointing at the IngestionJob recorded for the run, and
  every run writes an audit entry (ADR-11) whether or not it created rows.
"""

import asyncio
import json
import sys
from typing import Any

from psycopg import AsyncConnection
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from legacy_api.audit import SYSTEM_USER_ID, write_audit_event
from legacy_api.seed.master_context_data import (
    CLAIMS,
    EXPECTED_FLAGGED_PREDICATES,
    OWNER_PERSON,
    PROJECT_STATUS_NOTE,
    PROJECTS,
    SOURCES,
)

MASTER_CONTEXT_SOURCE = "master_context"


def check_dataset() -> None:
    """Refuse to import a dataset that drifted from its own invariants.

    The flagged set must be exactly the six section 12 verification items
    (BUILD_ORDER step 13 acceptance), and every claim must reference known
    sources and subjects.
    """
    flagged = [claim for claim in CLAIMS if claim["tier"] == "flagged"]
    if len(flagged) != len(EXPECTED_FLAGGED_PREDICATES):
        raise ValueError(
            f"flagged claims: expected {len(EXPECTED_FLAGGED_PREDICATES)}, "
            f"dataset has {len(flagged)}"
        )
    for predicate, keyword in EXPECTED_FLAGGED_PREDICATES:
        matches = [
            claim
            for claim in flagged
            if claim["predicate"] == predicate and keyword in claim["statement"]
        ]
        if len(matches) != 1:
            raise ValueError(f"section 12 item ({predicate}, {keyword}): {len(matches)} matches")
    for claim in CLAIMS:
        if claim["tier"] not in ("verified", "self_reported", "flagged"):
            raise ValueError(f"unknown tier {claim['tier']!r}")
        unknown = set(claim["sources"]) - set(SOURCES)
        if unknown:
            raise ValueError(f"unknown source keys {unknown}")
        kind, slug = claim["subject"]
        if kind == "project" and slug not in PROJECTS:
            raise ValueError(f"unknown project slug {slug!r}")
        if kind not in ("owner", "project"):
            raise ValueError(f"unknown subject kind {kind!r}")


async def _ensure_owner(conn: AsyncConnection[Any], job_id: str, counts: dict[str, int]) -> str:
    """The owner Person (DATABASE_SCHEMA 4.3: relationship_to_owner 'self')."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "SELECT id FROM person WHERE relationship_to_owner = 'self' "
            "AND deleted_at IS NULL ORDER BY created_at LIMIT 1"
        )
        row = await cur.fetchone()
        if row:
            return str(row["id"])
        await cur.execute(
            """
            INSERT INTO person (full_name, aliases, relationship_to_owner,
                                created_by, origin_type, origin_ref_type, origin_ref_id)
            VALUES (%s, %s, 'self', %s, 'ingestion', 'IngestionJob', %s)
            RETURNING id
            """,
            (
                OWNER_PERSON["full_name"],
                Jsonb(OWNER_PERSON["aliases"]),
                SYSTEM_USER_ID,
                job_id,
            ),
        )
        created = await cur.fetchone()
        assert created is not None
        counts["persons_created"] += 1
        return str(created["id"])


async def _ensure_project(
    conn: AsyncConnection[Any], slug: str, meta: dict[str, str], job_id: str,
    counts: dict[str, int],
) -> str:
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            INSERT INTO project (name, slug, status, summary,
                                 created_by, origin_type, origin_ref_type, origin_ref_id)
            VALUES (%s, %s, %s, %s, %s, 'ingestion', 'IngestionJob', %s)
            ON CONFLICT (slug) WHERE deleted_at IS NULL DO NOTHING
            RETURNING id
            """,
            (meta["name"], slug, meta["status"], PROJECT_STATUS_NOTE, SYSTEM_USER_ID, job_id),
        )
        row = await cur.fetchone()
        if row:
            counts["projects_created"] += 1
            return str(row["id"])
        await cur.execute(
            "SELECT id FROM project WHERE slug = %s AND deleted_at IS NULL", (slug,)
        )
        existing = await cur.fetchone()
        assert existing is not None
        return str(existing["id"])


async def _ensure_source(
    conn: AsyncConnection[Any], stub: dict[str, str | None], job_id: str,
    counts: dict[str, int],
) -> str:
    """Find-or-create by title (source has no natural unique index)."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "SELECT id FROM source WHERE title = %s AND deleted_at IS NULL "
            "ORDER BY created_at LIMIT 1",
            (stub["title"],),
        )
        row = await cur.fetchone()
        if row:
            return str(row["id"])
        await cur.execute(
            """
            INSERT INTO source (source_type, title, url, publisher, reliability_note,
                                created_by, origin_type, origin_ref_type, origin_ref_id)
            VALUES (%s, %s, %s, %s, %s, %s, 'ingestion', 'IngestionJob', %s)
            RETURNING id
            """,
            (
                stub["source_type"],
                stub["title"],
                stub["url"],
                stub["publisher"],
                stub["reliability_note"],
                SYSTEM_USER_ID,
                job_id,
            ),
        )
        created = await cur.fetchone()
        assert created is not None
        counts["sources_created"] += 1
        return str(created["id"])


async def _ensure_claim(
    conn: AsyncConnection[Any], claim: dict[str, Any], subject_type: str, subject_id: str,
    job_id: str, counts: dict[str, int],
) -> str:
    """Insert at the transcribed tier; an existing row is left untouched
    (never an upgrade, never a downgrade, from this path)."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            INSERT INTO claim (subject_type, subject_id, predicate, statement,
                               confidence_tier, tier_rationale,
                               created_by, origin_type, origin_ref_type, origin_ref_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'ingestion', 'IngestionJob', %s)
            ON CONFLICT (subject_type, subject_id, predicate, md5(statement))
                WHERE deleted_at IS NULL DO NOTHING
            RETURNING id
            """,
            (
                subject_type,
                subject_id,
                claim["predicate"],
                claim["statement"],
                claim["tier"],
                _rationale(claim),
                SYSTEM_USER_ID,
                job_id,
            ),
        )
        row = await cur.fetchone()
        if row:
            counts["claims_created"] += 1
            return str(row["id"])
        counts["claims_existing"] += 1
        await cur.execute(
            """
            SELECT id FROM claim
            WHERE subject_type = %s AND subject_id = %s AND predicate = %s
              AND md5(statement) = md5(%s) AND deleted_at IS NULL
            """,
            (subject_type, subject_id, claim["predicate"], claim["statement"]),
        )
        existing = await cur.fetchone()
        assert existing is not None
        return str(existing["id"])


def _rationale(claim: dict[str, Any]) -> str:
    """tier_rationale always records the MASTER_CONTEXT section; the curated
    rationale (mixed markers, section 12 pointers) is appended when present."""
    base = f"MASTER_CONTEXT section {claim['section']}."
    rationale = claim.get("rationale")
    return f"{base} {rationale}" if rationale else base


async def _link(
    conn: AsyncConnection[Any], claim_id: str, source_id: str, support_type: str,
    job_id: str, counts: dict[str, int],
) -> None:
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            INSERT INTO claim_source (claim_id, source_id, support_type,
                                      created_by, origin_type, origin_ref_type, origin_ref_id)
            VALUES (%s, %s, %s, %s, 'ingestion', 'IngestionJob', %s)
            ON CONFLICT (claim_id, source_id) WHERE deleted_at IS NULL DO NOTHING
            RETURNING id
            """,
            (claim_id, source_id, support_type, SYSTEM_USER_ID, job_id),
        )
        if await cur.fetchone():
            counts["links_created"] += 1


async def import_master_context(conn: AsyncConnection[Any]) -> dict[str, Any]:
    """Run one import pass in a single transaction; returns the run summary.

    Every run, including a no-op re-run, is recorded as an IngestionJob
    and an audit entry, so the import history is inspectable.
    """
    check_dataset()
    counts = {
        "claims_created": 0,
        "claims_existing": 0,
        "sources_created": 0,
        "links_created": 0,
        "persons_created": 0,
        "projects_created": 0,
    }

    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            INSERT INTO ingestion_job (job_type, source_descriptor, status,
                                       created_by, origin_type)
            VALUES ('bulk_import', %s, 'parsing', %s, 'system')
            RETURNING id
            """,
            (
                Jsonb(
                    {
                        "kind": "master_context_seed",
                        "document": "knowledge/MASTER_CONTEXT.md",
                        "dataset": "legacy_api.seed.master_context_data",
                        "claim_count": len(CLAIMS),
                    }
                ),
                SYSTEM_USER_ID,
            ),
        )
        job_row = await cur.fetchone()
        assert job_row is not None
        job_id = str(job_row["id"])

    owner_id = await _ensure_owner(conn, job_id, counts)
    project_ids = {
        slug: await _ensure_project(conn, slug, meta, job_id, counts)
        for slug, meta in PROJECTS.items()
    }
    source_ids = {
        key: await _ensure_source(conn, stub, job_id, counts)
        for key, stub in SOURCES.items()
    }

    for claim in CLAIMS:
        kind, slug = claim["subject"]
        if kind == "owner":
            subject_type, subject_id = "Person", owner_id
        else:
            subject_type, subject_id = "Project", project_ids[slug]
        claim_id = await _ensure_claim(conn, claim, subject_type, subject_id, job_id, counts)
        # The consolidated document mentions every claim; listed platform
        # sources support theirs (master_context_data transcription rules).
        await _link(conn, claim_id, source_ids[MASTER_CONTEXT_SOURCE], "mentions", job_id, counts)
        for key in claim["sources"]:
            await _link(conn, claim_id, source_ids[key], "supports", job_id, counts)

    await conn.execute(
        "UPDATE ingestion_job SET status = 'complete', progress_percent = 100, "
        "items_created = %s WHERE id = %s",
        (Jsonb(counts), job_id),
    )
    await write_audit_event(
        conn,
        actor_type="system",
        actor_id=None,
        action="seed_import",
        subject_type="IngestionJob",
        subject_id=job_id,
        payload={"seed": "master_context", **counts},
    )
    await conn.commit()
    return {"job_id": job_id, **counts}


async def _amain() -> int:
    from legacy_api.config import get_settings

    settings = get_settings()
    if not settings.database_url:
        print("LEGACY_DATABASE_URL is required (DEP-18)", file=sys.stderr)
        return 2
    conn = await AsyncConnection.connect(settings.database_url)
    try:
        summary = await import_master_context(conn)
    finally:
        await conn.close()
    print(json.dumps(summary, indent=2))
    return 0


def main() -> None:
    raise SystemExit(asyncio.run(_amain()))


if __name__ == "__main__":
    main()
