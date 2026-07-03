"""Alembic environment. The URL comes from LEGACY_DATABASE_URL only."""

import os

from alembic import context
from sqlalchemy import create_engine

config = context.config

# Schema is defined by hand-written SQL migrations (database/DATABASE_SCHEMA.md
# is the contract); there is no ORM metadata to autogenerate from.
target_metadata = None


def get_url() -> str:
    url = os.environ.get("LEGACY_DATABASE_URL")
    if not url:
        raise RuntimeError(
            "LEGACY_DATABASE_URL is not set. Migrations never use a committed "
            "URL (DEP-18); export the environment variable and retry."
        )
    # Standard postgresql:// URLs (Supabase's form) run on the psycopg 3 driver.
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def run_migrations_offline() -> None:
    context.configure(url=get_url(), literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(get_url())
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
