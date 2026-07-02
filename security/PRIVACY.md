# PRIVACY
### Privacy and data governance: tier model, POPIA alignment, data subject rights, LLM data flows, and post-mortem privacy

| Field | Value |
|-------|-------|
| Status | Draft |
| Owner | Linford Musiyambodza |
| Last updated | 2026-07-02 |
| Depends on | [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md), [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md), [SECURITY](./SECURITY.md), [AUTHORIZATION](./AUTHORIZATION.md) |

---

## 1. Purpose

Legacy stores a lifelong personal record: journals, prayer reflections, private conversations, projects, and relationships. This document defines how that data is classified, governed, shared, retained, exported, and eventually released or destroyed. It is the authoritative definition of the privacy tier model (P0 through P3), the platform's alignment with POPIA (the anchor regulation, since the owner operates from Strand, Cape Town, South Africa, a ✅ verified fact in MASTER_CONTEXT section 1), and the handling of third parties whose personal data appears in the knowledge graph.

Privacy here is not a compliance checkbox. Prayer reflections reveal religious belief; journals reveal inner life. The design stance is: the platform must deserve the trust required to hold this data for decades.

## 2. Goals

1. Give every piece of content exactly one privacy tier with unambiguous semantics and safe defaults.
2. Guarantee that content only becomes less restricted through explicit, confirmed Owner action; agents may propose, never apply.
3. Protect third parties (collaborators, mentors, family) whose personal data lives in the graph, with a working removal path.
4. Align with POPIA's eight conditions for lawful processing, using GDPR concepts (portability, erasure) as voluntary guidance where POPIA is silent.
5. Keep P3 content inside the system boundary absolutely: it never reaches an LLM provider and is never included in model context.
6. Define post-mortem privacy: what the Steward may do, what gets released, and what stays sealed forever.

## 3. Scope

**In scope**

- Privacy tier definitions, defaults, and transition rules.
- Data inventory and classification across the knowledge domains.
- Third-party personal data governance and removal workflow.
- Regulatory alignment (POPIA primary, GDPR as guidance).
- Data subject rights workflows: access, correction, erasure, portability.
- LLM provider data flows and the P3 exclusion rule.
- Retention, archival, and post-mortem privacy (sealed release, memorial mode).
- Privacy by design checkpoints in the SDLC.

**Out of scope**

- Enforcement mechanics of tiers at runtime (see [AUTHORIZATION](./AUTHORIZATION.md)).
- Encryption and key hierarchy for sealed content (see [SECURITY](./SECURITY.md)).
- Succession activation authentication (see [AUTHENTICATION](./AUTHENTICATION.md)); this document covers what activation releases, not how it is verified.
- Backup retention mechanics (see [BACKUP_AND_RECOVERY](../deployment/BACKUP_AND_RECOVERY.md)).

## 4. Requirements

