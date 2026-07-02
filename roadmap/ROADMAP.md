# ROADMAP
### Phase-based delivery roadmap for Legacy, from completed specification to a living, succession-ready platform

| Field | Value |
|-------|-------|
| Status | Draft |
| Owner | Linford Musiyambodza |
| Last updated | 2026-07-02 |
| Depends on | [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md), [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md), [VISION](../docs/VISION.md), [TASKS](./TASKS.md), [RISKS](./RISKS.md) |

---

## 1. Purpose

This document defines the delivery plan for Legacy as an ordered sequence of phases, each with an objective, feature scope, entry criteria, testable exit criteria, key risks, and decision gates. It exists so that a solo founder (or any future maintainer or AI session) always knows what to build next, what "done" means for the current phase, and which decisions must be revisited before proceeding.

Planning is phase-based, not date-based. The owner's actual weekly availability, budget, and team size are unknown, so this roadmap never promises calendar dates; it promises ordering, dependencies, and completion tests.

> TODO(verify): Owner's sustained weekly capacity for implementation work, monthly infrastructure and LLM budget, and whether any collaborator time is available. Source: a direct planning conversation with the owner. Until confirmed, all phases assume a single part-time builder.

## 2. Goals

1. Sequence the sixteen features (F1-F16) so that each phase produces standalone value even if later phases are delayed or abandoned.
2. Make every phase completion objectively testable, so "done" is never a feeling.
3. Front-load the capabilities that make the platform personally valuable early, directly mitigating the motivation risk in [RISKS](./RISKS.md) (RISK-02).
4. Encode decision gates at phase exits so that architecture defaults (Supabase, Postgres graph modeling, model routing) are re-examined with real evidence rather than locked in forever.
5. Keep the specification repository (Phase 0 output) current as the system evolves, per the maintenance tasks in [TASKS](./TASKS.md).

## 3. Scope

### 3.1 In scope

- Phases 0 through 5, their objectives, feature scope, entry and exit criteria, key risks, and decision gates.
- A milestone dependency diagram across phases.
- A "first 90 days of usage" narrative describing Phase 1 value in practice.

### 3.2 Out of scope

- Task-level breakdowns: see [TASKS](./TASKS.md) (TASK-001 upward).
- The full risk register: see [RISKS](./RISKS.md) (RISK-01 upward).
- Post-v1 candidates: see [FUTURE_FEATURES](./FUTURE_FEATURES.md), none of which are committed.
- Calendar dates, deadlines, and staffing plans (capacity unknown, see the TODO above).

## 4. Requirements

### 4.1 Planning principles

| Principle | Meaning |
|-----------|---------|
| Phase order is normative | A phase does not start until its entry criteria hold; exit criteria are the only definition of phase completion |
| Value every phase | Each phase must leave the owner with something he uses weekly, even if the project pauses afterward |
| Gates before momentum | Decision gates at phase exits are mandatory review points, recorded as ADR updates in [MASTER_ARCHITECTURE](../architecture/MASTER_ARCHITECTURE.md) |
| Specs stay live | Any implementation deviation from a spec triggers a spec update and a [CHANGELOG](../CHANGELOG.md) entry before the code is considered done |
| No date promises | Progress is measured by exit criteria met, not by time elapsed |

### 4.2 Phase overview

| Phase | Name | Feature scope | Headline outcome |
|-------|------|---------------|------------------|
| 0 | Specification | This repository | A complete, implementable specification set (complete) |
| 1 | Foundation | F1 partial, F11 partial | Sign in, capture documents and notes, everything backed up |
| 2 | Knowledge Core | F2, F3, F4, F9 MVP | Structured knowledge: graph, timeline, search, verification queue |
| 3 | Intelligence | F5, F7, F13 | Cited answers from the corpus, persistent memory, explorer |
| 4 | Twin and Agents | F6, F8, F14, F15 | An honest twin, orchestrated agents, mentor and writing support |
| 5 | Legacy and Public | F10, F12, F16 | Public portfolio, sealed journals, vault export and succession |

