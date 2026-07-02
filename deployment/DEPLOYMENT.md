# DEPLOYMENT
### Deployment architecture and environment strategy for the Legacy platform

| Field | Value |
|-------|-------|
| Status | Draft |
| Owner | Linford Musiyambodza |
| Last updated | 2026-07-02 |
| Depends on | [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md), [MASTER_ARCHITECTURE](../architecture/MASTER_ARCHITECTURE.md), [CI_CD](./CI_CD.md), [SECURITY](../security/SECURITY.md) |

---

## 1. Purpose

This specification defines how Legacy is deployed and operated: its environments, its reference hosting topology, its infrastructure as code expectations, its configuration and secrets handling, its deployment and rollback procedures, its scaling and cost posture, and its exit strategy from every managed vendor. Legacy is a single-owner, lifelong platform, so the deployment design optimizes for operability by one person, decade-scale durability, and freedom to leave any provider, rather than for multi-tenant scale.

## 2. Goals

1. Run exactly one production instance, dedicated to the owner, with staging and local environments that faithfully mirror it.
2. Adopt a managed-first posture so that a solo founder spends time on the product, not on server administration.
3. Make every deployment reproducible from version-controlled definitions and reversible within minutes.
4. Keep the corpus exportable at all times through the Legacy Vault path, independent of any hosting vendor.
5. Keep monthly cost within a defined ceiling and review it on a fixed cadence.
6. Document a credible migration path away from each managed service before that service is adopted.

## 3. Scope

### In scope
- Environment strategy: local development, staging, production.
- Reference topology decision for frontend, backend, data, and model providers.
- Region preference and data residency considerations.
- Infrastructure as code expectations (described, not implemented).
- Configuration and secrets handling per environment.
- Deployment, smoke test, and rollback procedure.
- Zero-downtime expectations and maintenance windows.
- Scaling posture and background job architecture at deployment level.
- Cost posture and review cadence.
- Offline Legacy Vault delivery path at the infrastructure level.
- Vendor exit strategy.

### Out of scope
- Pipeline stage definitions (see [CI_CD](./CI_CD.md)).
- Telemetry, alerting, and SLOs (see [OBSERVABILITY](./OBSERVABILITY.md)).
- Backup schedules, retention, and restore runbooks (see [BACKUP_AND_RECOVERY](./BACKUP_AND_RECOVERY.md)).
- Application-level architecture (see [MASTER_ARCHITECTURE](../architecture/MASTER_ARCHITECTURE.md)).
- Any executable infrastructure definitions: this repository contains prose and tables only.

## 4. Requirements

