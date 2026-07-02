# USER_STORIES
### User stories (US-001 to US-055) grouped by persona and feature, with acceptance criteria

| Field | Value |
|-------|-------|
| Status | Draft |
| Owner | Linford Musiyambodza |
| Last updated | 2026-07-02 |
| Depends on | [USER_PERSONAS](./USER_PERSONAS.md), [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md), [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md) |

---

## 1. Purpose

This document enumerates the user stories that drive Legacy's functional design. Stories are grouped by persona ([USER_PERSONAS](./USER_PERSONAS.md)), then by canonical feature (F1-F16). Each story states persona, capability, benefit, a MoSCoW priority (Must, Should, Could; deliberately not P0-P3, which are privacy tiers), and Given/When/Then acceptance criteria. Stories feed the functional requirements (FR domain groups in [FUNCTIONAL_REQUIREMENTS](./FUNCTIONAL_REQUIREMENTS.md)) and the feature specs FS-001 to FS-016.

## 2. Goals

- Cover all sixteen canonical features with at least two stories each.
- Encode provenance-sensitive behavior as testable stories (verification, tier-aware refusal).
- Encode succession and offline-vault behavior as first-class stories, not afterthoughts.
- Keep every story independently testable via its Given/When/Then criteria.

## 3. Scope

**In scope:** stories US-001 to US-055 for personas PERS-01 to PERS-07. **Out of scope:** implementation detail (architecture and AI docs), exhaustive edge cases (feature specs), and requirement-level phrasing (requirements docs). Story IDs are stable; retired stories are marked Deprecated, never renumbered.

## 4. Requirements

### 4.1 PERS-01 Owner stories

#### F1 Capture and Ingestion

**US-001 (Must, F1).** As the Owner, I want to capture a quick note or idea in under ten seconds from web or CLI so that fleeting thoughts enter the corpus before they are lost.
- Given an authenticated owner session, When I submit a text capture, Then a `Note` is created at tier P2 with timestamp and capture source recorded.
- Given a capture, When ingestion completes, Then the note is searchable (F4) without further manual steps.

**US-002 (Must, F1).** As the Owner, I want to upload a batch of documents (PDF, Markdown, images, presentations) so that existing archives are parsed, chunked, and indexed in one operation.
- Given a batch upload, When the `IngestionJob` runs, Then each file becomes an `Artifact` with extracted text, `EmbeddingChunk` records, and a linked `Source`.
- Given a batch with one corrupt file, When the job finishes, Then valid files are indexed and the corrupt file is reported without failing the batch.
- Given a completed job, When I open its report, Then per-file status, counts, and warnings are listed.

**US-003 (Must, F1).** As the Owner, I want to connect a GitHub repository (account `linfordlee14`, ✅) so that code history, READMEs, and releases are ingested as project evidence.
- Given a connected repository, When ingestion runs, Then commits, README content, and release notes become `Artifact` records linked to the matching `Project`.
- Given a re-sync, When no changes exist upstream, Then no duplicate artifacts are created.

**US-004 (Should, F1).** As the Owner, I want failed ingestion jobs to surface actionable errors and support retry so that no content silently disappears.
- Given a failed `IngestionJob`, When I view the workspace dashboard, Then the failure appears with cause and a retry action.
- Given a retry, When it succeeds, Then the job history shows both attempts in the audit trail.

#### F2 Knowledge Graph and Entity Linking

**US-005 (Must, F2).** As the Owner, I want extracted entities (Person, Organization, Project, Event) and their relationships presented for review so that the graph reflects reality, not extraction guesses.
- Given a completed ingestion, When entity extraction proposes new entities or `Edge` records, Then they are queued as pending until I confirm, merge, or reject them.
- Given a rejection, When I decline a proposed entity, Then it does not appear in search or twin answers.

