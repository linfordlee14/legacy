# USE_CASES
### Detailed use cases (UC-001 to UC-016) with flows, alternates, exceptions, and postconditions

| Field | Value |
|-------|-------|
| Status | Draft |
| Owner | Linford Musiyambodza |
| Last updated | 2026-07-02 |
| Depends on | [USER_PERSONAS](./USER_PERSONAS.md), [USER_STORIES](./USER_STORIES.md), [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md) |

---

## 1. Purpose

This document specifies Legacy's canonical end-to-end use cases. Where user stories state single capabilities, use cases describe complete interactions: actors, preconditions, triggers, numbered main flows, alternate flows (A), exception flows (E), and postconditions. They are the primary input for integration test design ([TESTING](../testing/TESTING.md)) and for the flow-level sections of [FEATURE_SPECIFICATIONS](./FEATURE_SPECIFICATIONS.md).

## 2. Goals

- Describe the sixteen most system-defining flows across all personas and all major features.
- Make privacy-tier enforcement, provenance discipline, and human approval gates visible as explicit flow steps, not implicit assumptions.
- Give every flow deterministic postconditions so integration tests have oracles.

## 3. Scope

**In scope:** UC-001 to UC-016 as end-to-end behavioral flows, technology-agnostic. **Out of scope:** UI layouts ([UI_UX](../ui/UI_UX.md)), API shapes ([API_SPECIFICATION](../api/API_SPECIFICATION.md)), agent internals ([MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md)), and non-functional targets ([NON_FUNCTIONAL_REQUIREMENTS](./NON_FUNCTIONAL_REQUIREMENTS.md)).

## 4. Requirements

Notation: actors reference [USER_PERSONAS](./USER_PERSONAS.md); agents reference the canonical roster in [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md) §7; entities are the canonical set of §6.

### UC-001: Ingest and index a document batch

- **Related feature:** F1 (also F2, F4). **Stories:** US-002, US-004.
- **Actors:** Owner (PERS-01); Ingestion Agent, Curation Agent.
- **Preconditions:** Authenticated owner session; storage quota available.
- **Trigger:** Owner uploads a batch of files (PDF, Markdown, images, slides) via workspace or CLI.
- **Main flow:**
  1. System creates an `IngestionJob` listing all files and returns a job ID immediately.
  2. Ingestion Agent parses each file: text extraction, media handling, format normalization.
  3. Each file becomes an `Artifact` (tier P2 by default) with a linked `Source` recording origin and upload time.
  4. Content is chunked into `EmbeddingChunk` records and embedded for search.
  5. Curation Agent proposes tags, detects duplicates against existing artifacts, and assigns quality scores.
  6. Entity extraction proposals (for F2) are queued for owner review, not auto-committed.
  7. Job completes; owner receives a per-file report (indexed, skipped duplicate, failed with cause).
- **Alternate flows:**
  - A1 (duplicate detected): file matches an existing artifact; system links the upload as an additional `Source` instead of creating a duplicate.
  - A2 (large batch): job processes in stages; partial results become searchable as each stage commits.
- **Exception flows:**
  - E1 (corrupt or unsupported file): file is marked failed with cause; remaining files proceed (US-002 criterion).
  - E2 (job crash): job resumes from the last committed stage on retry; no partial artifact is left unindexed and invisible.
- **Postconditions:** every valid file is a searchable `Artifact` with source and embeddings; failures are visible and retryable; audit trail records the job.

### UC-002: Ingest a GitHub repository

- **Related feature:** F1 (also F13). **Stories:** US-003.
- **Actors:** Owner; Ingestion Agent, Graph Agent.
- **Preconditions:** Owner has connected the GitHub account `linfordlee14` (✅) with read authorization.
- **Trigger:** Owner selects a repository for ingestion or a scheduled re-sync fires.
- **Main flow:**
  1. System registers the repository as a `Source` and creates an `IngestionJob`.
  2. Ingestion Agent fetches repository metadata, README, release notes, and commit history summary.
  3. Content is stored as `Artifact` records (code snapshot class) linked to a matching `Project` node; if no project exists, a proposal is queued.
  4. Graph Agent proposes edges: Project built-with Skill, Project has-artifact, Project relates-to Event (release dates feed F3).
  5. Timeline Agent derives `Event` candidates from releases and first/last commit dates.
  6. Owner reviews proposed project links and entity merges; confirmed items commit to the graph.
