# IMPLEMENTATION_TASKS
### Actionable engineering tasks for the Legacy MVP, derived one-to-one from the specifications

| Field | Value |
|-------|-------|
| Status | Draft |
| Owner | Linford Musiyambodza |
| Last updated | 2026-07-02 |
| Depends on | [MVP_PLAN](MVP_PLAN.md), [TASKS](TASKS.md), [BUILD_ORDER](BUILD_ORDER.md) |

---

## 1. Purpose

This document converts the specifications into engineering tasks sized for single implementation sessions. It covers the MVP scope defined in [MVP_PLAN](MVP_PLAN.md). Each task carries a stable `MVP-###` ID, acceptance criteria drawn from spec sections, dependencies, effort, and priority. The `MVP-` prefix is defined by this document; every MVP task maps to its parent canonical `TASK-###` in [TASKS](TASKS.md) where one exists, and completing an MVP task partially or fully discharges its parent.

## 2. Goals

- Give any implementation session (human or AI) a task it can complete without design decisions: the specs already made them.
- Keep acceptance criteria testable and anchored to spec sections, never to opinion.
- Preserve traceability: MVP-### → TASK-### → FS/FR/NFR → spec section.

## 3. Scope

**In scope:** all MVP stages 1 to 4 from [MVP_PLAN](MVP_PLAN.md) §4. **Out of scope:** post-MVP work (remains in [TASKS](TASKS.md)).

**Conventions:** Priority P0 = MVP-blocking, P1 = should ship, P2 = stretch. Effort in focused engineering days (d), tests included. A task is done only when its acceptance criteria pass in CI and the change cites its spec sections (spec-first rule, [QUALITY_ASSURANCE](../testing/QUALITY_ASSURANCE.md)).

## 4. Requirements

### 4.1 Stage 1: Bedrock

**MVP-001 · Project scaffolding and environments** (parent TASK-101)
- **Description:** Create the implementation repository structure (Next.js web app, FastAPI backend, infrastructure definitions), provision dev/staging/prod per [DEPLOYMENT](../deployment/DEPLOYMENT.md) §4.1 to §4.5, wire secrets management.
- **Acceptance criteria:** All three environments reachable; configuration and secrets flow per spec (no secrets in code); a hello-world deploy and rollback completes per §4.6.
- **Dependencies:** none. **Effort:** 1.5d. **Priority:** P0.

**MVP-002 · CI pipeline with quality gates** (parent TASK-102)
- **Description:** Implement the pipeline stages of [CI_CD](../deployment/CI_CD.md) §4.2 (spec checks: markdown link check, conventions compliance, no-em-dash lint) and §4.3 baseline (lint, type check, unit tests, dependency audit, accessibility checks).
- **Acceptance criteria:** Pipeline blocks merges on any failing gate; spec checks run against this repository; a deliberately broken test blocks a trial PR.
- **Dependencies:** MVP-001. **Effort:** 1d. **Priority:** P0.

**MVP-003 · Full logical schema migration** (parent TASK-105)
- **Description:** Migrate every entity in [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md) §4.3 to §4.6 (knowledge entities, provenance sub-model, Edge, system entities) with the common base fields of §4.2 (including `privacy_tier` defaulting P2) and the indexing strategy of §4.7.
- **Acceptance criteria:** Migration applies cleanly to an empty database and is reversible; base-field defaults verified; the claim-tier enum and never-auto-upgrade constraint (§4.4) enforced at the data layer; schema migration test per [TESTING](../testing/TESTING.md) passes.
- **Dependencies:** MVP-001. **Effort:** 2d. **Priority:** P0.

**MVP-004 · Authentication: OIDC, MFA, sessions** (parent TASK-103)
- **Description:** Owner sign-in per [AUTHENTICATION](../security/AUTHENTICATION.md) §4.1 to §4.3: OIDC via the managed provider, mandatory MFA for Owner (passkey preferred, TOTP fallback), short-lived access tokens, rotating refresh, revocation, step-up for sensitive actions, brute-force protections.
- **Acceptance criteria:** AuthN test matrix rows for Owner pass; no MFA-bypass path exists (review plus tests); every auth event writes an `AuditLogEntry` (§4.6); new-device sign-in triggers notification.
- **Dependencies:** MVP-001, MVP-003. **Effort:** 2d. **Priority:** P0.

