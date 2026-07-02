# LEGACY_PRINCIPLES
### Binding design principles for every specification and every future implementation of Legacy

| Field | Value |
|-------|-------|
| Status | Draft |
| Owner | Linford Musiyambodza |
| Last updated | 2026-07-02 |
| Depends on | [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md), [SPEC_CONVENTIONS](./SPEC_CONVENTIONS.md), [VISION](./VISION.md), [MISSION](./MISSION.md) |

---

## 1. Purpose

This document defines the seventeen design principles that bind all Legacy specifications and any eventual implementation. Each principle carries a definition (what it means here, precisely), design implications (what specs and systems must do because of it), and acceptance signals (observable evidence that the principle is being honored). Principles are cited by name, for example "the Provenance First principle"; no separate identifier scheme is introduced for them.

## 2. Goals

- Give contributors and future AI sessions a decision framework that resolves design questions consistently without re-litigating philosophy in every spec.
- Make principle compliance checkable: every principle has acceptance signals a reviewer can test against a spec or a build.
- Encode the two platform-specific obligations that generic engineering principles miss: provenance discipline and faith-respectful handling of the owner's spiritual life.

## 3. Scope

**In scope:** the seventeen principles, their precedence when they conflict, and how compliance is assessed.

**Out of scope:** concrete requirements (owned by `specs/`), architecture decisions implementing the principles (owned by `architecture/MASTER_ARCHITECTURE.md` as ADRs), and operational procedures (owned by `deployment/`).

## 4. Requirements

The principles below are normative. Fifteen are general engineering principles adapted to Legacy; the final two (Provenance First, Faith-Respectful Stewardship) are platform-specific and grounded directly in [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md).

### 4.1 Specification Driven

**Definition.** The system is defined by written specifications before and above any implementation; this repository is the product's source of truth. This mirrors the owner's own self-reported SDD practice (🟡 per MASTER_CONTEXT §2), adopted here as a binding design decision.

**Design implications.**
- No capability exists officially until a spec describes it; implementations follow specs, never the reverse.
- Changes flow spec-first: update the spec, then the build. Divergence discovered in a build is a defect in one of the two.
- Specs follow [SPEC_CONVENTIONS](./SPEC_CONVENTIONS.md) exactly: 12 sections, title block, stable IDs, traceability chain.

**Acceptance signals.**
- Every implemented feature traces to requirement IDs; every requirement traces forward to feature specs and tasks.
- Repository review (per [CONTRIBUTING](../CONTRIBUTING.md)) finds no undocumented behavior.

### 4.2 Modular

**Definition.** The system decomposes into components with narrow, explicit contracts (ingestion, graph, memory, retrieval, agents, surfaces) that can be built, replaced, or reasoned about independently.

**Design implications.**
- The sixteen identities in [VISION](./VISION.md) share one substrate but are separable at module boundaries; no identity reaches into another's internals.
- Agents communicate through the Orchestrator Agent's defined delegation contract, not through shared hidden state.
- Each `specs/` and domain directory owns its module's contract; cross-module assumptions are stated as Dependencies.

**Acceptance signals.**
- A module (for example the Timeline Engine) can be re-specified without editing more than its own spec plus declared dependents.
- No spec references another module's internal mechanics, only its published contract.

### 4.3 Future Proof

**Definition.** Legacy is designed for a lifetime-plus-generations horizon: it must survive vendor deaths, model deprecations, format churn, and decades of neglect between maintenance episodes.

**Design implications.**
- Open, documented formats for all exports (Markdown, JSON, standard media); the Legacy Vault export of SPEC_CONVENTIONS §9 is mandatory, not optional.
- Vendor-specific services (Supabase, LLM providers) sit behind abstractions with documented replacement paths.
- The spec repository itself is preservation-grade: plain Markdown, no tooling required to read it.

**Acceptance signals.**
- A rebuild-from-scratch narrative exists and is periodically reviewed (see `deployment/BACKUP_AND_RECOVERY.md`).
- No capability depends irreplaceably on a single vendor's proprietary feature.

