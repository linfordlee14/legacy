"""PersonalAccessToken (DATABASE_SCHEMA 4.6, added as a documented defect fix;
AUTHENTICATION 4.3; API_SPECIFICATION 4.5). Additive only (expand-and-contract,
DEP-26).

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-03
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE personal_access_token (
            id uuid PRIMARY KEY DEFAULT uuid_v7(),
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now(),
            deleted_at timestamptz,
            created_by uuid NOT NULL REFERENCES app_user(id),
            origin_type text NOT NULL DEFAULT 'manual'
                CHECK (origin_type IN ('manual','ingestion','agent','system')),
            origin_ref_type text,
            origin_ref_id uuid,
            row_version integer NOT NULL DEFAULT 1,
            user_id uuid NOT NULL REFERENCES app_user(id),
            label text NOT NULL,
            token_hash text NOT NULL,
            scopes jsonb NOT NULL,
            expires_at timestamptz NOT NULL,
            last_used_at timestamptz,
            revoked_at timestamptz,
            CHECK (expires_at > created_at),
            -- Belt for the 12-month maximum (AUTHENTICATION 4.3); the service
            -- layer enforces 365 days exactly.
            CHECK (expires_at <= created_at + interval '370 days')
        )
    """)
    op.execute("CREATE UNIQUE INDEX uq_pat_token_hash ON personal_access_token (token_hash)")
    op.execute("CREATE INDEX ix_pat_user ON personal_access_token (user_id)")
    op.execute("""
        CREATE TRIGGER trg_touch_personal_access_token
        BEFORE UPDATE ON personal_access_token
        FOR EACH ROW EXECUTE FUNCTION touch_row()
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS personal_access_token CASCADE")
