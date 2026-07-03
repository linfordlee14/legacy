# legacy-api

The Legacy platform API service (FastAPI). Governing specifications:
`architecture/MASTER_ARCHITECTURE.md`, `api/API_SPECIFICATION.md`,
`deployment/DEPLOYMENT.md`.

Current scope (BUILD_ORDER steps 1-5): service skeleton, health endpoints,
the full schema migration, authentication, and the authorization core. The
`/v1` conventions layer arrives at step 6 (MVP-007).

## Authorization (security/AUTHORIZATION.md)

`policy.py` is the single decision service behind every enforcement point
(4.4): deny by default, role permission matrix (4.2), privacy-tier ceilings
intersected with live grants (revocation is immediate), scoped trusted
access via Grant rows and membership edges (4.3), and agent identities that
inherit the invoking principal's ceiling with tier/grant/seal actions hard
denied and per-agent tool allowlists failing closed (4.5). Every denial and
every sensitive allow is audited with the policy version (4.7). Reads go
through `read_or_not_found`, which makes missing rows and above-ceiling rows
byte-identical (no existence leaks). Endpoints resolve their context with
`resolve_context` plus `authenticate` or `authenticate_optional` (the public
visitor path).

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
