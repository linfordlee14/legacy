# PRODUCT_REQUIREMENTS
### Product requirements for Legacy, the lifelong AI digital legacy platform for Linford Musiyambodza

| Field | Value |
|-------|-------|
| Status | Draft |
| Owner | Linford Musiyambodza |
| Last updated | 2026-07-02 |
| Depends on | [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md), [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md) |

## 1. Purpose

This document defines what the Legacy product must do, expressed as stable product requirements (`PR-###`). It is the top of the traceability chain defined in [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md): every functional requirement in [FUNCTIONAL_REQUIREMENTS](./FUNCTIONAL_REQUIREMENTS.md) and every non-functional requirement in [NON_FUNCTIONAL_REQUIREMENTS](./NON_FUNCTIONAL_REQUIREMENTS.md) traces back to at least one requirement here, and feature specifications in [FEATURE_SPECIFICATIONS](./FEATURE_SPECIFICATIONS.md) implement them.

Legacy is a single-owner, production-grade platform that captures, organizes, verifies, and represents the life's work of one person over decades, and that can outlive its owner through a governed succession process. Requirements are grouped by the sixteen canonical features (F1 to F16) plus three cross-cutting groups: provenance, privacy, and longevity.

## 2. Goals

- Preserve every knowledge domain of the owner's life and work (see §4.1.2) in open, durable, exportable form.
- Make the corpus retrievable through search, timeline, graph navigation, and grounded question answering with citations.
- Represent the owner faithfully through a disclosed AI digital twin that never fabricates and never overstates unverified claims.
- Productize the confidence-tier discipline of [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md) §0 so that verification is a workflow, not a footnote.
- Publish a public portfolio (P0 surface) that is always accurate, always cited, and always under explicit owner control.
- Remain operable, affordable, and meaningful for a solo founder today and for successors after the owner's death.

## 3. Scope

**In scope**

- Product-level requirements for all sixteen canonical features F1 to F16.
- Cross-cutting product requirements for provenance, privacy, and longevity.
- The knowledge domain inventory that the product must be able to preserve.

**Out of scope**

- System composition and integrations: see [SYSTEM_REQUIREMENTS](./SYSTEM_REQUIREMENTS.md).
- Testable behavior-level detail: see [FUNCTIONAL_REQUIREMENTS](./FUNCTIONAL_REQUIREMENTS.md).
- Quality attributes and compliance targets: see [NON_FUNCTIONAL_REQUIREMENTS](./NON_FUNCTIONAL_REQUIREMENTS.md).
- Native mobile applications (deferred per the baseline decisions in [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md) §9).
- Multi-tenant or commercial SaaS operation: Legacy is designed for exactly one owner.

## 4. Requirements

### 4.1 Product context

#### 4.1.1 The owner

All personal facts below carry the confidence tiers of [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md) and must never be upgraded by this or any downstream document.

| Fact | Tier |
|------|------|
| Linford Musiyambodza, based in Strand, Cape Town, South Africa | ✅ |
| Founder and CEO of Linfy Tech Solutions; CTO of NeuroGrowth Labs | ✅ |
| Zimbabwean origin | 🟡 |
| Public tagline "Building in public. Building for Africa."; faith signature "El Roi" | ✅ |
| Primary code presence: GitHub `linfordlee14`; hackathon handle `hacker1401` | ✅ |
| Practices Specification-Driven Development (mission, roadmap, techstack files first) | 🟡 |
| Documented style guide: no em dashes, builder-narrative tone, faith-driven closings | 🟡 |

The owner lives in South Africa, which makes POPIA the primary privacy statute for the product (see [NON_FUNCTIONAL_REQUIREMENTS](./NON_FUNCTIONAL_REQUIREMENTS.md) and [../security/PRIVACY.md](../security/PRIVACY.md)).

#### 4.1.2 Knowledge domains to preserve