**US-006 (Should, F2).** As the Owner, I want to merge duplicate entities (for example "Linfy Tech" and "Linfy Tech Solutions") so that the graph stays clean.
- Given two entities selected for merge, When I confirm, Then edges, tags, and claims re-point to the survivor and the merge is logged.
- Given a wrong merge, When I undo within the retention window, Then the prior state is restored.

#### F3 Timeline Engine

**US-007 (Must, F3).** As the Owner, I want a chronological timeline of my life and work, filterable by project, tag, and tier, so that I can see and navigate my own history.
- Given ingested events, When I open the timeline, Then `Event` records render in order with links to their source artifacts.
- Given a filter (project, tag, date range, tier), When applied, Then only matching events remain visible.

**US-008 (Should, F3).** As the Owner, I want to correct an event's date or details while preserving provenance so that fixes never erase where information came from.
- Given an event with a wrong date, When I edit it, Then the correction is stored with the original value retained in history.
- Given a corrected event, When the twin or RAG cites it, Then the corrected value is used.

#### F4 Search

**US-009 (Must, F4).** As the Owner, I want natural language search across the whole corpus so that I find things by meaning, not filenames.
- Given the query "that phishing detector I built", When search runs, Then PhishGuard-related items rank in the top results with entity-type labels.
- Given zero results, When the query completes, Then the system suggests related entities or broader terms instead of an empty page.

**US-010 (Should, F4).** As the Owner, I want hybrid filters (keyword plus semantic, entity type, privacy tier, date range) so that precise retrieval is possible.
- Given a semantic query with filter tier=P2 and type=JournalEntry, When search runs, Then only matching private journal items return.
- Given identical queries, When repeated, Then ranking is stable enough to reproduce results (no random reshuffle).

#### F5 RAG Question Answering

**US-011 (Must, F5).** As the Owner, I want answers to corpus questions with inline citations so that every statement is traceable to a source.
- Given a question answerable from the corpus, When the answer renders, Then each factual sentence carries at least one citation resolvable to a `Source` or `Artifact`.
- Given a question the corpus cannot answer, When the pipeline completes, Then the system says so explicitly rather than guessing.

**US-012 (Must, F5).** As the Owner, I want answers to distinguish verified from self-reported claims and to decline asserting flagged claims so that the MASTER_CONTEXT §0 rule holds in every response.
- Given a question touching a 🟡 claim, When answered, Then the claim is attributed ("Linford states that...") rather than asserted.
- Given a question touching a 🔴 claim, When answered, Then the answer marks it unverified and links its verification queue entry.

#### F6 AI Digital Twin

**US-013 (Must, F6).** As the Owner, I want the twin to speak in my documented voice (direct, warm, builder-narrative, "El Roi" signature where appropriate, no em dashes; style guide 🟡) so that it represents me recognizably.
- Given a twin response, When rendered, Then it conforms to the style rules defined in [DIGITAL_TWIN](../ai/DIGITAL_TWIN.md), including the no-em-dash rule.
- Given a topic outside my documented views, When asked for an opinion, Then the twin says it cannot speak for me on that rather than improvising values.

**US-014 (Must, F6).** As the Owner, I want the twin to refuse to state a 🔴 claim as fact so that my legacy never launders unverified claims.
- Given the question "Did SpazaLink place 3rd at SA Startup Week 2026?" (🔴 in MASTER_CONTEXT §7), When the twin answers, Then it reports the claim as flagged/unverified and does not assert it.
- Given a claim upgraded to ✅ after verification (F9), When asked again, Then the twin may assert it with citation.

#### F7 Long-Term Memory Engine

**US-015 (Must, F7).** As the Owner, I want conversations and agent sessions to persist as long-term memory (episodic, semantic, procedural, reflective) so that no session starts from zero.
- Given a prior conversation about a project decision, When I raise the topic in a new session, Then relevant `MemoryRecord` items are recalled and cited as memory, not fact.
- Given memory recall, When surfaced, Then each memory shows its origin (conversation, date).

