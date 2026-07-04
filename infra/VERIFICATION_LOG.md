# Outstanding verification log

Items verified in one environment but pending confirmation in another.
Reviewed at each phase gate alongside the Gate evidence log (MVP-023).

| Recorded | Item | Verified where | Pending where | Owner action |
|----------|------|----------------|---------------|--------------|
| 2026-07-03 | Docker image build and `make up` compose path (step 1); local Postgres via compose (steps 3+) | CI runners (docker-image and backup-drill jobs); sandbox Postgres 16.13 with pgvector 0.6.0 | Owner laptop: Docker/PostgreSQL cannot run there | Validate on provisioned infrastructure or a Docker-capable machine at Gate G1 |
| 2026-07-03 | `npm audit` gate (step 2) | Sandbox and CI (registry reachable; 0 vulnerabilities at last run) | Owner laptop: npm registry unreachable | Re-run `make audit` from a connected network; CI remains the authoritative gate |
| 2026-07-03 | Monthly scheduled CI run (restore drill cadence, step 8) | Workflow syntax validated; per-push drill green | First scheduled firing (3rd of next month) | Confirm the scheduled run appears in Actions history |
| 2026-07-04 | Semantic and hybrid golden-set recall, and NFR-002 hybrid latency with real provider round-trips (step 17) | Store path and fusion verified with the deterministic test embedder (lexical recall@10 baseline 1.00; lexical p95 95 ms; hybrid store-path p95 98 ms) | Real `gemini-embedding-001` vectors: needs LEGACY_GEMINI_API_KEY | Provision the key, run `make reindex`, re-run the golden suite, and record semantic/hybrid recall plus with-provider NFR-002 at Gate G2 |
| 2026-07-04 | NFR-002 and NFR-005 with real provider round-trips; production-hardware re-run of the MVP-019 baseline (step 19) | Store-path baseline recorded in PERFORMANCE_BASELINE.md (all measured budgets green in the sandbox) | Real `gemini-embedding-001` calls and the production hardware profile | Provision the key and infrastructure, run `make perf-baseline` there, update PERFORMANCE_BASELINE.md at Gate G1/G2 |
| 2026-07-04 | NFR-009/NFR-010 page interactivity audits (step 19) | Next build green in CI; no interactivity measurement exists | Deployed environment plus the defined mid-range hardware and 10 Mbps profile | Run a Lighthouse-class audit against staging at provisioning |
| 2026-07-04 | NFR-053 steward restore drill (step 19) | Automated restore drill passes (3.5 s, 35 tables verified) | A human steward following documentation alone | Schedule the steward drill before Gate G1 sign-off |