**MVP-005 · Personal access tokens** (parent TASK-103)
- **Description:** Scoped, expiring, revocable PATs per [AUTHENTICATION](../security/AUTHENTICATION.md) §4.3 and the scope list in [API_SPECIFICATION](../api/API_SPECIFICATION.md) §4.5.
- **Acceptance criteria:** Token shown once at creation; scope enforcement tested per scope; every use audited; revocation effective within 60 seconds.
- **Dependencies:** MVP-004, MVP-007. **Effort:** 1d. **Priority:** P1 (descope ladder rung 2).

**MVP-006 · Authorization core: policy service and tier ceilings** (parent TASK-104)
- **Description:** Central policy decision service implementing [AUTHORIZATION](../security/AUTHORIZATION.md) §4.1 to §4.5: role catalog (Owner active; other roles defined but dormant), tier ceilings, deny-by-default, uniform `not_found` for above-ceiling items, agent-identity scaffolding, decision audit with policy version.
- **Acceptance criteria:** Authorization matrix tests for Owner, unauthenticated, and a dormant-role principal pass; existence-leak test (identical response shape for missing versus above-ceiling) passes; every denial audited.
- **Dependencies:** MVP-003, MVP-004. **Effort:** 2d. **Priority:** P0.

**MVP-007 · API skeleton: conventions, errors, pagination, idempotency** (parent TASK-106)
- **Description:** Implement [API_SPECIFICATION](../api/API_SPECIFICATION.md) §4.1 to §4.3: `/v1` base, error envelope with canonical codes, cursor pagination, `Idempotency-Key` replay, rate limiting, RFC 3339 timestamps, provenance block serialization.
- **Acceptance criteria:** Contract tests for the conventions layer pass, including idempotency replay and the documented error codes; provenance block present on a sample factual resource.
- **Dependencies:** MVP-006. **Effort:** 1.5d. **Priority:** P0.

**MVP-008 · Observability baseline** (parent TASK-110)
- **Description:** Structured leveled logging with content-ID-only redaction middleware, request tracing, token/cost metric hooks (dormant until stretch), audit sink, and owner alerting per [OBSERVABILITY](../deployment/OBSERVABILITY.md).
- **Acceptance criteria:** Redaction test proves no P2 content string reaches logs; a traced request is reconstructable end to end; a test alert reaches the owner channel.
- **Dependencies:** MVP-007. **Effort:** 1d. **Priority:** P0.

**MVP-009 · Backup baseline and restore runbooks 1-2** (parent TASK-109)
- **Description:** Continuous point-in-time database backup, daily snapshots, storage incrementals, encrypted per [BACKUP_AND_RECOVERY](../deployment/BACKUP_AND_RECOVERY.md) §4.1 to §4.4; write and test runbooks 1 (item restore) and 2 (point-in-time restore) from §4.6; automate the monthly restore drill.
- **Acceptance criteria:** One point-in-time restore drill passes to a scratch environment with checksum verification; drill automation scheduled; backup credentials separate from production credentials.
- **Dependencies:** MVP-001, MVP-003. **Effort:** 1d. **Priority:** P0.

### 4.2 Stage 2: Capture

**MVP-010 · Ingestion pipeline: documents and notes** (parent TASK-107)
- **Description:** `IngestionJob` lifecycle per FS-001: upload and quick-add paths, text extraction for common document formats, normalization to `Artifact` and `Note` rows (tier P2 default), content-hash dedup, original-file preservation, per-item status, resumable batches, review flags for unparseable files.
- **Acceptance criteria:** FS-001 document and note scenarios pass; NFR-005 (searchable within 2 minutes) measured once search exists, provisionally time-to-stored under 30 seconds; duplicate upload dedups; a corrupt file lands as a review flag with the original preserved.
- **Dependencies:** MVP-006, MVP-007. **Effort:** 2.5d. **Priority:** P0.

