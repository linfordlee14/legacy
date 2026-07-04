# Go-live checklist (MVP-021)

Status vocabulary, used exactly: **measured** (a number was produced by a
recorded method), **verified** (a behavior was executed and observed),
**simulated** (executed with a documented stand-in), **provisioning-time**
(cannot exist before real infrastructure), **outstanding** (needs a person
or a scheduled event). Nothing below is estimated.

Run record: 2026-07-04, sandbox container, PostgreSQL 16.13 + pgvector
0.6.0, reference corpus (72 seeded claims, repository documents, seeded
audit history). Cross-references: [PERFORMANCE_BASELINE](PERFORMANCE_BASELINE.md),
[VERIFICATION_LOG](VERIFICATION_LOG.md), [G1_EVIDENCE](G1_EVIDENCE.md).

| # | Item | Spec anchor | Status | Evidence |
|---|------|-------------|--------|----------|
| 1 | Full platform restore drill (runbook 3 + runbook 5 verification) | BACKUP_AND_RECOVERY 4.6-4.7 | **verified + measured** | `make full-restore-drill`: PASS, duration 5 s against the provisional 3600 s gate (NFR-052 budget 72 h); database plus object storage restored to fresh scratch; schema 0004 and ANN/FTS/uniqueness indexes present; 35 table row counts matched the manifest; audit log continuous through sequence 8; 3 sampled artifact reads byte-identical; API booted on restored state; smoke test green |
| 2 | Backup coverage includes object storage | BACKUP_AND_RECOVERY 4.2 | **verified** | backup.sh archives and encrypts the storage tree with the same hybrid scheme; restore.sh verifies its checksum; absence of the storage dir is a loud warning, never silent |
| 3 | Security re-test of auth and tier paths | MVP-021; SEC-37 | **verified** | `make security-retest`: 122 tests passed (auth, authz, PATs, content, edit, search leak suite, verification queue) |
| 4 | SAST clean | SEC-35 | **verified** | bandit high-severity: no findings (make audit, every CI run) |
| 5 | Dependency audit clean | SEC-36 | **verified** | pip-audit: no known vulnerabilities; npm audit high: 0 (make audit) |
| 6 | Alert pipeline delivers | OBSERVABILITY 4.5 | **verified (local channel)** | `make test-alert`: SEV-2 emission delivered to the owner notification channel (log notifier); real channel bindings are provisioning-time |
| 7 | Metrics exposed | OBSERVABILITY 4.4 | **verified** | /metrics serves request, latency, token-spend, and searchable-lag instruments (perf harness assertion, step 19) |
| 8 | Performance budgets | NFR 4.1 | **measured (store path)** | See PERFORMANCE_BASELINE.md: NFR-001 103.1 ms p95 (budget 300); NFR-002 107.2 ms p95 store path (budget 1500); NFR-005 0.63 s (budget 120 s); with-provider re-run is outstanding (Gemini key) |
| 9 | Verification queue operational | MVP-020; FS-009 | **verified** | Six section 12 items listed; end-to-end resolution proven by test; production resolution of one real claim is outstanding (owner action) |
| 10 | LLM red-team set (SEC-38) | SECURITY 4.4 | **not applicable yet** | Gated on agent/twin behavior releases; no generation surface exists in the MVP |
| 11 | Penetration test (SEC-39) | SECURITY 4.4 | **outstanding** | Cadence and provider are an open owner budget decision (TODO(verify) in SECURITY); schedule before public surface exposure |
| 12 | Point-in-time restore (runbook 2) | BACKUP_AND_RECOVERY 4.6 | **verified (logical fallback)** | `make restore-drill`: PASS 3.5 s (step 19 record); provider PITR is provisioning-time (Supabase project setting) |
| 13 | Steward drill (runbook 4 support; NFR-053) | BACKUP_AND_RECOVERY 4.7 | **outstanding** | Needs a human steward; vault-only runbook 4 arrives with vault work (TASK-504/508) |
| 14 | Offsite immutable backup destination | BACKUP_AND_RECOVERY 4.3 | **provisioning-time** | Owner-controlled storage independent of the production provider; scripts are destination-agnostic |
| 15 | Production secrets, OIDC provider, domain, TLS | DEPLOYMENT; DEP-18 | **provisioning-time** | Supabase project, secret manager entries (database URL, LEGACY_GEMINI_API_KEY), DNS |
| 16 | Key escrow for backup encryption | BACKUP_AND_RECOVERY 4.4; DEP-22 | **provisioning-time / outstanding** | Owner generates the real key pair and places escrow copies; drills used ephemeral pairs (synthetic data only), which the scripts mark explicitly |
| 17 | Monthly scheduled CI drill firing | CI_CD | **outstanding** | Workflow present and per-push drill green; first scheduled firing confirmed in Actions history (VERIFICATION_LOG, step 8 row) |

## Sign-off

Owner signature (required before go-live; MVP-021 acceptance): _pending_

Prepared 2026-07-04 at BUILD_ORDER step 21. Items 10-17 do not block the
checklist's preparation; items 11, 13, 16, and 17 must be closed or
explicitly accepted by the owner at Gate G1.
