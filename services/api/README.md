# legacy-api

The Legacy platform API service (FastAPI). Governing specifications:
`architecture/MASTER_ARCHITECTURE.md`, `api/API_SPECIFICATION.md`,
`deployment/DEPLOYMENT.md`.

Current scope (BUILD_ORDER steps 1-4): service skeleton, health endpoints,
the full schema migration, and authentication. The `/v1` conventions layer
arrives at step 6 (MVP-007).

## Authentication (security/AUTHENTICATION.md)

The API is an OIDC resource server: the managed provider (Supabase Auth by
default decision) owns login, MFA ceremonies, and refresh-token rotation;
this service verifies provider-signed JWTs (issuer, audience, signature via
JWKS), maps `auth_subject` to `app_user`, enforces mandatory MFA for the
owner (aal2 or an accepted amr factor; SMS is not accepted), detects new
devices from audit history, applies progressive rate limiting, and audits
every event. Configure with `LEGACY_OIDC_ISSUER` and `LEGACY_OIDC_AUDIENCE`
(non-secret); `LEGACY_OIDC_JWKS_URL` overrides the derived JWKS location.
Sensitive endpoints use the `require_step_up` dependency
(AUTHENTICATION 4.3: authentication event within 10 minutes).

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