- **Alternate flows:**
  - A1 (re-sync, no changes): job completes as a no-op; no duplicates (US-003 criterion).
  - A2 (private repository): artifacts are marked P2 and flagged so the P0 publish scan (UC-006) treats code content conservatively.
- **Exception flows:**
  - E1 (API rate limit or auth failure): job pauses with actionable error; retry honors upstream limits.
  - E2 (repository deleted upstream): existing artifacts are retained with the source marked unavailable; nothing is silently deleted.
- **Postconditions:** repository evidence is linked to its project; timeline candidates exist; provenance to the repo `Source` is complete.

### UC-003: Ask the Digital Twin a biographical question (tier-aware answer)

- **Related feature:** F6 (also F5, F9). **Stories:** US-013, US-014, US-036.
- **Actors:** Owner, Descendant, or Collaborator (tier-scoped); Twin Agent, Retrieval Agent, Verification Agent.
- **Preconditions:** Asker is authenticated with a known tier scope (or is public, P0 scope); twin persona profile is configured per [DIGITAL_TWIN](../ai/DIGITAL_TWIN.md).
- **Trigger:** Asker submits a biographical question, for example "Did you win anything at SA Startup Week?"
- **Main flow:**
  1. Retrieval Agent assembles context restricted to the asker's tier scope.
  2. Verification Agent annotates retrieved `Claim` records with tiers (verified, self_reported, flagged).
  3. Twin Agent composes an answer in the owner's documented voice (🟡 style guide), obeying tier rules: assert ✅ with citation, attribute 🟡, disclose 🔴 as unverified.
  4. Response renders with inline citations and visible tier markers; the exchange is stored as a `Conversation`.
  5. Memory-worthy facts from the exchange are proposed to the Long-Term Memory Engine (F7) rather than silently stored.
- **Alternate flows:**
  - A1 (no evidence in scope): twin states it cannot answer from the asker's accessible record, without hinting at private content.
  - A2 (opinion question outside documented views): twin declines to improvise values (US-013 criterion).
- **Exception flows:**
  - E1 (retrieval failure): twin reports degraded capability instead of answering uncited.
  - E2 (tier metadata missing on a claim): claim is treated as flagged by default and the gap is logged for the verification queue.
- **Postconditions:** answer is tier-faithful and cited; conversation is persisted at the asker's scope; no privacy leakage occurred.

### UC-004: Explore the timeline

- **Related feature:** F3. **Stories:** US-007, US-008, US-037.
- **Actors:** Owner (full), Descendant/Collaborator/Visitor (tier-scoped slice); Timeline Agent.
- **Preconditions:** Events exist from ingestion and confirmations.
- **Trigger:** Actor opens the timeline surface.
- **Main flow:**
  1. System renders `Event` records within the actor's tier scope, chronologically, grouped by era.
  2. Actor applies filters (project, tag, date range, and for the owner, tier).
  3. Actor opens an event to see linked artifacts, people, organizations, and source citations.
  4. Owner-only: actor edits an event date; correction is saved with original value retained in history (US-008).
- **Alternate flows:**
  - A1 (descendant mode): narrative era summaries render alongside raw events.
  - A2 (public slice): only P0 events render, for example the GDG Cape Town Pet Projects presentation on 30 June 2026 (✅).
- **Exception flows:**
  - E1 (conflicting dates from two sources): event displays the preferred value with a conflict marker linking both sources; conflict enters the curation queue.
- **Postconditions:** navigation leaves no state changes except logged owner edits; every displayed event remains source-linked.

### UC-005: Search the corpus in natural language

- **Related feature:** F4. **Stories:** US-009, US-010, US-045.
- **Actors:** Any persona within tier scope; Retrieval Agent.
- **Preconditions:** Index is populated.
- **Trigger:** Actor submits a query, for example "that phishing detector I built".
- **Main flow:**
  1. System runs hybrid retrieval (semantic plus keyword) over the actor's tier scope.
  2. Results rank with entity-type labels, snippet, tier badge, and source link.
  3. Actor refines with filters (entity type, date range, tag; owner may filter by tier).
  4. Actor opens a result; the access decision is logged.
