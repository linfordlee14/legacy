"""Chunk metadata columns and the version-scoped indexes (MVP-016;
DATABASE_SCHEMA 4.6 EmbeddingChunk defect fix and 4.7 indexing strategy;
ADR-16). Additive only (expand-and-contract, DEP-26).

The embedding column stays dimension-untyped (dimension is a property of
the model version); the ANN index types it through a cast expression, so
one index exists per active embedding_model_version exactly as 4.7
requires, and queries use the same expression to hit it.

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-04
"""

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

ACTIVE_VERSION = "gemini-embedding-001:1536"  # ADR-16 pin, point-in-time
DIMENSIONS = 1536


def upgrade() -> None:
    # RAG-05 provenance packet fields (defect fix documented in the spec).
    op.execute("ALTER TABLE embedding_chunk ADD COLUMN heading_path text")
    op.execute("ALTER TABLE embedding_chunk ADD COLUMN language text")
    op.execute(
        "ALTER TABLE embedding_chunk "
        "ADD COLUMN injection_flag boolean NOT NULL DEFAULT false"
    )

    # One ANN index per active embedding model version (4.7; AIA-11).
    op.execute(f"""
        CREATE INDEX ix_embedding_chunk_ann_gemini_1536 ON embedding_chunk
        USING hnsw ((embedding::vector({DIMENSIONS})) vector_cosine_ops)
        WHERE embedding_model_version = '{ACTIVE_VERSION}'
          AND superseded_by IS NULL
    """)

    # Lexical index over live chunk text (RAG-07b).
    op.execute("""
        CREATE INDEX ix_embedding_chunk_text_fts ON embedding_chunk
        USING gin (to_tsvector('english', chunk_text))
        WHERE superseded_by IS NULL
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_embedding_chunk_text_fts")
    op.execute("DROP INDEX IF EXISTS ix_embedding_chunk_ann_gemini_1536")
    op.execute("ALTER TABLE embedding_chunk DROP COLUMN injection_flag")
    op.execute("ALTER TABLE embedding_chunk DROP COLUMN language")
    op.execute("ALTER TABLE embedding_chunk DROP COLUMN heading_path")
