# BUILD_ORDER
### The exact build sequence for Legacy implementation sessions

| Field | Value |
|-------|-------|
| Status | Draft |
| Owner | Linford Musiyambodza |
| Last updated | 2026-07-02 |
| Depends on | [MVP_PLAN](MVP_PLAN.md), [IMPLEMENTATION_TASKS](IMPLEMENTATION_TASKS.md), [TASKS](TASKS.md) |

---

## 1. Purpose

This document tells any future implementation session, human or AI, exactly what to build first, second, third, and so on, and how to work so the result stays aligned with the specifications. If you are a fresh session about to write Legacy code: start here, follow the session protocol, take the lowest-numbered incomplete step.

## 2. Goals

- Zero ambiguity about what comes next at any point in the build.
- Every session starts with the right spec sections loaded, not with rediscovery.
- The build order preserves the invariants (tiers, provenance, audit, backups) by constructing them before the features that depend on them.

## 3. Scope

**In scope:** the session protocol, the strict MVP build sequence (steps 1 to 22 plus stretch steps S1 to S3), and the post-MVP continuation order. **Out of scope:** task detail (see [IMPLEMENTATION_TASKS](IMPLEMENTATION_TASKS.md)) and rationale for scope choices (see [MVP_PLAN](MVP_PLAN.md)).

## 4. Requirements

### 4.1 Session protocol (follow this every session)

1. **Orient.** Read [`docs/SPEC_CONVENTIONS.md`](../docs/SPEC_CONVENTIONS.md) fully, then [`knowledge/MASTER_CONTEXT.md`](../knowledge/MASTER_CONTEXT.md) §0 (tier rules). Never upgrade a 🟡 or 🔴 claim anywhere, including in test fixtures.
2. **Pick work.** Take the lowest-numbered incomplete step below. Do not skip ahead: later steps assume earlier invariants exist.
3. **Load context.** Read the "Read first" spec sections for that step before writing anything. They contain the decisions; do not re-make them.
4. **Spec-first rule.** If implementation reveals a spec conflict or gap, STOP: update the spec (with a [CHANGELOG](../CHANGELOG.md) entry) before writing the code that deviates ([QUALITY_ASSURANCE](../testing/QUALITY_ASSURANCE.md)).
5. **Test with the invariants.** Every step's tests include, where touched: tier filtering, deny-by-default, audit writes, provenance presence, and the no-em-dash lint for UI strings.
6. **Close out.** Acceptance criteria green in CI; commit messages cite the MVP task and spec sections; mark the step complete; note anything learned for the Gate G1 evidence log (step 21 creates it).
7. **Never do:** invent facts about the owner; put P2/P3 content in logs, fixtures, or external calls; add features not in the current step; bypass the policy service "just for now."

### 4.2 MVP build sequence

Steps map one-to-one to tasks in [IMPLEMENTATION_TASKS](IMPLEMENTATION_TASKS.md). Complete in order; parallelize only where the dependency column allows.

