# FUTURE_FEATURES
### Post-v1 candidates for the Legacy platform: explored, not committed

| Field | Value |
|-------|-------|
| Status | Draft |
| Owner | Linford Musiyambodza |
| Last updated | 2026-07-02 |
| Depends on | [ROADMAP](ROADMAP.md), [FEATURE_SPECIFICATIONS](../specs/FEATURE_SPECIFICATIONS.md), [RISKS](RISKS.md) |

---

## 1. Purpose

This document holds everything worth remembering but not worth building yet. Each candidate gets a concept, its value, a trigger condition (what must be true before investing), spec impact, and rough complexity. Nothing here is committed; this is the pressure valve that keeps the v1 scope honest (RISK-10 in [RISKS](RISKS.md)).

## 2. Goals

- Capture good ideas without letting them distort the phase plan.
- Give every candidate an objective trigger so revisiting is a decision, not a mood.
- Record which specifications each candidate would touch, so future design starts informed.

## 3. Scope

**In scope:** post-v1 platform candidates. **Out of scope:** anything already in the sixteen v1 features (see [FEATURE_SPECIFICATIONS](../specs/FEATURE_SPECIFICATIONS.md)) and speculative ideas with no articulable value yet (those live as `Idea` entities in the corpus itself once the platform runs).

**Everything in this document is explicitly NOT committed.**

## 4. Requirements

### 4.1 Candidate register

**FF-01 · Android companion app**
- **Concept.** Native capture-first Android app: quick text, photo, voice capture, offline queue, notification-based agent approvals.
- **Value.** Capture friction is the biggest threat to corpus growth (RISK-15); the owner's Android skills are verified (✅ Kotlin, Jetpack Compose, MASTER_CONTEXT §5), making this unusually cheap for him to build.
- **Trigger.** Phase 3 complete, and mobile-web capture demonstrably losing captures (measured, not felt).
- **Spec impact.** New mobile spec; extensions to [API_SPECIFICATION](../api/API_SPECIFICATION.md) (offline sync, push approvals); [AUTHENTICATION](../security/AUTHENTICATION.md) device credentials.
- **Complexity.** Large.

**FF-02 · Full voice interface**
- **Concept.** Spoken conversations with the twin and voice-driven capture and search, building on the transcription pipeline.
- **Value.** Hands-free capture; accessibility win; natural fit with the twin. The owner has studied voice agents (🟡, DeepLearning.AI coursework, §8).
- **Trigger.** FS-006 stable with high persona-fidelity scores; voice capture (FS-001 subset) proven in demand.
- **Spec impact.** [AI_ARCHITECTURE](../ai/AI_ARCHITECTURE.md) voice stack section; [DIGITAL_TWIN](../ai/DIGITAL_TWIN.md) spoken-disclosure rules; [ACCESSIBILITY](../ui/ACCESSIBILITY.md) voice interaction patterns.
- **Complexity.** Large.

**FF-03 · Family multi-user expansion**
- **Concept.** Family members get their own corpora and twins under one family instance, with shared family spaces.
- **Value.** Extends the mission from one life to a family's living memory across generations.
- **Trigger.** Explicit demand from actual family members; single-owner platform stable through a full year of production use.
- **Spec impact.** Deep: tenancy model in [MASTER_ARCHITECTURE](../architecture/MASTER_ARCHITECTURE.md) (ADR revision), [AUTHORIZATION](../security/AUTHORIZATION.md) cross-corpus rules, [PRIVACY](../security/PRIVACY.md) inter-family tiers.
- **Complexity.** Very large.
- > TODO(verify): no family member requirements exist on record; gather them before any design work.

**FF-04 · Linfy Tech Solutions company knowledge base mode**
- **Concept.** A multi-tenant evolution hosting company knowledge (projects, decisions, agents) for Linfy Tech Solutions (✅ the company exists; its internal agent ecosystem plans are 🟡, §6 and §11).
- **Value.** Reuses the platform for the owner's company; aligns with his stated ambition of an internal multi-agent operating layer (🟡).
- **Trigger.** Company headcount or knowledge volume that a personal instance clearly cannot serve; Legacy v1 complete.
- **Spec impact.** Tenancy, branding (the white-label note in [DESIGN_SYSTEM](../ui/DESIGN_SYSTEM.md)), org roles in [AUTHORIZATION](../security/AUTHORIZATION.md). Keep Legacy's agent roster distinct from Hermes naming per [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md) §1.
- **Complexity.** Very large.

