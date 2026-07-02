# TASKS
### The implementation backlog for the Legacy platform, phase by phase

| Field | Value |
|-------|-------|
| Status | Draft |
| Owner | Linford Musiyambodza |
| Last updated | 2026-07-02 |
| Depends on | [ROADMAP](ROADMAP.md), [FEATURE_SPECIFICATIONS](../specs/FEATURE_SPECIFICATIONS.md), [FUNCTIONAL_REQUIREMENTS](../specs/FUNCTIONAL_REQUIREMENTS.md) |

---

## 1. Purpose

This document is the working backlog: every implementation task carries a stable TASK ID, a phase, a feature mapping, a definition of done anchored in specification documents, a size estimate, and its dependencies. Task IDs are never renumbered; completed tasks are marked, not deleted.

## 2. Goals

- Make the roadmap executable: each phase in [ROADMAP](ROADMAP.md) decomposes into tasks a session can pick up cold.
- Keep every task's definition of done (DoD) traceable to specs, honoring the spec-first rule in [QUALITY_ASSURANCE](../testing/QUALITY_ASSURANCE.md).
- Include repository maintenance work (verification queue, source URLs, changelog discipline), not just build work.

## 3. Scope

**In scope:** Phase 1 through Phase 5 implementation tasks plus ongoing spec-repo maintenance tasks. Sizes: S (a focused session), M (several sessions), L (a sustained effort needing its own breakdown before starting).

**Out of scope:** post-v1 candidates (see [FUTURE_FEATURES](FUTURE_FEATURES.md)); tasks are not scheduled to dates (see the capacity TODO in [ROADMAP](ROADMAP.md)).

## 4. Requirements

### 4.1 Ongoing: specification repository maintenance

| ID | Task | Feature | DoD | Size | Depends on |
|----|------|---------|-----|------|------------|
| TASK-001 | Attach source URLs from `Research/15 Sources.md` to every ✅ claim in MASTER_CONTEXT | F9 | Each ✅ claim in `knowledge/MASTER_CONTEXT.md` §1 to §9 has a source reference; §12 item 1 closed | M | none |
| TASK-002 | Work the seeded verification queue (IUS Africa role, SpazaLink placement, HBS Foundry, ADEL, ICMM, WorldQuant) | F9 | Each 🔴 item in MASTER_CONTEXT §12 resolved or documented as still open with evidence attempts recorded | M | TASK-001 |
| TASK-003 | Confirm live repos and demos for §6 projects; mark concept-stage items | F13 | MASTER_CONTEXT §12 item 5 closed; project records annotated | S | none |
| TASK-004 | Keep CHANGELOG and spec Status fields current each working session | all | Every merged spec change has a CHANGELOG entry; stale Draft statuses reviewed monthly | S | none |
| TASK-005 | Owner decisions: brand palette and typeface, monthly cost ceiling, corpus growth estimate | F10, F11 | TODOs in [DESIGN_SYSTEM](../ui/DESIGN_SYSTEM.md) §4.1 and [NON_FUNCTIONAL_REQUIREMENTS](../specs/NON_FUNCTIONAL_REQUIREMENTS.md) §10 resolved and recorded | S | none |
| TASK-006 | Obtain legal review of succession mechanics (South African estate law) | F16 | TODO(verify) items in [AUTHENTICATION](../security/AUTHENTICATION.md) §4.5 and [BACKUP_AND_RECOVERY](../deployment/BACKUP_AND_RECOVERY.md) §4.4 replaced with reviewed decisions | M | none |

### 4.2 Phase 1: Foundation

