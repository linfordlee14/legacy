"""Revision (DATABASE_SCHEMA 4.6, added as a documented defect fix;
API_SPECIFICATION 4.4 revisions endpoint; UI_UX soft delete with undo;
MVP-015). Additive only (expand-and-contract, DEP-26).

Base-field exceptions per the spec: a revision is an immutable point-in-time
record, so it carries no updated_at, deleted_at, privacy_tier, origin fields,
or row_version of its own. Immutability outside the redaction workflow is
enforced by a guard trigger using the same transaction-local authorization
mechanism as claim_tier_guard (legacy.redaction_authorized).

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-04
"""

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE revision (
            id uuid PRIMARY KEY DEFAULT uuid_v7(),
            created_at timestamptz NOT NULL DEFAULT now(),
            created_by uuid NOT NULL REFERENCES app_user(id),
            entity_type text NOT NULL,
            entity_id uuid NOT NULL,
            row_version integer NOT NULL,
            change_kind text NOT NULL CHECK (change_kind IN ('update','tier_change')),
            snapshot jsonb NOT NULL
        )
    """)
    op.execute("""
        CREATE UNIQUE INDEX uq_revision_version ON revision
        (entity_type, entity_id, row_version)
    """)
    op.execute("CREATE INDEX ix_revision_entity ON revision (entity_type, entity_id)")

    op.execute("""
        CREATE OR REPLACE FUNCTION revision_guard() RETURNS trigger AS $$
        BEGIN
            IF current_setting('legacy.redaction_authorized', true) IS DISTINCT FROM 'true' THEN
                RAISE EXCEPTION
                    'revision rows are immutable outside the redaction workflow (DATABASE_SCHEMA 4.6)';
            END IF;
            IF TG_OP = 'DELETE' THEN
                RETURN OLD;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER trg_revision_guard
        BEFORE UPDATE OR DELETE ON revision
        FOR EACH ROW EXECUTE FUNCTION revision_guard()
    """)


def downgrade() -> None:
    op.execute("DROP TABLE revision")
    op.execute("DROP FUNCTION IF EXISTS revision_guard()")
