"""Schema migration tests (MVP-003, DATABASE_SCHEMA sections 4.2-4.7).

Covers the BUILD_ORDER step 3 'done when': clean apply to an empty database,
reversibility, tier defaults, and the claim-tier never-auto-upgrade guard.
Requires LEGACY_TEST_DATABASE_URL pointing at a disposable database that the
tests may own entirely (CI-09); skipped when unset.
"""

import os
import uuid
from collections.abc import Iterator
from pathlib import Path

import pytest

DB_URL = os.environ.get("LEGACY_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not DB_URL, reason="LEGACY_TEST_DATABASE_URL not set (disposable database required)"
)

if DB_URL:
    import psycopg
    from alembic import command
    from alembic.config import Config

API_DIR = Path(__file__).resolve().parent.parent
SYSTEM_USER_ID = "00000000-0000-7000-8000-000000000001"

EXPECTED_TABLES = {
    "app_user", "role", "access_grant", "person", "organization", "project",
    "artifact", "event", "idea", "note", "journal_entry", "conversation",
    "skill", "certification", "achievement", "goal", "lesson", "book", "talk",
    "article", "tag", "collection", "source", "claim", "claim_source", "edge",
    "memory_record", "embedding_chunk", "audit_log_entry", "ingestion_job",
    "agent_run", "schema_metadata", "personal_access_token",
}