Formal cross-repository requirement IDs (the FR-PRIV group) are maintained in [FUNCTIONAL_REQUIREMENTS](../specs/FUNCTIONAL_REQUIREMENTS.md). Identifiers below (PRIV-##) are local anchors.

### 4.1 The privacy tier model in depth

The four tiers are canonical across the repository (defined in [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md) section 5; semantics elaborated here).

| Tier | Name | Definition | Who can see it | Typical content |
|------|------|------------|----------------|-----------------|
| P0 | Public | Published to the public site and the public twin surface | Anyone | Portfolio projects, published articles, talks, public bio facts (✅ tier claims only) |
| P1 | Trusted | Visible to explicitly granted collaborators, mentees, family via scoped Grants | Owner plus Grant holders | Shared project notes, mentorship material, selected lessons |
| P2 | Private | Owner only | Owner (and, after succession activation, the Steward within the configured ceiling) | Journals, prayer reflections, AI conversations, drafts, most `MemoryRecord` rows |
| P3 | Sealed | Time-locked or succession-gated; cryptographically sealed | Nobody, until release conditions are met | Journals or reflections the Owner explicitly seals, letters to family, sensitive entries |

- **PRIV-01 (default).** New content defaults to P2. No ingestion path, agent, or import may create content at P0 or P1 without explicit Owner instruction.
- **PRIV-02 (journals and reflections).** `JournalEntry` records and prayer reflections default to P2 and offer one-action sealing to P3. Sealing is reversible only by the Owner while alive (unsealing is a tier transition and follows PRIV-04).
- **PRIV-03 (single tier).** Every content record carries exactly one tier. Derived artifacts (chunks, embeddings, summaries, memory records) inherit the tier of their most restricted source. A summary that draws on P2 and P1 content is P2.
- **PRIV-04 (transition rule, downward).** Only the Owner may move content to a less restrictive tier, and the action requires an explicit confirmation step that names the item, the old tier, the new tier, and the consequence (for example "this becomes publicly visible"). Bulk downgrades require per-batch confirmation with a listing.
- **PRIV-05 (transition rule, upward).** Moving content to a more restrictive tier takes effect immediately and propagates to derived artifacts within one processing cycle: embeddings are re-tiered, caches invalidated, and any active Grants on the item suspended pending review.
- **PRIV-06 (agents propose, never apply).** Agents (for example the Curation Agent suggesting "this note looks portfolio-worthy, publish?") may create tier-change proposals. A proposal is inert data until the Owner confirms it in the UI. No agent has a tier-write tool. This is enforced by the per-agent tool allowlists in [SECURITY](./SECURITY.md).
- **PRIV-07 (propagation audit).** Every tier transition produces an `AuditLogEntry` recording who, what, old tier, new tier, proposal source if any, and the confirmation event.

### 4.2 Data inventory and classification

Mapping of canonical entities (SPEC_CONVENTIONS section 6) to default tiers and sensitivity notes:

| Domain | Entities | Default tier | Sensitivity notes |
|--------|----------|--------------|-------------------|
| Journals and reflection | `JournalEntry`, `Note` (personal), `Lesson` (personal) | P2, P3 available | Prayer reflections reveal religious belief: special personal information under POPIA section 26. Highest protection class. |
| Conversations | `Conversation` (AI conversations) | P2 | Contains unguarded thinking; never auto-shared. |
| Memory system | `MemoryRecord`, `EmbeddingChunk` | Inherit source tier | Embeddings of P2 content are P2 data; see PRIV-03. |
| Projects and work | `Project`, `Artifact`, `Idea`, `Goal` | P2, promotable to P1/P0 | Portfolio pipeline: draft private, publish deliberately. |
| Knowledge and career | `Skill`, `Certification`, `Achievement`, `Book`, `Talk`, `Article` | P2, many promoted to P0 | Public claims must respect MASTER_CONTEXT confidence tiers: only ✅ claims are published as fact; 🟡 published only with attribution framing; 🔴 not published. |
| People and network | `Person`, `Organization`, `Edge` | P1 ceiling by default (see 4.3) | Third-party personal data: POPIA duties apply to Legacy as responsible party. |
| Provenance | `Claim`, `Source` | Follow subject content | Confidence tier is metadata, not a privacy tier. |
| System | `User`, `Role`, `Grant`, `AuditLogEntry`, `IngestionJob`, `AgentRun` | System-internal | Never exposed publicly; audit data retained per section 4.7. |

### 4.3 Third-party personal data

The knowledge graph names real people: collaborators, mentors, community organizers (MASTER_CONTEXT section 10 lists several, all 🟡 self-reported relationships). These people are data subjects in their own right, and Legacy processes their personal information as the responsible party under POPIA.

- **PRIV-08 (minimal public exposure).** `Person` records for third parties are never published at P0 by default. Public mention of a third party requires an explicit Owner decision per person, limited to professional, already-public facts (for example a conference talk credit).
- **PRIV-09 (consent posture).** For P1 sharing that exposes a third party's data to other Grant holders, the default posture is: professional collaboration facts may be shared within the trusted circle; personal observations about a third party (for example notes about a friend's private circumstances) stay P2 regardless of the containing document's tier where technically separable, and the Owner is warned when sharing items that mention third parties.
- **PRIV-10 (removal on request).** Any person named in the graph may request removal. Workflow: request received (email or form), identity plausibility check, Owner review, then within 30 days: P0 references removed or anonymized, P1 exposure revoked, graph record minimized to a non-identifying stub if link integrity requires it, requester notified. The Owner's private memories (P2 journals mentioning the person) are not deleted by third-party request: the lawful-basis analysis for retaining them in a purely personal archive needs legal confirmation.
- **PRIV-11 (lawful basis).** Working assumption: processing third-party data rests on legitimate interest (maintaining a personal and professional archive) for P2 content, and on consent or the data subject's own prior publication for anything exposed at P0/P1.
> TODO(verify): the lawful-basis mapping (POPIA section 11 justifications), the household/personal-activity exclusion question for a single-owner archive, and the special-personal-information analysis all require review by a South African privacy attorney. No legal counsel is currently engaged.