The product must be able to capture, organize, and retrieve every domain below. Default privacy tier follows [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md) §5 (new content defaults to P2; the owner promotes or seals explicitly). Entity names are the canonical entities of SPEC_CONVENTIONS §6.

| Knowledge domain | Primary features | Canonical entities | Default tier |
|------------------|------------------|--------------------|--------------|
| Biography and identity | F2, F5, F6, F10 | Person, Claim, Source | P2, curated subset P0 |
| Life and career timeline | F3, F10 | Event | P2, curated subset P0 |
| Projects (WildGuard AI, CyberBuddy, and all others) | F1, F13, F10 | Project, Artifact | P2, curated subset P0 |
| GitHub repositories and code | F1, F13 | Artifact (code snapshot) | P2 |
| Articles and technical writing (DEV.to and others) | F1, F15, F10 | Article, Source | P0 when already public |
| Talks (for example GDG Cape Town Pet Projects 2026) | F1, F10 | Talk, Event | P0 when already public |
| Research notes and findings | F1, F13 | Note, Source | P2 |
| Hackathons and competitions | F3, F13 | Event, Achievement | P2, curated subset P0 |
| Certifications and education | F2, F14 | Certification | P2, curated subset P0 |
| Skills and expertise | F2, F14 | Skill | P2, curated subset P0 |
| Companies and roles | F2, F3 | Organization, Claim | P2, curated subset P0 |
| Leadership and community roles | F2, F9 | Organization, Claim | P2 |
| Ideas and concepts | F1, F13 | Idea | P2 |
| Design decisions and rationale | F1, F13 | Note, Artifact | P2 |
| AI conversations | F1, F7 | Conversation | P2 |
| Source documents | F1, F9 | Artifact, Source | P2 |
| Photos | F1, F3 | Artifact (photo) | P2 |
| Videos | F1, F3 | Artifact (video) | P2 |
| Presentations | F1, F15 | Artifact (presentation) | P2 |
| Architecture documents and specifications | F1, F13 | Artifact | P2 |
| Personal notes | F1, F11 | Note | P2 |
| Journal entries | F12 | JournalEntry | P2 or P3 |
| Prayer reflections | F12 | JournalEntry | P3 |
| Goals and roadmaps | F14, F11 | Goal | P2 |
| Lessons learned and failures | F7, F12, F14 | Lesson | P2 |
| Books and reading history | F2, F14 | Book | P2 |
| Learning history | F3, F14 | Event, Certification | P2 |
| Networking, mentors, collaborators | F2 | Person, Edge | P2, POPIA duties apply |
| Achievements and recognition | F9, F10 | Achievement, Claim | P0 only when verified |
| Future plans | F11, F14 | Goal, Note | P2 |

### 4.2 Requirement conventions