### 4.3 Milestone dependency diagram

```
Phase 0 (complete)
+----------------------------------------------------------------------+
| M0 Specification repository (all specs authored per SPEC_CONVENTIONS)|
+----------------------------------------------------------------------+
      |
      v
Phase 1: Foundation
+----------------------------------------------------------------------+
| M1 Identity and auth      M2 Database schema v1                      |
|        \                   /        \                                |
|         v                 v          v                               |
| M3 Ingestion MVP (F1 partial)   M4 Private workspace shell (F11)     |
|         (documents and notes)                                        |
+----------------------------------------------------------------------+
      |            [Gate G1: stack confirmation]
      v
Phase 2: Knowledge Core
+----------------------------------------------------------------------+
| M5 Knowledge graph (F2) <- needs M2, M3                              |
| M6 Timeline engine (F3) <- needs M5                                  |
| M7 Search (F4)          <- needs M2, M3                              |
| M8 Verification queue MVP (F9) <- needs M2; seeded from              |
|                                   MASTER_CONTEXT section 12          |
+----------------------------------------------------------------------+
      |            [Gate G2: graph database re-evaluation]
      v
Phase 3: Intelligence
+----------------------------------------------------------------------+
| M9  RAG with citations (F5) <- needs M7, M8                          |
| M10 Long-term memory (F7)   <- needs M2, M7                          |
| M11 Project and research explorer (F13) <- needs M5, M6, M7          |
+----------------------------------------------------------------------+
      |            [Gate G3: RAG quality and spend review]
      v
Phase 4: Twin and Agents
+----------------------------------------------------------------------+
| M12 Multi-agent orchestration (F8) <- needs M9, M10                  |
| M13 Digital twin, tier-aware honesty (F6) <- needs M8, M9, M10       |
| M14 Mentor (F14) and M15 Writing (F15) <- need M12                   |
+----------------------------------------------------------------------+
      |            [Gate G4: twin honesty gate]
      v
Phase 5: Legacy and Public
+----------------------------------------------------------------------+
| M16 Public portfolio (F10) <- needs M8 (publication gate)            |
| M17 Journals with sealing (F12) <- needs M1 privacy tiers            |
| M18 Vault export and succession (F16) <- needs M2, backup discipline |
+----------------------------------------------------------------------+
      |            [Gate G5: public launch and v1 declaration]
      v
Ongoing operation, maintenance, and FUTURE_FEATURES triggers
```

### 4.4 Phase 0: Specification (complete)

- **Objective:** Produce a complete, conventions-compliant specification repository from which the entire system can be implemented without redesign.
- **Feature scope:** No product features; the deliverable is this repository, including [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md) with its confidence tiers and section 12 verification queue.
- **Entry criteria:** Decision to build Legacy as a specification-driven project.
- **Exit criteria (met):** Every document in the repository map of [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md) exists and follows the mandatory structure; MASTER_CONTEXT is consolidated with tiered claims and an explicit verification queue; ID schemes are assigned without collisions.
- **Key risks:** RISK-09 (verification debt begins here if the section 12 queue is ignored), RISK-03 (spec scope creep).
- **Decision gates:** None; the standing obligation is spec maintenance (TASK-001 through TASK-008 in [TASKS](./TASKS.md)).

### 4.5 Phase 1: Foundation

- **Objective:** Stand up the minimum trustworthy system of record: the owner can sign in, capture documents and notes with privacy tier defaults, and nothing captured can be silently lost.
- **Feature scope:** Identity and authentication, authorization scaffolding with privacy tiers P0-P3 (default P2), database schema v1, ingestion MVP for documents and notes (F1 partial, the FR-ING group), private workspace shell (F11 partial), backups, CI/CD, observability baseline.
- **Entry criteria:** Phase 0 exit criteria met; hosting and Supabase accounts provisioned; secrets management in place.
- **Exit criteria (testable):**
  1. The owner signs in via OAuth 2.0 / OIDC and a personal access token, per [AUTHENTICATION](../security/AUTHENTICATION.md); every sign-in writes an `AuditLogEntry`.
  2. A document and a note uploaded through the workspace are stored as `Artifact` and `Note` rows with tier P2 by default, with an `IngestionJob` recording the pipeline outcome.
  3. Automated backups run on schedule and one full restore drill has passed, per [BACKUP_AND_RECOVERY](../deployment/BACKUP_AND_RECOVERY.md).
  4. CI runs the test baseline in [TESTING](../testing/TESTING.md) on every change and blocks on failure.
  5. The seed corpus (existing documents, writing, and this repository) is imported and listed in the workspace.