| ID | Task | Feature | DoD | Size | Depends on |
|----|------|---------|-----|------|------------|
| TASK-101 | Provision environments (dev, staging, prod) per DEPLOYMENT | infra | Environments live, IaC-defined, secrets managed per [DEPLOYMENT](../deployment/DEPLOYMENT.md) | M | none |
| TASK-102 | Stand up CI pipeline: lint, tests, spec-conventions checks | infra | Pipeline gates per [CI_CD](../deployment/CI_CD.md) §spec-repo stages, including the no-em-dash and link checks | M | TASK-101 |
| TASK-103 | Implement identity and authentication (OIDC, MFA, sessions, PATs) | F11 | AuthN test matrix in [TESTING](../testing/TESTING.md) passes; [AUTHENTICATION](../security/AUTHENTICATION.md) §4.1 to §4.4 implemented | L | TASK-101 |
| TASK-104 | Implement authorization core: roles, tiers, Grants, policy service | F11 | Matrix tests per [AUTHORIZATION](../security/AUTHORIZATION.md) §5 pass; deny-by-default proven | L | TASK-103 |
| TASK-105 | Implement logical schema: entities, Claim/Source, Edge, audit | F1, F9 | All entities in [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md) migrated; base-field and provenance constraints enforced | L | TASK-101 |
| TASK-106 | Build API skeleton: conventions, errors, pagination, idempotency | all | Contract tests for [API_SPECIFICATION](../api/API_SPECIFICATION.md) §4.1 to §4.3 pass | M | TASK-104, TASK-105 |
| TASK-107 | Ingestion MVP: documents and notes, IngestionJob lifecycle | F1 | FS-001 document and note scenarios pass; NFR-005 met on reference corpus | L | TASK-105 |
| TASK-108 | Private Workspace shell: navigation, dashboard, capture inbox | F11 | [UI_UX](../ui/UI_UX.md) IA implemented for Phase 1 areas; accessibility CI gate green | L | TASK-106 |
| TASK-109 | Backup baseline: continuous DB backup, daily snapshots, restore runbook 1 and 2 | F16 | Monthly automated restore drill passing per [BACKUP_AND_RECOVERY](../deployment/BACKUP_AND_RECOVERY.md) §4.7 | M | TASK-101 |
| TASK-110 | Observability baseline: structured logs, request tracing, cost metrics, audit sink | infra | [OBSERVABILITY](../deployment/OBSERVABILITY.md) logging and audit requirements live; P2/P3 log-redaction test passes | M | TASK-106 |
| TASK-111 | Seed the corpus: ingest MASTER_CONTEXT as Claims with tiers | F9 | Every MASTER_CONTEXT claim exists as a `Claim` row with correct tier and section provenance | M | TASK-105, TASK-107 |

### 4.3 Phase 2: Knowledge Core

| ID | Task | Feature | DoD | Size | Depends on |
|----|------|---------|-----|------|------------|
| TASK-201 | Embedding and indexing pipeline (pgvector plus lexical) | F4 | Chunks embedded per [RAG_PIPELINE](../ai/RAG_PIPELINE.md); rebuild-from-source drill passes (NFR-024) | L | TASK-107 |
| TASK-202 | Search API and UI: lexical, semantic, hybrid | F4 | FS-004 scenarios pass; NFR-001/NFR-002 latencies met; tier filtering proven at retrieval layer | L | TASK-201 |
| TASK-203 | Graph Agent v1: entity and relationship extraction with merge proposals | F2 | FS-002 behavior per [KNOWLEDGE_GRAPH](../knowledge/KNOWLEDGE_GRAPH.md); no auto-merge below threshold | L | TASK-111 |
| TASK-204 | Graph explorer UI with list-first accessibility | F2 | [UI_UX](../ui/UI_UX.md) graph screen with the [ACCESSIBILITY](../ui/ACCESSIBILITY.md) §4.5 list-primary rule | M | TASK-203 |
| TASK-205 | Timeline Agent and explorer | F3 | FS-003 scenarios including partial dates and the undated shelf | M | TASK-203 |
| TASK-206 | Verification queue MVP seeded from MASTER_CONTEXT §12 | F9 | FS-009 queue workflow live; owner can resolve a claim end to end with audit trail | M | TASK-111 |
| TASK-207 | GitHub connector: ingest `linfordlee14` repositories | F1 | Repos ingested as Projects and Artifacts with code understanding chunks | M | TASK-107 |
| TASK-208 | Graph database decision gate review | F2 | ADR review documented per the decision gate in [ROADMAP](ROADMAP.md) Phase 2 exit | S | TASK-203 |

### 4.4 Phase 3: Intelligence