Every requirement below has a stable ID (never renumbered), a MoSCoW priority (Must, Should, Could, Won't-for-v1), a one-line rationale, and a feature mapping. "The product" is the subject of every statement. Requirement text uses MUST and SHOULD in the RFC 2119 sense.

### 4.3 F1 Capture and Ingestion

| ID | Feature | Priority | Requirement | Rationale |
|----|---------|----------|-------------|-----------|
| PR-001 | F1 | Must | The product MUST ingest documents, photos, videos, presentations, code repositories, AI conversations, notes, and voice recordings through a unified capture surface. | Every knowledge domain in §4.1.2 arrives in one of these formats. |
| PR-002 | F1 | Must | Every ingested item MUST be stamped at capture time with source, capture method, timestamp, and initial privacy tier (default P2). | Provenance is unusable if reconstructed after the fact. |
| PR-003 | F1 | Should | The product SHOULD make everyday capture (a note, a photo, a link) possible in under one minute of owner effort. | A lifelong archive only works if capture friction is near zero. |
| PR-004 | F1 | Should | The product SHOULD detect and flag near-duplicate content at ingestion rather than silently storing copies. | Decades of capture will otherwise degrade retrieval quality. |

### 4.4 F2 Knowledge Graph and Entity Linking

| ID | Feature | Priority | Requirement | Rationale |
|----|---------|----------|-------------|-----------|
| PR-005 | F2 | Must | The product MUST link ingested content to canonical entities (Person, Organization, Project, Skill, Event, and the rest of SPEC_CONVENTIONS §6) with typed relationships. | Retrieval and the twin need structure, not a document pile. |
| PR-006 | F2 | Must | The product MUST support owner curation of the graph: merging duplicate entities, correcting links, and mapping aliases (for example the "Linford Lee" alias flagged 🟡 in MASTER_CONTEXT §1). | Automated extraction will be wrong sometimes; the owner is the editor of record. |
| PR-007 | F2 | Should | The product SHOULD let users navigate relationships in both directions (project to collaborators to talks to articles). | Associative browsing is how a legacy is explored by others. |

### 4.5 F3 Timeline Engine

| ID | Feature | Priority | Requirement | Rationale |
|----|---------|----------|-------------|-----------|
| PR-008 | F3 | Must | The product MUST build a chronological timeline of the owner's life and work from ingested content, with owner curation on top of automatic extraction. | The timeline is the narrative spine of the legacy. |
| PR-009 | F3 | Should | The product SHOULD represent date uncertainty explicitly (year-only, approximate, disputed) instead of forcing false precision. | Biographical sources rarely carry exact dates. |

### 4.6 F4 Search

| ID | Feature | Priority | Requirement | Rationale |
|----|---------|----------|-------------|-----------|
| PR-010 | F4 | Must | The product MUST answer natural-language search queries across all content the requesting user is permitted to see, and no other content. | Search is the primary retrieval path and the primary leak risk. |
| PR-011 | F4 | Should | The product SHOULD combine semantic and keyword retrieval with filters for entity, time range, content type, and privacy tier. | Neither pure vector nor pure keyword search is sufficient alone. |

### 4.7 F5 RAG Question Answering

| ID | Feature | Priority | Requirement | Rationale |
|----|---------|----------|-------------|-----------|
| PR-012 | F5 | Must | Every factual answer the product generates MUST carry citations to specific owned Sources or Claims. | An uncited answer about a person's legacy is a liability, not a feature. |
| PR-013 | F5 | Must | Answers MUST be tier-aware: 🟡 and 🔴 claims are attributed ("Linford states that...") or flagged, never presented as established fact. | Direct productization of the MASTER_CONTEXT §0 rule for downstream AI. |
| PR-014 | F5 | Must | When the corpus lacks sufficient evidence, the product MUST say so rather than extrapolate. | Fabrication in a legacy system is unrecoverable reputational damage. |

### 4.8 F6 AI Digital Twin

| ID | Feature | Priority | Requirement | Rationale |
|----|---------|----------|-------------|-----------|
| PR-015 | F6 | Must | The product MUST provide a digital twin that answers as a representation of the owner, grounded exclusively in the corpus and its Claims. | The twin is the interactive form of the legacy. |
| PR-016 | F6 | Must | The twin MUST always disclose that it is an AI representation and MUST never present itself as the living owner. | Non-negotiable honesty requirement; also protects the owner's reputation. |
| PR-017 | F6 | Should | The twin SHOULD reproduce the owner's documented voice and style (🟡 self-reported style guide in MASTER_CONTEXT §2), calibrated from P0 and P2 writing samples. | Fidelity of voice is what makes the twin feel like a legacy rather than a chatbot. |

### 4.9 F7 Long-Term Memory Engine

| ID | Feature | Priority | Requirement | Rationale |
|----|---------|----------|-------------|-----------|
| PR-018 | F7 | Must | The product MUST maintain persistent long-term memory across sessions using the canonical memory types (episodic, semantic, procedural, reflective) of [MEMORY_SYSTEM](../memory/MEMORY_SYSTEM.md). | Without durable memory the assistant restarts from zero every session. |
| PR-019 | F7 | Must | The owner MUST be able to inspect, correct, and permanently delete individual memories, with deletion propagating to all derived stores. | Memory the owner cannot govern is a privacy defect. |
| PR-020 | F7 | Should | The product SHOULD periodically consolidate raw memories into higher-level reflective summaries without discarding the originals. | Decades of raw memory becomes noise without consolidation. |

### 4.10 F8 Multi-Agent Orchestration

| ID | Feature | Priority | Requirement | Rationale |
|----|---------|----------|-------------|-----------|
| PR-021 | F8 | Must | The product MUST route all AI work through the canonical twelve-agent roster of SPEC_CONVENTIONS §7, entered via the Orchestrator Agent. | One roster, one entry point: prevents ad hoc agent sprawl over the years. |
| PR-022 | F8 | Must | Consequential agent actions (publishing, deletion, tier changes, external communication) MUST require explicit human approval before execution. | Human-in-the-loop is the safety boundary of an autonomous system. |
| PR-023 | F8 | Should | Every agent run SHOULD be logged with inputs, tools used, cost, and outputs, reviewable by the owner. | Trust in agents is built on auditability. |

### 4.11 F9 Verification and Citation Engine

| ID | Feature | Priority | Requirement | Rationale |
|----|---------|----------|-------------|-----------|
| PR-024 | F9 | Must | Every atomic biographical statement MUST be stored as a Claim with a confidence tier (verified, self_reported, flagged) linked to Source records. | The Claim model of SPEC_CONVENTIONS §6 is the provenance backbone. |
| PR-025 | F9 | Must | The product MUST provide a manual verification queue that turns MASTER_CONTEXT §12 (known gaps and verification items) into a tracked workflow with evidence attached to each resolution. | The verification queue already exists on paper; the product must operationalize it. |
| PR-026 | F9 | Must | Tier transitions (for example 🔴 to ✅) MUST require attached evidence and MUST be audited; no automatic upgrades. | Preserves the "never upgrade without new evidence" rule of MASTER_CONTEXT §0. |

### 4.12 F10 Public Portfolio

| ID | Feature | Priority | Requirement | Rationale |
|----|---------|----------|-------------|-----------|
| PR-027 | F10 | Must | The product MUST publish a public portfolio site that renders P0 content only, with server-side enforcement. | The P0 surface is the owner's public face; leakage is unacceptable. |
| PR-028 | F10 | Must | Publishing to P0 MUST require an explicit owner approval step, and 🔴 flagged claims MUST NOT appear on the public surface as fact. | Publishing is a consequential action under PR-022 and a verification gate under PR-024. |
| PR-029 | F10 | Should | The portfolio SHOULD present projects, articles, talks, achievements, certifications, and a public timeline with visible confidence and citation affordances. | These are the domains in §4.1.2 with public value. |

### 4.13 F11 Private Workspace

| ID | Feature | Priority | Requirement | Rationale |
|----|---------|----------|-------------|-----------|
| PR-030 | F11 | Must | The product MUST provide an authenticated private workspace where the owner can access, search, and manage the full corpus at tiers P0 to P2, with P3 access under its unlock rules. | The workspace is the owner's daily operating surface. |
| PR-031 | F11 | Should | The workspace SHOULD support granting trusted users (P1) scoped, revocable access to selected collections. | Mentees, collaborators, and family need partial views without full exposure. |

### 4.14 F12 Journals and Reflections

| ID | Feature | Priority | Requirement | Rationale |
|----|---------|----------|-------------|-----------|
| PR-032 | F12 | Must | The product MUST support journal entries and prayer reflections with P3 sealing: time locks or succession gates chosen by the owner at write time. | Faith practice is central to the owner's identity (✅ MASTER_CONTEXT §2) and demands the strongest privacy. |
| PR-033 | F12 | Must | Sealed P3 content MUST be excluded from search, RAG, twin grounding, memory, and exports until its unlock condition is met. | A seal that leaks through a side channel is not a seal. |
| PR-034 | F12 | Could | The product COULD offer reflection prompts (weekly review, lessons learned) that feed the reflective memory type. | Turns journaling into structured legacy input, but is not launch-critical. |

### 4.15 F13 Project and Research Explorer

| ID | Feature | Priority | Requirement | Rationale |
|----|---------|----------|-------------|-----------|
| PR-035 | F13 | Should | The product SHOULD aggregate everything about a Project (repositories, documents, decisions, events, collaborators, outcomes) into a single explorable view. | Projects are the strongest evidence of skill per MASTER_CONTEXT §5. |
| PR-036 | F13 | Should | The explorer SHOULD distinguish verified public projects from self-reported or in-development ones, mirroring the two tables of MASTER_CONTEXT §6. | Prevents concept-stage work being presented as shipped. |

### 4.16 F14 Mentor and Career Advisor

| ID | Feature | Priority | Requirement | Rationale |
|----|---------|----------|-------------|-----------|
| PR-037 | F14 | Should | The product SHOULD provide a mentor advisor grounded in the owner's goals, skills, certifications, learning history, and lessons learned. | Converts the archive into forward-looking value for the owner. |
| PR-038 | F14 | Could | The mentor COULD produce periodic progress reviews against stated goals and roadmaps. | Useful cadence, but dependent on mature goal data. |

### 4.17 F15 Writing and Presentation Assistant

| ID | Feature | Priority | Requirement | Rationale |
|----|---------|----------|-------------|-----------|
| PR-039 | F15 | Should | The product SHOULD draft articles, talks, and presentations grounded in the corpus, with citations and in the owner's documented style. | Extends the build-in-public practice (✅ MASTER_CONTEXT §2) with grounded drafting. |
| PR-040 | F15 | Must | All generated drafts MUST be marked as AI-assisted and MUST require owner approval before any publication path. | Applies PR-022 to content creation; the owner's byline is his own. |

### 4.18 F16 Legacy Vault Export and Succession

| ID | Feature | Priority | Requirement | Rationale |
|----|---------|----------|-------------|-----------|
| PR-041 | F16 | Must | The product MUST produce a versioned, offline-readable Legacy Vault export (Markdown, JSON, media manifest) of all content the export policy includes. | The vault is the guarantee that the legacy outlives any vendor or system. |
| PR-042 | F16 | Must | The product MUST support a succession plan: named successors, activation conditions, and tier-aware release rules including P3 unlock. | A digital legacy without succession dies with its infrastructure. |
| PR-043 | F16 | Should | Vault generation SHOULD run on a schedule with integrity verification, not only on demand. | An export nobody remembered to run protects nothing. |

### 4.19 Cross-cutting: provenance

| ID | Feature | Priority | Requirement | Rationale |
|----|---------|----------|-------------|-----------|
| PR-044 | F1, F9 | Must | Every stored item MUST retain full provenance: original source, capture method, and every transformation applied (OCR, transcription, summarization). | Downstream trust decisions require knowing how content came to exist. |
| PR-045 | All | Must | AI-generated or AI-transformed content MUST be distinguishable from owner-authored content on every surface. | Conflating the two corrupts the historical record. |

### 4.20 Cross-cutting: privacy

| ID | Feature | Priority | Requirement | Rationale |
|----|---------|----------|-------------|-----------|
| PR-046 | All | Must | Every item MUST carry exactly one privacy tier (P0 to P3 of SPEC_CONVENTIONS §5), defaulting to P2, enforced identically across search, RAG, twin, graph, timeline, memory, API, and export. | One tier model, zero exceptions, or the model is decorative. |
| PR-047 | All | Must | No content moves to a less restrictive tier without an explicit, audited owner action. | Restates the SPEC_CONVENTIONS §5 invariant as a product commitment. |
| PR-048 | F2, F10 | Must | Personal information about third parties (collaborators, mentors, network contacts in MASTER_CONTEXT §10) MUST be handled under POPIA obligations, including minimization on public surfaces and removal on request. | The owner is in South Africa and the graph contains other people's data. |

### 4.21 Cross-cutting: longevity

| ID | Feature | Priority | Requirement | Rationale |
|----|---------|----------|-------------|-----------|
| PR-049 | All | Must | All content MUST be stored in or exportable to open, documented formats; no capability of the product may depend on a format that cannot be read outside it. | Decades-scale survival requires format independence. |
| PR-050 | All | Must | The complete corpus MUST be exportable by the owner at any time without vendor assistance. | Vendor exit is a product feature, not an operations task. |
| PR-051 | F16 | Should | The product SHOULD define and follow a format and model migration policy so that embeddings, media, and documents can be re-processed as technology changes. | Ten-year-old embeddings and codecs will need migration, planned or panicked. |

## 5. Acceptance criteria

1. Every PR above appears in the traceability index of [FUNCTIONAL_REQUIREMENTS](./FUNCTIONAL_REQUIREMENTS.md) or [NON_FUNCTIONAL_REQUIREMENTS](./NON_FUNCTIONAL_REQUIREMENTS.md) with at least one downstream requirement, or is explicitly marked deferred.
2. For each knowledge domain in §4.1.2, at least one ingestion path (PR-001) and one retrieval path (PR-010 or PR-012) exists in the functional requirements.
3. A sample audit of any 20 stored items shows 100 percent carry provenance metadata (PR-002, PR-044) and exactly one privacy tier (PR-046).
4. A red-team style review of the public portfolio finds zero P1, P2, or P3 content and zero 🔴 claims stated as fact (PR-027, PR-028).
5. Ten sampled RAG answers each carry at least one citation, and any answer touching a 🟡 or 🔴 claim uses attribution language (PR-012, PR-013).
6. The twin, when asked "are you Linford?", discloses its AI nature in 10 out of 10 trials (PR-016).
7. A generated Legacy Vault opens and is navigable on a machine with no network access and no proprietary software (PR-041).
8. A simulated succession activation releases exactly the content the succession plan permits, including correct P3 handling (PR-042, PR-033).

## 6. Dependencies

- [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md): all biographical facts, tiers, and the §12 verification queue seeded into PR-025.
- [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md): ID schemes, privacy tiers, canonical entities, agent roster, baseline architecture defaults.
- [SYSTEM_REQUIREMENTS](./SYSTEM_REQUIREMENTS.md): the system composition that hosts these capabilities.
- The owner persona and audience personas defined in [USER_PERSONAS](./USER_PERSONAS.md) motivate the priority assignments here.
- Vision-level intent in [../docs/VISION.md](../docs/VISION.md) and [../docs/LEGACY_PRINCIPLES.md](../docs/LEGACY_PRINCIPLES.md).

## 7. Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Scope is lifelong; v1 tries to build all sixteen features at once | Nothing ships | MoSCoW discipline: Musts define v1, Shoulds sequence via [../roadmap/ROADMAP.md](../roadmap/ROADMAP.md) |
| Twin misrepresents unverified claims as fact | Reputational harm to the owner | PR-013, PR-016, PR-026 plus the verification workflow in F9 |
| P3 journal or prayer content leaks through a derived store (memory, embeddings, vault) | Deep personal harm, loss of trust in the product | PR-033 and PR-046 enforced at every derived surface; tested by acceptance criterion 8 |
| Capture friction too high; the archive silently starves | Product becomes a museum of one import | PR-003, ingestion breadth in PR-001 |
| Solo-founder cost of always-on AI features | Product abandoned for cost reasons | Cost ceilings in [NON_FUNCTIONAL_REQUIREMENTS](./NON_FUNCTIONAL_REQUIREMENTS.md); budget controls in PR-021 orchestration |
| Third-party personal data on public surfaces | POPIA exposure | PR-048 and privacy requirements in [../security/PRIVACY.md](../security/PRIVACY.md) |

## 8. Future enhancements

- Native Android application (Kotlin, Jetpack Compose) as anticipated by SPEC_CONVENTIONS §9.
- Multi-language surfaces (the owner's Africa-focused mission suggests future localization; labeled a design idea, not a stated owner requirement).
- Family and mentee co-archives: P1 users contributing their own memories about shared events.
- Voice interface for the twin, building on the voice ingestion pipeline of F1.
- Automated public-web monitoring that proposes new Claims and Sources to the verification queue.

## 9. Examples

**Example 1: tier-aware answer (PR-012, PR-013).** Question on the private workspace: "Did SpazaLink win anything at SA Startup Week 2026?" Acceptable answer: "Linford reports that SpazaLink placed 3rd at SA Startup Week 2026 at Makers Landing. This claim is currently flagged 🔴 (unverified) in the verification queue. [Claim ref, Source ref]". Unacceptable answer: "Yes, SpazaLink won 3rd place."

**Example 2: publishing gate (PR-027, PR-028).** The Writing Agent drafts a portfolio page for RhinoGuardians including "accepted into HBS Foundry". The Verification Agent blocks publication because that acceptance is 🔴 in MASTER_CONTEXT §7; the page publishes only after the claim is verified or the sentence is rewritten as attributed.

**Example 3: requirement trace record (illustrative JSON).**

```json
{
  "id": "PR-013",
  "feature": "F5",
  "priority": "Must",
  "downstream": ["FR-RAG-*", "FR-VER-*", "NFR explainability group"],
  "verified_by": ["acceptance-criterion-5"]
}
```

## 10. Open questions

> TODO(verify): Which knowledge domains already have digital source material ready to import (existing archives, drive folders, exports), and which must be captured from scratch? Owner inventory needed.

> TODO(verify): Who are the intended P1 trusted users at launch (family, Dean Silaule, mentees)? Names in MASTER_CONTEXT §10 are 🟡 and consent is required before onboarding anyone.

> TODO(verify): The owner's intended succession designees and activation conditions for PR-042 are unknown and must come from the owner directly.

> TODO(verify): Should already-public content (DEV.to articles, GDG talk) default to P0 on import, or still require explicit approval? Current text of PR-028 assumes explicit approval in all cases.

## 11. References

- [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md) §0 (tiers), §2 (values), §6 (projects), §7 (achievements), §12 (verification queue).
- [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md) §4 (IDs), §5 (privacy tiers), §6 (entities), §7 (agents), §9 (baseline decisions).
- RFC 2119 key words (MUST, SHOULD) as interpreted in §4.2.

## 12. Related specifications

- [SYSTEM_REQUIREMENTS](./SYSTEM_REQUIREMENTS.md), [FUNCTIONAL_REQUIREMENTS](./FUNCTIONAL_REQUIREMENTS.md), [NON_FUNCTIONAL_REQUIREMENTS](./NON_FUNCTIONAL_REQUIREMENTS.md): the sibling requirement sets.
- [USER_PERSONAS](./USER_PERSONAS.md), [USER_STORIES](./USER_STORIES.md), [USE_CASES](./USE_CASES.md): who needs these requirements and why.
- [FEATURE_SPECIFICATIONS](./FEATURE_SPECIFICATIONS.md): feature-level elaboration of F1 to F16.
- [../architecture/MASTER_ARCHITECTURE.md](../architecture/MASTER_ARCHITECTURE.md), [../ai/RAG_PIPELINE.md](../ai/RAG_PIPELINE.md), [../ai/DIGITAL_TWIN.md](../ai/DIGITAL_TWIN.md), [../agents/MULTI_AGENT_ARCHITECTURE.md](../agents/MULTI_AGENT_ARCHITECTURE.md), [../memory/MEMORY_SYSTEM.md](../memory/MEMORY_SYSTEM.md), [../security/PRIVACY.md](../security/PRIVACY.md).