**US-016 (Must, F7).** As the Owner, I want to correct or delete a memory record so that wrong or stale memories cannot compound.
- Given an incorrect memory, When I edit or delete it, Then future recalls reflect the change and the action is audit-logged.
- Given a deleted memory, When any agent runs, Then the deleted content is not retrievable by any pipeline.

#### F8 Multi-Agent Orchestration

**US-017 (Must, F8).** As the Owner, I want to delegate a multi-step task (for example "research and draft a grant application summary from my conservation projects") so that agents plan and execute with my approval at defined gates.
- Given a delegated task, When the Orchestrator Agent produces a plan, Then I approve, edit, or reject the plan before execution.
- Given execution, When a step would publish, delete, or contact anyone externally, Then it blocks on explicit human approval.
- Given completion, When I open the `AgentRun`, Then every step, agent, and tool call is inspectable.

**US-018 (Should, F8).** As the Owner, I want per-run budget caps (tokens, cost, wall time) so that agent work stays economically bounded.
- Given a run with a cap, When the cap is reached, Then the run pauses with partial results and requests continuation approval.

#### F9 Verification and Citation Engine

**US-019 (Must, F9).** As the Owner, I want a verification queue of flagged claims (seeded from MASTER_CONTEXT §12) so that I can work the backlog down systematically.
- Given the queue, When opened, Then each 🔴 `Claim` shows its statement, current tier, existing sources, and suggested verification steps.
- Given queue ordering, When rendered, Then claims most cited by public surfaces rank first.

**US-020 (Must, F9).** As the Owner, I want to attach a source to a claim and change its tier with an audit trail so that upgrades are deliberate and reversible.
- Given a flagged claim, When I attach a `Source` and set tier to verified, Then the change records who, when, and on what evidence.
- Given an upgrade, When public surfaces re-render, Then tier markers update everywhere the claim appears.
- Given insufficient evidence, When the Verification Agent reviews my proposed upgrade, Then it can recommend against it, but the owner decision is final and logged.

#### F10 Public Portfolio

**US-021 (Must, F10).** As the Owner, I want to publish a project page through an explicit P0 review gate so that nothing goes public by accident.
- Given a draft page, When I request publication, Then a review checklist (content, claims, privacy scan) must pass before the item's tier changes to P0.
- Given publication, When complete, Then the tier change and reviewer decisions are audit-logged.

**US-022 (Must, F10).** As the Owner, I want a pre-publish privacy scan that flags P1+ content embedded in a candidate page so that leaks are caught before exposure.
- Given a draft citing a P2 journal passage, When the scan runs, Then the passage is flagged and publication is blocked until resolved.
- Given a clean scan, When publication proceeds, Then the scan result is stored with the published version.

#### F11 Private Workspace

**US-023 (Must, F11).** As the Owner, I want a private dashboard (recent captures, pending entity reviews, verification queue size, agent runs) so that the system's state is visible at a glance.
- Given the dashboard, When loaded, Then all listed panels reflect live state and deep-link into their features.

**US-024 (Must, F11).** As the Owner, I want every new item to default to P2 so that privacy is the baseline, not an option I must remember.
- Given any capture or agent-created artifact, When stored, Then its tier is P2 unless I explicitly set otherwise.
- Given a tier decrease action (toward public), When attempted, Then explicit confirmation is required; increases (toward private) apply immediately.

#### F12 Journals and Reflections

**US-025 (Must, F12).** As the Owner, I want to write journal entries, including prayer reflections, at tier P3 so that my most personal writing is sealed by default conditions I control.
- Given a new `JournalEntry` marked P3, When saved, Then it is excluded from all search, RAG, twin, and agent contexts except explicitly P3-scoped owner sessions.
- Given a P3 entry, When any export other than the full owner vault runs, Then the entry is excluded or included encrypted per vault policy.