| ID | Task | Feature | DoD | Size | Depends on |
|----|------|---------|-----|------|------------|
| TASK-301 | Model router over Claude, Gemini, Groq with budgets | all AI | Routing policy per [AI_ARCHITECTURE](../ai/AI_ARCHITECTURE.md); cost caps and alerts live (NFR-049) | L | TASK-110 |
| TASK-302 | RAG pipeline end to end with mandatory citations | F5 | FS-005 scenarios; citation coverage 100 percent (NFR-037); groundedness eval baseline recorded | L | TASK-201, TASK-301 |
| TASK-303 | Tier-discipline eval suite and CI gate | F5, F9 | NFR-038 evals pass; gate blocks releases per [CI_CD](../deployment/CI_CD.md) | M | TASK-302 |
| TASK-304 | Ask UI with streaming, citation chips, confidence badges | F5 | [UI_UX](../ui/UI_UX.md) chat patterns; [ACCESSIBILITY](../ui/ACCESSIBILITY.md) live-region behavior verified | M | TASK-302 |
| TASK-305 | Memory system: MemoryRecords, consolidation, redaction | F7 | FS-007 lifecycle per [MEMORY_SYSTEM](../memory/MEMORY_SYSTEM.md); redaction tombstone test passes | L | TASK-302 |
| TASK-306 | Project and research explorer | F13 | FS-013 project pages assemble graph neighborhoods with tier labeling | M | TASK-204 |
| TASK-307 | Multimedia ingestion: OCR, transcription, alt text capture | F1 | FS-001 media scenarios; transcripts attached and labeled per [ACCESSIBILITY](../ui/ACCESSIBILITY.md) §4.2 | L | TASK-107 |

### 4.5 Phase 4: Twin and Agents

| ID | Task | Feature | DoD | Size | Depends on |
|----|------|---------|-----|------|------------|
| TASK-401 | Agent runtime: Orchestrator, AgentRun traces, approval gates | F8 | FS-008 scenarios; A2 gates and kill switch proven per [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md) | L | TASK-301, TASK-110 |
| TASK-402 | Specialist agents wave 1: Ingestion, Curation, Graph, Timeline as managed agents | F8 | Existing pipelines run as audited agents with allowlists | L | TASK-401 |
| TASK-403 | Twin Agent with disclosure, modes, and persona grounding | F6 | FS-006 scenarios; disclosure compliance 100 percent; persona fidelity review with the owner done | L | TASK-401, TASK-303 |
| TASK-404 | Research and Verification Agents with evidence packets | F9 | FS-009 research-assisted verification flow live; proposals owner-applied only | L | TASK-401 |
| TASK-405 | Mentor Agent: goals, evidence-based coaching | F14 | FS-014 scenarios with demonstrated-versus-claimed skill distinction | M | TASK-403 |
| TASK-406 | Writing Agent and Studio: drafts, voice profile, review flow | F15 | FS-015 scenarios; all output A2-gated; voice profile per [DIGITAL_TWIN](../ai/DIGITAL_TWIN.md) | L | TASK-403 |
| TASK-407 | Reflection Agent: rollups and consolidation schedules | F7 | Weekly rollup and consolidation jobs per [MEMORY_SYSTEM](../memory/MEMORY_SYSTEM.md) running as A1 | M | TASK-401, TASK-305 |
| TASK-408 | A2A protocol adoption decision | F8 | The §4.3 TODO in [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md) resolved with an ADR | S | TASK-401 |
| TASK-409 | Prompt-injection resistance test suite | F8 | Injection scenarios in [TESTING](../testing/TESTING.md) pass; instruction/data separation verified | M | TASK-402 |

### 4.6 Phase 5: Legacy and Public