**MVP-011 · Capture inbox and quick add** (parent TASK-108)
- **Description:** The CaptureQuickAdd global modal (text, file, link modes; voice deferred) and the capture inbox per [UI_UX](../ui/UI_UX.md) §4.1 and §4.4, using [DESIGN_SYSTEM](../ui/DESIGN_SYSTEM.md) components with the neutral placeholder palette.
- **Acceptance criteria:** Capture reachable in one action (button plus `c` shortcut) from every screen; focus-trapped, keyboard-complete modal ([ACCESSIBILITY](../ui/ACCESSIBILITY.md) §4.3); end-to-end capture in under one minute, measured.
- **Dependencies:** MVP-010. **Effort:** 1.5d. **Priority:** P0.

**MVP-012 · Workspace shell: navigation, dashboard v0, item views** (parent TASK-108)
- **Description:** Left navigation, minimal dashboard (recent captures, job statuses, queue count placeholder), item list and detail views with PrivacyTierIndicator and ConfidenceBadge where provenance exists, settings page, per [UI_UX](../ui/UI_UX.md) §4.1 to §4.3 and §4.5 states.
- **Acceptance criteria:** All Stage 2 IA areas reachable; empty/loading/error states implemented; accessibility CI gate green; keyboard walkthrough of capture-to-detail passes.
- **Dependencies:** MVP-011. **Effort:** 2d. **Priority:** P0.

**MVP-013 · Seed import: MASTER_CONTEXT as tiered Claims** (parent TASK-111)
- **Description:** Import every claim in `knowledge/MASTER_CONTEXT.md` as `Claim` rows with correct tier (`verified`, `self_reported`, `flagged`), section provenance, and `Source` stubs per [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md) §4.4.
- **Acceptance criteria:** Spot-check of 20 sampled claims shows correct tiers; the six §12 items exist as flagged claims; the import is idempotent and re-runnable.
- **Dependencies:** MVP-010. **Effort:** 1d. **Priority:** P0.

**MVP-014 · Seed import: owner document batch**
- **Description:** Batch-ingest the owner's selected existing documents through the Stage 2 pipeline (roadmap Phase 1 exit criterion 5).
- **Acceptance criteria:** Batch completes with per-item statuses; failures reviewed, not silent; corpus listed in the workspace.
- **Dependencies:** MVP-010, owner input (document selection). **Effort:** 0.5d. **Priority:** P0.

**MVP-015 · Revision history and soft delete**
- **Description:** Revisions on edit and soft delete with undo per [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md) §4.8 and [API_SPECIFICATION](../api/API_SPECIFICATION.md) content endpoints; permanent erasure deferred to the redaction workflow (post-MVP).
- **Acceptance criteria:** Edit produces a revision; delete is reversible; NFR-022 data-layer test passes.
- **Dependencies:** MVP-010. **Effort:** 1d. **Priority:** P1 (descope ladder rung 2).

### 4.3 Stage 3: Findability

**MVP-016 · Chunking, embedding, and lexical indexing** (parent TASK-201)
- **Description:** Content-type-aware chunking per [RAG_PIPELINE](../ai/RAG_PIPELINE.md), embeddings into pgvector `EmbeddingChunk` rows (tier inherited, model version recorded), lexical index, index rebuild path.
- **Acceptance criteria:** All stored content chunked and indexed; rebuild-from-source drill passes (NFR-024); chunk rows carry tier and provenance metadata.
- **Dependencies:** MVP-013, MVP-014. **Effort:** 2d. **Priority:** P0.

**MVP-017 · Search API with retrieval-layer tier filtering** (parent TASK-202)
- **Description:** `GET /v1/search` with lexical, semantic, and hybrid modes per [API_SPECIFICATION](../api/API_SPECIFICATION.md); tier filtering applied before ranking per NFR-035 and [AUTHORIZATION](../security/AUTHORIZATION.md) §4.4 point 2.
- **Acceptance criteria:** Tier-filtering suite proves no above-ceiling result, snippet, or count leaks; NFR-001/NFR-002 latency met on the reference corpus; golden query set (built here) recall recorded as the baseline.
- **Dependencies:** MVP-016. **Effort:** 1.5d. **Priority:** P0.