**US-026 (Must, F12).** As the Owner, I want to define unlock conditions per sealed entry or collection (time lock, succession event, named recipients) so that release is governed by my intent.
- Given an entry with a ten-year time lock, When the date passes, Then it becomes readable to its designated audience and the release is logged.
- Given conflicting conditions, When saving, Then validation rejects the configuration with a clear explanation.

#### F13 Project and Research Explorer

**US-027 (Should, F13).** As the Owner, I want a project view combining repo history, notes, artifacts, events, and lessons so that each project's full story lives in one place.
- Given a `Project` (for example CyberBuddy, ✅), When opened, Then linked artifacts, timeline events, collaborator pattern, and lessons render together.

**US-028 (Should, F13).** As the Owner, I want project status honesty (verified public vs described-as-building, per MASTER_CONTEXT §6 guidance) so that the explorer never overstates a project's public footprint.
- Given a 🟡 project (for example SafeWatch SA), When displayed, Then it is labeled as described by the owner, not as a verified public project.
- Given a project gaining a verified public source, When its claim is upgraded (F9), Then the label updates.

#### F14 Mentor and Career Advisor

**US-029 (Should, F14).** As the Owner, I want career advice grounded in my actual history (skills, certifications, achievements, goals) with citations so that coaching is evidence-based.
- Given a question ("what should I strengthen before applying to X"), When the Mentor Agent answers, Then recommendations cite my `Skill`, `Certification`, and `Project` records.
- Given advice referencing a 🟡 credential, When rendered, Then the credential is marked self-reported.

**US-030 (Could, F14).** As the Owner, I want a skill-gap analysis against a stated goal so that learning plans are concrete.
- Given a `Goal`, When analysis runs, Then present skills, missing skills, and suggested evidence-building steps are listed.

#### F15 Writing and Presentation Assistant

**US-031 (Should, F15).** As the Owner, I want to generate a presentation outline and speaker notes from a project's history so that talk preparation starts at eighty percent done.
- Given a project selection and audience, When generation runs, Then a structured deck outline with per-slide sources is produced as an `Artifact` at P2.
- Given included claims, When the deck is drafted, Then 🟡/🔴 claims are marked for my decision before any public use.

**US-032 (Should, F15).** As the Owner, I want article drafts in my brand voice (🟡 style guide) with AI assistance disclosed in metadata so that publishing stays authentic and honest.
- Given a draft request, When produced, Then the draft follows the style rules and records itself as AI-assisted in artifact metadata.

#### F16 Legacy Vault Export and Succession

**US-033 (Must, F16).** As the Owner, I want to export a versioned Legacy Vault (Markdown, JSON, media manifest) so that the whole corpus exists outside the platform.
- Given an export request with a tier scope, When complete, Then the vault contains all in-scope entities, claims with tiers, sources, and media manifest, with a version stamp and integrity checksums.
- Given a vault, When validated, Then the manifest verifies complete and uncorrupted.

**US-034 (Must, F16).** As the Owner, I want the vault readable offline with no platform dependency so that the legacy survives any vendor or infrastructure failure.
- Given a vault on a clean machine with no network, When opened, Then content is readable with commodity software (plain files, human-readable structure).
- Given the vault's claims data, When read, Then confidence tiers are present and legible in both the Markdown and JSON forms.

**US-035 (Must, F16).** As the Owner, I want to configure a succession plan (steward identity, activation verification, release schedule, heir designations) so that handover is governed by my documented intent.
- Given a completed plan, When saved, Then it validates (no orphan releases, reachable steward contact) and is itself included in the vault.
- Given a plan change, When saved, Then prior versions are retained and the change is audit-logged.

### 4.2 PERS-02 Future Family Member / Descendant stories

**US-036 (Must, F6).** As a Descendant, I want to ask the twin biographical questions and receive honest, tier-aware answers so that I learn who he truly was, not a polished myth.
- Given the question "what did he believe?", When answered, Then the twin grounds its answer in cited values content (MASTER_CONTEXT §2 pattern) and speaks in his voice.
- Given a question touching an unverified claim, When answered, Then the twin discloses the uncertainty in plain language a non-technical reader understands.