| ID | Task | Feature | DoD | Size | Depends on |
|----|------|---------|-----|------|------------|
| TASK-501 | Journals with sealing: P3 mechanics, release conditions | F12 | FS-012 scenarios; NFR-032 egress test passes; sealed placeholders per [DESIGN_SYSTEM](../ui/DESIGN_SYSTEM.md) | L | TASK-104, TASK-305 |
| TASK-502 | Public Portfolio: publish gate, P0 rendering, cache purge | F10 | FS-010 scenarios; publish preview accurate; NFR-010 performance met | L | TASK-304 |
| TASK-503 | Public twin mode with P0 scope and disclosure banner | F6, F10 | Public mode ceiling tests pass; disclosure landmark per [ACCESSIBILITY](../ui/ACCESSIBILITY.md) §4.5 | M | TASK-403, TASK-502 |
| TASK-504 | Legacy Vault exporter with manifest and verification | F16 | FS-016 vault scenarios; NFR-019 and NFR-021 verified by the quarterly drill | L | TASK-109, TASK-501 |
| TASK-505 | Succession protocol: pre-registration, activation, cancellation, policy switch | F16 | Staging succession drill per [AUTHORIZATION](../security/AUTHORIZATION.md) §5 passes end to end | L | TASK-504, TASK-006 |
| TASK-506 | Steward documentation pack and first steward drill | F16 | NFR-053 drill passes with an outsider | M | TASK-504, TASK-505 |
| TASK-507 | Accessibility statement and pre-launch manual audit | F10 | [ACCESSIBILITY](../ui/ACCESSIBILITY.md) §4.8 statement live; audit findings triaged | M | TASK-502 |
| TASK-508 | Full disaster restore drill (yearly drill, first run) | F16 | RTO/RPO targets met per [BACKUP_AND_RECOVERY](../deployment/BACKUP_AND_RECOVERY.md) §4.7 | M | TASK-504 |

## 5. Acceptance Criteria

- Every task's DoD points at specific spec sections, and completing all tasks in a phase satisfies that phase's exit criteria in [ROADMAP](ROADMAP.md).
- No task is marked done without its referenced tests or drills passing.
- Dependency ordering is acyclic and respected in execution.
- New work discovered mid-phase enters as new TASK IDs (never renumbering existing ones).

## 6. Dependencies

- [ROADMAP](ROADMAP.md): phase structure and exit criteria this backlog serves.
- All referenced specifications: each task's DoD source of truth.
- Owner availability and decisions: TASK-005 and TASK-006 gate several downstream tasks.

## 7. Risks

- L-sized tasks hide complexity; the rule is that any L task gets its own breakdown before starting (tracked as sub-items under its ID).
- Maintenance tasks (§4.1) starve while build tasks proceed; mitigated by treating TASK-001 through TASK-006 as standing work reviewed at every phase gate.
- Dependency chains through TASK-301 (model router) and TASK-401 (agent runtime) concentrate risk; both are flagged for earliest-possible spikes.

## 8. Future Enhancements

- Import this backlog into a tracked issue system at implementation start, preserving TASK IDs bidirectionally.
- Burn-down reporting per phase once tasks are tracked.

## 9. Examples

A future session picks up TASK-206: it reads FS-009 in [FEATURE_SPECIFICATIONS](../specs/FEATURE_SPECIFICATIONS.md), the FR-VER group, and the queue screen in [UI_UX](../ui/UI_UX.md); implements the queue seeded with the six §12 items from MASTER_CONTEXT; proves the owner can resolve the WorldQuant enrollment claim end to end with an audit trail; and marks the task done with links to passing tests. No architectural decisions were needed: they were already made here.

## 10. Open Questions

- Should Phase 1 include a minimal read-only vault export (subset of TASK-504) so durability exists from day one? Leaning yes; decide at Phase 1 planning.

## 11. References

- [`knowledge/MASTER_CONTEXT.md`](../knowledge/MASTER_CONTEXT.md) §12 (the manual verification queue seeding TASK-001 through TASK-003).
- [`docs/SPEC_CONVENTIONS.md`](../docs/SPEC_CONVENTIONS.md) §4 (TASK ID rules).

## 12. Related Specifications

- [ROADMAP](ROADMAP.md), [RISKS](RISKS.md), [FUTURE_FEATURES](FUTURE_FEATURES.md)
- [FEATURE_SPECIFICATIONS](../specs/FEATURE_SPECIFICATIONS.md), [FUNCTIONAL_REQUIREMENTS](../specs/FUNCTIONAL_REQUIREMENTS.md), [NON_FUNCTIONAL_REQUIREMENTS](../specs/NON_FUNCTIONAL_REQUIREMENTS.md)
- [QUALITY_ASSURANCE](../testing/QUALITY_ASSURANCE.md), [CI_CD](../deployment/CI_CD.md)
