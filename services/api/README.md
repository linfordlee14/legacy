# legacy-api

The Legacy platform API service (FastAPI). Governing specifications:
`architecture/MASTER_ARCHITECTURE.md`, `api/API_SPECIFICATION.md`,
`deployment/DEPLOYMENT.md`.

Current scope (BUILD_ORDER step 1): service skeleton with configuration and
health endpoints. The `/v1` API surface arrives at step 6 (MVP-007).

## Run locally

```
cd services/api
uv venv && uv pip install -e ".[dev]"
LEGACY_ENV=local .venv/bin/uvicorn legacy_api.main:app --reload
```

## Database migrations

The schema is defined by hand-written Alembic migrations implementing
`database/DATABASE_SCHEMA.md` exactly. The URL always comes from the
environment (DEP-18):

```
make db-up                                  # local Postgres with pgvector
make migrate                                # alembic upgrade head
make migrate-down                           # step back one revision
```

## Test

```
.venv/bin/pytest                            # unit tests
LEGACY_TEST_DATABASE_URL=postgresql://legacy:legacy@localhost:5432/legacy_test \
  .venv/bin/pytest                          # plus schema migration tests
```

The migration tests require a disposable database they may own entirely
(CI-09); never point them at a database with real content.
