# legacy-api

The Legacy platform API service (FastAPI). Governing specifications:
`architecture/MASTER_ARCHITECTURE.md`, `api/API_SPECIFICATION.md`,
`deployment/DEPLOYMENT.md`.

Current scope (BUILD_ORDER steps 1-10 and 13-17): service skeleton,
health endpoints, the full schema migration, authentication with PATs, the
authorization core, the `/v1` conventions layer with the claims resource,
the observability baseline, the ingestion pipeline for documents and
notes, the MASTER_CONTEXT seed import, the owner document batch import,
revision history with soft delete and undo, and the chunk store with
embeddings and lexical indexing.

## Search (MVP-017; API_SPECIFICATION 4.4; FS-004; NFR-035)

`GET /v1/search?q=...&mode=hybrid|lexical|semantic&limit=` serves ranked
retrieval over the chunk store for any caller, ceiling-filtered: the
privacy-tier predicate executes inside the datastore query before ranking
or response assembly (NFR-035), trusted callers get per-row grant-scope
refinement, and counts reflect only at-or-below-ceiling content, so
existence above the ceiling never leaks, not even as a number. Hybrid
fuses the independently retrieved lexical and semantic lists by
reciprocal rank fusion (ADR-17; k and pool sizes are configuration);
lexical uses full-text search with stemming and exact-phrase support
(bare multi-word queries are OR-joined for recall, ranked by match
density). Results carry title, snippet, heading-path locator, privacy
tier, mode-specific score, and the provenance block. Semantic and hybrid
degrade to lexical-only with an explicit `degraded: true` flag when the
query cannot be embedded (never silently); overlong queries truncate
with notice; zero lexical matches return an empty list, never an
invention. The golden query set (`tests/golden/search_golden.json`, v1)
records the regression baseline: lexical recall@10 of 1.00 on the
repository corpus, lexical p95 well inside NFR-001, hybrid store-path
p95 well inside NFR-002 (with-provider latency lands at provisioning).

## Chunking, embeddings, and indexes (MVP-016; RAG_PIPELINE 4.2-4.4; ADR-16)

Stored notes and artifacts are chunked heading-aware (RAG-04; sizes are
configuration) and embedded through the Model Router (`ai/`): the single
choke point of ADR-06, pinned by ADR-16 to exactly `gemini-embedding-001`
at 1536 dimensions (`LEGACY_GEMINI_API_KEY` via the environment; never an
auto-tracking alias, AIA-07). Every EmbeddingChunk row carries the RAG-05
provenance packet: parent reference, ordinal, heading path for citation
locators, inherited privacy tier (re-tiering propagates in the same
transaction, RAG-32), content hash, injection-flag status, and the exact
model version. Unchanged sources are no-ops and identical text reuses
cached vectors by content hash (RAG-03; cost control); text changes
supersede the old generation, never delete it. Two indexes serve the
store (RAG-07): a version-scoped HNSW cosine index (vectors from
different versions are never compared, AIA-11) and a lexical full-text
index. Retrieval primitives (`rag/retrieval.py`) apply the caller's tier
predicate inside the store (RAG-12) and exclude soft-deleted parents
immediately; the fused query pipeline and search API arrive with MVP-017.
When the embedding provider is unreachable, ingestion continues and
entities queue for `make reindex`, counted by the searchable-lag metric
(RAG-08); `make reindex` is also the rebuild-from-source drill (NFR-024).

## Revision history and soft delete (MVP-015; DATABASE_SCHEMA 4.6, 4.8)

`PATCH /v1/{collection}/{id}` edits the editable field set per collection
(notes: title, body, note_context; artifacts: title and the derived
canonical_markdown, never the stored original). Every edit preserves the
displaced version as an immutable Revision row in the same transaction;
`GET .../revisions` lists them owner-only, newest first. Privacy tier
moves require the explicit `tier_change` sub-action with a fresh
authentication event and stay within P0 to P2 (P3 sealing belongs to the
journal workflow). `DELETE` is soft per NFR-022: the row and content
survive, hidden from every default read immediately, reversible via
`POST .../restore` while retained (90-day window; permanent erasure only
via the post-MVP redaction workflow). All mutations honor Idempotency-Key,
flow through the policy service, and write audit entries. Revision rows
are guarded in the database: updates and deletes raise unless the
redaction workflow explicitly authorizes them.

## Owner document batch (MVP-014; roadmap Phase 1 exit criterion 5)

`make seed-docs DOCS="path/to/folder" [TIER=P0-P3] [EXT=".md,.txt,.pdf"]`
(or `python -m legacy_api.seed.documents`) walks the given files and
directories and runs them through the ingestion pipeline: originals stored
content-addressed before parsing, extraction into `canonical_markdown` for
Markdown, text, and PDF, checksum dedup, review flags for failures (the
CLI exits 1 while items need review, and prints their names), and
ingestion provenance plus the P2 default tier on every row. Re-running a
batch is idempotent: existing content dedups to the existing Artifact
rows, while each run is still recorded as its own IngestionJob and audit
entry. DOCS paths are relative to the repository root; the storage
directory must be the same one the API serves from.

## Seed import (MVP-013; DATABASE_SCHEMA 4.4)

`make seed` (or `python -m legacy_api.seed`) imports the curated
transcription of `knowledge/MASTER_CONTEXT.md` (`seed/master_context_data.py`)
as Claim rows at their exact confidence tiers, with Source stubs and
ClaimSource links (the document mentions every claim; verified claims cite
their platform source, URLs pending TASK-001), attributed to the owner
Person and the section 6 Projects. The import is idempotent: claims,
sources, projects, and links are find-or-create, and an existing claim's
tier is never touched (tier changes belong solely to the owner-verified
path). Every run is recorded as an IngestionJob plus an audit entry, and
the six section 12 verification items land as exactly six flagged claims
ready for the MVP-020 queue.

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

## Content reads (API_SPECIFICATION 4.4)

`GET /v1/{collection}` and `GET /v1/{collection}/{id}` serve the notes and
artifacts collections for the workspace shell: tier-filtered through the
policy service with per-row grant-scope refinement for trusted callers,
cursor-paginated, uniform not_found on single reads, and the provenance
block attached on detail. Writes continue to flow through ingestion;
editing with revisions arrives at MVP-015.

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