| Step | Build | Task | Read first | Done when |
|------|-------|------|-----------|-----------|
| 1 | Repo scaffolding, environments, secrets | MVP-001 | [DEPLOYMENT](../deployment/DEPLOYMENT.md) §4.1-§4.6 | Deploy and rollback of a stub succeeds in all environments |
| 2 | CI pipeline and quality gates | MVP-002 | [CI_CD](../deployment/CI_CD.md) §4.2-§4.3 | A broken test demonstrably blocks a merge |
| 3 | Full logical schema migration | MVP-003 | [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md) §4.2-§4.7 | Clean apply, reversibility, tier default and claim-tier constraints tested |
| 4 | AuthN: OIDC, MFA, sessions | MVP-004 | [AUTHENTICATION](../security/AUTHENTICATION.md) §4.1-§4.3, §4.6 | Owner matrix rows pass; no MFA bypass; auth events audited |
| 5 | AuthZ: policy service, ceilings, deny-by-default | MVP-006 | [AUTHORIZATION](../security/AUTHORIZATION.md) §4.1-§4.5, §4.7 | Matrix and existence-leak tests pass; denials audited |
| 6 | API skeleton: envelope, pagination, idempotency | MVP-007 | [API_SPECIFICATION](../api/API_SPECIFICATION.md) §4.1-§4.3 | Conventions contract tests pass |
| 7 | Observability: logs, redaction, tracing, alerts | MVP-008 | [OBSERVABILITY](../deployment/OBSERVABILITY.md) logging, tracing, audit sections | Redaction test proves no P2 content in logs; test alert received |
| 8 | Backups: continuous, snapshots, runbooks 1-2 | MVP-009 | [BACKUP_AND_RECOVERY](../deployment/BACKUP_AND_RECOVERY.md) §4.1-§4.4, §4.6 | Point-in-time restore drill passes to scratch |
| 9 | PATs (may run parallel to 10-12) | MVP-005 | [AUTHENTICATION](../security/AUTHENTICATION.md) §4.3; [API_SPECIFICATION](../api/API_SPECIFICATION.md) §4.5 | Scope enforcement and revocation tests pass |
| 10 | Ingestion pipeline: documents and notes | MVP-010 | FS-001 in [FEATURE_SPECIFICATIONS](../specs/FEATURE_SPECIFICATIONS.md); FR-ING group | FS-001 scenarios pass; dedup and review-flag paths tested |
| 11 | CaptureQuickAdd and capture inbox | MVP-011 | [UI_UX](../ui/UI_UX.md) §4.1, §4.4; [DESIGN_SYSTEM](../ui/DESIGN_SYSTEM.md) §4.2; [ACCESSIBILITY](../ui/ACCESSIBILITY.md) §4.3 | One-action capture everywhere; keyboard-complete; under a minute measured |
| 12 | Workspace shell: nav, dashboard v0, item views | MVP-012 | [UI_UX](../ui/UI_UX.md) §4.1-§4.3, §4.5 | IA reachable; all states implemented; accessibility gate green |
| 13 | Seed MASTER_CONTEXT as tiered Claims | MVP-013 | [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md) §4.4; MASTER_CONTEXT §0, §12 | Sampled tiers correct; six flagged §12 claims present; idempotent |
| 14 | Seed owner document batch | MVP-014 | [MVP_PLAN](MVP_PLAN.md) §6 owner inputs | Batch listed in workspace; failures reviewed |
| 15 | Revision history and soft delete | MVP-015 | [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md) §4.8 | NFR-022 test passes; undo works |
| 16 | Chunking, embeddings, lexical index | MVP-016 | [RAG_PIPELINE](../ai/RAG_PIPELINE.md) chunking and indexing sections | Rebuild drill passes (NFR-024); chunks carry tier and provenance |
| 17 | Search API with tier filtering | MVP-017 | [API_SPECIFICATION](../api/API_SPECIFICATION.md) search; [RAG_PIPELINE](../ai/RAG_PIPELINE.md) query pipeline; NFR-035 | Leak suite passes; NFR-001/002 met; golden-set baseline recorded |
| 18 | Search UI with provenance badges | MVP-018 | [UI_UX](../ui/UI_UX.md) search; [ACCESSIBILITY](../ui/ACCESSIBILITY.md) §4.5 | FS-004 scenarios; badges text-labeled (NFR-043) |
| 19 | Performance verification | MVP-019 | [NON_FUNCTIONAL_REQUIREMENTS](../specs/NON_FUNCTIONAL_REQUIREMENTS.md) §4.1 | Measurements recorded; Must NFRs green or triaged |
| 20 | Verification queue MVP | MVP-020 | FS-009; [UI_UX](../ui/UI_UX.md) queue screen | Six §12 items listed; one resolved end to end in production |
| 21 | Hardening, full restore drill, go-live checklist | MVP-021 | [BACKUP_AND_RECOVERY](../deployment/BACKUP_AND_RECOVERY.md) §4.6-§4.7; [SECURITY](../security/SECURITY.md) controls | Runbook 3 drill passes; checklist signed; G1 evidence log opened |
| 22 | MVP acceptance run and spec sync | MVP-022, MVP-023 | [MVP_PLAN](MVP_PLAN.md) §5; [QUALITY_ASSURANCE](../testing/QUALITY_ASSURANCE.md) release criteria | Criteria 1-6 pass in production; CHANGELOG updated; zero undocumented deviations |

**Stretch steps (only after step 22, only if the window allows):**

