"""Database access: a single async connection pool owned by the app lifespan."""

from psycopg_pool import AsyncConnectionPool


def create_pool(database_url: str) -> AsyncConnectionPool:
    # psycopg accepts standard postgresql:// URLs directly.
    return AsyncConnectionPool(database_url, min_size=1, max_size=5, open=False)