**US-037 (Should, F3).** As a Descendant, I want to explore his timeline by life period and theme so that I get a narrative entry point into a large archive.
- Given the timeline in descendant mode, When opened, Then only tiers I am entitled to appear, organized by era with narrative summaries.

**US-038 (Must, F12/F16).** As a Descendant, I want to read sealed journals and prayer reflections released to me by his rules so that his most personal voice reaches the audience he intended, when he intended.
- Given a P3 entry addressed to descendants with met conditions, When I open my released items view, Then the entry is readable and marked with its release reason and date.
- Given an unmet condition, When I browse, Then the entry is neither readable nor enumerable.

**US-039 (Must, F16).** As a Descendant, I want to open the Legacy Vault offline decades from now so that the legacy does not depend on any company surviving.
- Given a vault copy and its reader instructions, When opened without network access, Then I can browse the corpus and identify claim tiers.

### 4.3 PERS-03 Trusted Collaborator or Mentee stories

**US-040 (Must, F11).** As a Collaborator, I want to accept a P1 grant and see exactly the shared scope so that trust boundaries are unambiguous.
- Given a grant invitation, When accepted, Then my workspace lists only in-scope collections and each item shows its sharing state.
- Given grant expiry or revocation, When it occurs, Then access ends immediately and I see a clear notice.

**US-041 (Must, F5).** As a Collaborator, I want corpus questions answered strictly from my granted scope so that answers never leak the owner's private context.
- Given a question whose best evidence is P2, When answered under my grant, Then the system answers from P0/P1 scope only or states it lacks sufficient shared context.
- Given any of my queries, When executed, Then the access decision is audit-logged.

**US-042 (Could, F14).** As a Mentee, I want curated learning paths derived from the owner's real journey so that mentorship survives beyond live sessions.
- Given a mentee grant, When I open the mentorship space, Then curated lessons and resources appear, each traceable to owner-approved content.

### 4.4 PERS-04 Public Visitor stories

**US-043 (Must, F10).** As a Public Visitor, I want to browse the portfolio (projects, talks, writing, timeline highlights) so that I can assess Linford's work quickly.
- Given the public site, When I browse, Then only P0 content renders and pages load without authentication.

**US-044 (Must, F9/F10).** As a recruiter-type Visitor, I want verification markers on public claims so that I can distinguish evidence from self-report during due diligence.
- Given a public achievement claim, When rendered, Then it shows verified-with-citation or a self-reported label, per its `Claim` tier.
- Given a citation, When followed, Then it resolves to the referenced public `Source`.

**US-045 (Should, F4).** As a Public Visitor, I want to search public content so that I can find specific projects or articles.
- Given a public search query, When executed, Then results draw from P0 content only, verified by authorization tests.

**US-046 (Must, security).** As a Public Visitor, I must never see or infer the existence of P1+ content so that privacy holds even against enumeration.
- Given crafted URLs or search probes for private items, When attempted, Then responses are indistinguishable from nonexistent content.
- Given public feeds and sitemaps, When generated, Then they contain P0 items only.

### 4.5 PERS-05 Estate Steward / Executor stories

**US-047 (Must, F16).** As the Estate Steward, I want to activate succession through multi-step verification so that activation is possible in a crisis yet resistant to fraud.
- Given an activation request, When initiated, Then identity verification, a mandatory waiting period, and owner-notification challenge all execute before any access changes.
- Given an owner response during the waiting period, When received, Then activation cancels and the attempt is logged.

**US-048 (Must, F16).** As the Estate Steward, I want to execute the P3 release schedule without reading sealed content so that I can honor the plan without violating its intimacy.
- Given a due release tranche, When I execute it, Then designated recipients gain access, contents are never displayed to me (unless the plan grants it), and each release is logged.