- **Alternate flows:**
  - A1 (zero results): system suggests related entities and broader queries (US-009 criterion).
  - A2 (query is a question): system offers to route to RAG answering (F5) instead of list results.
- **Exception flows:**
  - E1 (vector index degraded): keyword search still serves results with a degraded-mode notice.
- **Postconditions:** no result outside tier scope was returned; query and access decisions are audit-logged.

### UC-006: Publish a project to the public portfolio (P0 review gate)

- **Related feature:** F10 (also F9). **Stories:** US-021, US-022.
- **Actors:** Owner; Writing Agent (draft support), Verification Agent, Curation Agent.
- **Preconditions:** Project exists with linked artifacts; owner has a draft page at P2.
- **Trigger:** Owner requests publication of the draft.
- **Main flow:**
  1. System opens a publication checklist: content review, claim review, privacy scan.
  2. Verification Agent lists every `Claim` referenced by the page with its tier; 🟡 claims must carry attribution phrasing, 🔴 claims block publication or must be removed or reworded as unverified.
  3. Privacy scan checks the page and its transitive citations for P1+ content (US-022).
  4. Owner resolves all blockers and explicitly confirms tier change to P0.
  5. Page publishes; version, scan result, claim list, and decision log are stored.
- **Alternate flows:**
  - A1 (scheduled publish): confirmation completes now, tier change executes at the scheduled time.
  - A2 (republish after edit): delta review runs on changed claims and content only.
- **Exception flows:**
  - E1 (privacy scan flags a P2 passage): publication blocks until the passage is removed or the source item is deliberately re-tiered by the owner.
  - E2 (claim upgraded evidence disputed): claim returns to the verification queue and the page must drop or attribute it.
- **Postconditions:** public page contains only P0 content; every public claim is tier-marked; the gate decision trail is auditable.

### UC-007: Grant a collaborator P1 access

- **Related feature:** F11. **Stories:** US-040, US-041.
- **Actors:** Owner; Collaborator (PERS-03).
- **Preconditions:** Content to share is organized in one or more `Collection` scopes.
- **Trigger:** Owner initiates a grant for a named collaborator.
- **Main flow:**
  1. Owner selects collections, permission level (read, comment, contribute), and expiry (time-boxed by default).
  2. System creates a `Grant` and sends an invitation.
  3. Collaborator authenticates and accepts; their workspace shows exactly the granted scope (US-040).
  4. All collaborator access decisions are audit-logged; owner can view a per-grant access report.
- **Alternate flows:**
  - A1 (grant extension): owner renews before expiry; renewal is logged.
  - A2 (contribution): collaborator submits a note or draft; it enters the owner's review queue at P2, attributed to the contributor.
- **Exception flows:**
  - E1 (revocation): owner revokes; sessions and tokens invalidate immediately; collaborator sees a clear notice.
  - E2 (invitation to a wrong address): unaccepted invitations are cancellable and expire on their own.
- **Postconditions:** collaborator sees only granted P1 scope; grant lifecycle is fully logged; expiry defaults prevent perpetual access.

### UC-008: Write a sealed journal entry (P3)

- **Related feature:** F12. **Stories:** US-025, US-026.
- **Actors:** Owner.
- **Preconditions:** Authenticated owner session on a trusted device context per [AUTHENTICATION](../security/AUTHENTICATION.md).
- **Trigger:** Owner starts a new journal entry and marks it sealed (P3), for example a prayer reflection.
- **Main flow:**
  1. Owner writes the entry; autosaves remain within P3 storage scope.
  2. Owner sets unlock conditions: time lock, succession event, designated audience (for example descendants), or combinations.
  3. System validates conditions (no contradictions, resolvable audience) and saves the `JournalEntry`.
  4. System confirms the exclusion set: not searchable, not RAG/twin/agent-visible, excluded from non-owner exports.