### 4.4 Production Ready

**Definition.** Legacy is specified as a production system for daily lifelong use, not a demo: reliability, error handling, migrations, and operations are first-class spec content.

**Design implications.**
- Every functional spec addresses failure modes, not only happy paths.
- Observability, backup, and recovery are specified in `deployment/` with the same rigor as features.
- Non-functional requirements (latency, durability, availability) are explicit in `specs/NON_FUNCTIONAL_REQUIREMENTS.md`.

**Acceptance signals.**
- Acceptance criteria in feature specs include failure-path behavior.
- The testing specs (`testing/`) cover degradation and recovery scenarios, not only functional correctness.

### 4.5 Secure by Default

**Definition.** Every surface, endpoint, and store starts in its most restrictive posture; access is opened deliberately, never assumed.

**Design implications.**
- Deny-by-default authorization; all access decisions consult role, grant, and per-item privacy tier (see the `security/` specs).
- Encryption in transit and at rest is baseline; secrets management and audit logging are specified from day one.
- Agents run with least privilege: each agent gets only the tools and tiers its role requires.

**Acceptance signals.**
- No spec describes an unauthenticated write path or a default-open read path beyond P0 content.
- Every privileged action lands in the `AuditLogEntry` record with actor, time, and justification.

### 4.6 Privacy First

**Definition.** The owner's data belongs to the owner. Exposure is a deliberate, reversible-where-possible act; the system never widens an audience on its own.

**Design implications.**
- Every content item carries exactly one tier, P0 to P3; new content defaults to P2 (SPEC_CONVENTIONS §5).
- Tier transitions toward broader audiences require explicit owner action and are audit-logged; automated processes may only narrow exposure.
- Private tiers are excluded from any external model training or third-party analytics.

**Acceptance signals.**
- Zero incidents of automatic exposure widening across audits.
- Every retrieval and rendering path in the specs filters by tier before ranking or display.

### 4.7 Offline Capable where possible

**Definition.** Core reading and reference of the owner's corpus must survive loss of connectivity and loss of cloud vendors; capabilities degrade gracefully rather than disappearing.

**Design implications.**
- The Legacy Vault export provides local, read-only access to the corpus in open formats.
- Specs distinguish connectivity-dependent capabilities (LLM reasoning, live search) from those that must work offline (reading, browsing exports, timeline review).
- The qualifier "where possible" is honest: agentic AI features may require hosted models; the specs must say which ones do.

**Acceptance signals.**
- A current Vault export opens and reads on a disconnected machine.
- Each feature spec states its offline behavior explicitly.

### 4.8 AI Native

**Definition.** AI is the operating layer of Legacy, not a bolt-on: ingestion, curation, retrieval, reflection, and expression are agent-mediated by design.

**Design implications.**
- The twelve-agent roster of SPEC_CONVENTIONS §7 is the canonical decomposition of AI responsibility; new AI behavior lands in an existing agent or via a specified roster change.
- Data structures are designed for machine consumption first (chunking, embeddings, typed edges), with human views built on top.
- Model routing across providers (Claude primary, Gemini and Groq behind an abstraction, per SPEC_CONVENTIONS §9) keeps AI capability portable.

**Acceptance signals.**
- Every agent behavior is specified in `agents/MULTI_AGENT_ARCHITECTURE.md` with inputs, outputs, tools, and tier scope.
- No feature spec treats AI output as unreviewable magic: prompts, context assembly, and failure handling are specified.

### 4.9 API First

**Definition.** Every capability is exposed through a documented API before any UI consumes it; UIs are clients, never privileged backdoors.

**Design implications.**
- The resource model and endpoint semantics live in `api/API_SPECIFICATION.md`; UI specs may not assume undocumented endpoints.
- REST JSON under `/v1` with SSE for AI streaming is the baseline style (SPEC_CONVENTIONS §9).
- Agents consume the same APIs (or explicitly specified internal contracts), keeping behavior testable.