**US-049 (Must, F16).** As the Estate Steward, I want a complete audit trail of every succession action so that my execution is accountable to heirs and law.
- Given any steward action, When performed, Then an `AuditLogEntry` records actor, action, target, and time, and the log is exportable.

**US-050 (Should, F16).** As the Estate Steward, I want an emergency freeze (suspend grants and API tokens) so that a compromise during transition can be contained.
- Given a freeze action, When executed, Then all non-steward access suspends, the freeze is logged, and unfreezing requires the same verification strength as activation.

### 4.6 PERS-06 Machine Consumer stories

**US-051 (Must, API).** As a Machine Consumer, I want scoped token access to the corpus API with tier enforcement so that automated reading obeys the same privacy rules as humans.
- Given a P0-scoped token, When any P1+ resource is requested, Then the API refuses without confirming resource existence.
- Given any request, When served, Then the response records in the audit log with token identity.

**US-052 (Must, F9).** As a Machine Consumer, I want claims delivered with machine-readable confidence tiers and source links so that downstream generation can obey the never-upgrade rule programmatically.
- Given a claims endpoint response, When parsed, Then every claim carries `tier` (`verified`, `self_reported`, `flagged`) and resolvable source references.
- Given a flagged claim, When consumed by a compliant agent, Then documented guidance instructs attribution rather than assertion.

**US-053 (Should, API).** As a Machine Consumer, I want stable IDs, pagination, and an incremental change feed so that long-lived consumers stay consistent without full re-reads.
- Given a change feed cursor, When polled, Then created, updated, and deleted items since the cursor are returned exactly once.

### 4.7 PERS-07 Linfy Tech Team Member stories

**US-054 (Could, F11).** As a Linfy Tech Team Member, I want access to company-scoped P1 collections so that company work uses shared context without touching personal material.
- Given a company grant, When I browse, Then only company-designated collections appear; journals and personal items are absent and non-enumerable.

**US-055 (Could, F15).** As a Linfy Tech Team Member, I want the writing assistant constrained to company scope and brand rules so that produced content is consistent and properly attributed.
- Given a draft request, When generated, Then sources come only from granted scope and the output carries AI-assistance and scope metadata.

## 5. Acceptance Criteria

- AC-1: All sixteen features F1-F16 are covered by at least two stories (see traceability table below).
- AC-2: Every story names one primary persona, one primary feature, a MoSCoW priority, and 2-4 Given/When/Then criteria.
- AC-3: Provenance-sensitive behavior is explicitly covered: US-012, US-014, US-019, US-020, US-028, US-044, US-052.
- AC-4: Succession is covered by US-035, US-038, US-047 to US-050; offline vault by US-033, US-034, US-039.
- AC-5: No story asserts a 🟡/🔴 MASTER_CONTEXT claim as fact; tier annotations appear wherever such claims are referenced.

| Feature | Stories |
|---------|---------|
| F1 | US-001, US-002, US-003, US-004 |
| F2 | US-005, US-006 |
| F3 | US-007, US-008, US-037 |
| F4 | US-009, US-010, US-045 |
| F5 | US-011, US-012, US-041 |
| F6 | US-013, US-014, US-036 |
| F7 | US-015, US-016 |
| F8 | US-017, US-018 |
| F9 | US-019, US-020, US-044, US-052 |
| F10 | US-021, US-022, US-043 |
| F11 | US-023, US-024, US-040, US-054 |
| F12 | US-025, US-026, US-038 |
| F13 | US-027, US-028 |
| F14 | US-029, US-030, US-042 |
| F15 | US-031, US-032, US-055 |
| F16 | US-033, US-034, US-035, US-039, US-047, US-048, US-049, US-050 |

## 6. Dependencies

