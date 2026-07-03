# legacy-api

The Legacy platform API service (FastAPI). Governing specifications:
`architecture/MASTER_ARCHITECTURE.md`, `api/API_SPECIFICATION.md`,
`deployment/DEPLOYMENT.md`.

Current scope (BUILD_ORDER steps 1-10): service skeleton, health endpoints,
the full schema migration, authentication with PATs, the authorization
core, the `/v1` conventions layer with the claims resource, the
observability baseline, and the ingestion pipeline for documents and notes.

## Ingestion (FS-001 slice; FR-ING-001, 007, 008)

`POST /v1/ingestion/jobs` accepts multipart files plus a JSON payload of
notes; originals are stored content-addressed in object storage BEFORE any
parsing (`storage.py`: local backend now, Supabase Storage behind the same
port at provisioning). The pipeline extracts text from Markdown, plain
text, and PDF into `canonical_markdown`, dedups by content hash (duplicate
items reference the existing artifact, no second row), flags unparseable
files for review with the original preserved, and stamps every row with
ingestion provenance and the P2 default tier. Jobs expose per-item status,
are listable and retryable (`POST /{id}/retry` reprocesses review and
failed items), and honor Idempotency-Key on creation. Creation requires
CONTENT_CREATE (owner or a write:content machine token); job reads are
owner-only.

## Observability (deployment/OBSERVABILITY.md)

`obs/` implements the baseline: structured JSON logs where every event
carries service, environment, request and trace ids, and typed fields only;
a redaction filter enforcing the absolute ID-only content rule (field
allowlist, content-field stripping, email/token/long-text scrubbing,
fail-closed drops); log-emitted spans reconstructable per trace id
(`X-Trace-ID` on every response); a per-app Prometheus registry at
`GET /metrics` (request latency and outcomes per route group, plus the
dormant token-spend counter the model router will feed); and the SEV-1 to
SEV-4 alert router with owner-configured quiet hours that SEV-1 overrides.
`make test-alert` proves the emission-to-owner-channel path. Channel
bindings, dashboards, and trace export bind at platform provisioning.

## /v1 conventions (api/API_SPECIFICATION.md 4.1 to 4.3)

`api/errors.py` renders every failure as the one envelope
(`{"error": {code, message, request_id, details?}}`) with the ten canonical
codes exactly; request ids are accepted via `X-Request-ID` or minted, and
echoed on every response. `api/pagination.py` implements opaque cursor
pagination (default 25, max 100). `api/idempotency.py` gives mutating routes
Idempotency-Key replay (identical retry returns the original result;
key reuse with a different request is refused as `idempotency_replay`).
`api/ratelimit.py` applies a token-bucket request budget to all of `/v1`
with `Retry-After`. `provenance.py` serializes the mandatory provenance
block (per-claim tier plus resolvable sources). First real resource:
`GET /v1/claims` and `GET /v1/claims/{id}`, tier-filtered through the policy
service with grant-scope refinement for trusted callers.

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

Personal access tokens (AUTHENTICATION 4.3, API_SPECIFICATION 4.5): minted
at `POST /v1/auth/tokens` (owner, step-up; the secret is shown exactly
once), listed as metadata, revoked immediately via DELETE. PATs authenticate
as dedicated service principals, are stored hash-only, expire within 12
months, are audited on every use, and confer a scope-derived ceiling capped
at P2 (never P3); `write:content` and `admin` scopes widen the machine
action set. Machines cannot pass step-up.

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