### 4.4 Regulatory alignment

| Aspect | POPIA (primary, binding) | GDPR (guidance, voluntary) |
|--------|--------------------------|----------------------------|
| Why it applies | Owner is based in South Africa (✅); processing occurs there | Not established that GDPR applies; used as a design benchmark |
| Lawful processing | Eight conditions (accountability, processing limitation, purpose specification, further processing limitation, information quality, openness, security safeguards, data subject participation) | Article 5 principles map closely |
| Special data | Section 26: religious beliefs (prayer reflections) and other special personal information require heightened justification | Article 9 analog |
| Breach notification | Section 22: notify Regulator and data subjects as soon as reasonably possible | 72-hour discipline adopted as internal target (see [SECURITY](./SECURITY.md) incident runbook) |
| Erasure | Section 24: correction and deletion rights | Article 17 informs the tombstone design (4.5) |
| Portability | Not an explicit POPIA right | Article 20 informs the Legacy Vault export (4.5) |
| Deceased persons | POPIA covers living natural persons; owner's own data likely falls outside POPIA after death, but third parties in the corpus remain protected | Member-state specific; not relied upon |

> TODO(verify): whether Legacy, operated by its sole data subject for personal purposes, falls partly under POPIA's personal/household activity exclusion, and what changes once trusted users or a public twin are served. Attorney review required; treat full POPIA compliance as the design target regardless.
> TODO(verify): whether registration or notification obligations with the Information Regulator apply (for example prior authorization scenarios under POPIA sections 57 and 58).

### 4.5 Data subject rights workflows

These workflows serve the Owner, trusted users (for their account data), and third parties in the graph.

| Right | Workflow | Notes |
|-------|----------|-------|
| Access | Requester authenticated (or plausibility-checked for graph third parties), report generated listing personal data held, tiers, and sources; delivered within 30 days | For the Owner this is trivially the product itself plus a formal export |
| Correction | Correction request creates a `Claim`-level change with provenance; original preserved in version history with the correction noted | Aligns with the Verification Engine's source discipline |
| Erasure | Tombstone model: the record's content is destroyed, a tombstone remains holding the record ID, deletion timestamp, requester category, and reason code; embeddings and derived chunks are hard-deleted; backups age out per retention schedule and the tombstone list is replayed after any restore | Tombstones prevent silent re-ingestion of erased content |
| Portability | Legacy Vault export: versioned archive (Markdown, JSON, media manifest) of all content the requester is entitled to; for the Owner, the full corpus including sealed items (Owner is always entitled to own data) | Vault format specified in [BACKUP_AND_RECOVERY](../deployment/BACKUP_AND_RECOVERY.md) |
| Objection | Third party may object to processing; handled through the PRIV-10 removal workflow | |

- **PRIV-12.** Erasure MUST propagate to: primary records, embeddings, memory records derived predominantly from the erased content, caches, and search indexes. Restores from backup MUST replay the tombstone list before serving traffic.
- **PRIV-13.** Every rights request and its resolution is audited.

