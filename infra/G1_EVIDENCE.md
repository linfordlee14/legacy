# Gate G1 evidence log

Opened at BUILD_ORDER step 21 (MVP-021 acceptance: "G1 evidence log
opened"). Gate G1 is the stack-confirmation decision of ROADMAP 4.5:
after real usage, confirm or revise the baseline defaults (Supabase,
FastAPI, Next.js) via ADR update in MASTER_ARCHITECTURE. The gate closes
with an owner decision recorded as an ADR; this log collects the evidence
that decision needs.

## Phase 1 exit criteria evidence

| # | Criterion (ROADMAP 4.5) | Evidence | State |
|---|--------------------------|----------|-------|
| 1 | Owner signs in via OIDC and PAT; every sign-in audited | OIDC resource-server auth with mandatory owner MFA, PAT lifecycle with hash-only storage and live revocation; every event audited (test_auth, test_pats; 122-test security re-test green) | Code-verified; production sign-in against the real provider is provisioning-time |
| 2 | Document and note stored as Artifact and Note at P2 with an IngestionJob record | Ingestion pipeline with preservation-before-parsing, dedup, review flags, provenance stamps (test_ingestion; test_seed_documents) | Code-verified and exercised on the reference corpus |
| 3 | Automated backups on schedule; one full restore drill passed | Runbook 2 drill PASS (3.5 s) and runbook 3 full-platform drill PASS (5 s, database + storage + config + indexes + API boot + smoke); CI runs the drill per push and monthly | Drills executed 2026-07-04; scheduled production cadence is provisioning-time |
| 4 | CI runs the test baseline on every change and blocks on failure | make ci: spec checks, lint, types, SAST, dependency audits, 230 API tests, 42 web tests, build; GitHub workflow mirrors it | Verified every step since step 2 |
| 5 | Seed corpus imported and listed in the workspace | 72 claims (MVP-013), repository documents (MVP-014 demo run), library + search + queue screens serve them | Verified on the reference corpus; the owner's personal document batch is deferred by owner decision until after v0.2.0-alpha |

## Stack observations for the G1 decision

- PostgreSQL 16 + pgvector 0.6.0 carried every feature to date (claims,
  provenance, revisions, chunk store, version-scoped ANN indexes) with the
  measured baselines in [PERFORMANCE_BASELINE](PERFORMANCE_BASELINE.md);
  nothing observed argues against the ADR-03/ADR-04 defaults at this scale.
- FastAPI + psycopg async served all 21 steps; the one recurring defect
  class was connection-state leakage on the shared pool (fixed, step 17),
  an argument for the per-cursor discipline now documented in db.py.
- Next.js App Router carried the workspace shell, search, and queue
  screens with the design-system placeholder palette; no framework
  friction recorded.
- Supabase-specific surfaces (managed auth, storage adapter, PITR) remain
  provisioning-time; the G1 decision cannot fully close until they carry
  real usage, per the gate's own definition.

## Outstanding before the gate closes

Tracked in [VERIFICATION_LOG](VERIFICATION_LOG.md) and
[GO_LIVE_CHECKLIST](GO_LIVE_CHECKLIST.md): provisioned infrastructure
re-runs (perf baseline, with-provider search), owner checklist sign-off,
escrowed real backup keys, one production claim resolution, and the
owner's stack-confirmation ADR itself.