**Acceptance signals.**
- For every UI feature in `ui/`, the backing API surface is identifiable in the API spec.
- External automation (for example the owner's own scripts) can accomplish anything the UI can, subject to auth and tiers.

### 4.10 Searchable

**Definition.** Everything stored is findable through semantic, keyword, hybrid, graph, and timeline access paths, within the querying identity's tier scope.

**Design implications.**
- Ingestion always produces search artifacts: chunks, embeddings (`EmbeddingChunk`), entity links, and timeline placements.
- Natural-language querying is a first-class interface specified in the FR-SRCH group of `specs/FUNCTIONAL_REQUIREMENTS.md`.
- Nothing is stored in an opaque blob without extracted, indexable metadata; media gets transcripts or descriptions where feasible.

**Acceptance signals.**
- Randomly sampled stored items are reachable by at least two access paths (for example search plus graph).
- Search results respect tier filtering in every specified path.

### 4.11 Version Controlled

**Definition.** The specifications, the knowledge corpus, and the system's own configuration all have history: prior states are recoverable and changes are attributable.

**Design implications.**
- This repository lives in Git with the branch and commit discipline of [CONTRIBUTING](../CONTRIBUTING.md); [CHANGELOG](../CHANGELOG.md) tracks released spec versions.
- Content entities carry revision history in the data model (see `database/DATABASE_SCHEMA.md`); destructive edits are soft by default.
- IDs are never renumbered; deprecation preserves history (SPEC_CONVENTIONS §4).

**Acceptance signals.**
- Any spec statement can be traced to the commit and rationale that introduced it.
- A content item's prior versions are retrievable through the specified API.

### 4.12 Maintainable

**Definition.** A future maintainer (human or AI) with no prior context can understand, modify, and extend the system using only this repository and its conventions.

**Design implications.**
- Consistent structure everywhere: the 12 mandatory sections, canonical vocabulary, one style guide.
- Every non-obvious decision is recorded as an ADR with context and consequences; tribal knowledge is a defect.
- Specs stay within a readable size and split when they outgrow it, with cross-references rather than duplication.

**Acceptance signals.**
- A cold-start reader can locate the authoritative definition of any concept within the repository map in SPEC_CONVENTIONS §10.
- Reviews find duplication and contradiction rates trending to zero.

### 4.13 Scalable

**Definition.** The design holds as the corpus grows from hundreds to millions of items over decades, and as agent workloads grow, without architectural rewrites.

**Design implications.**
- Data model and retrieval specs state expected growth envelopes and their scaling strategy (indexing, partitioning, archival tiers).
- Costful operations (embedding, LLM calls) are budgeted and batchable; the Orchestrator Agent enforces budget control.
- Scale targets are lifetime-realistic, specified in `specs/NON_FUNCTIONAL_REQUIREMENTS.md`, and revisited at roadmap milestones.

**Acceptance signals.**
- No spec assumes whole-corpus scans or unbounded context windows for routine operations.
- Performance NFRs hold in testing at the specified multi-year corpus envelope.

### 4.14 Explainable

**Definition.** The system can always answer "why": why this search result, why this claim, why this agent action, why this tier decision.

**Design implications.**
- AI answers cite their sources and expose retrieval provenance; the Citation Engine behavior is specified in the FR-VER group.
- Agent runs are recorded (`AgentRun`) with plan, tools invoked, and outputs, reviewable by the owner.
- Ranking, deduplication, and consolidation behaviors are specified deterministically enough to be explained, not just observed.

**Acceptance signals.**
- Every biographical answer surface shows citations and tiers.
- The owner can reconstruct any agent decision from the audit and run records alone.

### 4.15 Accessible

**Definition.** Legacy's human surfaces are usable by people of varying abilities, devices, and bandwidth realities, including the low-bandwidth contexts of its South African and Zimbabwean audiences.

**Design implications.**
- `ui/ACCESSIBILITY.md` specifies the conformance target (WCAG-aligned) and it applies to the public portfolio as strictly as to the private workspace.
- Keyboard operability, screen-reader semantics, contrast, and reduced-motion behavior are specified per surface in `ui/`.
- Performance budgets treat low-bandwidth, mobile-first access as a primary case, not an edge case.

**Acceptance signals.**
- Accessibility acceptance criteria appear in UI feature specs, and testing specs include assistive-technology passes.
- The public portfolio remains readable and navigable on constrained connections per the UI performance budgets.

### 4.16 Provenance First (platform-specific)

**Definition.** Confidence tiers are first-class data, not documentation garnish. Every factual claim about Linford's life and work is a `Claim` carrying ✅ Verified, 🟡 Self-reported, or 🔴 Flagged, linked to `Source` records. Per MASTER_CONTEXT §0, a 🟡 or 🔴 claim is never upgraded to stated fact without new evidence, by any human, agent, or model, at any layer.

**Design implications.**
- The data model makes tier a required attribute of `Claim`; ingestion assigns it, the Verification Agent alone changes it, and every change is audit-logged with the evidence.
- Every generation surface (twin, mentor, writing, portfolio) renders attribution language for 🟡 ("Linford reports that...") and explicit unverified framing for 🔴.
- Tier information survives every transformation: chunking, embedding, summarization, consolidation, and export all carry it forward.
- Spec text obeys the same rule: repository authors preserve tiers when restating MASTER_CONTEXT content and use `> TODO(verify): ...` for gaps.

**Acceptance signals.**
- Zero occurrences, in specs or system output, of a 🟡/🔴 claim presented as established fact.
- Tier-change audit history exists for every `Claim` whose tier ever changed, each with attached evidence.
- The 🔴 queue from MASTER_CONTEXT §12 is tracked in the system and shrinks only through evidence, never through drift.

### 4.17 Faith-Respectful Stewardship (platform-specific)

**Definition.** Linford's faith identity is documented and real: he closes public posts with "El Roi" (✅ per MASTER_CONTEXT §1) and frames his work as faith-driven service (✅ per §2). Legacy treats this dimension of the corpus, especially devotional content such as prayer reflections, as sacred trust: represented faithfully, never performed artificially, and protected by default. Prayer reflections and similar devotional entries default to P2 and are P3-capable (sealable with time locks or succession conditions).

**Design implications.**
- The data model recognizes devotional content (for example `JournalEntry` items flagged as prayer reflections) so tier defaults and sealing rules can attach to it specifically.
- The Twin Agent reflects the owner's documented faith voice (including the "El Roi" signature where the owner uses it) only in contexts the owner has approved, and never generates novel theological claims or prayers in his name.
- Curation, consolidation, and reflection processes may organize devotional content but never rewrite its wording.
- Succession and sealing rules give faith content explicit handling: the owner decides what family sees, when, and whether anything is released publicly at all.

**Acceptance signals.**
- All prayer-reflection content in the system sits at P2 or P3; none reaches P0/P1 without an explicit, logged owner action.
- Twin honesty reviews include a faith-content pass: no fabricated devotional voice, no unapproved "El Roi" usage.
- Sealed devotional items honor their unlock conditions exactly in succession tests.

### 4.18 Precedence when principles conflict

Conflicts are resolved in this order (a design decision): (1) Provenance First and Privacy First together outrank all others, with Faith-Respectful Stewardship governing any case touching faith content; (2) Secure by Default outranks convenience-oriented principles (Searchable, AI Native, API First); (3) Future Proof outranks short-term optimization under Scalable or Production Ready. A conflict a spec cannot resolve with this ordering is recorded in its Open Questions and escalated to an ADR.

## 5. Acceptance Criteria

- Every specification in this repository declares no principle violations at review time, using the checklist in [CONTRIBUTING](../CONTRIBUTING.md); reviewers spot-check against the acceptance signals above.
- Each principle's acceptance signals are traceable to at least one requirement group or spec document that operationalizes them.
- The two platform-specific principles are reflected in the data model (`Claim` tiers; devotional content handling) and in agent behavior specs, not only in prose.
- Any principle exception is explicit: recorded as an ADR with rationale, scope, and expiry or review date.

## 6. Dependencies

- [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md) §0 (tier system), §1 to §2 (faith identity and values), §12 (verification queue): the factual grounding for §4.16 and §4.17.
- [SPEC_CONVENTIONS](./SPEC_CONVENTIONS.md): tier names, entity names, agent roster, and baseline decisions the principles reference.
- [VISION](./VISION.md) and [MISSION](./MISSION.md): the outcomes these principles protect.

## 7. Risks

| Risk | Effect | Mitigation |
|------|--------|------------|
| Principle inflation | Seventeen principles become wallpaper nobody applies | Acceptance signals make each checkable; review checklist requires explicit pass |
| Conflicting principles paralyze design | Specs stall on Searchable vs Privacy First and similar tensions | Precedence rule (§4.18); ADR escalation path |
| Platform principles read as marketing | Provenance First and Faith-Respectful Stewardship degrade into slogans | Both are bound to data model attributes and agent behaviors with testable signals |
| Offline promise overstated | "Offline Capable" implies more than exports can deliver | The qualifier "where possible" plus per-feature offline statements keep the promise honest |
| Faith handling errors by AI | An agent generates devotional content in the owner's voice | Explicit prohibition in §4.17; twin honesty review includes a faith pass |

## 8. Future Enhancements

- A principle scorecard: periodic automated checks (link integrity, tier-attribution linting, em dash detection) reporting per-principle repository health.
- Worked case-law appendix: as ADRs resolve principle conflicts, index them here by principle so precedent accumulates.
- A P1 "principles for collaborators" digest explaining to mentees and family how their data and access are governed.

## 9. Examples

**Provenance First in retrieval.** A user asks the twin about certifications. Retrieval returns the ALX Africa alumni claim (✅) and the USAII CAIE certification claim (🟡). The rendered answer states the first as fact and the second as "Linford reports holding...", with citations to both `Source` records. No prompt wording can flip the second into a bare assertion.

**Faith-Respectful Stewardship in ingestion.** A journal upload containing prayer reflections is ingested. The Ingestion Agent flags the devotional entries, they land at P2 automatically, and the owner is offered (not defaulted into) sealing them at P3 with a succession-based unlock.

**Precedence in a feature decision.** A proposed "share search result" button would let a P1 collaborator forward results externally. Searchable and API First favor it; Privacy First outranks them: the feature ships only with tier-checked, watermark-logged export for P0 content, and P1+ content is non-forwardable.

**Secure by Default in agent design.** The Research Agent needs web access but not journal access. Its tool grant excludes P2/P3 stores entirely, so even a prompt-injected instruction inside a fetched web page cannot exfiltrate private content.

## 10. Open Questions

- Should the precedence rule in §4.18 itself be an ADR in `architecture/MASTER_ARCHITECTURE.md` so it gains a decision record and history? Proposed: yes, at first conflict.
- What is the exact conformance target for Accessible (WCAG version and level)? To be fixed in `ui/ACCESSIBILITY.md`.
- `> TODO(verify): whether Linford wants the "El Roi" signature available to the twin in any automated context, or reserved exclusively for his personal posts.`

## 11. References

- [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md) §0, §1, §2, §12.
- [SPEC_CONVENTIONS](./SPEC_CONVENTIONS.md) §2, §5, §6, §7, §9.

## 12. Related Specifications

- [VISION](./VISION.md) and [MISSION](./MISSION.md): the outcomes and commitments these principles enforce.
- [CONTRIBUTING](../CONTRIBUTING.md): the review checklist that operationalizes principle compliance.
- `architecture/MASTER_ARCHITECTURE.md`: ADRs implementing and, where necessary, excepting these principles.
- `security/PRIVACY.md` and `security/SECURITY.md`: enforcement of Privacy First and Secure by Default.
- `ai/DIGITAL_TWIN.md` and `agents/MULTI_AGENT_ARCHITECTURE.md`: enforcement of Provenance First and Faith-Respectful Stewardship in AI behavior.
