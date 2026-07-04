"""Database access: a single async connection pool owned by the app lifespan."""

from psycopg_pool import AsyncConnectionPool


def create_pool(database_url: str) -> AsyncConnectionPool:
    # psycopg accepts standard postgresql:// URLs directly.
    # Connection-level state must not be mutated by borrowers: the pool
    # does not reset it on return, so it would leak into later requests
    # (use per-cursor row factories, never conn.row_factory).
    return AsyncConnectionPool(database_url, min_size=1, max_size=5, open=False)