**FF-05 · Public researcher API**
- **Concept.** A documented read-only API over P0 content with generous quotas for researchers, journalists, and archivists.
- **Value.** Serves the machine-consumer persona at internet scale; furthers the build-in-public mission (✅ §1).
- **Trigger.** Portfolio live and stable; observed third-party scraping or integration interest.
- **Spec impact.** [API_SPECIFICATION](../api/API_SPECIFICATION.md) public tier (keys, quotas, terms); [OBSERVABILITY](../deployment/OBSERVABILITY.md) abuse monitoring.
- **Complexity.** Medium.

**FF-06 · Dedicated graph database migration**
- **Concept.** Move the knowledge graph from Postgres tables to a purpose-built graph store.
- **Value.** Faster deep traversals and richer graph algorithms if scale demands it.
- **Trigger.** The standing decision gate: Phase 2 exit review (TASK-208) or later measurements showing Postgres traversal genuinely limiting product behavior (per the ADR in [MASTER_ARCHITECTURE](../architecture/MASTER_ARCHITECTURE.md)).
- **Spec impact.** [KNOWLEDGE_GRAPH](../knowledge/KNOWLEDGE_GRAPH.md) storage mapping, [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md), [BACKUP_AND_RECOVERY](../deployment/BACKUP_AND_RECOVERY.md) coverage.
- **Complexity.** Large.

**FF-07 · On-device and local models**
- **Concept.** Local inference for embedding, routine A0 agent work, and eventually a local twin mode.
- **Value.** Cost control (RISK-05), provider independence (RISK-06), and the only path to AI over P3 content without boundary violations (NFR-032 today simply excludes P3 from AI).
- **Trigger.** Local models matching the quality bar for specific task classes at acceptable hardware cost; measured API spend justifying the effort.
- **Spec impact.** [AI_ARCHITECTURE](../ai/AI_ARCHITECTURE.md) routing tiers; [SECURITY](../security/SECURITY.md) local-inference boundary analysis; possibly a revised P3 policy in [PRIVACY](../security/PRIVACY.md) (owner decision).
- **Complexity.** Large.

**FF-08 · Photo and video story generation**
- **Concept.** Curated narrative albums: the system assembles media, timeline context, and text into shareable stories.
- **Value.** Makes the archive emotionally legible to family and future generations, not just queryable.
- **Trigger.** Media corpus large enough (thousands of items) and FS-003/FS-015 mature.
- **Spec impact.** New feature spec; [UI_UX](../ui/UI_UX.md) story surfaces; publish gates from FS-010 reused.
- **Complexity.** Medium.

**FF-09 · "Ask my career" recruiter mode**
- **Concept.** A focused public twin preset for recruiters and partners: verified career facts, evidence-linked skills, availability posture.
- **Value.** Converts the portfolio from static pages into a differentiating interactive experience, with tier discipline as the trust story.
- **Trigger.** Public twin (TASK-503) live with clean disclosure and tier-discipline record; owner actively job-market-visible or partnership-seeking.
- **Spec impact.** [DIGITAL_TWIN](../ai/DIGITAL_TWIN.md) mode addition; portfolio UI preset.
- **Complexity.** Small.

**FF-10 · Integration expansion pack**
- **Concept.** Automated ingestion connectors: DEV.to articles (✅ presence, §9), LinkedIn archive imports, hackathon platform history (`hacker1401`, ✅), calendar and email opt-in capture.
- **Value.** Corpus completeness with less manual capture; several sources are already verified public footprints.
- **Trigger.** Per connector: stable FS-001 pipeline plus an owner request for that source. LinkedIn and email raise consent and terms-of-service questions to resolve first (note POPIA posture in [PRIVACY](../security/PRIVACY.md)).
- **Spec impact.** Connector sections in the ingestion domain; per-source provenance rules.
- **Complexity.** Small to Medium per connector.