Document-local requirement IDs (DEP-##) are used below. They roll up to the FR-OPS group and the non-functional catalog defined in the `specs/` documents; numeric cross-document IDs are assigned there, not here.

### 4.1 Environment strategy

| ID | Requirement |
|----|-------------|
| DEP-01 | Legacy runs three environments: `local`, `staging`, `production`. No other long-lived environments exist. |
| DEP-02 | Production is single-tenant: one instance, one owner, no shared infrastructure with other products. |
| DEP-03 | Staging mirrors production topology and configuration shape (same services, same versions, smaller sizing) and uses synthetic or P0-only data. P2 and P3 content never enters staging. |
| DEP-04 | Local development runs the frontend and backend natively or in containers, against a local Supabase stack or a dedicated development Supabase project, never against production. |
| DEP-05 | Every environment is fully described by versioned configuration; recreating an environment from scratch must require no undocumented manual steps. |
| DEP-06 | Environment identity (which environment a process believes it is in) is set by exactly one configuration value and is visible in logs, health endpoints, and the UI footer for non-production. |

| Environment | Purpose | Data | Model API usage |
|-------------|---------|------|-----------------|
| local | Day-to-day development | Synthetic fixtures | Cheapest routed model, low budget cap |
| staging | Pre-production verification, AI evaluation gate | Synthetic plus P0 samples | Production-like routing, capped budget |
| production | The owner's live system | Full corpus (P0 to P3) | Full model router policy |

### 4.2 Reference topology (decision)

Decision: Legacy adopts a managed-first topology. A solo founder cannot sustainably operate self-hosted databases, queues, and orchestration for decades; managed services with documented exits are the deliberate trade.

| ID | Requirement |
|----|-------------|
| DEP-07 | The Next.js frontend deploys to a managed Next.js hosting platform with preview deployments per branch. |
| DEP-08 | The FastAPI backend deploys as a container image to a managed container platform (build once, promote the same image from staging to production). |
| DEP-09 | Data lives in Supabase managed PostgreSQL (with pgvector) and Supabase Storage, per the baseline defaults in [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md). |
| DEP-10 | Model providers (Claude, Gemini, Groq) are consumed as external APIs through the model router; no models are self-hosted in v1. |
| DEP-11 | Background work (ingestion, agent runs, scheduled exports) executes in worker processes consuming a queue, deployed on the same container platform as the API but scaled independently. |
| DEP-12 | A single reverse entry point (the managed platform's load balancer plus a CDN for the frontend) terminates TLS; no service is reachable except through it and the Supabase APIs. |

```
                        +---------------------------+
   Owner's browser ---> |  Managed Next.js host     |
                        |  (frontend, CDN, TLS)     |
                        +------------+--------------+
                                     | REST /v1 + SSE
                        +------------v--------------+
                        |  Managed container        |
                        |  platform                 |
                        |  +---------------------+  |
                        |  | FastAPI API service |  |
                        |  +---------------------+  |
                        |  | Worker service      |  |
                        |  | (queue consumers:   |  |
                        |  |  ingestion, agents, |  |
                        |  |  scheduled exports) |  |
                        |  +---------------------+  |
                        +---+----------------+------+
                            |                |
              +-------------v---+   +--------v-----------------+
              | Supabase        |   | External model APIs      |
              | Postgres +      |   | Claude / Gemini / Groq   |
              | pgvector +      |   | via model router         |
              | Storage         |   +--------------------------+
              +-------+---------+
                      |
              +-------v------------------+
              | Owner-controlled storage |
              | (Legacy Vault exports,   |
              |  offsite backups)        |
              +--------------------------+
```

> TODO(verify): concrete vendor selection for the Next.js host and the container platform. Candidates must be evaluated against the exit criteria in section 4.10 and recorded as an ADR in [MASTER_ARCHITECTURE](../architecture/MASTER_ARCHITECTURE.md).

### 4.3 Region and data residency

| ID | Requirement |
|----|-------------|
| DEP-13 | Region preference is the closest available region to Cape Town, South Africa, for latency and for data residency posture. Where a vendor has no nearby region, the tie-break order is: residency compliance, then latency, then cost. |
| DEP-14 | The chosen regions for compute, database, and storage are recorded in one place (the environment configuration register) and reviewed whenever a vendor adds a closer region. |

> TODO(verify): data residency decision under POPIA (South Africa's Protection of Personal Information Act): whether all P2/P3 content must remain in-country, which vendors offer a South African region, and whether cross-border transfer conditions are met for those that do not. This is a legal decision, to be resolved with reference to [PRIVACY](../security/PRIVACY.md) before production launch.

### 4.4 Infrastructure as code

| ID | Requirement |
|----|-------------|
| DEP-15 | All infrastructure (hosting projects, environment variables, domains, database configuration, storage buckets, alert rules) is defined declaratively in a versioned repository and applied through a reviewed change process. Manual console changes are permitted only during a declared incident and must be backported to the definitions within 48 hours. |
| DEP-16 | Applying the definitions twice produces no changes the second time (idempotent, reproducible). |
| DEP-17 | The infrastructure definition repository is itself included in the backup scope of [BACKUP_AND_RECOVERY](./BACKUP_AND_RECOVERY.md). |

> TODO(verify): infrastructure as code tool choice. The decision (and the trade-off against vendor-native configuration) is deferred to an ADR; this spec only fixes the expectation of declarative, versioned, reproducible definitions.

### 4.5 Configuration and secrets

| ID | Requirement |
|----|-------------|
| DEP-18 | Configuration follows a strict split: non-secret configuration lives in versioned files per environment; secrets live only in the platform secret manager of each environment and are injected at runtime. |
| DEP-19 | Secrets are never committed to any repository, never written to logs, and never shared across environments (staging model API keys are distinct from production keys). |
| DEP-20 | Every secret has a named owner (the owner), a documented rotation procedure, and a rotation cadence of at most 12 months, with immediate rotation on suspected exposure. |
| DEP-21 | The full inventory of secrets (name, purpose, where stored, rotation date) is maintained as a register referenced from [SECURITY](../security/SECURITY.md); the values themselves are never in the register. |
| DEP-22 | Encryption keys that protect backups and the Legacy Vault are owner-held and follow the escrow procedure in [BACKUP_AND_RECOVERY](./BACKUP_AND_RECOVERY.md); they are not stored in the hosting platforms' secret managers. |

### 4.6 Deployment procedure

| ID | Requirement |
|----|-------------|
| DEP-23 | Every production deployment follows the same five-step procedure: build, verify, deploy, smoke test, and (if needed) rollback. No ad hoc production changes. |
| DEP-24 | The unit of deployment for the backend is an immutable container image identified by digest; the image promoted to production is byte-identical to the one verified in staging. |
| DEP-25 | Rollback restores the previously deployed frontend build and backend image within 10 minutes of the decision to roll back, using platform-native re-deploy of the prior artifact. |
| DEP-26 | Database schema migrations are expand-and-contract: additive changes deploy first, code that uses them second, destructive cleanup only after a full release cycle, so that rollback never requires a schema downgrade. |
| DEP-27 | Each deployment writes a deployment record (who, when, artifact digests, migration list, smoke test result) to the audit trail described in [OBSERVABILITY](./OBSERVABILITY.md). |

Procedure narrative:

1. Build: CI produces the frontend build and the backend container image, both tagged with the git commit and release version (see [CI_CD](./CI_CD.md)).
2. Verify: staging receives the artifacts automatically; automated tests and the AI evaluation gate run against staging.
3. Deploy: the owner approves promotion; the platform shifts traffic to the new version.
4. Smoke test: a scripted post-deploy check exercises login, one search query, one RAG answer with citation, one ingestion enqueue, and the health endpoints, within 15 minutes of deploy.
5. Rollback: if any smoke check fails or an alert fires within the first hour, roll back first and investigate second.

### 4.7 Zero-downtime expectations and maintenance windows

| ID | Requirement |
|----|-------------|
| DEP-28 | Routine deployments are zero-downtime: rolling or blue-green replacement on the container platform, atomic build swaps on the frontend host. In-flight SSE streams may be terminated by a deploy; clients must reconnect gracefully. |
| DEP-29 | Planned maintenance that cannot be zero-downtime (for example a major Postgres version upgrade) uses a declared maintenance window, announced to the owner at least 48 hours ahead, scheduled outside the owner's usual working hours, with a tested rollback plan. |
| DEP-30 | Because the platform has one user, availability targets (see [OBSERVABILITY](./OBSERVABILITY.md)) tolerate short planned windows; durability targets never relax. |

### 4.8 Scaling posture

| ID | Requirement |
|----|-------------|
| DEP-31 | Baseline sizing is modest: single-owner interactive load is small. The API service runs a minimum of one instance with autoscale to a small cap; the worker service scales on queue depth. |
| DEP-32 | Ingestion bursts (bulk imports, large media) never degrade interactive latency: bulk work is queued and rate-limited, not processed inline in API requests. |
| DEP-33 | Agent workloads run as background jobs with per-run budget caps enforced by the Orchestrator Agent design in [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md); deployment provides the queue and worker capacity, not the budget logic. |
| DEP-34 | Database and storage scale vertically within Supabase plans; the trigger to review sizing is sustained saturation metrics, not anticipation. |

### 4.9 Cost posture

| ID | Requirement |
|----|-------------|
| DEP-35 | Total monthly infrastructure plus model API spend has a hard ceiling; spend at 80 percent of ceiling raises a warning alert, and reaching the ceiling pauses non-essential background work (reflection runs, re-embedding) while preserving interactive use and backups. |
| DEP-36 | Cost is reviewed monthly against the ceiling and per-service breakdown; the review is a recurring owner task with its outcome noted in the operations log. |
| DEP-37 | Every new managed service or model adoption states its expected monthly cost before adoption. |

> TODO(verify): the actual monthly cost ceiling (an owner budget decision, in ZAR or USD). Until set, staging uses minimal sizing and production sizing decisions are deferred.

### 4.10 Vendor exit strategy

| ID | Requirement |
|----|-------------|
| DEP-38 | No managed service is adopted without a written exit note: what data or capability it holds, the export mechanism, the estimated migration effort, and the fallback target. |
| DEP-39 | Exit notes are reviewed annually and whenever a vendor changes pricing or terms materially. |

| Vendor / service | What it holds | Exit path |
|------------------|---------------|-----------|
| Managed Next.js host | Frontend builds, domains, edge config | Frontend is standard Next.js; redeploy to any Node-capable host or container platform; domains transfer via DNS |
| Managed container platform | API and worker containers | Images are standard OCI containers; redeploy to any container runtime |
| Supabase Postgres | The corpus, graph, memory, audit log | Standard `pg_dump` logical exports (part of backup cadence); restore to any Postgres 15+ with pgvector |
| Supabase Storage | Media artifacts | S3-compatible API; bulk copy to any object store; checksums verified against the vault manifest |
| Model APIs (Claude, Gemini, Groq) | No data at rest (zero retention configuration where offered) | Model router abstraction allows provider swap; prompts and evals are versioned in-repo |
| Owner-controlled vault storage | Legacy Vault exports, offline backups | Already owner-controlled; by definition the destination of last resort |

### 4.11 Legacy Vault delivery path

| ID | Requirement |
|----|-------------|
| DEP-40 | A scheduled export job (worker service) produces the Legacy Vault (open formats, integrity manifest, defined fully in [BACKUP_AND_RECOVERY](./BACKUP_AND_RECOVERY.md)) and delivers it to owner-controlled storage outside all hosting vendors. |
| DEP-41 | The delivery path is push-based from the worker to the owner-controlled destination; the destination credentials are write-only from the platform side (the platform cannot read or delete existing vault generations). |
| DEP-42 | Vault delivery success and manifest verification are first-class metrics and alerts in [OBSERVABILITY](./OBSERVABILITY.md); a missed vault export is a high-severity event. |

## 5. Acceptance Criteria

1. All three environments exist, and recreating staging from the versioned definitions succeeds with no undocumented manual steps.
2. Production is single-tenant, reachable only through the defined entry points, and its environment identity is visible in logs and health endpoints.
3. A full deployment (build to smoke test) completes with zero downtime for interactive requests, demonstrated by a synthetic probe running through the deploy.
4. A rollback drill restores the previous frontend build and backend image in under 10 minutes.
5. No secret value appears in any repository, log, or build artifact, verified by secret scanning in CI.
6. Staging contains no P2 or P3 content, verified by a data audit query.
7. A vault export lands in owner-controlled storage on schedule and its manifest verifies.
8. Every adopted vendor has an exit note; a tabletop exercise walks the Supabase exit path end to end on paper.
9. Cost reporting shows spend against the ceiling per service, and the 80 percent warning alert is tested.

## 6. Dependencies

- [MASTER_ARCHITECTURE](../architecture/MASTER_ARCHITECTURE.md): component boundaries and ADRs this topology realizes.
- [CI_CD](./CI_CD.md): produces the artifacts this document deploys and defines promotion gates.
- [OBSERVABILITY](./OBSERVABILITY.md): smoke tests, deployment records, cost and vault alerts.
- [BACKUP_AND_RECOVERY](./BACKUP_AND_RECOVERY.md): backup scope, vault format, key escrow.
- [SECURITY](../security/SECURITY.md) and [PRIVACY](../security/PRIVACY.md): secret handling, POPIA residency inputs.
- [API_SPECIFICATION](../api/API_SPECIFICATION.md): health endpoints and SSE behavior assumed by deploys.
- External: availability and regional coverage of the selected managed vendors.

## 7. Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Vendor discontinues a service or exits the region | Forced migration under time pressure | Exit notes per vendor (DEP-38), annual review, backups independent of every vendor |
| Solo operator unavailable during an incident | Prolonged outage | Managed-first posture, automated rollback, runbooks written for a future steward |
| POPIA residency decision arrives late and contradicts chosen regions | Rework of data placement | Residency flagged as a launch blocker (DEP-13, DEP-14 TODO) |
| Cost creep from model APIs | Budget breach | Ceiling with automatic soft-stop (DEP-35), monthly review |
| Staging drift from production | Deploys pass staging but fail production | Same artifacts promoted (DEP-24), declarative definitions (DEP-15, DEP-16) |
| Migration executed destructively | Data loss on rollback | Expand-and-contract migrations (DEP-26), backups before every migration |

## 8. Future Enhancements

- Warm standby of the database in a second region once budget allows.
- Preview environments with masked synthetic corpora for feature branches.
- Self-hosted inference for a small local model as a resilience fallback for core search.
- Automated infrastructure drift detection comparing live state to definitions on a schedule.
- Android client delivery pipeline (out of scope for v1 per the baseline decisions).

## 9. Examples

Deployment record (illustrative JSON, written by the deploy step):

```json
{
  "deployment_id": "dep_2026_07_02_001",
  "environment": "production",
  "actor": "linford",
  "frontend_build": "web@9f31c2a",
  "backend_image_digest": "sha256:4be1...",
  "migrations_applied": ["0042_add_agentrun_budget_fields"],
  "started_at": "2026-07-02T18:05:00Z",
  "smoke_test": {
    "login": "pass",
    "search_query": "pass",
    "rag_answer_with_citation": "pass",
    "ingestion_enqueue": "pass",
    "health_endpoints": "pass"
  },
  "result": "success",
  "rollback_target": "sha256:77aa..."
}
```

Environment configuration register (illustrative excerpt, prose table):

| Key | local | staging | production |
|-----|-------|---------|------------|
| ENV_NAME | local | staging | production |
| DB target | local Supabase stack | staging Supabase project | production Supabase project |
| Model budget/day | minimal | capped | full policy |
| Vault export | disabled | dry-run | enabled, scheduled |

## 10. Open Questions

1. > TODO(verify): vendor selection for the managed Next.js host and container platform, decided as an ADR with exit notes.
2. > TODO(verify): POPIA data residency ruling and the resulting region constraints for Postgres, Storage, and compute.
3. > TODO(verify): the monthly cost ceiling and the currency it is tracked in.
4. > TODO(verify): infrastructure as code tool choice versus vendor-native declarative configuration.
5. Should staging run continuously or be created on demand to save cost? Leaning on demand once definitions are proven reproducible.

## 11. References

- [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md), section 9: baseline architecture defaults this topology realizes.
- [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md), section 5: the owner's demonstrated stack (FastAPI ✅, Supabase 🟡) informing the managed-first defaults.
- POPIA (Protection of Personal Information Act, South Africa) as the residency driver; legal reading tracked in [PRIVACY](../security/PRIVACY.md).

## 12. Related Specifications

- [CI_CD](./CI_CD.md)
- [OBSERVABILITY](./OBSERVABILITY.md)
- [BACKUP_AND_RECOVERY](./BACKUP_AND_RECOVERY.md)
- [MASTER_ARCHITECTURE](../architecture/MASTER_ARCHITECTURE.md)
- [SECURITY](../security/SECURITY.md), [PRIVACY](../security/PRIVACY.md)
- [API_SPECIFICATION](../api/API_SPECIFICATION.md)
- [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md)