- **Key risks:** RISK-02 (early value must be real or the project stalls), RISK-03 (scope creep into later phases), RISK-13 (data loss before backup discipline exists), RISK-01 (bus factor).
- **Decision gate G1, stack confirmation:** After real usage, confirm or revise the baseline defaults (Supabase, FastAPI, Next.js) via ADR update in [MASTER_ARCHITECTURE](../architecture/MASTER_ARCHITECTURE.md). Changing datastore later is far more expensive than changing it here.

### 4.6 Phase 2: Knowledge Core

- **Objective:** Turn the stored corpus into structured, navigable knowledge: entities and relationships, a chronology, fast search, and a working provenance discipline.
- **Feature scope:** F2 knowledge graph (node and edge tables in PostgreSQL per the baseline decision), F3 timeline engine, F4 search (semantic and hybrid over pgvector), F9 verification and citation engine MVP: the `Claim` and `Source` model plus a verification queue whose seed data is exactly the MASTER_CONTEXT section 12 items.
- **Entry criteria:** Phase 1 exit criteria met; Gate G1 decision recorded; corpus contains enough real content for extraction and search to be meaningfully testable.
- **Exit criteria (testable):**
  1. Entity extraction over the corpus produces `Person`, `Organization`, `Project`, and `Event` records with typed `Edge` relationships, each traceable to its source `Artifact`, per [KNOWLEDGE_GRAPH](../knowledge/KNOWLEDGE_GRAPH.md).
  2. The timeline renders owner-confirmed events in chronological order at multiple zoom levels, per the FR-TL group in [FUNCTIONAL_REQUIREMENTS](../specs/FUNCTIONAL_REQUIREMENTS.md).
  3. Hybrid search returns relevant results for natural-language queries within the latency targets of [NON_FUNCTIONAL_REQUIREMENTS](../specs/NON_FUNCTIONAL_REQUIREMENTS.md), and respects privacy tiers.
  4. The verification queue exists, is seeded with every MASTER_CONTEXT section 12 item, and at least one 🔴 item has been resolved end to end (evidence attached, tier updated, MASTER_CONTEXT changelog entry written).
  5. No graph or search operation exposes content above the querying identity's tier.
- **Key risks:** RISK-17 (extraction errors polluting the graph), RISK-09 (verification queue treated as decoration), RISK-18 (search quality), RISK-05 (tier leaks through new query paths).
- **Decision gate G2, graph database re-evaluation:** With real graph size and query patterns known, decide whether PostgreSQL node and edge tables remain sufficient or a dedicated graph database migration (see [FUTURE_FEATURES](./FUTURE_FEATURES.md)) is warranted. Also lock the embedding model choice and record the re-embedding cost implications.

### 4.7 Phase 3: Intelligence