- [USER_PERSONAS](./USER_PERSONAS.md): persona definitions and tier mappings assumed by every story.
- [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md): factual grounding and tier examples used in criteria (SpazaLink 🔴, style guide 🟡).
- [FEATURE_SPECIFICATIONS](./FEATURE_SPECIFICATIONS.md): behavioral detail these stories summarize.
- [FUNCTIONAL_REQUIREMENTS](./FUNCTIONAL_REQUIREMENTS.md): FR domain groups (ING, KG, TL, SRCH, RAG, TWIN, MEM, AGT, VER, UI, SEC, PRIV, API, DATA, OPS) that formalize these stories.
- [AUTHORIZATION](../security/AUTHORIZATION.md) and [PRIVACY](../security/PRIVACY.md): enforcement semantics behind tier-scoped criteria.

## 7. Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Criteria drift from feature specs during parallel authoring | Untestable or contradictory acceptance tests | Reconciliation pass after first full repo draft; feature specs are the behavioral authority |
| Owner-heavy story set underserves passive personas | Descendant and visitor experience degrades | Persona coverage check in AC-1 review; PERS-02/PERS-04 stories are Must where they guard trust |
| MoSCoW priorities read as privacy tiers | Planning confusion | Explicit naming rule in Purpose; reviews reject "P1 priority" phrasing |
| GWT criteria stated at UI level too early | Brittle tests | Criteria phrased at behavior level, UI specifics deferred to [UI_UX](../ui/UI_UX.md) |

## 8. Future Enhancements

- Story sizing and release mapping once [ROADMAP](../roadmap/ROADMAP.md) phases are fixed.
- Negative-path story pack for security testing (abuse cases) coordinated with [SECURITY](../security/SECURITY.md).
- Mentee-program stories expanded if Linfy Academy (🟡) becomes an operating program.
- Localization stories (multi-language corpus consumption) for future family members.

## 9. Examples

**Worked example, US-014 in test form.**

```json
{
  "story": "US-014",
  "given": "Claim 'SpazaLink placed 3rd at SA Startup Week 2026' has tier 'flagged'",
  "when": "Twin is asked 'Did SpazaLink win anything at SA Startup Week?'",
  "then": [
    "Response attributes the claim to the owner's own account",
    "Response includes an unverified marker",
    "Response does not contain an unqualified assertion of the placement"
  ]
}
```

**Worked example, US-024 default-privacy check.** Create ten items across capture channels (note, upload, agent-generated draft). Query their tiers. Expected: ten of ten are P2. Any other value fails the story.

## 10. Open Questions

- Should Could-priority stories (US-030, US-042, US-054, US-055) be deferred out of v1 scope entirely? Pending [ROADMAP](../roadmap/ROADMAP.md).
- Do descendant-mode narrative summaries (US-037) require an editorial review gate like P0 publishing? Leaning yes; decision owed to F3/F10 spec reconciliation.
- > TODO(verify): whether mentee users may include minors (affects US-042 consent and safety criteria; depends on Linfy Academy program details, 🟡).

## 11. References

- [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md) §0 (tier rules), §6-§7 (project and achievement tiers used in examples), §12 (verification queue seed).
- [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md) §4 (US ID scheme), §5 (privacy tiers), §6 (entities).

## 12. Related Specifications

- [USER_PERSONAS](./USER_PERSONAS.md): persona roster these stories are grouped by.
- [USE_CASES](./USE_CASES.md): end-to-end flows that string these stories together.
- [FEATURE_SPECIFICATIONS](./FEATURE_SPECIFICATIONS.md): FS-001 to FS-016 behavioral detail.
- [PRODUCT_REQUIREMENTS](./PRODUCT_REQUIREMENTS.md), [FUNCTIONAL_REQUIREMENTS](./FUNCTIONAL_REQUIREMENTS.md), [NON_FUNCTIONAL_REQUIREMENTS](./NON_FUNCTIONAL_REQUIREMENTS.md): requirement formalization.
- [TESTING](../testing/TESTING.md): where Given/When/Then criteria become executable acceptance tests.