def alembic_config() -> "Config":
    cfg = Config(str(API_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(API_DIR / "migrations"))
    os.environ["LEGACY_DATABASE_URL"] = DB_URL or ""
    return cfg


def list_tables(conn: "psycopg.Connection") -> set[str]:
    rows = conn.execute(
        "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
    ).fetchall()
    return {row[0] for row in rows} - {"alembic_version"}


@pytest.fixture(scope="module")
def migrated() -> Iterator["psycopg.Connection"]:
    """Apply the migration to an empty database; downgrade fully afterwards."""
    cfg = alembic_config()
    with psycopg.connect(DB_URL, autocommit=True) as conn:
        for table in list_tables(conn):
            conn.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
        conn.execute("DROP TABLE IF EXISTS alembic_version CASCADE")
    command.upgrade(cfg, "head")
    with psycopg.connect(DB_URL, autocommit=True) as conn:
        yield conn
    command.downgrade(cfg, "base")


def new_user(conn: "psycopg.Connection", kind: str = "human", owner: bool = False) -> str:
    return conn.execute(
        """
        INSERT INTO app_user (email, display_name, user_kind, is_owner, created_by)
        VALUES (%s, %s, %s, %s, %s) RETURNING id
        """,
        (f"{uuid.uuid4().hex}@example.test", "Test User", kind, owner, SYSTEM_USER_ID),
    ).fetchone()[0]


def test_all_expected_tables_exist(migrated: "psycopg.Connection") -> None:
    assert list_tables(migrated) == EXPECTED_TABLES


def test_reference_data_seeded(migrated: "psycopg.Connection") -> None:
    roles = dict(
        migrated.execute("SELECT name, max_privacy_tier FROM role ORDER BY name").fetchall()
    )
    assert roles == {
        "owner": "P3", "steward": "P3", "trusted": "P1", "public": "P0", "service": "P2"
    }
    kind = migrated.execute(
        "SELECT user_kind FROM app_user WHERE id = %s", (SYSTEM_USER_ID,)
    ).fetchone()
    assert kind == ("service",)
    version = migrated.execute(
        "SELECT value FROM schema_metadata WHERE key = 'schema_version'"
    ).fetchone()
    assert version == ("1",)


def test_privacy_tier_defaults(migrated: "psycopg.Connection") -> None:
    creator = new_user(migrated)
    person_tier = migrated.execute(
        "INSERT INTO person (full_name, created_by) VALUES ('Test', %s) RETURNING privacy_tier",
        (creator,),
    ).fetchone()[0]
    assert person_tier == "P2"
    journal_tier = migrated.execute(
        """
        INSERT INTO journal_entry (entry_date, body, created_by)
        VALUES (current_date, 'entry', %s) RETURNING privacy_tier
        """,
        (creator,),
    ).fetchone()[0]
    assert journal_tier == "P3"


def test_invalid_privacy_tier_rejected(migrated: "psycopg.Connection") -> None:
    creator = new_user(migrated)
    with pytest.raises(psycopg.errors.CheckViolation):
        migrated.execute(
            "INSERT INTO note (body, privacy_tier, created_by) VALUES ('x', 'P9', %s)",
            (creator,),
        )


def test_updated_at_and_row_version_maintained(migrated: "psycopg.Connection") -> None:
    creator = new_user(migrated)
    note_id = migrated.execute(
        "INSERT INTO note (body, created_by) VALUES ('v1', %s) RETURNING id", (creator,)
    ).fetchone()[0]
    row = migrated.execute(
        """
        UPDATE note SET body = 'v2' WHERE id = %s
        RETURNING row_version, updated_at >= created_at
        """,
        (note_id,),
    ).fetchone()
    assert row == (2, True)


def test_artifact_checksum_dedupe_respects_soft_delete(
    migrated: "psycopg.Connection",
) -> None:
    creator = new_user(migrated)

    def insert(checksum: str) -> str:
        return migrated.execute(
            """
            INSERT INTO artifact
                (title, artifact_type, storage_ref, mime_type, byte_size, checksum, created_by)
            VALUES ('doc', 'document', 'k', 'text/plain', 1, %s, %s) RETURNING id
            """,
            (checksum, creator),
        ).fetchone()[0]

    first = insert("dup-hash")
    with pytest.raises(psycopg.errors.UniqueViolation):
        insert("dup-hash")
    migrated.execute("UPDATE artifact SET deleted_at = now() WHERE id = %s", (first,))
    insert("dup-hash")


def test_single_owner_rule(migrated: "psycopg.Connection") -> None:
    new_user(migrated, owner=True)
    with pytest.raises(psycopg.errors.UniqueViolation):
        new_user(migrated, owner=True)


def make_claim(conn: "psycopg.Connection", creator: str, tier: str = "flagged") -> str:
    return conn.execute(
        """
        INSERT INTO claim
            (subject_type, subject_id, predicate, statement, confidence_tier, created_by)
        VALUES ('Person', %s, 'test_predicate', %s, %s, %s) RETURNING id
        """,
        (str(uuid.uuid4()), f"statement {uuid.uuid4().hex}", tier, creator),
    ).fetchone()[0]


def test_tier_raise_blocked_without_authorization(migrated: "psycopg.Connection") -> None:
    creator = new_user(migrated)
    claim_id = make_claim(migrated, creator)
    with pytest.raises(psycopg.errors.RaiseException, match="never-auto-upgrade"):
        migrated.execute(
            "UPDATE claim SET confidence_tier = 'self_reported' WHERE id = %s", (claim_id,)
        )


def test_verification_requires_support_and_human(migrated: "psycopg.Connection") -> None:
    human = new_user(migrated, kind="human")
    claim_id = make_claim(migrated, human, tier="self_reported")

    with psycopg.connect(DB_URL) as txn:
        txn.execute("SET LOCAL legacy.tier_change_authorized = 'true'")
        with pytest.raises(psycopg.errors.RaiseException, match="supporting ClaimSource"):
            txn.execute(
                """
                UPDATE claim SET confidence_tier = 'verified',
                       verified_at = now(), verified_by = %s WHERE id = %s
                """,
                (human, claim_id),
            )

    source_id = migrated.execute(
        "INSERT INTO source (source_type, title, created_by) "
        "VALUES ('url', 'Evidence', %s) RETURNING id",
        (human,),
    ).fetchone()[0]
    migrated.execute(
        "INSERT INTO claim_source (claim_id, source_id, support_type, created_by) "
        "VALUES (%s, %s, 'supports', %s)",
        (claim_id, source_id, human),
    )

    service = new_user(migrated, kind="service")
    with psycopg.connect(DB_URL) as txn:
        txn.execute("SET LOCAL legacy.tier_change_authorized = 'true'")
        with pytest.raises(psycopg.errors.RaiseException, match="human principal"):
            txn.execute(
                """
                UPDATE claim SET confidence_tier = 'verified',
                       verified_at = now(), verified_by = %s WHERE id = %s
                """,
                (service, claim_id),
            )

    with psycopg.connect(DB_URL) as txn:
        txn.execute("SET LOCAL legacy.tier_change_authorized = 'true'")
        txn.execute(
            """
            UPDATE claim SET confidence_tier = 'verified',
                   verified_at = now(), verified_by = %s WHERE id = %s
            """,
            (human, claim_id),
        )
        txn.commit()

    tier = migrated.execute(
        "SELECT confidence_tier FROM claim WHERE id = %s", (claim_id,)
    ).fetchone()[0]
    assert tier == "verified"

    # Automated downgrade needs no authorization, but the tier/verifier
    # consistency CHECK requires clearing the verification columns.
    migrated.execute(
        """
        UPDATE claim SET confidence_tier = 'flagged',
               verified_at = NULL, verified_by = NULL WHERE id = %s
        """,
        (claim_id,),
    )


def test_verified_columns_require_verified_tier(migrated: "psycopg.Connection") -> None:
    creator = new_user(migrated)
    with pytest.raises(psycopg.errors.CheckViolation):
        migrated.execute(
            """
            INSERT INTO claim
                (subject_type, subject_id, predicate, statement, confidence_tier,
                 verified_at, verified_by, created_by)
            VALUES ('Person', %s, 'p', 's', 'flagged', now(), %s, %s)
            """,
            (str(uuid.uuid4()), creator, creator),
        )


def test_audit_log_is_append_only(migrated: "psycopg.Connection") -> None:
    actor = new_user(migrated)
    entry_id = migrated.execute(
        """
        INSERT INTO audit_log_entry (actor_type, actor_id, action, created_by)
        VALUES ('user', %s, 'create', %s) RETURNING id
        """,
        (actor, actor),
    ).fetchone()[0]
    with pytest.raises(psycopg.errors.RaiseException, match="append-only"):
        migrated.execute(
            "UPDATE audit_log_entry SET action = 'update' WHERE id = %s", (entry_id,)
        )
    with pytest.raises(psycopg.errors.RaiseException, match="append-only"):
        migrated.execute("DELETE FROM audit_log_entry WHERE id = %s", (entry_id,))


def test_edge_uniqueness_with_null_validity(migrated: "psycopg.Connection") -> None:
    creator = new_user(migrated)
    a, b = str(uuid.uuid4()), str(uuid.uuid4())
    migrated.execute(
        """
        INSERT INTO edge (from_type, from_id, to_type, to_id, edge_type, created_by)
        VALUES ('Person', %s, 'Project', %s, 'collaborated_on', %s)
        """,
        (a, b, creator),
    )
    with pytest.raises(psycopg.errors.UniqueViolation):
        migrated.execute(
            """
            INSERT INTO edge (from_type, from_id, to_type, to_id, edge_type, created_by)
            VALUES ('Person', %s, 'Project', %s, 'collaborated_on', %s)
            """,
            (a, b, creator),
        )


def test_vector_columns_accept_embeddings(migrated: "psycopg.Connection") -> None:
    creator = new_user(migrated)
    dims = migrated.execute(
        """
        INSERT INTO memory_record
            (memory_type, content, salience, embedding, embedding_model_version, created_by)
        VALUES ('semantic', 'remembers', 0.5, '[0.1, 0.2, 0.3]', 'test-model-1', %s)
        RETURNING vector_dims(embedding)
        """,
        (creator,),
    ).fetchone()[0]
    assert dims == 3


def test_downgrade_is_reversible() -> None:
    """Applies after the module fixture has torn down: base leaves nothing,
    and a fresh upgrade succeeds again (clean apply twice over)."""
    cfg = alembic_config()
    command.downgrade(cfg, "base")
    with psycopg.connect(DB_URL, autocommit=True) as conn:
        assert list_tables(conn) == set()
    command.upgrade(cfg, "head")
    with psycopg.connect(DB_URL, autocommit=True) as conn:
        assert list_tables(conn) == EXPECTED_TABLES
    command.downgrade(cfg, "base")
    with psycopg.connect(DB_URL, autocommit=True) as conn:
        assert list_tables(conn) == set()