- **Objective:** Make the corpus answer questions honestly: retrieval-augmented answers with citations and confidence tiers, a memory engine that persists across sessions, and an explorer for projects and research.
- **Feature scope:** F5 RAG question answering with mandatory citations, F7 long-term memory engine (`MemoryRecord`, the four long-term memory types of [MEMORY_SYSTEM](../memory/MEMORY_SYSTEM.md)), F13 project and research explorer, model routing abstraction (Anthropic primary, Gemini and Groq secondary per the baseline decision), prompt injection defenses, cost tracking.
- **Entry criteria:** Phase 2 exit criteria met; Gate G2 decision recorded; verification queue operational so citations can carry tiers.
- **Exit criteria (testable):**
  1. Every RAG answer cites its sources with confidence tiers, per [RAG_PIPELINE](../ai/RAG_PIPELINE.md) and the FR-VER group; answers with no supporting content return an explicit "not in my knowledge" refusal instead of invention.
  2. The RAG evaluation harness reports citation coverage and faithfulness above the thresholds defined in [QUALITY_ASSURANCE](../testing/QUALITY_ASSURANCE.md).
  3. Memory records persist across sessions and consolidation produces reflective summaries, per [MEMORY_SYSTEM](../memory/MEMORY_SYSTEM.md).
  4. The explorer browses projects and research with graph, timeline, and search integration (F13).
  5. Adversarial content planted in an ingested document does not alter system behavior (prompt injection suite in [SECURITY](../security/SECURITY.md) passes).
  6. Monthly LLM spend is visible on a dashboard with alert thresholds.
- **Key risks:** RISK-04 (cost escalation begins with heavy LLM use), RISK-06 (prompt injection surface opens), RISK-10 (behavior drift), RISK-18 (retrieval quality gates answer quality).
- **Decision gate G3, RAG quality and spend review:** Twin work (Phase 4) does not start until citation coverage, refusal accuracy, and cost-per-answer are measured and accepted. A twin built on a weak retrieval layer would be fluent and wrong, which is the worst outcome for this project.

### 4.8 Phase 4: Twin and Agents

- **Objective:** Introduce the digital twin with tier-aware honesty and the multi-agent runtime, then layer mentor and writing capabilities on top.
- **Feature scope:** F6 AI digital twin (voice and values per [DIGITAL_TWIN](../ai/DIGITAL_TWIN.md), honesty rules productizing MASTER_CONTEXT section 0), F8 multi-agent orchestration using the canonical roster of [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md) section 7, F14 mentor and career advisor, F15 writing and presentation assistant.
- **Entry criteria:** Phase 3 exit criteria met; Gate G3 thresholds accepted; style calibration corpus assembled (owner writing samples, with stylistic preferences kept at their 🟡 tier).
- **Exit criteria (testable):**
  1. The twin passes the honesty red-team suite: it attributes 🟡 claims ("Linford states that"), flags 🔴 claims as unverified, never upgrades a tier, and refuses questions outside its knowledge, per [DIGITAL_TWIN](../ai/DIGITAL_TWIN.md) and the FR-TWIN group.
  2. The Orchestrator Agent routes multi-step requests across at least four roster agents with per-run budget caps and full `AgentRun` audit trails, per [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md).
  3. No agent publishes, messages, or deletes anything without explicit owner approval (autonomy boundary tests pass).
  4. The Mentor Agent produces advice grounded in the owner's recorded trajectory, goals, and lessons, with citations (F14).
  5. The Writing Agent drafts an article and a presentation outline conforming to the documented style guide, including the no-em-dash rule (F15).
  6. A behavioral regression baseline is pinned so that provider model upgrades can be diffed before adoption.
- **Key risks:** RISK-08 (twin misrepresentation is the flagship reputational risk), RISK-10 (drift invalidating calibration), RISK-04 (agent loops multiply cost), RISK-03 (agent scope creep).
- **Decision gate G4, twin honesty gate:** No twin or agent output surface may be exposed beyond the owner (P1 or P0) until the honesty suite pass rate meets the [QUALITY_ASSURANCE](../testing/QUALITY_ASSURANCE.md) threshold at two consecutive review points.

### 4.9 Phase 5: Legacy and Public