- **Alternate flows:**
  - A1 (reclassify later): owner may lower an entry to P2 with explicit confirmation; the change is logged.
  - A2 (owner rereads own sealed entries): permitted by default; if a self-lock is configured, reading is blocked until conditions pass (see Open Questions in [USER_PERSONAS](./USER_PERSONAS.md)).
- **Exception flows:**
  - E1 (invalid conditions): save is rejected with a specific validation message; content is preserved as an unsaved draft.
  - E2 (attempted agent access): any pipeline request touching P3 content outside an owner P3 session is denied and logged as a policy violation.
- **Postconditions:** entry exists at P3 with machine-checkable release conditions; zero exposure to search, agents, or non-owner surfaces.

### UC-009: Run the verification queue on a flagged claim

- **Related feature:** F9. **Stories:** US-019, US-020.
- **Actors:** Owner; Verification Agent, Research Agent.
- **Preconditions:** Queue is seeded with 🔴 claims (initially from MASTER_CONTEXT §12, for example the SpazaLink placement claim).
- **Trigger:** Owner opens the verification queue and selects a claim.
- **Main flow:**
  1. System displays the `Claim`, current tier, linked `Source` records, and every surface citing it.
  2. Research Agent proposes candidate public sources (with human-visible provenance for each candidate).
  3. Owner evaluates evidence and attaches accepted sources to the claim.
  4. Owner sets the new tier; Verification Agent records a recommendation (agree or advise against) alongside the owner's final decision.
  5. System propagates the tier everywhere the claim renders (portfolio badges, twin behavior, API payloads).
- **Alternate flows:**
  - A1 (verification fails): claim stays flagged; the failed attempt and reviewed sources are recorded so work is not repeated.
  - A2 (claim is wrong): owner marks the claim retracted; surfaces citing it update to remove or correct it.
- **Exception flows:**
  - E1 (source link rot): a previously attached source becomes unreachable; claim is flagged for re-verification, not silently kept verified.
- **Postconditions:** claim tier reflects evidence; audit trail records who changed what on which evidence; downstream surfaces are consistent.

### UC-010: Generate a presentation from project history

- **Related feature:** F15 (also F13). **Stories:** US-031.
- **Actors:** Owner; Writing Agent, Retrieval Agent, Verification Agent.
- **Preconditions:** Target project has ingested history (for example CyberBuddy with its GDG Cape Town talk, ✅).
- **Trigger:** Owner requests "a talk deck about <project> for <audience>".
- **Main flow:**
  1. Retrieval Agent assembles the project's artifacts, events, lessons, and claims.
  2. Writing Agent produces a structured outline: narrative arc, per-slide content, speaker notes, and per-slide source citations.
  3. Verification Agent marks any 🟡/🔴 claims in the draft for owner decision.
  4. Owner edits and approves; the deck outline is saved as an `Artifact` at P2.
  5. Optional: owner routes the deck through UC-006 if it will be published.
- **Alternate flows:**
  - A1 (audience variant): owner requests a second variant (technical vs community audience); both versions link to the same sources.
- **Exception flows:**
  - E1 (insufficient project history): system reports the gaps (for example no captured outcomes) instead of fabricating content.
- **Postconditions:** deck artifact exists at P2 with citation map and claim markers; nothing was published without the P0 gate.

### UC-011: Agent-orchestrated research task with human approval

- **Related feature:** F8 (also F5, F9). **Stories:** US-017, US-018.
- **Actors:** Owner; Orchestrator Agent, Research Agent, Writing Agent, Verification Agent.
- **Preconditions:** Task delegation is enabled with configured budget defaults.
- **Trigger:** Owner delegates, for example, "research grant opportunities for African conservation tech and draft a shortlist memo".
- **Main flow:**
  1. Orchestrator Agent drafts a plan: steps, agents, tools, budget estimate, and approval gates.
  2. Owner reviews and approves (or edits) the plan; approval is logged in the `AgentRun`.
  3. Research Agent gathers external sources; every gathered fact is stored as `Claim` candidates with `Source` links, never as bare text.
  4. Verification Agent tiers the gathered claims (external claims default to unverified until reviewed).
  5. Writing Agent drafts the memo citing the claims; the draft saves at P2.
  6. Run completes under budget; owner reviews the memo and the full step-by-step trace.