### 4.6 LLM provider data flows

Model calls leave the system boundary to Anthropic (Claude), Google (Gemini), and Groq via the model router ([AI_ARCHITECTURE](../ai/AI_ARCHITECTURE.md)).

**On the record, a binding design decision: P3 (Sealed) content never leaves the system boundary. It is excluded from model context entirely, for every agent, every provider, every purpose. There is no override. P3 content is not embedded, not summarized by hosted models, not used in retrieval. If future functionality requires AI processing of sealed content, that functionality waits for local inference (see Future Enhancements).**

| Data category | May be sent to providers | Conditions |
|---------------|--------------------------|------------|
| P0 content | Yes | None beyond logging |
| P1 content | Yes | Only in sessions of principals entitled to it; minimized to what the task needs |
| P2 content | Yes, Owner sessions only | Data minimization at context assembly; per-request logging of what categories left the boundary |
| P3 content | Never | Hard exclusion at the retrieval layer and re-checked at the model router (defense in depth) |
| Credentials, secrets, keys | Never | Router-level pattern filter as backstop |
| Third-party `Person` details | Minimized | Only when the task requires them |

- **PRIV-14.** Provider accounts MUST be configured for zero data retention and no training on inputs wherever the provider offers it; where unavailable, that provider is restricted to P0/P1 workloads.
- **PRIV-15.** The model router logs, per request: provider, model, purpose, invoking principal, and the highest tier present in context. Content itself is not duplicated into logs.
> TODO(verify): review current data processing terms, retention windows, and training-use policies for the Anthropic API, Google Gemini API, and Groq API; record findings and account settings per provider. Not yet done; treat all providers as retaining data until verified.

### 4.7 Retention and archival

| Data class | Retention | Rationale |
|------------|-----------|-----------|
| Corpus content (all tiers) | Indefinite, lifelong by design | The product is a legacy archive; deletion only by Owner action or rights workflow |
| Tombstones | Indefinite | Needed to keep erasure durable across restores |
| Audit log: security events | 7 years proposed | Breach forensics and dispute evidence |
| Audit log: routine reads | 1 year detailed, then aggregated | Cost control (see [SECURITY](./SECURITY.md) risks) |
| Ingestion raw originals | Indefinite, cold storage after 1 year | Provenance: sanitized working copies derive from them |
| Session and telemetry data | 90 days | Operational only |
| Backups | Per [BACKUP_AND_RECOVERY](../deployment/BACKUP_AND_RECOVERY.md); encrypted, tombstone-replay on restore | |

> TODO(verify): retention numbers above are proposed defaults, not legal minima or maxima; confirm against POPIA's retention condition (records kept no longer than necessary for the purpose, with the personal-archive purpose being lifelong by definition).

### 4.8 Post-mortem privacy

This section is a design proposal; its legal mechanics are unverified.