**MVP-018 · Search UI with provenance badges** (parent TASK-202)
- **Description:** Unified search screen per [UI_UX](../ui/UI_UX.md): mode selection, SearchResult rows with type, tier, ConfidenceBadge, semantic snippet highlighting, zero-result state that suggests without fabricating.
- **Acceptance criteria:** FS-004 key scenarios pass; badges render text labels per NFR-043; keyboard and screen reader behavior per [ACCESSIBILITY](../ui/ACCESSIBILITY.md) §4.5.
- **Dependencies:** MVP-017, MVP-012. **Effort:** 1.5d. **Priority:** P0.

**MVP-019 · Performance and drill verification**
- **Description:** Measure NFR-001, NFR-002, NFR-005 on production-shaped data; record results; file gaps as defects.
- **Acceptance criteria:** Measurements documented against the reference corpus; Must-level NFRs green or defects filed and triaged.
- **Dependencies:** MVP-017. **Effort:** 0.5d. **Priority:** P1.

### 4.4 Stage 4: Truth and hardening

**MVP-020 · Verification queue MVP** (parent TASK-206)
- **Description:** Queue listing open 🔴 and stale 🟡 claims, evidence attachment, owner resolve flow (apply or reject tier change) with step-up auth and audit trail, per FS-009 and the [UI_UX](../ui/UI_UX.md) queue screen; no agent automation.
- **Acceptance criteria:** All six MASTER_CONTEXT §12 items listed; one claim resolved end to end in production with audit entries (roadmap Phase 2 exit criterion 4); only the Owner can apply tier changes.
- **Dependencies:** MVP-013, MVP-012. **Effort:** 2d. **Priority:** P0 (descope ladder rung 3 moves UI, never the data, to week 5).

**MVP-021 · Production hardening and full restore drill**
- **Description:** Go-live checklist: full-platform restore drill per [BACKUP_AND_RECOVERY](../deployment/BACKUP_AND_RECOVERY.md) §4.6 runbook 3, security re-test of auth and tier paths, dependency audit clean, alert channels verified.
- **Acceptance criteria:** Restore drill meets provisional RTO on scratch infrastructure; checklist signed off; no Critical or High findings open.
- **Dependencies:** MVP-009, MVP-017. **Effort:** 1d. **Priority:** P0.

**MVP-022 · MVP acceptance run**
- **Description:** Execute every criterion in [MVP_PLAN](MVP_PLAN.md) §5 against production and record results.
- **Acceptance criteria:** Criteria 1 through 6 pass (7 only if stretch shipped); failures block ship per [QUALITY_ASSURANCE](../testing/QUALITY_ASSURANCE.md) release criteria.
- **Dependencies:** all P0 tasks. **Effort:** 1d. **Priority:** P0.

**MVP-023 · Spec sync and Gate G1 evidence log**
- **Description:** Update [CHANGELOG](../CHANGELOG.md), reconcile any deviations spec-first, and open the Gate G1 evidence log (stack observations, capture friction, schema fit) for the formal review after sustained usage per [ROADMAP](ROADMAP.md) §9.1.
- **Acceptance criteria:** CHANGELOG entry merged; zero undocumented deviations; G1 log exists with first entries.
- **Dependencies:** MVP-022. **Effort:** 0.5d. **Priority:** P0.

**MVP-024 · STRETCH: model router skeleton, Claude only** (parent TASK-301)
- **Description:** The router abstraction from [AI_ARCHITECTURE](../ai/AI_ARCHITECTURE.md) with a single registered provider (Anthropic Claude), version pinning, token accounting into the MVP-008 metrics, and a hard daily budget cap.
- **Acceptance criteria:** All model calls flow through the router; spend visible on the dashboard; cap halts calls with a clear error.
- **Dependencies:** MVP-008. **Effort:** 1d. **Priority:** P2.