- **Alternate flows:**
  - A1 (budget cap reached): run pauses with partial results and requests continuation approval (US-018).
  - A2 (plan change mid-run): any step outside the approved plan requires re-approval.
- **Exception flows:**
  - E1 (gate violation attempt): a step attempting external contact or publication without approval is blocked and the run is flagged for review.
  - E2 (tool failure): the failing step retries within policy, then the run pauses with a diagnostic rather than skipping silently.
- **Postconditions:** deliverable exists at P2 with full provenance; complete `AgentRun` trace and budget accounting are stored; no unapproved side effects occurred.

### UC-012: Correct a long-term memory record

- **Related feature:** F7. **Stories:** US-015, US-016.
- **Actors:** Owner; Reflection Agent.
- **Preconditions:** Memory records exist from prior conversations and agent runs.
- **Trigger:** Owner notices an incorrect recall (for example a wrong project decision remembered) and opens the memory inspector.
- **Main flow:**
  1. Owner searches memory records with their origin (conversation, date, type: episodic, semantic, procedural, reflective).
  2. Owner edits the incorrect `MemoryRecord` or deletes it.
  3. System re-embeds or removes the record; dependent consolidations are queued for the Reflection Agent to rebuild.
  4. Action is audit-logged; future recalls reflect the correction.
- **Alternate flows:**
  - A1 (bulk forget): owner deletes all memories derived from a specific conversation in one action.
- **Exception flows:**
  - E1 (recall of deleted content via stale cache): pipelines must revalidate memory liveness; stale hits are dropped and logged as defects.
- **Postconditions:** corrected or deleted memories are not retrievable by any pipeline; consolidation debt is queued, not ignored.

### UC-013: Career review session with the Mentor Agent

- **Related feature:** F14. **Stories:** US-029, US-030.
- **Actors:** Owner; Mentor Agent, Retrieval Agent.
- **Preconditions:** Skills, certifications, achievements, and goals are ingested (with tiers, for example ALX Africa ✅, OctoPrep 🟡).
- **Trigger:** Owner starts a career review, for example "prepare me for a senior AI engineering application".
- **Main flow:**
  1. Mentor Agent retrieves `Skill`, `Certification`, `Achievement`, `Goal`, and `Lesson` records with tiers.
  2. Agent produces an evidence-based assessment: demonstrated strengths (project-linked, per MASTER_CONTEXT §5 guidance), claimed-but-unevidenced areas, and gaps.
  3. Agent proposes a plan: evidence-building steps, learning items, and portfolio updates.
  4. Owner accepts items into `Goal` records; the session persists as a `Conversation` with memory proposals.
- **Alternate flows:**
  - A1 (mentee mode): a granted mentee receives coaching drawn only from owner-approved P1 material.
- **Exception flows:**
  - E1 (advice would rest on a 🔴 credential): the agent excludes it from the evidence base and tells the owner why.
- **Postconditions:** advice is fully cited to corpus records; self-reported credentials are labeled; goals are updated only by explicit acceptance.

### UC-014: Export the Legacy Vault

- **Related feature:** F16. **Stories:** US-033, US-034, US-039.
- **Actors:** Owner (or Estate Steward post-activation).
- **Preconditions:** Corpus is consistent (no half-committed ingestion stages); export policy configured.
- **Trigger:** Owner requests an export (scheduled exports also fire this flow).
- **Main flow:**
  1. Owner selects scope: full owner vault (P0-P3 per policy) or a tier-limited vault (for example P0-P1 for family distribution).
  2. System snapshots the corpus version and generates the vault: Markdown for human reading, JSON for machine reading, media manifest with checksums.
  3. Claims export with confidence tiers and source references in both forms (US-034 criterion).
  4. P3 items are included only in the full owner vault, encrypted per vault policy, with release conditions carried alongside.
  5. System validates the vault (manifest completeness, checksum pass, sample-open test) and records the export version.
- **Alternate flows:**
  - A1 (incremental export): a delta vault since the previous version is produced with the same validation.
- **Exception flows:**
  - E1 (validation failure): the vault is not released; the failure report identifies the defective items.
  - E2 (interrupted export): partial outputs are discarded; exports are atomic per version.