- **Sealed content release conditions.** Each P3 item carries a release rule chosen at sealing time: `release_on_succession`, `release_at_date`, `release_to_named_person`, or `never_release` (destroy on death). Default: `never_release`. The release engine evaluates rules only after succession activation ([AUTHENTICATION](./AUTHENTICATION.md)).
- **Steward duties.** The Steward, post-activation, operates under a configured ceiling (see [AUTHORIZATION](./AUTHORIZATION.md)): administer the platform, execute release rules as written, honor third-party removal requests, and refrain from reading anything the rules do not release. Duties are documented in a steward handbook artifact maintained by the Owner.
- **Memorial mode.** A platform state activated during succession: the public site gains a memorial notice, the Twin Agent either switches to a clearly-labeled memorial persona (answers about the Owner in third person, from P0 content, with provenance) or is disabled entirely, per the Owner's pre-recorded choice; ingestion stops; trusted-user Grants are frozen pending Steward review.
- **Third parties after the Owner's death.** POPIA protection of the Owner's own data likely lapses (living persons only), but every third party in the corpus remains a protected data subject; the Steward inherits the removal-workflow duty.
> TODO(verify): the entire post-mortem framework (validity of release instructions, steward's legal standing, interaction with a will and South African estate law) requires an estate attorney. No such counsel exists yet. Until verified, this section is a product design, not a legal instrument, and the Owner's will should reference it explicitly.

### 4.9 Privacy by design checkpoints

| SDLC stage | Checkpoint |
|------------|------------|
| Spec | Any new feature spec declares data touched, tiers involved, and third-party exposure; a "privacy impact" subsection is mandatory for features touching P2+ |
| Design review | Verify defaults (P2), agent propose-only rule, and P3 exclusion are unaffected |
| Implementation gate | CI checks from [CI_CD](../deployment/CI_CD.md): authorization regression suite includes tier tests |
| Pre-release | For features expanding data flows to providers: PRIV-14/PRIV-15 review |
| Periodic | Quarterly privacy review alongside the access review in [AUTHORIZATION](./AUTHORIZATION.md): sample audit logs, verify tombstone replay, re-check provider settings |

## 5. Acceptance Criteria

1. Creating content through every ingestion path without an explicit tier yields P2, verified by automated tests per path.
2. No API, agent tool, or background job can lower a tier; only the Owner-confirmation flow can, and the attempt without confirmation is denied and audited.
3. A sealed (P3) item is absent from: retrieval candidates, model router payloads, embeddings jobs, and exports by non-Owner principals; verified by an integration test that plants a canary P3 document and asserts zero egress.
4. Tier upgrades propagate to derived artifacts within one processing cycle in tests.
5. The erasure workflow removes content and derived data, leaves a tombstone, and a backup-restore test replays tombstones successfully.
6. A Legacy Vault export round-trips: exported corpus re-imports with tiers, provenance, and structure intact.
7. The third-party removal workflow completes end to end in a staging exercise within the 30-day window.
8. Provider accounts show verified retention/training settings, or the affected provider is restricted per PRIV-14.
9. Memorial mode, when simulated in staging, freezes Grants, stops ingestion, and switches or disables the twin per configuration.
10. Every TODO(verify) here is tracked in section 10.

## 6. Dependencies

- [AUTHORIZATION](./AUTHORIZATION.md): runtime enforcement of tiers and ceilings.
- [SECURITY](./SECURITY.md): envelope encryption for P3, incident notification duty, agent tool allowlists.
- [AUTHENTICATION](./AUTHENTICATION.md): succession activation that gates post-mortem workflows.
- [RAG_PIPELINE](../ai/RAG_PIPELINE.md) and [MEMORY_SYSTEM](../memory/MEMORY_SYSTEM.md): tier inheritance for chunks, embeddings, and memory records.
- [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md): tier column semantics, tombstones, Grant and audit structures.
- [BACKUP_AND_RECOVERY](../deployment/BACKUP_AND_RECOVERY.md): Legacy Vault format, tombstone replay on restore.
- [DIGITAL_TWIN](../ai/DIGITAL_TWIN.md): memorial persona behavior.

## 7. Risks

| Risk | Notes | Mitigation direction |
|------|-------|----------------------|
| Legal assumptions wrong | POPIA analysis and post-mortem mechanics are unreviewed by counsel | TODOs tracked; design to the stricter reading; engage counsel before serving external users |
| Tier inheritance bugs leak P2 via derivatives | Summaries, embeddings, and memory records are easy to mis-tier | PRIV-03 tests, canary documents, derived-artifact re-tiering jobs |
| Third-party harm from Owner's own notes | Even P2 journals can harm others if breached | Encryption posture in [SECURITY](./SECURITY.md); minimization warnings (PRIV-09) |
| Provider policy drift | Retention terms change silently | Scheduled DPA re-review, router-level restriction switch per provider |
| Sealed-forever regret | `never_release` destroys content the family might have wanted | Sealing UI explains consequences; Owner can revise rules while alive |
| Steward overreach post-mortem | Nobody supervises the Steward after activation | Ceiling below P3-by-default, release rules evaluated by the system not the Steward, immutable audit |

## 8. Future Enhancements

- Local or self-hosted inference tier so P2 (and eventually P3, Owner-live only) content can be processed without leaving the boundary.
- Differential exposure for the public twin: automated redaction suggestions when promoting content to P0.
- Third-party consent ledger: recorded consent events per `Person` for P1 exposure.
- Formal Data Protection Impact Assessment template once counsel is engaged.
- Per-item release rules with multi-party conditions (for example release to a named person only after a second condition).

## 9. Examples

Agent tier-change proposal (inert until Owner confirms, per PRIV-06):

```json
{
  "proposal_id": "tcp_0031",
  "created_by": "agent:curation",
  "item": "note_7f21",
  "current_tier": "P2",
  "proposed_tier": "P0",
  "rationale": "Polished write-up of the CyberBuddy GDG talk (verified public event); portfolio candidate.",
  "third_party_mentions": ["person_jessica_randall"],
  "warning": "Item mentions a third party; review PRIV-08 before publishing.",
  "status": "pending_owner_confirmation"
}
```

Tombstone left after erasure (PRIV-12):

```json
{
  "tombstone_id": "tmb_0202",
  "erased_record": "person_note_5510",
  "record_type": "Note",
  "erased_at": "2026-07-02T09:14:00Z",
  "requester_category": "third_party_data_subject",
  "reason_code": "removal_request",
  "derived_artifacts_deleted": 14,
  "replay_required_on_restore": true
}
```

Sealing flow, narrative example: the Owner writes a prayer reflection (created at P2 by default), taps "Seal", chooses `release_on_succession` with recipient "family", confirms the consequence text, and the item is envelope-encrypted under the Sealed KEK ([SECURITY](./SECURITY.md)). From that moment it is invisible to retrieval, agents, exports by others, and every LLM provider.

## 10. Open Questions

1. Lawful basis mapping and the personal/household exclusion under POPIA: attorney review needed. (4.3, 4.4)
2. Information Regulator registration or prior-authorization obligations. (4.4)
3. Retention numbers versus POPIA's necessity condition. (4.7)
4. Legal force of release rules and steward standing under South African estate law; coordination with the Owner's will. (4.8)
5. Provider data processing terms for Anthropic, Google, Groq: unreviewed. (4.6)
6. Should erased third-party references also be scrubbed from the Owner's raw ingestion originals, or does provenance win? Owner decision pending.

## 11. References

- POPIA: Protection of Personal Information Act 4 of 2013, notably sections 8 to 25 (conditions), 26 to 27 (special personal information), 22 (notification), 23 to 24 (access and correction).
- GDPR articles 17 (erasure) and 20 (portability), used as voluntary design guidance only.
- [MASTER_CONTEXT](../knowledge/MASTER_CONTEXT.md): section 1 (Cape Town base, ✅), section 10 (named third parties, 🟡), section 0 (confidence tiers used for publication decisions).
- [SPEC_CONVENTIONS](../docs/SPEC_CONVENTIONS.md) section 5 (canonical tiers) and section 6 (canonical entities).

## 12. Related Specifications

- [SECURITY](./SECURITY.md), [AUTHENTICATION](./AUTHENTICATION.md), [AUTHORIZATION](./AUTHORIZATION.md)
- [RAG_PIPELINE](../ai/RAG_PIPELINE.md), [MEMORY_SYSTEM](../memory/MEMORY_SYSTEM.md), [DIGITAL_TWIN](../ai/DIGITAL_TWIN.md), [AI_ARCHITECTURE](../ai/AI_ARCHITECTURE.md)
- [DATABASE_SCHEMA](../database/DATABASE_SCHEMA.md), [API_SPECIFICATION](../api/API_SPECIFICATION.md)
- [BACKUP_AND_RECOVERY](../deployment/BACKUP_AND_RECOVERY.md), [CI_CD](../deployment/CI_CD.md)
- [KNOWLEDGE_GRAPH](../knowledge/KNOWLEDGE_GRAPH.md)
