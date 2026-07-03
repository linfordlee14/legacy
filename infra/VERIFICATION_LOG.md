# Outstanding verification log

Items verified in one environment but pending confirmation in another.
Reviewed at each phase gate alongside the Gate evidence log (MVP-023).

| Recorded | Item | Verified where | Pending where | Owner action |
|----------|------|----------------|---------------|--------------|
| 2026-07-03 | Docker image build and `make up` compose path (step 1); local Postgres via compose (steps 3+) | CI runners (docker-image and backup-drill jobs); sandbox Postgres 16.13 with pgvector 0.6.0 | Owner laptop: Docker/PostgreSQL cannot run there | Validate on provisioned infrastructure or a Docker-capable machine at Gate G1 |
| 2026-07-03 | `npm audit` gate (step 2) | Sandbox and CI (registry reachable; 0 vulnerabilities at last run) | Owner laptop: npm registry unreachable | Re-run `make audit` from a connected network; CI remains the authoritative gate |
| 2026-07-03 | Monthly scheduled CI run (restore drill cadence, step 8) | Workflow syntax validated; per-push drill green | First scheduled firing (3rd of next month) | Confirm the scheduled run appears in Actions history |