- **Postconditions:** a versioned, checksummed, offline-readable vault exists; its scope and validation results are logged.

### UC-015: Activate succession (estate steward)

- **Related feature:** F16 (also F12). **Stories:** US-047, US-048, US-049, US-050.
- **Actors:** Estate Steward (PERS-05); designated heirs (PERS-02) as recipients.
- **Preconditions:** Owner has a saved succession plan naming the steward, verification method, waiting period, and release schedule.
- **Trigger:** Steward initiates activation, citing the triggering circumstance.
- **Main flow:**
  1. System verifies steward identity per the plan's method.
  2. Mandatory waiting period starts; the owner is notified through all configured channels with a one-step cancellation.
  3. Waiting period elapses with no owner cancellation; activation confirms.
  4. System executes the plan: steward role becomes active, heir grants are created, scheduled P3 releases begin per their conditions (steward does not read sealed content, US-048).
  5. Steward runs the final vault export (UC-014) and, per plan, transfers or winds down infrastructure.
  6. Every action is written to the audit log and an activation report is generated for heirs.
- **Alternate flows:**
  - A1 (planned handover while owner is alive): owner co-confirms and the waiting period is skipped.
  - A2 (staged releases): P3 tranches release over years per plan; each tranche logs independently.
- **Exception flows:**
  - E1 (owner cancels during waiting period): activation aborts, attempt is logged, plan integrity is reviewed (US-047).
  - E2 (fraudulent attempt suspected): failed verification locks succession attempts for a policy-defined cooldown and alerts all configured contacts.
  - E3 (compromise during transition): steward triggers emergency freeze (US-050); unfreezing requires activation-strength verification.
- **Postconditions:** access reflects the plan exactly; sealed releases obey their conditions; a complete, exportable audit trail exists.

### UC-016: Machine consumer reads the corpus via API

- **Related feature:** API surface over F2, F5, F9 (PERS-06). **Stories:** US-051, US-052, US-053.
- **Actors:** Machine Consumer (PERS-06); Owner as token issuer.
- **Preconditions:** Owner issued a scoped token (default P0); API version documented in [API_SPECIFICATION](../api/API_SPECIFICATION.md).
- **Trigger:** Consumer begins a sync or a question-answering session against the API.
- **Main flow:**
  1. Consumer authenticates; token scope and identity are attached to all requests.
  2. Consumer reads entities, claims (with `tier` and source references), timeline events, and embeddings within scope.
  3. Consumer polls the change feed with a cursor for incremental sync (US-053).
  4. All requests are rate-limited per policy and recorded as audit entries.
- **Alternate flows:**
  - A1 (elevated scope): a P1-scoped token (owner-issued) reads granted collections; same enforcement path as human grants.
- **Exception flows:**
  - E1 (out-of-scope request): refusal without existence disclosure (US-051).
  - E2 (revoked token): immediate rejection; cursor state remains valid if the token is re-issued.
- **Postconditions:** consumer state is consistent with the corpus at its cursor; zero tier violations; complete access log.

## 5. Acceptance Criteria

- AC-1: Each use case defines actors, preconditions, trigger, numbered main flow, at least one alternate flow, at least one exception flow, postconditions, and a related feature.
- AC-2: The twelve system-defining flows are present: document batch (UC-001), GitHub repo (UC-002), twin biographical question (UC-003), timeline (UC-004), P0 publish gate (UC-006), P1 grant (UC-007), sealed journal (UC-008), verification queue (UC-009), presentation generation (UC-010), vault export (UC-014), succession activation (UC-015), orchestrated research with approval (UC-011).
- AC-3: Every flow that crosses a privacy boundary contains an explicit enforcement or gate step (UC-003 step 1, UC-006 steps 2-4, UC-007, UC-008 step 4, UC-015, UC-016).
- AC-4: Every flow that touches claims preserves tier semantics (UC-003, UC-006, UC-009, UC-010, UC-011, UC-013, UC-014, UC-016).
- AC-5: Postconditions are stated as verifiable system states usable as integration-test oracles.

## 6. Dependencies