**MVP-025 · STRETCH: owner-only cited ask** (parent TASK-302)
- **Description:** `POST /v1/ask` behind an owner-only flag: hybrid retrieval, tier-filtered context assembly, SSE streaming, mandatory citations, explicit refusal when the corpus lacks an answer, per [RAG_PIPELINE](../ai/RAG_PIPELINE.md) generation rules and [API_SPECIFICATION](../api/API_SPECIFICATION.md).
- **Acceptance criteria:** 100 percent citation coverage on the golden mini-set (NFR-037); refusal behavior verified; NFR-003 first-token latency met.
- **Dependencies:** MVP-017, MVP-024. **Effort:** 2d. **Priority:** P2.

**MVP-026 · STRETCH: tier-discipline mini-eval** (parent TASK-303)
- **Description:** A seed eval suite asserting answers never present 🟡/🔴 claims as fact (NFR-038), wired as a CI gate on the ask path.
- **Acceptance criteria:** Eval runs in CI; a seeded violation case fails the gate; flag stays off if the suite is red.
- **Dependencies:** MVP-025. **Effort:** 1d. **Priority:** P2.

## 5. Acceptance Criteria

- Every MVP task cites spec sections in its acceptance criteria; none requires a design decision to start.
- The P0 set completes the MVP acceptance run (MVP-022) with criteria 1 through 6 of [MVP_PLAN](MVP_PLAN.md) §5 green.
- Dependency ordering matches [BUILD_ORDER](BUILD_ORDER.md) exactly; the graph is acyclic.
- Parent TASK mappings are recorded so [TASKS](TASKS.md) progress is derivable (TASK-101 through TASK-111, TASK-201, TASK-202, TASK-206 discharged fully or partially; partial discharges noted against the parent).

## 6. Dependencies

External account and owner-input dependencies are listed in [MVP_PLAN](MVP_PLAN.md) §6; inter-task dependencies are per task above.

## 7. Risks

The MVP risk table and descope ladder live in [MVP_PLAN](MVP_PLAN.md) §7 and are not duplicated here. Task-level watch items: MVP-004 and MVP-006 are the security keystones (no time-boxing them down), and MVP-016's embedding model choice must be recorded (model and version) because Gate G2 later reviews re-embedding cost.

## 8. Future Enhancements

Post-MVP tasks remain canonical in [TASKS](TASKS.md); this document gains no new entries after the MVP ships (a completed MVP freezes it as a record).

## 9. Examples

An implementation session picks up MVP-017: it reads the search endpoint contract in [API_SPECIFICATION](../api/API_SPECIFICATION.md), the query pipeline and tier-filtering sections of [RAG_PIPELINE](../ai/RAG_PIPELINE.md), NFR-035, and the enforcement-point rules in [AUTHORIZATION](../security/AUTHORIZATION.md) §4.4. It implements the three modes, writes the leak tests first (a P2 item invisible to a dormant-role principal), measures latency against the seeded corpus, records the golden-set baseline, and merges citing those sections. MVP-018 is now unblocked.

## 10. Open Questions

- Should MVP-013 claim extraction be fully scripted or human-in-the-loop for ambiguous claim boundaries? Default: scripted with a review pass; decide during the task.

## 11. References

- [`knowledge/MASTER_CONTEXT.md`](../knowledge/MASTER_CONTEXT.md) §12 (MVP-013 and MVP-020 seed data).
- [`docs/SPEC_CONVENTIONS.md`](../docs/SPEC_CONVENTIONS.md) §4 (ID discipline this document extends with the MVP- prefix).

## 12. Related Specifications

- [MVP_PLAN](MVP_PLAN.md), [BUILD_ORDER](BUILD_ORDER.md), [TASKS](TASKS.md)
- [FEATURE_SPECIFICATIONS](../specs/FEATURE_SPECIFICATIONS.md), [FUNCTIONAL_REQUIREMENTS](../specs/FUNCTIONAL_REQUIREMENTS.md), [NON_FUNCTIONAL_REQUIREMENTS](../specs/NON_FUNCTIONAL_REQUIREMENTS.md)
- [TESTING](../testing/TESTING.md), [QUALITY_ASSURANCE](../testing/QUALITY_ASSURANCE.md)