- **Objective:** Open the platform outward and secure it downward: a public portfolio that never overstates, sealed journals, and an export and succession pathway that works without the owner.
- **Feature scope:** F10 public portfolio (P0 content only), F12 journals and reflections with P3 sealing, F16 legacy vault export and succession.
- **Entry criteria:** Phase 4 exit criteria met; Gate G4 passed; POPIA review scheduled; verification queue healthy (no untriaged 🔴 items older than the staleness threshold defined in the verification specs).
- **Exit criteria (testable):**
  1. The public portfolio serves only P0 content; the publication gate blocks any 🔴 claim and renders 🟡 claims with attribution, per the FR-VER group and [PRIVACY](../security/PRIVACY.md).
  2. Journal entries can be sealed to P3 with time-lock or succession-gated release conditions, and no query path (search, RAG, twin, export to third parties) can read sealed content before its condition is met (F12).
  3. A versioned Legacy Vault export (Markdown, JSON, media manifest) is produced, restored on a clean machine, and read offline end to end (F16).
  4. The succession runbook has been exercised in a steward simulation: a technically competent person other than the owner completes the documented steps to gain steward access and operate core functions.
  5. POPIA compliance review is complete and the third-party complaint process (for named collaborators in the corpus) is documented and reachable from the public site.
- **Key risks:** RISK-05 (public surface raises breach stakes), RISK-14 (POPIA), RISK-15 (third-party complaints), RISK-16 (succession failure), RISK-09 (verification debt leaking into public content).
- **Decision gate G5, public launch and v1 declaration:** Go/no-go on public exposure, then declare v1 and move remaining ambitions to [FUTURE_FEATURES](./FUTURE_FEATURES.md) triage.

## 5. Acceptance Criteria

This roadmap itself is accepted when:

1. Every phase has an objective, feature scope, entry criteria, testable exit criteria, key risks (cross-referenced to RISK IDs), and a decision gate or an explicit statement that none exists.
2. All sixteen features F1-F16 are assigned to exactly one primary phase (partial early delivery is called out explicitly, as with F1 and F11 in Phase 1).
3. Every exit criterion is verifiable by a named artifact, test, or drill, not by opinion.
4. The dependency diagram is consistent with the per-phase entry criteria and with task dependencies in [TASKS](./TASKS.md).
5. No calendar dates appear anywhere in the plan.

## 6. Dependencies

- [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md): confidence tiers and the section 12 queue that seeds the Phase 2 verification MVP.
- [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md): baseline architecture defaults that Gates G1 and G2 re-examine, canonical agent roster for Phase 4.
- [TASKS](./TASKS.md) and [RISKS](./RISKS.md): the task backlog and risk register this roadmap sequences and cites.
- The requirements suite in `specs/` (referenced by document name and domain group) for what each feature must do.
- [BACKUP_AND_RECOVERY](../deployment/BACKUP_AND_RECOVERY.md), [SECURITY](../security/SECURITY.md), [PRIVACY](../security/PRIVACY.md): the operational specs that several exit criteria test against.
- External: Supabase, hosting, and LLM provider accounts; owner capacity (unknown, see the TODO in section 1).

## 7. Risks

The full register is [RISKS](./RISKS.md). Roadmap-level concentrations:

| Phase | Dominant risks |
|-------|----------------|
| 1 | RISK-01, RISK-02, RISK-03, RISK-13 |
| 2 | RISK-05, RISK-09, RISK-17, RISK-18 |
| 3 | RISK-04, RISK-06, RISK-10, RISK-18 |
| 4 | RISK-03, RISK-04, RISK-08, RISK-10 |
| 5 | RISK-05, RISK-09, RISK-14, RISK-15, RISK-16 |
| All | RISK-01 (bus factor), RISK-11 (vendors), RISK-12 (format rot) |

The single most important structural mitigation is ordering: honesty infrastructure (F9) ships two phases before the twin (F6), and the twin ships one phase before anything public (F10).

## 8. Future Enhancements

- Post-v1 candidates, triggers, and complexity estimates live in [FUTURE_FEATURES](./FUTURE_FEATURES.md); none are committed.
- A possible Phase 6 (multi-user or company mode) would only be planned if the corresponding triggers in that document fire.
- Roadmap re-baselining: once owner capacity is verified, this document may gain coarse effort bands per phase (still not dates).

## 9. Examples

### 9.1 The first 90 days of usage (Phase 1 value narrative)