- [USER_PERSONAS](./USER_PERSONAS.md) and [USER_STORIES](./USER_STORIES.md): actors and story-level criteria referenced per flow.
- [FEATURE_SPECIFICATIONS](./FEATURE_SPECIFICATIONS.md): behavioral detail behind each step.
- [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md): agent responsibilities assumed in flows.
- [AUTHORIZATION](../security/AUTHORIZATION.md), [PRIVACY](../security/PRIVACY.md), [AUTHENTICATION](../security/AUTHENTICATION.md): enforcement semantics for tier and grant steps.
- [BACKUP_AND_RECOVERY](../deployment/BACKUP_AND_RECOVERY.md): vault export atomicity assumptions in UC-014.

## 7. Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Flows assume agent capabilities not yet specified | Unimplementable steps | Reconcile against agents and AI specs after first full draft; flows state intent, agent docs state mechanism |
| Succession flow untested until needed | Catastrophic failure at activation | Rehearsal mode requirement: UC-015 must be executable end-to-end in a drill environment ([TESTING](../testing/TESTING.md)) |
| Exception flows undercount real failure modes | Gaps discovered in production | Failure-mode review per release; observability requirements in [OBSERVABILITY](../deployment/OBSERVABILITY.md) |
| Review gates create fatigue and get rubber-stamped | Privacy or provenance regressions | Keep gates few and high-stakes (publish, release, external side effects); batch low-stakes reviews |

## 8. Future Enhancements

- UC pack for mobile capture flows when Android scope opens (post-v1 per [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md) §9).
- Dedicated abuse-case catalog (attacker actor) coordinated with [SECURITY](../security/SECURITY.md).
- Multi-steward succession variants (split-key activation) pending the open question in [USER_PERSONAS](./USER_PERSONAS.md).
- Family onboarding flow (first-session experience for PERS-02) once descendant mode UX is designed.

## 9. Examples

**Trace example, UC-009 on a real seed claim.** Queue item: "RhinoGuardians accepted into HBS Foundry via Aspire Seed Fund" (🔴 per MASTER_CONTEXT §6). Research Agent proposes candidate sources; none authoritative. Owner records "verification failed, keep flagged". Result: twin and portfolio continue to present the claim only as the owner's account; the queue entry shows one completed verification attempt with reviewed sources.

**State example, UC-008 postcondition check.**

```json
{
  "entity": "JournalEntry",
  "tier": "P3",
  "unlock_conditions": [{ "type": "succession_event" }, { "type": "time_lock", "after": "2036-07-02" }],
  "visible_to_search": false,
  "visible_to_agents": false,
  "included_in_exports": ["owner_full_vault_encrypted"]
}
```

## 10. Open Questions

- Should UC-006 require a second reviewer (a trusted collaborator) for high-stakes public claims, or is single-owner review with agent assistance sufficient? Pending owner decision.
- What is the default succession waiting period (candidates: 14 or 30 days)? > TODO(verify): owner decision; interacts with estate-law advice.
- Should UC-016 offer a signed, cacheable public corpus snapshot for machine consumers instead of live-only API reads? Deferred to API and vault spec reconciliation.

## 11. References

- [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md) §0 (tier rules applied in UC-003/009), §6-§7 (seed claims used in examples), §12 (verification queue seed).
- [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md) §4 (UC ID scheme), §5 (tiers), §6 (entities), §7 (agent roster).

## 12. Related Specifications

- [USER_PERSONAS](./USER_PERSONAS.md), [USER_STORIES](./USER_STORIES.md): actors and story criteria.
- [FEATURE_SPECIFICATIONS](./FEATURE_SPECIFICATIONS.md): FS-001 to FS-016 detail behind these flows.
- [MULTI_AGENT_ARCHITECTURE](../agents/MULTI_AGENT_ARCHITECTURE.md), [RAG_PIPELINE](../ai/RAG_PIPELINE.md), [DIGITAL_TWIN](../ai/DIGITAL_TWIN.md): mechanism specs for agent-driven steps.
- [AUTHORIZATION](../security/AUTHORIZATION.md), [PRIVACY](../security/PRIVACY.md): tier enforcement referenced throughout.
- [TESTING](../testing/TESTING.md): integration tests derived from these flows.