| Step | Build | Task | Read first | Done when |
|------|-------|------|-----------|-----------|
| S1 | Model router skeleton, Claude only | MVP-024 | [AI_ARCHITECTURE](../ai/AI_ARCHITECTURE.md) router and cost sections | All calls routed; spend visible; cap halts |
| S2 | Owner-only cited ask | MVP-025 | [RAG_PIPELINE](../ai/RAG_PIPELINE.md) generation rules; [API_SPECIFICATION](../api/API_SPECIFICATION.md) ask | Citation coverage 100 percent on mini-set; refusals verified |
| S3 | Tier-discipline mini-eval gate | MVP-026 | NFR-038; [TESTING](../testing/TESTING.md) AI evaluation category | Seeded violation fails the gate; flag off while red |

### 4.3 After the MVP

Continue in [TASKS](TASKS.md) order, respecting roadmap gates:

1. **Finish Phase 2:** TASK-203 (Graph Agent), TASK-204 (graph explorer), TASK-205 (timeline), TASK-207 (GitHub connector), then the G2 review (TASK-208) with real graph data.
2. **Phase 3:** TASK-301 completion (Gemini and Groq routing), TASK-302 to TASK-304 hardening of ask into full RAG (or first build if stretch was skipped), TASK-305 (memory), TASK-306 (explorer), TASK-307 (multimedia ingestion), then Gate G3.
3. **Phase 4:** TASK-401 to TASK-409 in their listed dependency order, then Gate G4 (twin honesty gate: two consecutive green review points before anything beyond the owner sees twin output).
4. **Phase 5:** TASK-501 to TASK-508, then Gate G5 (public launch and v1 declaration).
5. **Always-on:** the maintenance tasks TASK-001 to TASK-006, especially the verification queue (RISK-08) and CHANGELOG discipline.

## 5. Acceptance Criteria

- Following steps 1 to 22 in order, with each step's "Done when" satisfied, produces exactly the MVP accepted by [MVP_PLAN](MVP_PLAN.md) §5.
- No step requires reading anything outside this repository to make a decision.
- The session protocol is sufficient for a fresh session to contribute safely without prior conversation history.
- The post-MVP continuation reaches v1 without ever contradicting a roadmap gate.

## 6. Dependencies

- [IMPLEMENTATION_TASKS](IMPLEMENTATION_TASKS.md) task definitions (this document adds ordering, not content).
- [MVP_PLAN](MVP_PLAN.md) §6 external dependencies, which gate step 1 (accounts) and step 14 (owner document selection).

## 7. Risks

- Sessions skipping the protocol's "Read first" column will re-make decisions the specs already made; the protocol's step 3 exists precisely for this, and review should reject changes that cite no spec sections.
- Parallel sessions could collide; the rule is one session per step, and steps 9-12 are the only sanctioned parallel window in the MVP.
- The descope ladder ([MVP_PLAN](MVP_PLAN.md) §7) changes step order under time pressure; if invoked, record the reordering here with a CHANGELOG entry.

## 8. Future Enhancements

- Once implementation begins, augment each step with links to the merged PRs that completed it, turning this document into a build log as well as a plan.
- Generate a machine-readable step-status file if multiple AI sessions begin coordinating.

## 9. Examples

A fresh session opens the repository, reads SPEC_CONVENTIONS and MASTER_CONTEXT §0 (protocol step 1), finds steps 1 through 7 marked complete and takes step 8 (backups). It reads BACKUP_AND_RECOVERY §4.1 to §4.4 and §4.6, implements continuous backup and the two runbooks, runs the point-in-time drill to a scratch environment, verifies checksums, commits citing MVP-009 and the spec sections, and marks step 8 complete. It does not touch ingestion (step 10): that is the next session's job.

## 10. Open Questions

- Where is step status tracked (checklist in this file versus issue tracker)? Default until decided: a status column maintained directly in this file's tables via pull requests.

## 11. References

- [`docs/SPEC_CONVENTIONS.md`](../docs/SPEC_CONVENTIONS.md) (the first read of every session).
- [`knowledge/MASTER_CONTEXT.md`](../knowledge/MASTER_CONTEXT.md) §0 (the tier discipline every step inherits).

## 12. Related Specifications

- [MVP_PLAN](MVP_PLAN.md), [IMPLEMENTATION_TASKS](IMPLEMENTATION_TASKS.md), [TASKS](TASKS.md), [ROADMAP](ROADMAP.md)
- [QUALITY_ASSURANCE](../testing/QUALITY_ASSURANCE.md) (the spec-first rule the protocol enforces)