This narrative describes the first 90 days of daily use after the Phase 1 exit criteria pass. It is relative to Phase 1 completion, not to any calendar date, and exists to make the early-value promise concrete (RISK-02 mitigation).

**Days 1 to 30: capture becomes a habit.** Linford signs in each morning and drops in whatever the previous day produced: a hackathon writeup, a project README, meeting notes, a DEV.to draft. Each item lands as P2 by default, gets an `IngestionJob` record, and appears in the workspace list within seconds. The friction target is under a minute per capture; anything slower gets logged as a bug. By day 30 the corpus holds the seed import plus a growing daily layer, and the first scheduled backup restore drill has already proven that nothing here can silently vanish.

**Days 31 to 60: the archive starts paying rent.** With a few hundred items stored, simple listing, filtering, and keyword lookup (the pre-semantic baseline) already beat scattered folders and platform searches. Linford stops re-explaining context to fresh AI chat sessions for anything he can paste from the workspace. Capture gaps discovered in real use (a file type that fails to parse, a note field that is too rigid) become backlog items in [TASKS](./TASKS.md) rather than reasons to abandon the system.

**Days 61 to 90: evidence for the next phase.** The corpus is now large and real enough that Phase 2 extraction and search can be tested against genuine material instead of toy data. Usage logs show which capture paths matter most, which informs entity extraction priorities. At day 90 the owner reviews Gate G1 with actual evidence: does Supabase feel right, is the schema holding, is capture friction low enough to sustain for decades? Only then does Phase 2 begin.

### 9.2 Example of a gate decision record

At Gate G2, an ADR update in [MASTER_ARCHITECTURE](../architecture/MASTER_ARCHITECTURE.md) might read: "Graph re-evaluated at Phase 2 exit with N nodes and M edges; PostgreSQL traversal latency within targets; dedicated graph database deferred; revisit trigger set at the thresholds recorded in FUTURE_FEATURES."

## 10. Open Questions

- > TODO(verify): Owner capacity, budget, and collaborator availability (section 1). This is the largest planning unknown.
- Should Phase 2 and Phase 3 overlap for a solo builder (search shipping while graph extraction matures), or is strict sequencing safer? Deferred to Gate G1 with usage evidence.
- What corpus size makes Phase 2 entry meaningful? A provisional heuristic (enough real documents to test extraction) is used; a concrete number should be set when the seed import completes.
- Where should the steward simulation participant come from (family, a trusted peer such as a named collaborator, or a professional)? Sensitive, owner decision; see also RISK-16.
- Does the ADEL or ICMM outcome (🔴 in MASTER_CONTEXT section 7) change portfolio priorities for Phase 5? Blocked on the verification queue.

## 11. References

- [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md), sections 0 (tiers), 5 (stack evidence), 6 (projects), 12 (verification queue).
- [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md), sections 4 (ID schemes), 5 (privacy tiers), 7 (agent roster), 9 (baseline architecture decisions).
- [VISION](../docs/VISION.md), the horizon model (H1 to H3) this roadmap operationalizes.

## 12. Related Specifications

- [TASKS](./TASKS.md): the backlog implementing this roadmap.
- [RISKS](./RISKS.md): the register cited throughout.
- [FUTURE_FEATURES](./FUTURE_FEATURES.md): everything intentionally excluded from v1.
- [MASTER_ARCHITECTURE](../architecture/MASTER_ARCHITECTURE.md): ADRs updated at every gate.
- [FUNCTIONAL_REQUIREMENTS](../specs/FUNCTIONAL_REQUIREMENTS.md) and [FEATURE_SPECIFICATIONS](../specs/FEATURE_SPECIFICATIONS.md): what each phase's features must do.
- [BACKUP_AND_RECOVERY](../deployment/BACKUP_AND_RECOVERY.md), [SECURITY](../security/SECURITY.md), [PRIVACY](../security/PRIVACY.md), [QUALITY_ASSURANCE](../testing/QUALITY_ASSURANCE.md): sources of the drills and thresholds used as exit criteria.