**FF-11 · Memorial and heritage mode enhancements**
- **Concept.** Post-succession refinements: memorial portfolio layout, guided family tours of the corpus, anniversary reflections, generational handover of stewardship itself.
- **Value.** The platform's ultimate purpose, treated with the care it deserves rather than as an afterthought of succession mechanics.
- **Trigger.** FS-016 complete and drilled; design work should happen while the owner can direct it (deliberately not waiting for need).
- **Spec impact.** [DIGITAL_TWIN](../ai/DIGITAL_TWIN.md) post-mortem mode expansion; [UI_UX](../ui/UI_UX.md) memorial surface; [AUTHORIZATION](../security/AUTHORIZATION.md) generational stewardship.
- **Complexity.** Medium.

**FF-12 · Multilingual support**
- **Concept.** Corpus and interface support beyond English: ingestion, search, and twin answers across languages relevant to the owner's context and family.
- **Value.** Zimbabwe and South Africa are multilingual contexts; future generations may not read English-first.
- **Trigger.** Owner decision on which languages matter.
- > TODO(verify): which languages are relevant to the owner and family is not on record; no language list may be assumed.
- **Spec impact.** Ingestion language detection, embedding model choices in [AI_ARCHITECTURE](../ai/AI_ARCHITECTURE.md), [ACCESSIBILITY](../ui/ACCESSIBILITY.md) language markup, UI localization infrastructure.
- **Complexity.** Large.

### 4.2 Register operations

Candidates are reviewed at each phase gate alongside [RISKS](RISKS.md). A candidate whose trigger fires gets a proper feature specification (new FS ID) before any implementation; a candidate dead for two consecutive yearly reviews is marked Retired with rationale, never deleted.

## 5. Acceptance Criteria

- Every candidate has all five fields (concept, value, trigger, spec impact, complexity) and any needed TODO(verify) notes.
- No candidate ships without first becoming a real FS specification through the change process in [CONTRIBUTING](../CONTRIBUTING.md).
- Phase gate reviews record trigger evaluations for at least the candidates nearest their triggers.

## 6. Dependencies

- [ROADMAP](ROADMAP.md) phase gates as the review rhythm.
- Trigger measurements from [OBSERVABILITY](../deployment/OBSERVABILITY.md) (capture friction, spend, usage).
- Owner decisions for FF-03 and FF-12 TODOs.

## 7. Risks

- This register becoming a graveyard of guilt; mitigated by the Retired state and honest triggers.
- Premature promotion of exciting candidates (FF-02, FF-07) over boring durability work; the trigger discipline and RISK-10 review are the controls.

## 8. Future Enhancements

Not applicable in the usual sense: this document IS the future-enhancement register for the platform. Its own enhancement is process: better trigger instrumentation over time.

## 9. Examples

At the Phase 3 gate, review shows mobile-web capture losing roughly a third of intended captures (measured via abandoned capture modals and owner notes). FF-01's trigger has fired: a proper feature specification is drafted as FS-017, scoped, and scheduled into a phase, and this register marks FF-01 as Promoted with a link. FF-03, by contrast, has no family demand on record and stays untouched.

## 10. Open Questions

- Should FF-11 design work be pulled earlier precisely because it needs the owner's living direction? Leaning yes; raise at the Phase 4 gate.
- FF-07's P3-local-AI possibility implies a future owner decision about whether sealed content should ever meet any model, even local; deliberately unresolved.

## 11. References

- [`knowledge/MASTER_CONTEXT.md`](../knowledge/MASTER_CONTEXT.md) §5 (✅ Android skills anchoring FF-01), §6 and §11 (🟡 Linfy Tech ambitions anchoring FF-04), §8 (🟡 voice coursework anchoring FF-02), §9 (✅ DEV.to and hackathon footprints anchoring FF-10).

## 12. Related Specifications

- [ROADMAP](ROADMAP.md), [TASKS](TASKS.md), [RISKS](RISKS.md)
- [FEATURE_SPECIFICATIONS](../specs/FEATURE_SPECIFICATIONS.md) (the bar candidates must clear to graduate)
- [AI_ARCHITECTURE](../ai/AI_ARCHITECTURE.md), [DIGITAL_TWIN](../ai/DIGITAL_TWIN.md), [DESIGN_SYSTEM](../ui/DESIGN_SYSTEM.md)
